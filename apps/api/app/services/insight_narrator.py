"""Weekly Owner Insight Narrative Service (Step 14.3).

Generates grounded 2-3 sentence executive briefs for the warehouse owner summarizing
past-week sales velocity, top movers, reorder risks, and dead stock capital.
Features Groq LLM integration with fallback to deterministic rule-based template engine
and 7-day response caching.
"""

import json
import logging
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from typing import Any

from app.models.retailer import SalesOrder, SOStatusEnum
from app.repositories.interfaces.sales_order_repository import SalesOrderRepositoryInterface
from app.schemas.analytics import WeeklyInsightMetrics, WeeklyInsightResponse
from app.services.dead_stock_service import DeadStockService
from app.services.reorder_suggestion_service import ReorderSuggestionService

logger = logging.getLogger(__name__)


class InsightNarratorService:
    """Domain service compiling weekly executive intelligence summaries for warehouse owners."""

    def __init__(
        self,
        so_repo: SalesOrderRepositoryInterface,
        reorder_service: ReorderSuggestionService,
        dead_stock_service: DeadStockService,
        groq_api_key: str = "",
        groq_model: str = "llama-3.3-70b-versatile",
        cache_ttl_days: int = 7,
    ) -> None:
        self.so_repo = so_repo
        self.reorder_service = reorder_service
        self.dead_stock_service = dead_stock_service
        self.groq_api_key = groq_api_key.strip()
        self.groq_model = groq_model
        self.cache_ttl_days = max(int(cache_ttl_days), 1)
        self._cached_insight: WeeklyInsightResponse | None = None

    def get_weekly_insight(self, force_refresh: bool = False) -> WeeklyInsightResponse:
        """Fetch or generate the 7-day grounded executive insight."""
        now = datetime.now(UTC)

        # Check cache if not forcing fresh recalculation
        if (
            not force_refresh
            and self._cached_insight is not None
            and now < self._cached_insight.expires_at
        ):
            # Return cached response with is_cached=True
            return WeeklyInsightResponse(
                headline=self._cached_insight.headline,
                narrative=self._cached_insight.narrative,
                metrics_summary=self._cached_insight.metrics_summary,
                generated_at=self._cached_insight.generated_at,
                expires_at=self._cached_insight.expires_at,
                is_ai_generated=self._cached_insight.is_ai_generated,
                is_cached=True,
            )

        # 1. Compile grounded metrics from actual repository & analytics services
        metrics = self._compile_weekly_metrics(now)

        # 2. Generate narrative using Groq LLM (if configured) or deterministic template fallback
        headline, narrative, is_ai = self._generate_narrative(metrics)

        expires_at = now + timedelta(days=self.cache_ttl_days)

        insight = WeeklyInsightResponse(
            headline=headline,
            narrative=narrative,
            metrics_summary=metrics,
            generated_at=now,
            expires_at=expires_at,
            is_ai_generated=is_ai,
            is_cached=False,
        )

        self._cached_insight = insight
        return insight

    def _compile_weekly_metrics(self, now: datetime) -> WeeklyInsightMetrics:
        """Query and compute grounded operational metrics across trailing 7 days."""
        cutoff = now - timedelta(days=7)

        # Fetch recent orders
        orders, _ = self.so_repo.list_all(limit=1000)
        weekly_orders: list[SalesOrder] = []
        for o in orders:
            o_date = getattr(o, "order_date", None)
            if o_date:
                if o_date.tzinfo is None:
                    o_date = o_date.replace(tzinfo=UTC)
                if o_date >= cutoff:
                    status = getattr(o, "status", None)
                    if status != SOStatusEnum.CANCELLED and status != "cancelled":
                        weekly_orders.append(o)

        weekly_revenue = sum(float(getattr(o, "total_amount", 0.0)) for o in weekly_orders)
        weekly_orders_count = len(weekly_orders)

        confirmed_count = sum(
            1
            for o in weekly_orders
            if getattr(o, "status", "")
            in [
                SOStatusEnum.CONFIRMED,
                SOStatusEnum.PACKED,
                SOStatusEnum.SHIPPED,
                SOStatusEnum.DELIVERED,
                "confirmed",
                "packed",
                "shipped",
                "delivered",
            ]
        )

        # Calculate top mover product
        product_sales: dict[str, dict[str, Any]] = {}
        for o in weekly_orders:
            for item in getattr(o, "items", []):
                p_id = getattr(item, "product_id", None)
                if not p_id:
                    continue
                qty = float(getattr(item, "qty", 0.0))
                p_name = getattr(item, "product_name", None)
                if not p_name and getattr(item, "product", None):
                    p_name = getattr(item.product, "name", None)
                if not p_name:
                    p_name = "Catalog Product"

                if p_id not in product_sales:
                    product_sales[p_id] = {"name": p_name, "qty": 0.0}
                product_sales[p_id]["qty"] += qty

        top_mover_name = None
        top_mover_units = 0.0
        if product_sales:
            best_id = max(product_sales.keys(), key=lambda k: product_sales[k]["qty"])
            top_mover_name = product_sales[best_id]["name"]
            top_mover_units = product_sales[best_id]["qty"]

        # Reorder suggestions count
        try:
            reorder_res = self.reorder_service.get_reorder_suggestions()
            reorder_needed_count = reorder_res.total_suggested_items
        except Exception as err:
            logger.warning("Could not fetch reorder suggestions for weekly insight: %s", err)
            reorder_needed_count = 0

        # Dead stock count and capital
        try:
            dead_stock_res = self.dead_stock_service.get_dead_stock(window_days=90)
            dead_stock_count = dead_stock_res.total_dead_items
            dead_stock_capital = dead_stock_res.total_tied_up_capital
        except Exception as err:
            logger.warning("Could not fetch dead stock for weekly insight: %s", err)
            dead_stock_count = 0
            dead_stock_capital = 0.0

        return WeeklyInsightMetrics(
            weekly_revenue=round(weekly_revenue, 2),
            weekly_orders_count=weekly_orders_count,
            confirmed_orders_count=confirmed_count,
            top_mover_product_name=top_mover_name,
            top_mover_units_sold=round(top_mover_units, 2),
            reorder_needed_count=reorder_needed_count,
            dead_stock_count=dead_stock_count,
            dead_stock_capital=round(dead_stock_capital, 2),
        )

    def _generate_narrative(self, metrics: WeeklyInsightMetrics) -> tuple[str, str, bool]:
        """Generate narrative using Groq LLM or deterministic fallback."""
        if self.groq_api_key:
            try:
                headline, narrative = self._call_groq_llm(metrics)
                return headline, narrative, True
            except Exception as err:
                logger.warning(
                    "Groq API call failed for weekly insight, falling back to deterministic template: %s",
                    err,
                )

        headline, narrative = self._deterministic_template(metrics)
        return headline, narrative, False

    def _call_groq_llm(self, metrics: WeeklyInsightMetrics) -> tuple[str, str]:
        """Call Groq API using JSON mode with strict metrics grounding."""
        system_prompt = (
            "You are the AI warehouse intelligence narrator for WareFlow, an Indian B2B SME inventory platform. "
            "Your task is to produce a concise 2-3 sentence executive weekly briefing for the warehouse owner "
            "based ONLY on the verified operational metrics provided below. "
            "STRICT RULES: Do NOT invent, hallucinate, or assume any facts, dates, or numbers not given. "
            "Always quote INR currency with ₹. Output strictly valid JSON with keys 'headline' (4-8 words) "
            "and 'narrative' (2-3 clear sentences)."
        )

        user_content = (
            f"Verified Trailing 7-Day Metrics:\n"
            f"- Sales Revenue: ₹{metrics.weekly_revenue:,.2f}\n"
            f"- Total Orders: {metrics.weekly_orders_count} ({metrics.confirmed_orders_count} confirmed)\n"
            f"- Top Velocity Item: {metrics.top_mover_product_name or 'N/A'} ({metrics.top_mover_units_sold:g} units sold)\n"
            f"- Stock Replenishment Alerts: {metrics.reorder_needed_count} products below reorder point\n"
            f"- Dead Inventory: {metrics.dead_stock_count} stagnant products (₹{metrics.dead_stock_capital:,.2f} locked capital)\n"
        )

        payload = {
            "model": self.groq_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
            "max_tokens": 300,
        }

        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Wareflow-InsightNarrator/1.0",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            content = res_data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            headline = parsed.get("headline", "").strip()
            narrative = parsed.get("narrative", "").strip()
            if headline and narrative:
                return headline, narrative
            raise ValueError("Incomplete JSON response from Groq")

    def _deterministic_template(self, metrics: WeeklyInsightMetrics) -> tuple[str, str]:
        """Generate reliable, high quality deterministic narrative when LLM is unavailable."""
        if metrics.weekly_revenue > 0:
            headline = f"Weekly Pulse: ₹{metrics.weekly_revenue:,.0f} Revenue Across {metrics.weekly_orders_count} Orders"
        elif metrics.reorder_needed_count > 0:
            headline = f"Restock Alert: {metrics.reorder_needed_count} Products Require Replenishment"
        else:
            headline = "Weekly Pulse: Stable Inventory & Operations"

        # Sentence 1: Sales velocity
        if metrics.weekly_orders_count > 0:
            s1 = (
                f"Over the trailing 7 days, warehouse operations generated ₹{metrics.weekly_revenue:,.2f} "
                f"across {metrics.weekly_orders_count} orders ({metrics.confirmed_orders_count} confirmed)"
            )
            if metrics.top_mover_product_name:
                s1 += f", led by top velocity item '{metrics.top_mover_product_name}' ({metrics.top_mover_units_sold:g} units sold)."
            else:
                s1 += "."
        else:
            s1 = "No sales orders were registered in the trailing 7 days."

        # Sentence 2: Inventory risk & action
        alerts: list[str] = []
        if metrics.reorder_needed_count > 0:
            alerts.append(f"{metrics.reorder_needed_count} items are currently at or below reorder threshold")
        if metrics.dead_stock_count > 0:
            alerts.append(f"₹{metrics.dead_stock_capital:,.2f} in dormant capital is tied up across {metrics.dead_stock_count} stagnant products")

        if alerts:
            s2 = " Action is advised as " + " and ".join(alerts) + "."
        else:
            s2 = " Stock levels remain healthy across all active catalog products."

        narrative = f"{s1}{s2}"
        return headline, narrative

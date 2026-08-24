"""Scheduled Owner Report Service (Step 16.3).

Compiles and dispatches 1-page Weekly Business Summary PDF and executive alerts
via Email, WhatsApp, and In-App notification channels to Owner and Manager users.
"""

from datetime import datetime, timedelta, timezone
import io
import logging
import uuid
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.repositories.interfaces.business_settings_repository import (
    BusinessSettingsRepositoryInterface,
)
from app.repositories.interfaces.invoice_repository import InvoiceRepositoryInterface
from app.repositories.interfaces.product_repository import (
    ProductRepositoryInterface,
)
from app.repositories.interfaces.profile_repository import ProfileRepository
from app.repositories.interfaces.sales_order_repository import (
    SalesOrderRepositoryInterface,
)
from app.repositories.interfaces.stock_repository import (
    StockRepositoryInterface,
)
from app.schemas.analytics import (
    SendWeeklyReportResponse,
    WeeklyReportData,
    WeeklyReportHighlightItem,
)
from app.services.comparison_service import ComparisonService
from app.services.notification_channels.base import NotificationPayload
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class ScheduledReportService:
    """Compiles weekly business summaries, builds 1-page executive PDFs, and delivers reports."""

    def __init__(
        self,
        sales_order_repo: SalesOrderRepositoryInterface,
        stock_repo: StockRepositoryInterface,
        product_repo: ProductRepositoryInterface,
        invoice_repo: InvoiceRepositoryInterface,
        profile_repo: ProfileRepositoryInterface,
        comparison_service: ComparisonService,
        notification_service: NotificationService,
        business_settings_repo: BusinessSettingsRepositoryInterface | None = None,
    ) -> None:
        self.sales_order_repo = sales_order_repo
        self.stock_repo = stock_repo
        self.product_repo = product_repo
        self.invoice_repo = invoice_repo
        self.profile_repo = profile_repo
        self.comparison_service = comparison_service
        self.notification_service = notification_service
        self.business_settings_repo = business_settings_repo

    def _get_business_name(self) -> str:
        """Fetch business name or return default."""
        if self.business_settings_repo:
            settings = self.business_settings_repo.get_settings()
            if settings and getattr(settings, "business_name", None):
                return str(settings.business_name)
        return "WareFlow Wholesale Logistics"

    def compile_weekly_report_data(
        self, as_of: datetime | None = None
    ) -> WeeklyReportData:
        """Aggregate all metrics for a 7-day period and compile the executive summary."""
        now = as_of or datetime.now(timezone.utc)
        start_7d = now - timedelta(days=7)

        # 1. Period comparisons for 7-day window
        comp_res = self.comparison_service.get_period_comparisons(period="7d", as_of=now)
        rev_metric = comp_res.metrics.get("revenue")
        margin_pct_metric = comp_res.metrics.get("gross_margin_pct")
        stock_val_metric = comp_res.metrics.get("stock_valuation")
        turnover_metric = comp_res.metrics.get("turnover_ratio")
        shrinkage_metric = comp_res.metrics.get("shrinkage_value")

        revenue_inr = rev_metric.current_value if rev_metric else 0.0
        revenue_delta_pct = rev_metric.delta_pct if rev_metric else 0.0
        gross_margin_pct = margin_pct_metric.current_value if margin_pct_metric else 0.0
        gross_margin_delta_pct = margin_pct_metric.delta_pct if margin_pct_metric else 0.0
        stock_valuation_inr = stock_val_metric.current_value if stock_val_metric else 0.0
        turnover_ratio_30d = turnover_metric.current_value if turnover_metric else 0.0
        shrinkage_inr = shrinkage_metric.current_value if shrinkage_metric else 0.0

        # 2. Product cost mapping & low stock count
        products = self.product_repo.list_products(limit=1000)
        product_cost_map: dict[str, float] = {}
        product_name_map: dict[str, str] = {}
        product_sku_map: dict[str, str] = {}
        product_min_stock_map: dict[str, float] = {}

        for p in products:
            p_id = p.id if hasattr(p, "id") else p["id"]
            p_name = p.name if hasattr(p, "name") else p.get("name", "Product")
            p_sku = getattr(p, "sku", "") if hasattr(p, "sku") else p.get("sku", "")
            cost = float(getattr(p, "cost_price", 0.0) if hasattr(p, "cost_price") else p.get("cost_price", 0.0) or 0.0)
            min_stock = float(
                getattr(p, "reorder_point", None)
                or getattr(p, "min_stock_level", None)
                or 10.0
                if hasattr(p, "reorder_point") or hasattr(p, "min_stock_level")
                else (p.get("reorder_point") or p.get("min_stock_level") or 10.0)
            )

            product_cost_map[p_id] = cost
            product_name_map[p_id] = p_name
            product_sku_map[p_id] = p_sku
            product_min_stock_map[p_id] = min_stock

        # Low stock count
        overview_data = self.stock_repo.get_stock_overview_data()
        low_stock_count = 0
        product_on_hand_map: dict[str, float] = {}

        for row in overview_data:
            prod = row.get("product")
            p_id = prod.id if hasattr(prod, "id") else (prod.get("id") if isinstance(prod, dict) else row.get("product_id"))
            on_hand = float(row.get("total_on_hand", 0.0))
            product_on_hand_map[p_id] = on_hand
            min_stk = product_min_stock_map.get(p_id, 10.0)
            if on_hand <= min_stk:
                low_stock_count += 1

        # 3. Fast movers (top revenue in 7d)
        if hasattr(self.sales_order_repo, "list_all"):
            so_res = self.sales_order_repo.list_all(limit=10000)
            all_orders = so_res[0] if isinstance(so_res, tuple) else so_res
        elif hasattr(self.sales_order_repo, "list_sales_orders"):
            all_orders = self.sales_order_repo.list_sales_orders()
        else:
            all_orders = []

        prod_7d_rev: dict[str, float] = {}
        prod_7d_units: dict[str, float] = {}

        for o in all_orders:
            st = (
                o.status.value.upper()
                if hasattr(o.status, "value")
                else str(getattr(o, "status", "")).upper()
            )
            if st in ("DRAFT", "CANCELLED", "VOID"):
                continue
            created = (
                getattr(o, "order_date", None) or getattr(o, "created_at", None)
                if hasattr(o, "order_date") or hasattr(o, "created_at")
                else (o.get("order_date") or o.get("created_at"))
            )
            if not created:
                continue
            if isinstance(created, str):
                try:
                    created = datetime.fromisoformat(created)
                except ValueError:
                    continue
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)

            if start_7d <= created <= now:
                items = o.items if hasattr(o, "items") else o.get("items", [])
                for it in items:
                    p_id = it.product_id if hasattr(it, "product_id") else it.get("product_id")
                    qty = float(
                        getattr(it, "qty", None) or getattr(it, "quantity", None)
                        if hasattr(it, "qty") or hasattr(it, "quantity")
                        else (it.get("qty") or it.get("quantity") or 0.0)
                    )
                    price = float(it.unit_price if hasattr(it, "unit_price") else it.get("unit_price", 0.0))
                    rev = qty * price

                    prod_7d_rev[p_id] = prod_7d_rev.get(p_id, 0.0) + rev
                    prod_7d_units[p_id] = prod_7d_units.get(p_id, 0.0) + qty

        sorted_fast = sorted(prod_7d_rev.items(), key=lambda x: x[1], reverse=True)[:3]
        top_fast_movers = [
            {
                "product_id": pid,
                "name": product_name_map.get(pid, "Unknown SKU"),
                "sku": product_sku_map.get(pid, ""),
                "revenue": round(rev, 2),
                "units": round(prod_7d_units.get(pid, 0.0), 1),
            }
            for pid, rev in sorted_fast
        ]

        # 4. Slow movers / sitting capital (on hand > 0 with 0 sales in 7d)
        slow_candidates = []
        for pid, cost in product_cost_map.items():
            on_hand = product_on_hand_map.get(pid, 0.0)
            units_7d = prod_7d_units.get(pid, 0.0)
            if on_hand > 0 and units_7d == 0:
                tied_capital = on_hand * cost
                slow_candidates.append(
                    {
                        "product_id": pid,
                        "name": product_name_map.get(pid, "Unknown SKU"),
                        "sku": product_sku_map.get(pid, ""),
                        "on_hand": on_hand,
                        "tied_up_capital": round(tied_capital, 2),
                    }
                )
        sorted_slow = sorted(slow_candidates, key=lambda x: x["tied_up_capital"], reverse=True)[:3]
        top_slow_movers = sorted_slow

        # 5. Overdue Invoices & AR
        inv_res = self.invoice_repo.list_invoices(page=1, page_size=10000)
        invoices = inv_res[0] if isinstance(inv_res, tuple) else inv_res
        overdue_invoices_count = 0
        overdue_amount_inr = 0.0

        for inv in invoices:
            inv_st = (
                inv.status.value.upper()
                if hasattr(inv.status, "value")
                else str(getattr(inv, "status", "")).upper()
            )
            if inv_st in ("PAID", "CANCELLED", "VOID", "DRAFT"):
                continue

            inv_dt = getattr(inv, "invoice_date", now)
            if isinstance(inv_dt, str):
                try:
                    inv_dt = datetime.fromisoformat(inv_dt)
                except ValueError:
                    inv_dt = now
            if inv_dt and inv_dt.tzinfo is None:
                inv_dt = inv_dt.replace(tzinfo=timezone.utc)

            due_dt = getattr(inv, "due_date", None)
            if due_dt is None and inv_dt:
                due_dt = inv_dt + timedelta(days=30)
            elif isinstance(due_dt, str):
                try:
                    due_dt = datetime.fromisoformat(due_dt)
                except ValueError:
                    due_dt = now

            if due_dt and due_dt.tzinfo is None:
                due_dt = due_dt.replace(tzinfo=timezone.utc)

            is_overdue = inv_st == "OVERDUE" or (due_dt and due_dt < now)

            if is_overdue:
                overdue_invoices_count += 1
                total = float(
                    getattr(inv, "total_amount", 0.0)
                    if hasattr(inv, "total_amount")
                    else inv.get("total_amount", 0.0) or 0.0
                )
                payments = getattr(inv, "payments", []) or []
                paid = sum(
                    float(getattr(p, "amount", 0.0) or 0.0) for p in payments
                )
                overdue_amount_inr += max(0.0, total - paid)

        # 6. Highlights & Narrative
        highlights: list[WeeklyReportHighlightItem] = []
        if top_fast_movers:
            top_m = top_fast_movers[0]
            highlights.append(
                WeeklyReportHighlightItem(
                    title="Top Revenue Driver",
                    description=f"{top_m['name']} generated ₹{top_m['revenue']:,.0f} ({top_m['units']} units) this week.",
                    category="movers",
                    metric_value=f"₹{top_m['revenue']:,.0f}",
                    badge_variant="success",
                )
            )

        if low_stock_count > 0:
            highlights.append(
                WeeklyReportHighlightItem(
                    title="Replenishment Alert",
                    description=f"{low_stock_count} catalog SKU(s) breached minimum safety stock thresholds.",
                    category="low_stock",
                    metric_value=f"{low_stock_count} SKUs",
                    badge_variant="warning",
                )
            )

        if overdue_amount_inr > 0:
            highlights.append(
                WeeklyReportHighlightItem(
                    title="Accounts Receivable Notice",
                    description=f"{overdue_invoices_count} invoice(s) overdue for a total outstanding balance of ₹{overdue_amount_inr:,.0f}.",
                    category="overdue_ar",
                    metric_value=f"₹{overdue_amount_inr:,.0f}",
                    badge_variant="error",
                )
            )

        if shrinkage_inr > 0:
            highlights.append(
                WeeklyReportHighlightItem(
                    title="Shrinkage & Damage Write-off",
                    description=f"₹{shrinkage_inr:,.0f} logged in stock adjustments due to damage or discrepancy.",
                    category="shrinkage",
                    metric_value=f"₹{shrinkage_inr:,.0f}",
                    badge_variant="neutral",
                )
            )

        narrative = (
            f"During the week of {start_7d.strftime('%d %b')} – {now.strftime('%d %b %Y')}, "
            f"WareFlow generated gross revenue of ₹{revenue_inr:,.0f} with an overall gross margin of {gross_margin_pct:.1f}%. "
            f"Total inventory holding valuation stands at ₹{stock_valuation_inr:,.0f}. "
            f"Action items: {low_stock_count} SKU(s) require replenishment and ₹{overdue_amount_inr:,.0f} is overdue across {overdue_invoices_count} invoice(s)."
        )

        report_id = f"REP-{now.strftime('%Y%W')}-{str(uuid.uuid4())[:8].upper()}"

        return WeeklyReportData(
            report_id=report_id,
            start_date=start_7d.strftime("%Y-%m-%d"),
            end_date=now.strftime("%Y-%m-%d"),
            period_label=f"{start_7d.strftime('%d %b')} – {now.strftime('%d %b %Y')}",
            generated_at=now,
            revenue_inr=round(revenue_inr, 2),
            revenue_delta_pct=revenue_delta_pct,
            gross_margin_pct=round(gross_margin_pct, 1),
            gross_margin_delta_pct=gross_margin_delta_pct,
            total_stock_valuation_inr=round(stock_valuation_inr, 2),
            turnover_ratio_30d=turnover_ratio_30d,
            low_stock_count=low_stock_count,
            overdue_invoices_count=overdue_invoices_count,
            overdue_amount_inr=round(overdue_amount_inr, 2),
            shrinkage_inr=round(shrinkage_inr, 2),
            top_fast_movers=top_fast_movers,
            top_slow_movers=top_slow_movers,
            highlights=highlights,
            narrative_summary=narrative,
        )

    def generate_weekly_report_pdf(self, as_of: datetime | None = None) -> bytes:
        """Build a clean, high-density 1-page A4 ReportLab PDF for the owner."""
        data = self.compile_weekly_report_data(as_of=as_of)
        biz_name = self._get_business_name()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#1e1b4b"),
            fontName="Helvetica-Bold",
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#64748b"),
            fontName="Helvetica",
        )
        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#334155"),
            fontName="Helvetica-Bold",
            spaceAfter=4,
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#1e293b"),
            fontName="Helvetica",
        )
        bold_cell = ParagraphStyle(
            "BoldCell",
            parent=body_style,
            fontName="Helvetica-Bold",
        )

        story = []

        # --- 1. Header Banner ---
        story.append(Paragraph(f"<b>{biz_name.upper()}</b>", title_style))
        story.append(Paragraph(f"Weekly Executive Business Summary — Period: {data.period_label} | Report ID: {data.report_id}", subtitle_style))
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4f46e5"), spaceAfter=10))

        # --- 2. Executive KPI Scorecard Grid ---
        story.append(Paragraph("1. Executive Scorecard (7-Day Performance)", section_heading))
        kpi_table_data = [
            [
                Paragraph("<b>Weekly Gross Revenue</b>", bold_cell),
                Paragraph(f"₹{data.revenue_inr:,.0f}", bold_cell),
                Paragraph(f"{'▲ +' if data.revenue_delta_pct >= 0 else '▼ '}{data.revenue_delta_pct:.1f}% vs prior wk", body_style),
                Paragraph("<b>Gross Profit Margin</b>", bold_cell),
                Paragraph(f"{data.gross_margin_pct:.1f}%", bold_cell),
                Paragraph(f"{'▲ +' if data.gross_margin_delta_pct >= 0 else '▼ '}{data.gross_margin_delta_pct:.1f}% vs prior wk", body_style),
            ],
            [
                Paragraph("<b>Total Stock Asset Value</b>", bold_cell),
                Paragraph(f"₹{data.total_stock_valuation_inr:,.0f}", bold_cell),
                Paragraph("Physical on-hand", body_style),
                Paragraph("<b>30d Turnover Ratio</b>", bold_cell),
                Paragraph(f"{data.turnover_ratio_30d:.2f}x", bold_cell),
                Paragraph("Velocity Index", body_style),
            ],
            [
                Paragraph("<b>Overdue AR Balance</b>", bold_cell),
                Paragraph(f"₹{data.overdue_amount_inr:,.0f}", bold_cell),
                Paragraph(f"{data.overdue_invoices_count} overdue invoice(s)", body_style),
                Paragraph("<b>Shrinkage / Damage</b>", bold_cell),
                Paragraph(f"₹{data.shrinkage_inr:,.0f}", bold_cell),
                Paragraph("7-day loss total", body_style),
            ],
        ]
        t_kpis = Table(kpi_table_data, colWidths=[110, 75, 80, 110, 65, 80])
        t_kpis.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("PADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ])
        )
        story.append(t_kpis)
        story.append(Spacer(1, 10))

        # --- 3. Fast Movers vs Slow Movers ---
        story.append(Paragraph("2. Top Product Movers & Capital Distribution", section_heading))
        movers_headers = [
            Paragraph("<b>Top Revenue Movers (Fast)</b>", bold_cell),
            Paragraph("<b>Units Sold</b>", bold_cell),
            Paragraph("<b>Revenue</b>", bold_cell),
            Paragraph("<b>Sitting Stagnant Inventory (Slow)</b>", bold_cell),
            Paragraph("<b>On Hand</b>", bold_cell),
            Paragraph("<b>Tied Capital</b>", bold_cell),
        ]
        movers_rows = [movers_headers]
        for i in range(3):
            fast = data.top_fast_movers[i] if i < len(data.top_fast_movers) else None
            slow = data.top_slow_movers[i] if i < len(data.top_slow_movers) else None
            row = [
                Paragraph(fast["name"] if fast else "—", body_style),
                Paragraph(f"{fast['units']:.0f}" if fast else "—", body_style),
                Paragraph(f"₹{fast['revenue']:,.0f}" if fast else "—", body_style),
                Paragraph(slow["name"] if slow else "—", body_style),
                Paragraph(f"{slow['on_hand']:.0f}" if slow else "—", body_style),
                Paragraph(f"₹{slow['tied_up_capital']:,.0f}" if slow else "—", body_style),
            ]
            movers_rows.append(row)

        t_movers = Table(movers_rows, colWidths=[120, 65, 75, 120, 60, 80])
        t_movers.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e7ff")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("PADDING", (0, 0), (-1, -1), 3.5),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ])
        )
        story.append(t_movers)
        story.append(Spacer(1, 10))

        # --- 4. Operational Highlights & Action Items ---
        story.append(Paragraph("3. Operational Highlights & Actionable Insights", section_heading))
        highlight_rows = []
        for h in data.highlights:
            highlight_rows.append([
                Paragraph(f"• <b>{h.title}</b>", bold_cell),
                Paragraph(h.description, body_style),
                Paragraph(h.metric_value or "", bold_cell),
            ])
        if not highlight_rows:
            highlight_rows.append([Paragraph("No critical alerts logged this period.", body_style), Paragraph("", body_style), Paragraph("", body_style)])

        t_hl = Table(highlight_rows, colWidths=[130, 310, 80])
        t_hl.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("PADDING", (0, 0), (-1, -1), 4),
            ])
        )
        story.append(t_hl)
        story.append(Spacer(1, 10))

        # --- 5. Executive Summary Paragraph ---
        story.append(Paragraph("4. Executive Briefing", section_heading))
        story.append(Paragraph(data.narrative_summary, body_style))
        story.append(Spacer(1, 12))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94a3b8"), spaceAfter=6))
        story.append(Paragraph("Generated automatically by WareFlow Intelligence. For real-time drills, log in to your dashboard at wareflow.com.", subtitle_style))

        doc.build(story)
        return buffer.getvalue()

    def send_weekly_report(
        self,
        as_of: datetime | None = None,
        recipients: list[str] | None = None,
        channels: list[str] | None = None,
    ) -> SendWeeklyReportResponse:
        """Compile report and dispatch via configured channels (Email, WhatsApp, In-App)."""
        target_channels = channels or ["email", "whatsapp", "in_app"]
        data = self.compile_weekly_report_data(as_of=as_of)

        # 1. Identify recipient staff/owners
        if hasattr(self.profile_repo, "list_all"):
            profiles = self.profile_repo.list_all(limit=100)
        elif hasattr(self.profile_repo, "list_profiles"):
            profiles = self.profile_repo.list_profiles()
        else:
            profiles = []

        def get_profile_role(p: Any) -> str:
            if hasattr(p, "role") and p.role and hasattr(p.role, "name"):
                return str(p.role.name).lower()
            if hasattr(p, "role_name"):
                return str(p.role_name or "").lower()
            if isinstance(p, dict):
                return str(p.get("role_name", "")).lower()
            return ""

        owner_profiles = [
            p for p in profiles if get_profile_role(p) in ("owner", "admin", "manager")
        ]

        if not owner_profiles:
            # Fallback to all profiles
            owner_profiles = profiles

        dispatched_channels: list[str] = []
        recipients_reached = 0

        # Build message summary
        summary_msg = (
            f"📊 *WareFlow Weekly Business Summary ({data.period_label})*\n"
            f"• Revenue: ₹{data.revenue_inr:,.0f} ({'+' if data.revenue_delta_pct >= 0 else ''}{data.revenue_delta_pct:.1f}%)\n"
            f"• Gross Margin: {data.gross_margin_pct:.1f}%\n"
            f"• Stock Valuation: ₹{data.total_stock_valuation_inr:,.0f}\n"
            f"• Low Stock Items: {data.low_stock_count}\n"
            f"• Overdue AR: ₹{data.overdue_amount_inr:,.0f} ({data.overdue_invoices_count} invoices)\n\n"
            f"{data.narrative_summary}"
        )

        for prof in owner_profiles:
            u_id = prof.id if hasattr(prof, "id") else prof.get("id")
            email = getattr(prof, "email", None) if hasattr(prof, "email") else prof.get("email")
            phone = getattr(prof, "phone", None) if hasattr(prof, "phone") else prof.get("phone")

            payload = NotificationPayload(
                user_id=u_id,
                type="weekly_report",
                title=f"Weekly Business Summary ({data.period_label})",
                body=summary_msg,
                recipient_email=email,
                recipient_phone=phone,
                metadata={
                    "report_id": data.report_id,
                    "revenue": data.revenue_inr,
                    "margin_pct": data.gross_margin_pct,
                    "low_stock_count": data.low_stock_count,
                    "overdue_ar": data.overdue_amount_inr,
                },
            )

            # Dispatch through NotificationService
            self.notification_service.notify(
                user_id=u_id,
                type=payload.type,
                title=payload.title,
                body=payload.body,
                channels=target_channels,
                recipient_email=email,
                recipient_phone=phone,
                metadata=payload.metadata,
            )
            recipients_reached += 1

        dispatched_channels = list(set(target_channels))

        logger.info(
            "Weekly report %s dispatched to %d recipient(s) across %s",
            data.report_id,
            recipients_reached,
            dispatched_channels,
        )

        return SendWeeklyReportResponse(
            success=True,
            report_id=data.report_id,
            dispatched_at=datetime.now(timezone.utc),
            channels_sent=dispatched_channels,
            recipients_count=recipients_reached,
            summary_text=summary_msg,
        )

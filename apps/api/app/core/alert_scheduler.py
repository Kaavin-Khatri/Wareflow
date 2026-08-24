"""In-process background scheduler for periodic alert evaluation and weekly owner reports (APScheduler)."""

import logging
from collections.abc import Callable
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class AlertScheduler:
    """
    Lightweight, in-process scheduler that executes rule engine scans and weekly owner report summaries.
    Resets on app redeploy (free tier friendly).
    """

    def __init__(
        self,
        alert_engine_factory: Callable[[], Any] | None = None,
        weekly_report_factory: Callable[[], Any] | None = None,
        interval_minutes: int = 30,
    ) -> None:
        self.alert_engine_factory = alert_engine_factory
        self.weekly_report_factory = weekly_report_factory
        self.interval_minutes = interval_minutes
        self._scheduler = BackgroundScheduler(timezone="UTC")
        self._is_running = False

    def _scheduled_job(self) -> None:
        """Scheduled execution callback for smart alert engine."""
        logger.info("Starting scheduled smart alert rule evaluation cycle...")
        if not self.alert_engine_factory:
            logger.warning("No alert engine factory configured for scheduler.")
            return

        try:
            alert_engine = self.alert_engine_factory()
            fired = alert_engine.evaluate_all()
            logger.info("Scheduled alert scan completed. Fired %d new alert(s).", len(fired))
        except Exception as exc:
            logger.error("Error during scheduled alert scan: %s", exc, exc_info=True)

    def _scheduled_weekly_report_job(self) -> None:
        """Scheduled Monday morning weekly executive report callback."""
        logger.info("Executing scheduled Monday morning weekly business summary dispatch...")
        if not self.weekly_report_factory:
            logger.warning("No weekly report factory configured for scheduler.")
            return

        try:
            report_service = self.weekly_report_factory()
            result = report_service.send_weekly_report()
            logger.info("Weekly report successfully dispatched: %s", getattr(result, "report_id", "OK"))
        except Exception as exc:
            logger.error("Error during scheduled weekly report dispatch: %s", exc, exc_info=True)

    @property
    def is_running(self) -> bool:
        """Check whether the background scheduler is currently active."""
        return self._is_running

    def start(self) -> None:
        """Start the background scheduler."""
        if self._is_running:
            return

        try:
            # 1. 30-minute interval smart alert job
            self._scheduler.add_job(
                self._scheduled_job,
                trigger=IntervalTrigger(minutes=self.interval_minutes),
                id="smart_alert_evaluation_job",
                name="Smart Alert Evaluation Job",
                replace_existing=True,
            )

            # 2. Weekly Monday morning executive summary report (02:30 UTC = 08:00 IST)
            if self.weekly_report_factory:
                self._scheduler.add_job(
                    self._scheduled_weekly_report_job,
                    trigger=CronTrigger(day_of_week="mon", hour=2, minute=30, timezone="UTC"),
                    id="weekly_owner_report_job",
                    name="Weekly Owner Summary Report",
                    replace_existing=True,
                )

            self._scheduler.start()
            self._is_running = True
            logger.info("AlertScheduler started (alerts every %d min + weekly report on Mon).", self.interval_minutes)
        except Exception as exc:
            logger.error("Failed to start AlertScheduler: %s", exc)

    def shutdown(self) -> None:
        """Gracefully terminate background scheduler threads."""
        if not self._is_running:
            return

        try:
            self._scheduler.shutdown(wait=False)
            self._is_running = False
            logger.info("AlertScheduler stopped.")
        except Exception as exc:
            logger.warning("Error shutting down AlertScheduler: %s", exc)

    def trigger_now(self) -> list[Any]:
        """Manually trigger an immediate evaluation cycle."""
        if not self.alert_engine_factory:
            return []
        alert_engine = self.alert_engine_factory()
        return alert_engine.evaluate_all()

    def trigger_weekly_report_now(self) -> Any:
        """Manually trigger immediate weekly report compilation and dispatch."""
        if not self.weekly_report_factory:
            return None
        report_service = self.weekly_report_factory()
        return report_service.send_weekly_report()


"""In-process background scheduler for periodic alert evaluation (APScheduler)."""

import logging
from collections.abc import Callable
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class AlertScheduler:
    """
    Lightweight, in-process scheduler that executes rule engine scans on a periodic timer.
    Resets on app redeploy (free tier friendly).
    """

    def __init__(
        self,
        alert_engine_factory: Callable[[], Any] | None = None,
        interval_minutes: int = 30,
    ) -> None:
        self.alert_engine_factory = alert_engine_factory
        self.interval_minutes = interval_minutes
        self._scheduler = BackgroundScheduler(timezone="UTC")
        self._is_running = False

    def _scheduled_job(self) -> None:
        """Scheduled execution callback."""
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

    @property
    def is_running(self) -> bool:
        """Check whether the background scheduler is currently active."""
        return self._is_running

    def start(self) -> None:
        """Start the background scheduler."""
        if self._is_running:
            return

        try:
            self._scheduler.add_job(
                self._scheduled_job,
                trigger=IntervalTrigger(minutes=self.interval_minutes),
                id="smart_alert_evaluation_job",
                name="Smart Alert Evaluation Job",
                replace_existing=True,
            )
            self._scheduler.start()
            self._is_running = True
            logger.info("AlertScheduler started (running every %d minutes).", self.interval_minutes)
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

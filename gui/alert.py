"""
Alert system for notifying users when fire or smoke is detected.

Logic:
    - Counts consecutive frames that contain at least one detection.
    - When the count reaches n_frames AND the cooldown period has elapsed,
      an alarm is triggered and is_alerting is set to True.
    - If a frame has no detections the counter resets to 0.

Usage example::

    alert = AlertSystem()
    for detections in stream:
        if alert.update(detections):
            overlay_warning(frame)
"""

import time

import config


class AlertSystem:
    """
    Stateful alert manager for fire/smoke detection events.

    Parameters
    ----------
    n_frames : int
        Number of consecutive positive frames required before an alert fires.
        Defaults to ``config.ALERT_N_FRAMES``.
    cooldown : float
        Minimum seconds between two consecutive alerts.
        Defaults to ``config.ALERT_COOLDOWN_SEC``.
    """

    def __init__(
        self,
        n_frames: int = config.ALERT_N_FRAMES,
        cooldown: float = config.ALERT_COOLDOWN_SEC,
    ) -> None:
        self.n_frames: int = n_frames
        self.cooldown: float = cooldown

        # Mutable state
        self.counter: int = 0
        self.last_alert_time: float = 0.0   # epoch seconds of the last alarm
        self.is_alerting: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self, detections: list) -> bool:
        """
        Process the detections from the current frame and decide
        whether an alert should be active.

        Parameters
        ----------
        detections : list
            List of detection results from the current frame.
            Any non-empty list is treated as a positive detection.

        Returns
        -------
        bool
            ``True`` if the alert is currently active, ``False`` otherwise.
        """
        if not detections:
            # No detection in this frame → reset streak
            self.counter = 0
            self.is_alerting = False
            return False

        # Positive detection
        self.counter += 1

        # Check whether we have enough consecutive frames
        if self.counter >= self.n_frames:
            now = time.time()
            cooldown_elapsed = (now - self.last_alert_time) >= self.cooldown

            if cooldown_elapsed:
                self.is_alerting = True
                self.last_alert_time = now
                self._trigger_alarm()
                return True

        return self.is_alerting

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _trigger_alarm(self) -> None:
        """Print a console alert message when the alarm threshold is met."""
        print("[ALERT] Fire/Smoke detected!")

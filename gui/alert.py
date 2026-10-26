"""Thread-safe, cancellable Windows sound alerts for consecutive detections."""

import os
import threading
import time

import config

try:
    import winsound as _winsound
except ImportError:
    _winsound = None

_ALARM_WAV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "assets", "alarm.wav")
# PlaySound controls one process-wide sound channel. Serialize all instances.
_AUDIO_LOCK = threading.RLock()
_AUDIO_OWNER = None


class AlertSystem:
    def __init__(self, n_frames=config.ALERT_N_FRAMES,
                 cooldown=config.ALERT_COOLDOWN_SEC):
        self.n_frames = n_frames
        self.cooldown = cooldown
        self.counter = 0
        self.last_alert_time = None
        self.is_alerting = False
        self._active = True

    def update(self, detections: list) -> bool:
        """Count positive frames; a stopped instance can never reactivate."""
        with _AUDIO_LOCK:
            if not self._active:
                return False
            if not detections:
                self.counter = 0
                self.is_alerting = False
                return False
            self.counter += 1
            now = time.monotonic()
            if self.counter >= self.n_frames:
                if (self.last_alert_time is None or
                        now - self.last_alert_time >= self.cooldown):
                    self.is_alerting = True
                    self.last_alert_time = now
                    self._trigger_alarm()
            return self.is_alerting

    def stop(self) -> None:
        """Disable future alerts and immediately cancel this instance's sound."""
        global _AUDIO_OWNER
        with _AUDIO_LOCK:
            self._active = False
            self.counter = 0
            self.is_alerting = False
            if _AUDIO_OWNER is self:
                try:
                    if _winsound is not None:
                        _winsound.PlaySound(None, 0)
                except RuntimeError as exc:
                    print(f"[ALERT] Could not stop sound: {exc}")
                finally:
                    _AUDIO_OWNER = None

    def _trigger_alarm(self) -> None:
        global _AUDIO_OWNER
        # Caller holds _AUDIO_LOCK until playback has been submitted.
        if not self._active:
            return
        print("[ALERT] Fire/Smoke detected!")
        if _winsound is None:
            print("[ALERT] winsound unavailable; audio skipped.")
            return
        # Native async playback returns immediately. NOSTOP refuses to replace
        # a sound still playing, even if the WAV is longer than the cooldown.
        flags = _winsound.SND_ASYNC | _winsound.SND_NOSTOP
        try:
            if os.path.isfile(_ALARM_WAV):
                _winsound.PlaySound(_ALARM_WAV, flags | _winsound.SND_FILENAME)
            else:
                _winsound.PlaySound("SystemExclamation", flags | _winsound.SND_ALIAS)
            _AUDIO_OWNER = self
        except RuntimeError as exc:
            # NOSTOP can reject a request while an existing alarm is playing.
            print(f"[ALERT] Sound request skipped or failed: {exc}")

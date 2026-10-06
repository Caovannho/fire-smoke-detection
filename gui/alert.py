"""
Alert system for notifying users when fire or smoke is detected.

Responsibilities:
    - Display a prominent visual warning overlay on the video canvas
    - Play an audible beep / alarm sound (cross-platform)
    - Write timestamped log entries to alerts.log
    - Throttle repeated alerts to avoid notification spam

Classes planned:
    AlertManager
        __init__(log_path, cooldown_sec)    - Configure logging and cooldown timer
        trigger(label, confidence, frame)   - Fire an alert for a detection event
        reset()                             - Clear active alert state

Functions planned:
    play_beep()             - Cross-platform audio alert (winsound / playsound)
    draw_alert_overlay(frame, label)  - Burn warning text/border onto frame
"""

# TODO: TVx implement


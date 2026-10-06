"""
Main GUI application for real-time fire and smoke detection.

Provides a desktop window that:
    - Displays a live camera feed or video file playback
    - Overlays bounding boxes and labels from the active detector
    - Lets the user switch between Traditional and YOLO detection modes
    - Shows FPS, detection count, and confidence scores in a side panel
    - Triggers alerts via the alert module when fire/smoke is detected

Classes planned:
    App
        __init__(root, config)  - Initialize UI widgets and detector instances
        run()                   - Start the main event loop
        update_frame()          - Grab next frame, run detector, refresh canvas
        toggle_mode(mode)       - Switch between 'traditional' and 'yolo'
        open_file()             - Open a video file via file dialog
        quit()                  - Release resources and close window
"""

# TODO: TVx implement


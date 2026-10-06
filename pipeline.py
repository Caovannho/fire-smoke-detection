"""
End-to-end detection pipeline entry point.

Orchestrates the full workflow:
    1. Load configuration from config.py
    2. Initialize the chosen detector (Traditional or YOLO)
    3. Open input source (webcam index or video file path)
    4. Process frames in a loop:
        a. Preprocess frame
        b. Run detection
        c. Trigger alerts if fire/smoke found
        d. Display annotated frame (optional)
    5. Release resources on exit

Usage:
    python pipeline.py --mode yolo --source 0
    python pipeline.py --mode traditional --source data/videos/test.mp4

Arguments planned:
    --mode      Detection mode: 'traditional' | 'yolo'  (default: yolo)
    --source    Input source: webcam index or video path (default: 0)
    --no-gui    Run headless without display window
    --save      Save annotated output video to disk
"""

# TODO: TVx implement


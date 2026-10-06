"""
YOLO inference wrapper for fire and smoke detection.

Uses the Ultralytics library to load a YOLOv8/v11 model and run
object detection on individual frames or video streams.

Classes planned:
    YOLODetector
        __init__(weights_path, conf_threshold, iou_threshold)
        predict(frame)          - Run inference, return list of Detection objects
        predict_video(path)     - Run inference on a video file, yield frames
        draw_results(frame, detections) - Annotate frame with bounding boxes

Data structures planned:
    Detection(label, confidence, bbox)  - Named tuple for a single detection result
"""

# TODO: TVx implement


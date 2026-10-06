"""
Rule-based fire detection using traditional computer vision techniques.

Approach:
    - HSV color thresholding to isolate fire-colored regions (red/orange/yellow)
    - Morphological operations to filter noise
    - Contour analysis to validate candidate fire regions
    - Optional: flicker detection via frame differencing

Classes planned:
    FireDetector - Stateful detector supporting frame-by-frame inference

Functions planned:
    detect_fire(frame)          - Return bounding boxes of detected fire regions
    classify_fire_region(roi)   - Validate if a region is actual fire
"""

# TODO: TVx implement


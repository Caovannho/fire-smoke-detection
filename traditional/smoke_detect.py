"""
Rule-based smoke detection using traditional computer vision techniques.

Approach:
    - HSV thresholding for gray/white smoke color ranges
    - Optical flow analysis to detect diffuse, rising motion patterns
    - Edge density analysis (smoke has low edge density)
    - Background subtraction to isolate moving smoke regions

Classes planned:
    SmokeDetector - Stateful detector supporting frame-by-frame inference

Functions planned:
    detect_smoke(frame, prev_frame)     - Return bounding boxes of smoke regions
    compute_optical_flow(f1, f2)        - Compute dense optical flow between frames
    classify_smoke_region(roi)          - Validate if a region is actual smoke
"""

# TODO: TVx implement


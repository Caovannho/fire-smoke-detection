"""
Evaluation utilities for comparing detection methods.

Computes standard object detection and classification metrics
and generates comparison reports (tables + charts).

Functions planned:
    compute_iou(box_a, box_b)               - Intersection over Union for two bounding boxes
    compute_precision_recall(tp, fp, fn)    - Precision and recall scalars
    compute_f1(precision, recall)           - F1 score
    compute_map(predictions, ground_truth)  - Mean Average Precision @ IoU thresholds
    measure_fps(detector, frames)           - Average FPS over a list of frames
    evaluate_method(detector, dataset_path) - Full evaluation pipeline, returns metrics dict
    plot_pr_curve(precisions, recalls)      - Draw Precision-Recall curve with matplotlib
    save_report(metrics, output_path)       - Export metrics to CSV / JSON
"""

# TODO: TVx implement


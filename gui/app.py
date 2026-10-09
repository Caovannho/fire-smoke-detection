"""
Main Tkinter GUI application for real-time fire and smoke detection.

Layout (top → bottom):
    ┌─────────────────────────────────────┐
    │  [Nguồn: ________] [Chọn video]    │  ← source_frame
    │  ○ traditional  ○ yolo  ○ combined  │  ← mode_frame
    │  [▶ Bắt đầu]  [⏹ Dừng]  FPS: --   │  ← btn_frame
    │  ┌───────────────────────────────┐  │
    │  │         video canvas          │  │  ← canvas_label
    │  └───────────────────────────────┘  │
    │  Sẵn sàng                           │  ← status_label
    └─────────────────────────────────────┘

Run:
    python gui/app.py
"""

import threading
import time
import tkinter as tk
from tkinter import filedialog, ttk

import cv2
from PIL import Image, ImageTk

import config
from gui.alert import AlertSystem
from pipeline import load_detector, _draw_detection


# ---------------------------------------------------------------------------
# Colour helpers for bbox drawing (mirror pipeline.py constants)
# ---------------------------------------------------------------------------
_BBOX_COLOR = {
    "fire":  (0, 0, 255),
    "smoke": (128, 128, 128),
}
_DEFAULT_COLOR = (0, 255, 0)


class FireSmokeApp:
    """
    Main Tkinter application window for fire/smoke detection.

    Parameters
    ----------
    root : tk.Tk
        The root Tkinter window passed in from __main__.
    """

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(config.WINDOW_TITLE)
        self.root.geometry("900x700")
        self.root.resizable(False, False)

        # Internal state
        self._cap: cv2.VideoCapture | None = None
        self._running: bool = False
        self._thread: threading.Thread | None = None
        self._alert_system = AlertSystem()
        self._fps: float = 0.0
        self._frame_count: int = 0
        self._t_fps: float = time.time()
        self._photo: ImageTk.PhotoImage | None = None  # prevent GC

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Create and arrange all UI widgets."""

        # ── 1. Source frame ──────────────────────────────────────────
        source_frame = tk.Frame(self.root, pady=6, padx=8)
        source_frame.pack(fill=tk.X)

        tk.Label(source_frame, text="Nguồn:", font=("Helvetica", 11)).pack(
            side=tk.LEFT
        )

        self._source_var = tk.StringVar(value="0")
        self._source_entry = tk.Entry(
            source_frame, textvariable=self._source_var,
            width=30, font=("Helvetica", 11)
        )
        self._source_entry.pack(side=tk.LEFT, padx=(4, 8))

        tk.Button(
            source_frame, text="Chọn video",
            command=self._browse_file,
            font=("Helvetica", 11)
        ).pack(side=tk.LEFT)

        # ── 2. Mode frame (radio buttons) ────────────────────────────
        mode_frame = tk.Frame(self.root, pady=4, padx=8)
        mode_frame.pack(fill=tk.X)

        tk.Label(mode_frame, text="Phương pháp:", font=("Helvetica", 11)).pack(
            side=tk.LEFT
        )

        self._method_var = tk.StringVar(value="combined")
        for method in ("traditional", "yolo", "combined"):
            tk.Radiobutton(
                mode_frame,
                text=method,
                variable=self._method_var,
                value=method,
                font=("Helvetica", 11)
            ).pack(side=tk.LEFT, padx=6)

        # ── 3. Button frame ──────────────────────────────────────────
        btn_frame = tk.Frame(self.root, pady=4, padx=8)
        btn_frame.pack(fill=tk.X)

        self._btn_start = tk.Button(
            btn_frame, text="▶ Bắt đầu",
            command=self.start,
            bg="#28a745", fg="white",
            font=("Helvetica", 11, "bold"), width=12
        )
        self._btn_start.pack(side=tk.LEFT, padx=(0, 6))

        self._btn_stop = tk.Button(
            btn_frame, text="⏹ Dừng",
            command=self.stop,
            bg="#dc3545", fg="white",
            font=("Helvetica", 11, "bold"), width=12,
            state=tk.DISABLED
        )
        self._btn_stop.pack(side=tk.LEFT, padx=(0, 16))

        self._fps_label = tk.Label(
            btn_frame, text="FPS: --",
            font=("Helvetica", 11), fg="#555"
        )
        self._fps_label.pack(side=tk.LEFT)

        # ── 4. Video canvas ──────────────────────────────────────────
        canvas_container = tk.Frame(
            self.root, bg="black",
            width=config.FRAME_WIDTH,
            height=config.FRAME_HEIGHT
        )
        canvas_container.pack(pady=6)
        canvas_container.pack_propagate(False)

        self._canvas_label = tk.Label(
            canvas_container, bg="black"
        )
        self._canvas_label.pack(expand=True, fill=tk.BOTH)

        # ── 5. Status bar ────────────────────────────────────────────
        self._status_label = tk.Label(
            self.root,
            text="Sẵn sàng",
            font=("Helvetica", 12, "bold"),
            fg="#333", anchor=tk.W, padx=10
        )
        self._status_label.pack(fill=tk.X, side=tk.BOTTOM)

    # ------------------------------------------------------------------
    # File browser
    # ------------------------------------------------------------------

    def _browse_file(self) -> None:
        """Open a file dialog and set the source entry to the chosen path."""
        path = filedialog.askopenfilename(
            title="Chọn video",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv"),
                ("All files", "*.*"),
            ]
        )
        if path:
            self._source_var.set(path)

    # ------------------------------------------------------------------
    # Start / Stop
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Open the video source, load the detector and launch the frame loop."""
        if self._running:
            return

        raw_source = self._source_var.get().strip()
        source = int(raw_source) if raw_source.isdigit() else raw_source

        self._cap = cv2.VideoCapture(source)
        if not self._cap.isOpened():
            self._set_status(f"❌ Không thể mở nguồn: {source!r}", color="red")
            return

        method = self._method_var.get()
        try:
            self._detector = load_detector(method)
        except Exception as exc:
            self._set_status(f"❌ Lỗi detector: {exc}", color="red")
            self._cap.release()
            return

        self._alert_system = AlertSystem()
        self._running = True
        self._frame_count = 0
        self._t_fps = time.time()
        self._fps = 0.0

        self._btn_start.config(state=tk.DISABLED)
        self._btn_stop.config(state=tk.NORMAL)
        self._set_status("Đang chạy…", color="#007bff")

        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Signal the loop to stop and release the capture device."""
        self._running = False
        if self._cap is not None:
            self._cap.release()
            self._cap = None

        self._btn_start.config(state=tk.NORMAL)
        self._btn_stop.config(state=tk.DISABLED)
        self._set_status("Sẵn sàng", color="#333")
        self._canvas_label.config(image="")

    # ------------------------------------------------------------------
    # Frame loop (runs in background thread)
    # ------------------------------------------------------------------

    def _loop(self) -> None:
        """
        Read frames from the capture device, run detection, draw results,
        update the alert system and refresh the Tkinter canvas.

        This method runs entirely in a daemon thread; all Tkinter updates
        are posted back to the main thread via ``root.after(0, ...)``.
        """
        while self._running:
            if self._cap is None or not self._cap.isOpened():
                break

            ret, frame = self._cap.read()
            if not ret:
                self.root.after(0, lambda: self._set_status(
                    "Kết thúc luồng video.", color="#555"))
                break

            # Resize
            frame = cv2.resize(
                frame,
                (config.FRAME_WIDTH, config.FRAME_HEIGHT)
            )

            # Detection
            try:
                detections = self._detector(frame)
            except Exception:
                detections = []

            # Draw bounding boxes
            for det in detections:
                x, y, w, h, label, score = det
                _draw_detection(frame, x, y, w, h, label, score)

            # Alert system
            alerting = self._alert_system.update(detections)

            # FPS
            self._frame_count += 1
            if self._frame_count % config.FPS_UPDATE_INTERVAL == 0:
                elapsed = time.time() - self._t_fps
                self._fps = (
                    config.FPS_UPDATE_INTERVAL / elapsed if elapsed > 0 else 0.0
                )
                self._t_fps = time.time()
                fps_text = f"FPS: {self._fps:.1f}"
                self.root.after(
                    0, lambda t=fps_text: self._fps_label.config(text=t)
                )

            # Convert BGR → RGB → PIL → ImageTk
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            photo = ImageTk.PhotoImage(image=img)

            # Post UI updates to main thread
            status_text = "🚨 CẢNH BÁO CHÁY KHÓI" if alerting else "✅ Bình thường"
            status_color = "red" if alerting else "#28a745"

            def _update(p=photo, st=status_text, sc=status_color):
                self._photo = p                          # prevent GC
                self._canvas_label.config(image=p)
                self._set_status(st, color=sc)

            self.root.after(0, _update)

        # Cleanup after loop exits
        self.root.after(0, self.stop)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_status(self, text: str, color: str = "#333") -> None:
        """Update the bottom status label (must be called from main thread)."""
        self._status_label.config(text=text, fg=color)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = FireSmokeApp(root)
    root.mainloop()

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

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading
import queue
import time
import tkinter as tk
from tkinter import filedialog, ttk

import cv2
from PIL import Image, ImageTk, ImageOps

import config
from gui.alert import AlertSystem
from pipeline import load_detector, _draw_detection, detect_frame, read_image


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

        self._stop_event = threading.Event()
        self._frames = queue.Queue(maxsize=1)
        self._closing = False
        self._events = queue.Queue()
        self._session = 0
        self._pending_preview = False
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.after(15, self._poll_frames)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Create and arrange all UI widgets."""

        # ── 1. Source frame ──────────────────────────────────────────
        source_frame = tk.Frame(self.root, pady=6, padx=8)
        source_frame.pack(fill=tk.X)

        self._source_type = tk.StringVar(value="Webcam")
        source_kind = ttk.Combobox(
            source_frame, textvariable=self._source_type, state="readonly",
            values=("Webcam", "Video", "Camera IP", "Image"), width=11)
        source_kind.pack(side=tk.LEFT, padx=(0, 6))
        source_kind.bind("<<ComboboxSelected>>", self._source_changed)

        self._source_var = tk.StringVar(value="0")
        self._source_entry = tk.Entry(
            source_frame, textvariable=self._source_var,
            width=25, font=("Helvetica", 11)
        )
        self._source_entry.pack(side=tk.LEFT, padx=(4, 8))

        tk.Button(
            source_frame, text="Chọn video",
            command=self._browse_file,
            font=("Helvetica", 11)
        ).pack(side=tk.LEFT)

        tk.Button(source_frame, text="Chọn ảnh", command=self._browse_image,
                  font=("Helvetica", 11)).pack(side=tk.LEFT, padx=6)

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
                command=self.stop,
                font=("Helvetica", 11)
            ).pack(side=tk.LEFT, padx=6)

        tk.Label(mode_frame, text="Traditional: điểm quy tắc | YOLO: confidence",
                 fg="#555", font=("Helvetica", 9)).pack(side=tk.LEFT, padx=8)

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
        self._btn_image = tk.Button(
            btn_frame, text="Nhận diện ảnh", command=self.detect_image,
            font=("Helvetica", 11), state=tk.DISABLED)
        self._btn_image.pack(side=tk.LEFT, padx=(0, 12))

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
            fg="#333", anchor=tk.W, padx=10, wraplength=870
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
            self._source_type.set("Video")
            self._source_changed()
            self._source_var.set(path)

    def _source_changed(self, event=None):
        self.stop()
        self._pending_preview = False
        self._source_var.set("0" if self._source_type.get() == "Webcam" else "")
        self._refresh_buttons()

    def _browse_image(self):
        path = filedialog.askopenfilename(
            title="Chọn ảnh", filetypes=[("Ảnh", "*.jpg *.jpeg *.png *.bmp")])
        if path:
            self._source_type.set("Image")
            self._source_changed()
            self._source_var.set(path)
            self._pending_preview = True
            if self._thread is None or not self._thread.is_alive():
                self._pending_preview = False
                self._launch("preview")

    # ------------------------------------------------------------------
    # Start / Stop
    # ------------------------------------------------------------------

    def _refresh_buttons(self):
        busy = self._thread is not None and self._thread.is_alive()
        image_mode = self._source_type.get() == "Image"
        self._btn_start.config(state=tk.NORMAL if not busy and not image_mode else tk.DISABLED)
        self._btn_image.config(state=tk.NORMAL if not busy and image_mode else tk.DISABLED)
        self._btn_stop.config(state=tk.NORMAL if busy else tk.DISABLED)

    def start(self) -> None:
        if self._source_type.get() == "Image":
            self.detect_image()
        else:
            self._launch("stream")

    def detect_image(self):
        self._launch("image")

    def _launch(self, task):
        if self._closing or (self._thread is not None and self._thread.is_alive()):
            return
        raw = self._source_var.get().strip()
        source_kind = self._source_type.get()
        if not raw:
            self._set_status("Vui lòng chọn nguồn đầu vào.", color="red")
            return
        if task == "stream" and source_kind == "Webcam" and not raw.isdigit():
            self._set_status("Chỉ số webcam phải là số nguyên không âm.", color="red")
            return
        source = int(raw) if task == "stream" and source_kind == "Webcam" else raw
        self._alert_system.stop()
        self._alert_system = AlertSystem()
        self._stop_event = threading.Event()
        self._frames = queue.Queue(maxsize=1)
        self._events = queue.Queue()
        self._session += 1
        self._running = True
        self._fps_label.config(text="FPS: --")
        self._set_status("Đang xử lý…", color="#007bff")
        self._thread = threading.Thread(
            target=self._worker,
            args=(self._session, task, source, self._method_var.get(),
                  self._alert_system, self._stop_event, self._frames, self._events),
            daemon=True)
        self._thread.start()
        self._refresh_buttons()

    def stop(self) -> None:
        self._running = False
        self._session += 1  # Reject queued frames/errors from the cancelled session.
        self._stop_event.set()
        self._alert_system.stop()
        self._pending_preview = False
        self._canvas_label.config(image="")
        self._photo = None
        self._fps_label.config(text="FPS: --")
        self._set_status("Đang dừng…" if self._thread and self._thread.is_alive()
                         else "Sẵn sàng", color="#333")
        self._refresh_buttons()

    def _close(self) -> None:
        self._closing = True
        self.stop()

    def _show_image(self, image):
        # Fit only the display copy; detector boxes are already in original pixels.
        fitted = ImageOps.contain(image, (config.FRAME_WIDTH, config.FRAME_HEIGHT))
        self._photo = ImageTk.PhotoImage(image=fitted)
        self._canvas_label.config(image=self._photo)

    def _poll_frames(self) -> None:
        """The worker never calls Tk, not even root.after or PhotoImage."""
        try:
            session, image, status, color, fps = self._frames.get_nowait()
        except queue.Empty:
            pass
        else:
            if session == self._session and not self._closing:
                self._show_image(image)
                self._set_status(status, color=color)
                self._fps_label.config(text=f"FPS: {fps:.1f}" if fps is not None else "FPS: --")
        while True:
            try:
                session, status, color = self._events.get_nowait()
            except queue.Empty:
                break
            if session == self._session and not self._closing:
                self._set_status(status, color=color)
        if self._thread is not None and not self._thread.is_alive():
            self._thread = None
            self._running = False
            self._refresh_buttons()
            if self._stop_event.is_set() and not self._closing:
                self._set_status("Sẵn sàng", color="#333")
            if self._pending_preview and not self._closing:
                self._pending_preview = False
                self._launch("preview")
        if self._closing and self._thread is None:
            self.root.destroy()
            return
        self.root.after(15, self._poll_frames)

    @staticmethod
    def _publish(frames, item):
        try:
            frames.get_nowait()
        except queue.Empty:
            pass
        frames.put_nowait(item)

    def _worker(self, session, task, source, method, alerts, stop_event, frames, events):
        """Own all I/O/inference resources until finally; one worker per session."""
        cap = None
        try:
            if task in ("preview", "image"):
                frame = read_image(source)
                if stop_event.is_set():
                    return
                if task == "preview":
                    status, color = "Ảnh xem trước — nhấn Nhận diện ảnh", "#333"
                else:
                    detector = load_detector(method, image_mode=True)
                    if stop_event.is_set():
                        return
                    detections = detect_frame(frame, detector)
                    for x, y, w, h, label, score in detections:
                        _draw_detection(frame, x, y, w, h, label, score)
                    status = (f"{method}: phát hiện {len(detections)} vùng lửa/khói"
                              if detections else "Không phát hiện lửa hoặc khói")
                    color = "red" if detections else "#28a745"
                if not stop_event.is_set():
                    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    self._publish(frames, (session, image, status, color, None))
                    events.put((session, status, color))
                return  # Static images never call alerts.update().

            cap = cv2.VideoCapture(source)
            if not cap.isOpened():
                raise RuntimeError("Không thể mở webcam/video/Camera IP đã chọn.")
            if stop_event.is_set():
                return
            detector = load_detector(method)
            frame_count, fps = 0, 0.0
            t_fps = time.monotonic()
            while not stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    if frame_count == 0:
                        raise RuntimeError("Nguồn đã mở nhưng không đọc được khung hình.")
                    events.put((session, "Kết thúc luồng hoặc mất kết nối nguồn.", "#555"))
                    break
                if stop_event.is_set():
                    break
                detections = detect_frame(frame, detector)
                if stop_event.is_set():
                    break
                for x, y, w, h, label, score in detections:
                    _draw_detection(frame, x, y, w, h, label, score)
                alerting = alerts.update(detections)
                frame_count += 1
                if frame_count % config.FPS_UPDATE_INTERVAL == 0:
                    now = time.monotonic()
                    elapsed = now - t_fps
                    fps = config.FPS_UPDATE_INTERVAL / elapsed if elapsed > 0 else 0.0
                    t_fps = now
                status = ("🚨 CẢNH BÁO CHÁY KHÓI" if alerting else
                          f"{method}: chưa đủ điều kiện cảnh báo ({len(detections)} vùng)"
                          if detections else f"{method}: Không phát hiện lửa hoặc khói")
                image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                self._publish(frames, (session, image, status,
                                      "red" if alerting else "#28a745", fps))
        except Exception as exc:
            if not stop_event.is_set():
                events.put((session, f"Lỗi: {exc}", "red"))
        finally:
            alerts.stop()
            if cap is not None:
                cap.release()

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

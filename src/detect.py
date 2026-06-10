"""
detect.py  —  Day 2: Baseline generic ADAS detection
Uses standard YOLOv8 on a dashcam video with no India-specific logic.

Outputs:
  outputs/baseline_detected.mp4   — annotated video (H.264, browser-ready)
  outputs/baseline_log.json       — detection counts by COCO label

Usage:
  python src/detect.py --video data/input.mp4
  python src/detect.py --video data/input.mp4 --conf 0.35 --device cpu
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

import cv2
from ultralytics import YOLO

# ── project root ──────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH   = PROJECT_ROOT / "yolov8n.pt"
DEFAULT_OUT  = str(PROJECT_ROOT / "outputs")

# ── constants ─────────────────────────────────────────────────────────────
DEFAULT_CONF   = 0.30
FONT           = cv2.FONT_HERSHEY_SIMPLEX
BOX_COLOR      = (55, 138, 221)
TEXT_COLOR     = (255, 255, 255)
BOX_THICKNESS  = 2
FONT_SCALE     = 0.55
FONT_THICKNESS = 1


# ─────────────────────────────────────────────────────────────────────────────
def open_ffmpeg_writer(path: Path, width: int, height: int, fps: float):
    """Return a subprocess writing H.264 MP4 via FFmpeg stdin pipe."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-pix_fmt", "bgr24",
        "-s", f"{width}x{height}",
        "-r", str(fps),
        "-i", "pipe:0",
        "-vcodec", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "23",
        str(path),
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)


def write_frame(proc, frame):
    proc.stdin.write(frame.tobytes())


def close_writer(proc):
    proc.stdin.close()
    proc.wait()


# ─────────────────────────────────────────────────────────────────────────────
def draw_box(frame, x1, y1, x2, y2, label: str, conf: float):
    cv2.rectangle(frame, (x1, y1), (x2, y2), BOX_COLOR, BOX_THICKNESS)
    text = f"{label} {conf:.2f}"
    (tw, th), baseline = cv2.getTextSize(text, FONT, FONT_SCALE, FONT_THICKNESS)
    bg_y1 = max(y1 - th - baseline - 4, 0)
    cv2.rectangle(frame, (x1, bg_y1), (x1 + tw + 4, y1), BOX_COLOR, -1)
    cv2.putText(frame, text, (x1 + 2, y1 - baseline - 2),
                FONT, FONT_SCALE, TEXT_COLOR, FONT_THICKNESS, cv2.LINE_AA)


def draw_hud(frame, frame_idx: int, fps: float, total_det: int):
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (280, 60), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)
    for i, line in enumerate([f"Frame : {frame_idx:>6}",
                               f"FPS   : {fps:>5.1f}",
                               f"Dets  : {total_det:>6}"]):
        cv2.putText(frame, line, (8, 18 + i * 16),
                    FONT, 0.46, (200, 200, 200), 1, cv2.LINE_AA)
    cv2.putText(frame, "GENERIC ADAS (Baseline)",
                (w - 260, h - 10), FONT, 0.5, (80, 138, 180), 1, cv2.LINE_AA)


# ─────────────────────────────────────────────────────────────────────────────
def run(video_path: str, output_dir: str, conf_threshold: float, device: str):
    src = Path(video_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        print(f"[ERROR] Video not found: {src}", file=sys.stderr)
        sys.exit(1)

    has_ffmpeg = shutil.which("ffmpeg") is not None
    if not has_ffmpeg:
        print("[WARN] ffmpeg not found — output may not play in browser. "
              "Install ffmpeg and re-run for best results.")

    print("[Baseline] Loading YOLOv8n …")
    model = YOLO(str(MODEL_PATH))
    model.to(device)

    cap = cv2.VideoCapture(str(src))
    if not cap.isOpened():
        print(f"[ERROR] Cannot open video: {src}", file=sys.stderr)
        sys.exit(1)

    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    in_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total  = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    out_vid = out / "baseline_detected.mp4"

    if has_ffmpeg:
        writer     = open_ffmpeg_writer(out_vid, width, height, in_fps)
        write_fn   = lambda f: write_frame(writer, f)
        release_fn = lambda:   close_writer(writer)
    else:
        writer     = cv2.VideoWriter(str(out_vid),
                                     cv2.VideoWriter_fourcc(*"mp4v"),
                                     in_fps, (width, height))
        write_fn   = lambda f: writer.write(f)
        release_fn = lambda:   writer.release()

    detection_counts: dict[str, int] = defaultdict(int)
    frame_idx = 0
    t0 = time.time()

    print(f"[Baseline] Processing {total} frames at {in_fps:.1f} fps …")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1
        results = model(frame, conf=conf_threshold, verbose=False)[0]

        for box in results.boxes:
            cls_id = int(box.cls[0])
            label  = model.names[cls_id]
            conf   = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            detection_counts[label] += 1
            draw_box(frame, x1, y1, x2, y2, label, conf)

        elapsed  = time.time() - t0
        live_fps = frame_idx / elapsed if elapsed > 0 else 0
        draw_hud(frame, frame_idx, live_fps, sum(detection_counts.values()))
        write_fn(frame)

        if frame_idx % 30 == 0 or frame_idx == total:
            pct = frame_idx / total * 100 if total else 0
            print(f"  {frame_idx}/{total} ({pct:.0f}%)  live_fps={live_fps:.1f}")

    cap.release()
    release_fn()

    log = {
        "source_video":     str(src),
        "total_frames":     frame_idx,
        "total_detections": sum(detection_counts.values()),
        "detection_counts": dict(sorted(detection_counts.items(), key=lambda x: -x[1])),
        "conf_threshold":   conf_threshold,
        "device":           device,
    }
    log_path = out / "baseline_log.json"
    log_path.write_text(json.dumps(log, indent=2))

    print(f"\n[Baseline] ✓ Done")
    print(f"  Video : {out_vid}")
    print(f"  Log   : {log_path}")
    for label, cnt in list(log["detection_counts"].items())[:8]:
        print(f"    {label:<25} {cnt:>6}")


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Baseline ADAS detection (generic COCO)")
    ap.add_argument("--video",  required=True,                    help="Path to input video")
    ap.add_argument("--output", default=DEFAULT_OUT,              help="Output directory")
    ap.add_argument("--conf",   type=float, default=DEFAULT_CONF, help="Confidence threshold")
    ap.add_argument("--device", default="cpu",                    help="cpu | cuda | mps")
    args = ap.parse_args()
    run(args.video, args.output, args.conf, args.device)
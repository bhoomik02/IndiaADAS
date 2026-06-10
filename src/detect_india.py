"""
detect_india.py  —  Day 2: India-context-aware ADAS detection

Outputs:
  outputs/india_detected.mp4   — annotated video (H.264, browser-ready)
  outputs/india_log.json       — structured log consumed by app.py (Day 3)

Usage:
  python src/detect_india.py --video data/input.mp4
  python src/detect_india.py --video data/input.mp4 --conf 0.30 --device cuda
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

# ── project root anchoring ────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH   = PROJECT_ROOT / "yolov8n.pt"
DEFAULT_OUT  = str(PROJECT_ROOT / "outputs")

sys.path.insert(0, str(Path(__file__).parent))
from india_mapper import (
    DENSE_TW_LABEL,
    DENSE_TW_THRESHOLD,
    DENSE_TW_TIER,
    TIER_CONFIG,
    map_coco_to_india,
)

# ── constants ─────────────────────────────────────────────────────────────
DEFAULT_CONF   = 0.30
FONT           = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE     = 0.52
FONT_THICKNESS = 1
BOX_THICKNESS  = 2
TW_COCO_LABELS = {"motorcycle", "bicycle"}


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
def tier_color(tier: str) -> tuple[int, int, int]:
    return TIER_CONFIG[tier]["color_bgr"]


def draw_india_box(frame, x1, y1, x2, y2, india_label: str, tier: str, conf: float):
    color = tier_color(tier)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, BOX_THICKNESS)
    text = f"{india_label}  {conf:.2f}"
    (tw, th), bl = cv2.getTextSize(text, FONT, FONT_SCALE, FONT_THICKNESS)
    bg_y1 = max(y1 - th - bl - 4, 0)
    cv2.rectangle(frame, (x1, bg_y1), (x1 + tw + 4, y1), color, -1)
    cv2.putText(frame, text, (x1 + 2, y1 - bl - 2),
                FONT, FONT_SCALE, (0, 0, 0), FONT_THICKNESS, cv2.LINE_AA)


def draw_dense_tw_banner(frame, count: int):
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, h - 48), (w, h), (0, 0, 200), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
    msg = f"WARNING: DENSE TWO-WHEELER SWARM ({count} units)"
    (tw, _), _ = cv2.getTextSize(msg, FONT, 0.65, 2)
    cv2.putText(frame, msg, ((w - tw) // 2, h - 16),
                FONT, 0.65, (255, 255, 255), 2, cv2.LINE_AA)


def draw_hud(frame, frame_idx: int, fps: float,
             hud_tier_counts: dict, alerts: int):
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (220, 112), (15, 15, 15), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    lines = [
        (f"Frame    : {frame_idx:>5}", (200, 200, 200)),
        (f"FPS      : {fps:>5.1f}",   (200, 200, 200)),
        (f"Alerts   : {alerts:>5}",   (100, 220, 255)),
        (f"Critical : {hud_tier_counts.get('critical', 0):>5}", tier_color("critical")),
        (f"High     : {hud_tier_counts.get('high', 0):>5}",     tier_color("high")),
        (f"Medium   : {hud_tier_counts.get('medium', 0):>5}",   tier_color("medium")),
    ]
    for i, (text, color) in enumerate(lines):
        cv2.putText(frame, text, (6, 18 + i * 16),
                    FONT, 0.44, color, 1, cv2.LINE_AA)
    h, w = frame.shape[:2]
    cv2.putText(frame, "INDIA ADAS — Context-Aware",
                (w - 268, h - 10), FONT, 0.5, (0, 200, 83), 1, cv2.LINE_AA)


def draw_alert_strip(frame, alerts_this_frame: list[tuple[str, str]]):
    if not alerts_this_frame:
        return
    h, w = frame.shape[:2]
    x0 = w - 264
    for i, (label, tier) in enumerate(alerts_this_frame[:6]):
        y0 = 8 + i * 26
        color = tier_color(tier)
        cv2.rectangle(frame, (x0, y0), (w - 4, y0 + 22), (20, 20, 20), -1)
        cv2.rectangle(frame, (x0, y0), (x0 + 4, y0 + 22), color, -1)
        cv2.putText(frame, label, (x0 + 8, y0 + 15),
                    FONT, 0.44, color, 1, cv2.LINE_AA)


def classify_frame_tier(detections: list[tuple[str, str]]) -> str:
    for t in ["critical", "high", "medium", "low"]:
        if any(tier == t for _, tier in detections):
            return t
    return "low"


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
        print("[WARN] ffmpeg not found — output may not play in browser.")

    print("[India ADAS] Loading YOLOv8n …")
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

    out_vid = out / "india_detected.mp4"

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

    tier_counts:        dict[str, int] = defaultdict(int)
    india_label_counts: dict[str, int] = defaultdict(int)
    hud_tier_counts:    dict[str, int] = defaultdict(int)
    total_alerts = 0
    frame_idx    = 0
    t0           = time.time()

    print(f"[India ADAS] Processing {total} frames at {in_fps:.1f} fps …")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1
        results = model(frame, conf=conf_threshold, verbose=False)[0]

        frame_detections: list[tuple[str, str]] = []
        tw_count = 0

        for box in results.boxes:
            cls_id     = int(box.cls[0])
            coco_label = model.names[cls_id].lower()
            conf       = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            india_label, tier = map_coco_to_india(coco_label)
            if coco_label in TW_COCO_LABELS:
                tw_count += 1

            frame_detections.append((india_label, tier))
            india_label_counts[india_label] += 1
            draw_india_box(frame, x1, y1, x2, y2, india_label, tier, conf)

        is_dense_tw = tw_count >= DENSE_TW_THRESHOLD
        if is_dense_tw:
            frame_detections.append((DENSE_TW_LABEL, DENSE_TW_TIER))
            india_label_counts[DENSE_TW_LABEL] += 1
            draw_dense_tw_banner(frame, tw_count)

        frame_tier = classify_frame_tier(frame_detections)
        tier_counts[frame_tier]     += 1
        hud_tier_counts[frame_tier] += 1

        if frame_tier in ("critical", "high"):
            total_alerts += 1

        high_prio = [(lbl, t) for lbl, t in frame_detections
                     if t in ("critical", "high")]
        draw_alert_strip(frame, high_prio)

        elapsed  = time.time() - t0
        live_fps = frame_idx / elapsed if elapsed > 0 else 0
        draw_hud(frame, frame_idx, live_fps, hud_tier_counts, total_alerts)
        write_fn(frame)

        if frame_idx % 30 == 0 or frame_idx == total:
            pct = frame_idx / total * 100 if total else 0
            print(f"  {frame_idx}/{total} ({pct:.0f}%)  fps={live_fps:.1f}  alerts={total_alerts}")

    cap.release()
    release_fn()

    log = {
        "source_video":      str(src),
        "total_frames":      frame_idx,
        "total_alerts":      total_alerts,
        "tier_counts":       dict(tier_counts),
        "india_label_counts": dict(sorted(india_label_counts.items(), key=lambda x: -x[1])),
        "conf_threshold":    conf_threshold,
        "device":            device,
    }
    log_path = out / "india_log.json"
    log_path.write_text(json.dumps(log, indent=2))

    print(f"\n[India ADAS] ✓ Done")
    print(f"  Video  : {out_vid}")
    print(f"  Log    : {log_path}")
    for tier in ["critical", "high", "medium", "low"]:
        cnt = tier_counts.get(tier, 0)
        pct = cnt / frame_idx * 100 if frame_idx else 0
        print(f"    {tier:<10} {cnt:>6} frames  ({pct:.1f}%)")


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="India-context-aware ADAS detection")
    ap.add_argument("--video",  required=True,                    help="Path to input video")
    ap.add_argument("--output", default=DEFAULT_OUT,              help="Output directory")
    ap.add_argument("--conf",   type=float, default=DEFAULT_CONF, help="Confidence threshold")
    ap.add_argument("--device", default="cpu",                    help="cpu | cuda | mps")
    args = ap.parse_args()
    run(args.video, args.output, args.conf, args.device)
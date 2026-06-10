"""
india_mapper.py  —  Day 2: COCO → India-specific label mapping + risk tier config
Imported by both detect_india.py and app.py (Day 3).
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# TIER CONFIG
# Each tier: (display_name, hex_color, priority_int)
# Priority 1 = highest urgency (triggers emergency brake / loudest alert)
# ─────────────────────────────────────────────────────────────────────────────
TIER_CONFIG: dict[str, dict] = {
    "critical": {
        "label":    "CRITICAL",
        "color_bgr": (0, 0, 255),       # red in BGR
        "color_hex": "#ff4444",
        "priority": 1,
        "description": "Immediate collision / fatality risk",
    },
    "high": {
        "label":    "HIGH",
        "color_bgr": (0, 140, 255),     # orange in BGR
        "color_hex": "#ff8c00",
        "priority": 2,
        "description": "High-risk road user or behaviour",
    },
    "medium": {
        "label":    "MEDIUM",
        "color_bgr": (0, 215, 255),     # gold in BGR
        "color_hex": "#ffd700",
        "priority": 3,
        "description": "Requires attention / moderate risk",
    },
    "low": {
        "label":    "LOW",
        "color_bgr": (83, 200, 0),      # green in BGR
        "color_hex": "#00c853",
        "priority": 4,
        "description": "Detected and tracked, low immediate risk",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# INDIA LABEL MAP
# Maps COCO class names → (india_display_label, risk_tier)
#
# Indian road context:
#   • Pedestrians jaywalk freely — elevated to CRITICAL
#   • Two-wheelers are everywhere, often overloaded, often no helmet
#   • Cattle (cow, horse, elephant) on roads = CRITICAL hazard
#   • Auto-rickshaws are unique mixed vehicle class
#   • Trucks stop randomly, often without lights at night
# ─────────────────────────────────────────────────────────────────────────────
INDIA_LABEL_MAP: dict[str, tuple[str, str]] = {
    # ── CRITICAL ──────────────────────────────────────────────────────────
    "person":       ("Pedestrian / Jaywalker",        "critical"),
    "cow":          ("Cattle / Buffalo",              "critical"),
    "horse":        ("Cattle / Buffalo",              "critical"),
    "elephant":     ("Cattle / Buffalo",              "critical"),
    "sheep":        ("Cattle / Buffalo",              "critical"),
    "dog":          ("Stray Animal",                  "critical"),
    "cat":          ("Stray Animal",                  "critical"),

    # ── HIGH ──────────────────────────────────────────────────────────────
    "motorcycle":   ("Two-Wheeler (Overload risk)",   "high"),
    "bicycle":      ("Two-Wheeler (Overload risk)",   "high"),

    # ── MEDIUM ────────────────────────────────────────────────────────────
    "car":          ("Car / Auto-Rickshaw",           "medium"),
    "truck":        ("Truck / Goods Vehicle",         "medium"),
    "bus":          ("Bus / Tempo Traveller",         "medium"),
    "van":          ("Bus / Tempo Traveller",         "medium"),

    # ── LOW ───────────────────────────────────────────────────────────────
    "traffic light":("Traffic Signal",               "low"),
    "stop sign":    ("Traffic Signal",               "low"),
    "boat":         ("Boat / Ferry",                 "low"),
    "train":        ("Train / Rail",                 "low"),
    "airplane":     ("Aircraft",                     "low"),

    # ── catch-all: unlisted COCO labels get LOW ───────────────────────────
    "__default__":  ("Other Object",                 "low"),
}


def map_coco_to_india(coco_label: str) -> tuple[str, str]:
    """Return (india_label, tier) for a given COCO class name."""
    return INDIA_LABEL_MAP.get(
        coco_label.lower(),
        INDIA_LABEL_MAP["__default__"]
    )


# ─────────────────────────────────────────────────────────────────────────────
# DENSE TRAFFIC RULE
# If the number of two-wheelers in a single frame exceeds this threshold,
# upgrade the tier to CRITICAL and flag as "Dense Two-Wheeler Traffic"
# ─────────────────────────────────────────────────────────────────────────────
DENSE_TW_THRESHOLD = 4          # ≥4 two-wheelers in one frame → dense swarm
DENSE_TW_LABEL     = "Dense Two-Wheeler Traffic"
DENSE_TW_TIER      = "critical"


# ─────────────────────────────────────────────────────────────────────────────
# COMPARISON TABLE  (used by app.py gap-analysis section)
# Each row: (coco_label, india_label, gap_type)
# gap_type ∈ {Wrong class, Missing context, Missing class,
#             Missing behaviour, Underdetected}
# ─────────────────────────────────────────────────────────────────────────────
COMPARISON_TABLE: list[tuple[str, str, str]] = [
    # Wrong class
    ("person (sidewalk)",   "Pedestrian / Jaywalker",       "Wrong class"),
    ("car",                 "Car / Auto-Rickshaw",          "Wrong class"),
    ("motorcycle",          "Two-Wheeler (Overload risk)",  "Wrong class"),

    # Missing context
    ("motorcycle ×1",       "Dense Two-Wheeler Traffic",    "Missing context"),
    ("person + car close",  "Near-miss alert",              "Missing context"),
    ("truck (night)",       "Truck — no tail lights",       "Missing context"),

    # Missing class
    ("— (not in COCO)",     "Cattle / Buffalo",             "Missing class"),
    ("— (not in COCO)",     "Auto-Rickshaw",                "Missing class"),
    ("— (not in COCO)",     "Stray Animal",                 "Missing class"),
    ("— (not in COCO)",     "Tempo Traveller",              "Missing class"),

    # Missing behaviour
    ("— (static model)",    "Wrong-way driving alert",      "Missing behaviour"),
    ("— (static model)",    "Sudden lane merge",            "Missing behaviour"),

    # Underdetected
    ("person (low conf)",   "Pedestrian in low light",      "Underdetected"),
    ("bicycle (missed)",    "Two-Wheeler in blind spot",    "Underdetected"),
]
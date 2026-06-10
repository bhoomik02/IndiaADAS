# IndiaADAS

IndiaADAS is an experimental Advanced Driver Assistance System (ADAS) prototype designed for Indian road environments.

Most commercial ADAS systems are trained on datasets collected in North America and Europe. While these systems can detect common road objects, they often fail to interpret road situations that are unique to Indian traffic conditions.

IndiaADAS addresses this gap by combining real-time object detection with an India-specific interpretation layer that converts generic detections into contextual risk assessments and driver alerts.

## Problem Statement

Modern ADAS solutions are primarily trained on datasets such as COCO, which contain limited representation of Indian road scenarios.

As a result, traditional systems struggle with:

* Dense two-wheeler traffic
* Overloaded motorcycles
* Pedestrians walking within the carriageway
* Cattle on roads
* Auto-rickshaw-like traffic patterns
* Region-specific traffic behavior

A generic object detector may correctly identify a motorcycle, but it does not understand whether that motorcycle contributes to a high-risk traffic situation.

IndiaADAS focuses on contextual understanding rather than raw detection.

## Key Idea

Instead of building a new detector from scratch, IndiaADAS uses a pretrained YOLOv8 model and adds an interpretation layer that applies India-specific rules and risk logic.

Example:

* Three or more motorcycles in a frame are classified as Dense Two-Wheeler Traffic
* Motorcycles with nearby people may indicate overload risk
* Pedestrians in the roadway are treated as critical hazards
* Cattle automatically trigger emergency alerts

This transforms object detection into actionable driving intelligence.

## Architecture

```text
Video Input
    ↓
YOLOv8 Detection
    ↓
India Mapping Layer
    ↓
Risk Classification
    ↓
Alert Generation
    ↓
Analytics Dashboard
```

### 1. Video Processing

Dashcam footage is processed frame by frame using OpenCV.

### 2. Object Detection

YOLOv8 performs real-time detection and returns:

* Bounding boxes
* Object classes
* Confidence scores

### 3. India Mapping Layer

Custom logic converts generic detections into India-specific categories and driving scenarios.

Examples include:

* Dense Two-Wheeler Traffic
* Overload Risk
* Pedestrian in Carriageway
* Cattle Hazard

### 4. Risk Tiering

Each detection is assigned a risk level:

* Critical
* High
* Medium
* Low

These risk levels drive alert generation and visualization.

### 5. Dashboard & Analytics

Detection results are stored as JSON and visualized through a Streamlit dashboard with:

* Detection statistics
* Risk summaries
* Video comparisons
* Interactive charts

## Technology Stack

* Python
* YOLOv8 (Ultralytics)
* OpenCV
* Streamlit
* Plotly
* JSON

## Repository Structure

```text
IndiaADAS/
│
├── src/
│   ├── detect.py
│   ├── detect_india.py
│   └── india_mapper.py
│
├── outputs/
├── yolov8n.pt
├── app.py
├── requirements.txt
└── README.md
```

## Installation

Clone the repository:

```bash
git clone https://github.com/bhoomik02/IndiaADAS.git
cd IndiaADAS
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the environment:

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Project

Run standard detection:

```bash
python src/detect.py
```

Run India-aware detection:

```bash
python src/detect_india.py
```

Launch the dashboard:

```bash
streamlit run app.py
```

## Why We Chose This Approach

Training a custom model requires:

* Large labeled datasets
* Significant compute resources
* Extensive experimentation

For this prototype, the focus was on solving the contextual understanding problem rather than rebuilding an object detector.

The interpretation layer can be improved, modified, and localized without retraining the underlying model.

## Future Work

* Fine-tuning on the India Driving Dataset (IDD)
* Native auto-rickshaw detection
* Speed breaker detection
* Pothole detection
* Multi-frame object tracking
* Wrong-way vehicle detection
* Night and monsoon condition testing

## Project Vision

IndiaADAS demonstrates that improving ADAS performance in India is not only a detection problem but also a context problem.

By combining proven object detection models with region-specific intelligence, ADAS systems can become safer, more explainable, and better suited to real-world Indian traffic conditions.

## License

MIT License

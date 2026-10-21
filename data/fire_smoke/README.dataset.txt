# Fire-Smoke-Detection-Yolov11 > Smoke-Fire Detection
https://universe.roboflow.com/sayed-gamall/fire-smoke-detection-yolov11

Provided by a Roboflow user
License: CC BY 4.0

# Real-Time Smoke and Fire Detection with YOLOv11

## Overview
This project aims to develop a **real-time smoke and fire detection system** leveraging the power of **YOLOv11**, a state-of-the-art object detection model. By providing **early and accurate** detection of fire and smoke, this system enhances safety measures across various environments, helping to mitigate potential hazards and property damage.

## Dataset
The dataset is a **comprehensive, well-annotated** collection of images containing instances of **fire and smoke** under diverse conditions. It is carefully curated to ensure robustness in model training, validation, and evaluation.

### Classes
- **Fire**
- **Smoke**

### Annotations
Each image is annotated with **precise bounding boxes** around instances of fire and smoke, enabling accurate localization and detection.

### Dataset Distribution
- **Training Set:** 9,156 images
- **Validation Set:** 872 images
- **Test Set:** 435 images

## Key Features
- **Real-Time Detection:** Processes video feeds in real-time, providing **instant alerts** upon detecting fire or smoke.
- **High Accuracy:** Utilizes **YOLOv11’s advanced capabilities** to achieve **robust performance** even in complex conditions.
- **Customizable & Scalable:** The model can be fine-tuned and **adapted to various environments**, making it ideal for applications in **industrial safety, residential monitoring, and surveillance systems.**

## Usage
This dataset is designed for training and evaluating **object detection models** tailored for real-time **fire and smoke detection**. It is suitable for:
- **Surveillance systems** (CCTV monitoring, smart security cameras)
- **Industrial safety applications** (factories, warehouses, refineries)
- **Residential safety solutions** (smart home fire detection)
- **Autonomous monitoring systems** (drones, robotics, IoT devices)

## Installation & Setup
Get started by cloning the dataset from **Roboflow**:

```python
from roboflow import Roboflow
rf = Roboflow(api_key="YOUR_API_KEY")
project = rf.workspace("sayed-gamall").project("fire-smoke-detection-yolov11")
dataset = project.version(2).download("yolov11")
```

## Get Started
1. **Download the dataset** using the above script.
2. **Train your YOLOv11 model** with the dataset.
3. **Deploy the trained model** for real-time fire and smoke detection.
4. **Integrate alerts and notifications** for automated safety monitoring.

This dataset provides a strong foundation for **developing intelligent fire and smoke detection systems** that can significantly improve safety and emergency response times.

---
### 🚀 Ready to Train?
Start building your real-time fire and smoke detection model today with **Roboflow**! 🔥


from ultralytics import YOLO
import os
import torch


# =========================================================
# SETTINGS
# =========================================================

DATASET = "helmet_dataset"

MODEL = "yolo11n-cls.pt"

EPOCHS = 40
IMAGE_SIZE = 224
BATCH_SIZE = 16


# =========================================================
# DEVICE
# =========================================================

if torch.cuda.is_available():
    DEVICE = 0
    print("GPU detected - training on GPU")
else:
    DEVICE = "cpu"
    print("GPU not detected - training on CPU")


# =========================================================
# CHECK DATASET
# =========================================================

required_folders = [
    "helmet_dataset/train/helmet",
    "helmet_dataset/train/no_helmet",
    "helmet_dataset/val/helmet",
    "helmet_dataset/val/no_helmet"
]

for folder in required_folders:

    if not os.path.exists(folder):

        print()
        print("ERROR: Missing folder:")
        print(folder)
        print()

        exit()


# =========================================================
# START TRAINING
# =========================================================

print()
print("==============================================")
print("      INDUSTRIGUARD AI - HELMET TRAINING")
print("==============================================")
print()

print("Classes:")
print("0 = helmet")
print("1 = no_helmet")
print()

print(f"Epochs: {EPOCHS}")
print(f"Image size: {IMAGE_SIZE}")
print(f"Batch size: {BATCH_SIZE}")
print()


# =========================================================
# LOAD CLASSIFICATION MODEL
# =========================================================

print("Loading YOLO classification model...")

model = YOLO(MODEL)

print("Model loaded.")
print()


# =========================================================
# TRAIN
# =========================================================

results = model.train(

    data=DATASET,

    epochs=EPOCHS,

    imgsz=IMAGE_SIZE,

    batch=BATCH_SIZE,

    device=DEVICE,

    workers=0,

    project="runs/classify",

    name="industrialguard_helmet",

    pretrained=True,

    patience=10,

    verbose=True
)


# =========================================================
# RESULT
# =========================================================

print()
print("==============================================")
print("       HELMET TRAINING COMPLETE")
print("==============================================")
print()

print("Your trained model should be here:")

print(
    "runs/classify/industrialguard_helmet/weights/best.pt"
)

print()
import os
import shutil
import random


# =========================================================
# SETTINGS
# =========================================================

SOURCE_DIR = "helmet_dataset/raw"
OUTPUT_DIR = "helmet_dataset"

TRAIN_RATIO = 0.80

CLASSES = [
    "helmet",
    "no_helmet"
]

IMAGE_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png"
)


# =========================================================
# CREATE DIRECTORIES
# =========================================================

for split in ["train", "val"]:

    for class_name in CLASSES:

        os.makedirs(
            os.path.join(
                OUTPUT_DIR,
                split,
                class_name
            ),
            exist_ok=True
        )


# =========================================================
# PROCESS EACH CLASS
# =========================================================

for class_name in CLASSES:

    source_class_dir = os.path.join(
        SOURCE_DIR,
        class_name
    )

    if not os.path.exists(source_class_dir):

        print(
            f"ERROR: Folder not found: "
            f"{source_class_dir}"
        )

        continue


    images = [
        file
        for file in os.listdir(source_class_dir)
        if file.lower().endswith(IMAGE_EXTENSIONS)
    ]


    random.shuffle(images)


    total = len(images)

    train_count = int(
        total * TRAIN_RATIO
    )


    train_images = images[:train_count]

    val_images = images[train_count:]


    print()
    print("=" * 50)
    print(f"CLASS: {class_name}")
    print(f"TOTAL: {total}")
    print(f"TRAIN: {len(train_images)}")
    print(f"VAL: {len(val_images)}")
    print("=" * 50)


    # -----------------------------------------------------
    # COPY TRAIN
    # -----------------------------------------------------

    for image_name in train_images:

        source = os.path.join(
            source_class_dir,
            image_name
        )

        destination = os.path.join(
            OUTPUT_DIR,
            "train",
            class_name,
            image_name
        )

        shutil.copy2(
            source,
            destination
        )


    # -----------------------------------------------------
    # COPY VALIDATION
    # -----------------------------------------------------

    for image_name in val_images:

        source = os.path.join(
            source_class_dir,
            image_name
        )

        destination = os.path.join(
            OUTPUT_DIR,
            "val",
            class_name,
            image_name
        )

        shutil.copy2(
            source,
            destination
        )


print()
print("==========================================")
print(" HELMET DATASET PREPARATION COMPLETE")
print("==========================================")
print()
print("Dataset structure:")
print()
print("helmet_dataset/")
print("├── train/")
print("│   ├── helmet/")
print("│   └── no_helmet/")
print("│")
print("└── val/")
print("    ├── helmet/")
print("    └── no_helmet/")
print()
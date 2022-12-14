from typing import List

import cv2
import torch
import numpy as np
import pandas as pd
import streamlit as st
from streamlit import caching
import matplotlib.colors as mcolors
from PIL import Image

from config import CLASSES_FRUITS, CLASSES_ANIMALS, CLASSES_YOLOV5

st.set_page_config(
    page_title="Statistical Machine Learning - Yolov5",
)

st.title("Statisical Machine Learning - Yolov5")


# Route


@st.cache(allow_output_mutation=True)
def get_yolo5(model_type="s", dataset="yolov5"):
    """
    Load yolov5 model by using torch hub
    """
    # Yolov5 Pretrained

    if dataset == "yolov5":
        return torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True, force_reload=True)
    else:
        # Custom trained
        return torch.hub.load(
            "ultralytics/yolov5", "custom", path="./{}.pt".format(dataset)
        )


@st.cache(max_entries=10)
def get_preds(img: np.ndarray) -> np.ndarray:
    """
    Return the image result
    """
    return model([img]).xyxy[0].numpy()


def get_colors(indexes: List[int]) -> dict:
    """
    Utility for color helper
    """
    to_255 = lambda c: int(c * 255)
    tab_colors = list(mcolors.TABLEAU_COLORS.values())
    tab_colors = [
        list(map(to_255, mcolors.to_rgb(name_color))) for name_color in tab_colors
    ]
    base_colors = list(mcolors.BASE_COLORS.values())
    base_colors = [list(map(to_255, name_color)) for name_color in base_colors]
    rgb_colors = tab_colors + base_colors
    rgb_colors = rgb_colors * 5

    color_dict = {}
    for i, index in enumerate(indexes):
        if i < len(rgb_colors):
            color_dict[index] = rgb_colors[i]
        else:
            color_dict[index] = (255, 0, 0)

    return color_dict


def get_legend_color(class_name: int):
    """
    Color the legend of classes
    """

    index = CLASSES.index(class_name)
    color = rgb_colors[index]
    return "background-color: rgb({color[0]},{color[1]},{color[2]})".format(color=color)


# Load model

CLASSES = []

dataset = st.sidebar.selectbox(
    "Select dataset",
    ("yolov5", "animals", "fruits"),
    index=0,
    format_func=lambda s: s.upper(),
)

print(dataset)

if dataset == "yolov5":
    CLASSES = CLASSES_YOLOV5
elif dataset == "animals":
    CLASSES = CLASSES_ANIMALS
else:
    CLASSES = CLASSES_FRUITS


with st.spinner("Loading the model..."):

    model = get_yolo5(model_type="s", dataset=dataset)
st.success("Loading the model.. Done!")


# UI elements
# sidebar
prediction_mode = st.sidebar.radio("", ("Single image", "Multiple images"), index=0)

classes_selector = st.sidebar.multiselect("Select classes", CLASSES, default=CLASSES[0])
all_labels_chbox = st.sidebar.checkbox("All classes", value=True)


# Prediction

# target labels and their colors
if all_labels_chbox:
    target_class_ids = list(range(len(CLASSES)))
elif classes_selector:
    target_class_ids = [CLASSES.index(class_name) for class_name in classes_selector]
else:
    target_class_ids = [0]

rgb_colors = get_colors(target_class_ids)
detected_ids = None


if prediction_mode == "Single image":

    # Upload image
    uploaded_file = st.file_uploader("Choose an image", type=["png", "jpg", "jpeg"])

    if uploaded_file is not None:

        # Get the result information

        bytes_data = uploaded_file.getvalue()
        file_bytes = np.asarray(bytearray(bytes_data), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result = get_preds(img)

        result_copy = result.copy()
        result_copy = result_copy[np.isin(result_copy[:, -1], target_class_ids)]

        detected_ids = []

        # Draw bounding box
        img_draw = img.copy().astype(np.uint8)
        for bbox_data in result_copy:
            xmin, ymin, xmax, ymax, _, label = bbox_data
            p0, p1, label = (int(xmin), int(ymin)), (int(xmax), int(ymax)), int(label)
            img_draw = cv2.rectangle(img_draw, p0, p1, rgb_colors[label], 2)

            # Add label on the image
            cv2.putText(
                img_draw,
                CLASSES[label],
                (p0[0], p0[1] - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                rgb_colors[label],
                2,
            )

            detected_ids.append(label)

        st.image(img_draw, use_column_width=True)

elif prediction_mode == "Multiple images":
    uploaded_files = st.file_uploader(
        "Choose an image", type=["png", "jpg", "jpeg"], accept_multiple_files=True
    )

    detected_ids = []

    for uploaded_file in uploaded_files:
        if uploaded_file is not None:

            bytes_data = uploaded_file.getvalue()
            file_bytes = np.asarray(bytearray(bytes_data), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            result = get_preds(img)

            result_copy = result.copy()
            result_copy = result_copy[np.isin(result_copy[:, -1], target_class_ids)]

            img_draw = img.copy().astype(np.uint8)
            for bbox_data in result_copy:
                xmin, ymin, xmax, ymax, _, label = bbox_data
                p0, p1, label = (
                    (int(xmin), int(ymin)),
                    (int(xmax), int(ymax)),
                    int(label),
                )
                img_draw = cv2.rectangle(img_draw, p0, p1, rgb_colors[label], 2)

                cv2.putText(
                    img_draw,
                    CLASSES[label],
                    (p0[0], p0[1] - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    rgb_colors[label],
                    2,
                )

                detected_ids.append(label)

            st.image(img_draw, use_column_width=True)


detected_ids = set(detected_ids if detected_ids is not None else target_class_ids)
labels = [CLASSES[index] for index in detected_ids]
legend_df = pd.DataFrame({"label": labels})
st.dataframe(legend_df.style.applymap(get_legend_color))


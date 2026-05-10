# app.py

import json
import random
from pathlib import Path

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials
from PIL import Image

# =========================================================
# CONFIG
# =========================================================

IMAGE_FOLDER = "study_images"
INSTRUCTION_FOLDER = "instructions"

TOTAL_IMAGES = 10

st.set_page_config(
    page_title="Image Quality Study",
    layout="centered"
)

# =========================================================
# GOOGLE SHEETS
# =========================================================

def get_gsheet(tab_name="image_pool"):

    credentials_data = st.secrets["google_sheets"]

    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    credentials = Credentials.from_service_account_info(
        credentials_data,
        scopes=scope
    )

    client = gspread.authorize(credentials)

    sheet = client.open_by_url(
        st.secrets["google_sheets"]["spreadsheet"]
    ).worksheet(tab_name)

    return sheet

def get_available_images(sheet):
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df[df["assigned"] == 0]


def assign_images(pool_sheet, n=10):
    data = pool_sheet.get_all_records()
    df = pd.DataFrame(data)

    available = df[df["assigned"] == 0]
    if len(available) < n:
        return None
    selected = available.sample(n)
    # mark as assigned in sheet
    for idx in selected.index:
        pool_sheet.update_cell(
            idx + 2,  # account for header row
            df.columns.get_loc("assigned") + 1,
            1
        )
    return selected.to_dict("records")


def save_response_to_sheet(response_row):
    sheet = get_gsheet("responses")
    sheet.append_row(response_row)


# =========================================================
# LOAD IMAGE/CAPTION DATA
# =========================================================

@st.cache_data
def load_items():
    with open("captions.json", "r") as f:
        files = json.load(f)
    base_path = Path("study_images")
    items = []

    for model_dir in base_path.iterdir():
        if model_dir.is_dir():
            model_name = model_dir.name
            for img_path in model_dir.glob("*"):
                items.append({
                    "image": str(img_path),
                    "caption": str(img_path).split('/')[-1][:-11],
                    "model": model_name
                })

    return items
#study_items = load_items()


# =========================================================
# SESSION STATE
# =========================================================

pool_sheet = get_gsheet("image_pool")

if "image_order" not in st.session_state:
    images = assign_images(pool_sheet, 10)
    if images is None:
        st.error("No more unassigned images available.")
        st.stop()
    st.session_state.image_order = images


#if "image_order" not in st.session_state:
#    random.shuffle(study_items)
#    st.session_state.image_order = study_items[:TOTAL_IMAGES]

if "page" not in st.session_state:
    st.session_state.page = "instructions"

if "current_index" not in st.session_state:
    st.session_state.current_index = 0

if "responses" not in st.session_state:
    st.session_state.responses = []

# =========================================================
# USER ID
# =========================================================

st.sidebar.title("Participant")

participant_id = st.sidebar.text_input("Enter your Prolific ID")

# =========================================================
# INSTRUCTION PAGE
# =========================================================

if st.session_state.page == "instructions":

    st.title("Instructions")

    st.markdown(
        """
        You will see a series of images paired with captions.

        For each image, answer the following questions:

        1. Does the image align with the caption?
        2. Is the image of good quality?

        Please answer carefully before continuing.
        """
    )

    st.write("---")

    instruction_images = sorted(
        Path(INSTRUCTION_FOLDER).glob("*")
    )

    for img_path in instruction_images:

        img = Image.open(img_path)

        st.image(
            img,
            use_container_width=True
        )

    st.write("---")

    if st.button("Start Study"):

        if not participant_id:
            st.error("Please enter your Prolific ID in the sidebar.")
        else:
            st.session_state.page = "study"
            st.rerun()

# =========================================================
# STUDY PAGE
# =========================================================

elif st.session_state.page == "study":

    idx = st.session_state.current_index

    if idx >= TOTAL_IMAGES:
        st.session_state.page = "complete"
        st.rerun()

    item = st.session_state.image_order[idx]

    #image_path = f"{IMAGE_FOLDER}/{item['model']}/{item['image']}"
    image_path = f"{item['image']}"
    caption = item["caption"]

    st.title(f"Image {idx + 1} / {TOTAL_IMAGES}")

    # -----------------------------------------------------
    # IMAGE
    # -----------------------------------------------------

    image = Image.open(image_path)

    st.image(
        image,
        use_container_width=True
    )

    # -----------------------------------------------------
    # CAPTION
    # -----------------------------------------------------

    st.markdown("### Caption")

    st.write(caption)

    st.write("---")

    # -----------------------------------------------------
    # QUESTION 1
    # -----------------------------------------------------

    q1 = st.radio(
        "Does the image align with the caption?",
        ["Yes", "No"],
        index=None,
        key=f"q1_{idx}"
    )

    # -----------------------------------------------------
    # QUESTION 2
    # -----------------------------------------------------

    q2 = st.radio(
        "Is the image of good quality?",
        ["Yes", "No"],
        index=None,
        key=f"q2_{idx}"
    )

    st.write("---")

    # -----------------------------------------------------
    # SUBMIT RESPONSE
    # -----------------------------------------------------

    if st.button("Next"):

        if not participant_id:
            st.error("Please enter your Prolific ID.")

        elif q1 is None or q2 is None:
            st.error("Please answer both questions.")

        else:

            response = [
                participant_id,
                idx + 1,
                item["image"],
                item["caption"],
                item["model"],
                q1,
                q2
            ]

            save_response_to_sheet(response)

            st.session_state.current_index += 1

            st.rerun()

# =========================================================
# COMPLETION PAGE
# =========================================================

elif st.session_state.page == "complete":

    st.title("Study Complete")

    st.success("Thank you for participating!")

    st.markdown(
        """
        Your responses have been successfully recorded.
        """
    )

    st.success(
        "Your Prolific completion code is: **CX6ASI8T**"
    )

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import os
from pathlib import Path
import pandas as pd
from pathlib import Path
import datetime
from github import Github
from github import Auth
import uuid

if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())[:8]  # short unique ID

user_id = st.session_state.user_id
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# -----------------------
# Configuration
# -----------------------

BASE_DIR = Path(__file__).parent
root_dir = BASE_DIR / "storm_images_cleaned"
fnames = os.listdir(root_dir)
ls = fnames[0:5]   # subset like your original

# -----------------------
# Session State Setup
# -----------------------
if "index" not in st.session_state:
    st.session_state.index = 0

if "selected_value" not in st.session_state:
    st.session_state.selected_value = {}

# -----------------------
# Helper Functions
# -----------------------
def get_img_id(filename):
    return (
        int(filename.split('_')[1]),
        int(filename.split('_')[3][:-4])
    )

def next_image():
    st.session_state.index = (st.session_state.index + 1) % len(ls)

def prev_image():
    st.session_state.index = (st.session_state.index - 1) % len(ls)

# -----------------------
# Layout
# -----------------------
st.title("MCS Storm Classification")

col1, col2 = st.columns(2)
with col1:
    st.button("Previous", on_click=prev_image)
with col2:
    st.button("Next", on_click=next_image)

# -----------------------
# Load Current Image
# -----------------------
current_file = ls[st.session_state.index]
img = np.load(f"{root_dir}/{current_file}")
img_ID = get_img_id(current_file)

# -----------------------
# Plot
# -----------------------
fig, ax = plt.subplots()
mesh = ax.pcolormesh(img, cmap="Greys_r")

tick_pos = np.linspace(0, 256, 5)
ax.set_xticks(tick_pos)
ax.set_yticks(tick_pos)
ax.set_xticklabels([str(round(x*4.4)) for x in tick_pos])
ax.set_yticklabels([str(round(x*4.4)) for x in tick_pos])

ax.set_xlabel("W-E (km)")
ax.set_ylabel("S-N (km)")
ax.set_aspect("equal")

selected_label = st.session_state.selected_value.get(str(img_ID), None)
ax.set_title(f"Storm ID {img_ID}\nSelected: {selected_label}")

# -----------------------
# Radio Buttons
# -----------------------
storm_options = [
    'Large Linear System',
    'Large Circular',
    'Smaller-scale Circular',
    'Smaller-scale Linear',
    'No Organisation',
    'None of the Above'
]

radio_key = f"radio_{img_ID}"

if selected_label in storm_options:
    default_index = storm_options.index(selected_label)
else:
    default_index = None

selection = st.radio(
    "Storm Type:",
    storm_options,
    index=default_index,
    key=radio_key
)

if selection:
    st.session_state.selected_value[str(img_ID)] = selection

# -----------------------
# Progress Bar
# -----------------------
num_labelled = len(st.session_state.selected_value)
progress = num_labelled / len(ls)

st.progress(progress)
st.write(f"Labelled: {num_labelled}/{len(ls)}")
st.pyplot(fig)

# -----------------------
# Save Labels
# -----------------------
df = pd.DataFrame([
    {"storm_ID": k.split(',')[0][1:], "frame_no": k.split(',')[1][:-1], "user_label": v} 
    for k, v in st.session_state.selected_value.items()
])

# Load GitHub secrets
token = st.secrets["github_token"]
repo_owner = st.secrets["repo_owner"]
repo_name = st.secrets["repo_name"]

# Example DataFrame
df = pd.DataFrame.from_dict(st.session_state.selected_value, orient="index", columns=["label"])

# Convert to CSV string
csv_content = df.to_csv(index=False)

# Connect to GitHub
auth = Auth.Token("access_token")

# Public Web Github
g = Github(auth=auth)
repo = g.get_user(repo_owner).get_repo(repo_name)

# Push file
unique_filename = f"user_classifications/storm_labels_{user_id}_{timestamp}.csv"

repo.create_file(
    path=unique_filename,
    message=f"Add new storm labels {unique_filename}",
    content=csv_content
)

# -----------------------
# Save Labels Button
# -----------------------

if st.button("Submit Labels"):

    # Convert session state to DataFrame
    df = pd.DataFrame.from_dict(
        st.session_state.selected_value,
        orient="index",
        columns=["label"]
    )

    csv_content = df.to_csv(index=False)

    # Load GitHub secrets
    token = st.secrets["github_token"]
    repo_owner = st.secrets["repo_owner"]
    repo_name = st.secrets["repo_name"]

    # Connect to GitHub
    g = Github(token)
    repo = g.get_user(repo_owner).get_repo(repo_name)

    unique_filename = f"user_classifications/storm_labels_{user_id}_{timestamp}.csv"

    repo.create_file(
        path=unique_filename,
        message=f"Add storm labels from user {user_id}",
        content=csv_content
    )

    st.success(f"✅ Saved to GitHub as {unique_filename}")

#st.download_button(
#    label="Download Labels as CSV",
#    data=df.to_csv(index=False),
#    file_name=f"storm_labels_{timestamp}.csv",
#    mime="text/csv"
#)

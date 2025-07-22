import streamlit as st
import pandas as pd
import os
from datetime import datetime, date, time
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# === Secure password from Streamlit Secrets ===
PASSWORD = st.secrets["REF_PLANNER_PASSWORD"]

# === File path config ===
FILE_PATH = "referees.xlsx"

# === Load and Save Functions ===
def load_data():
    if os.path.exists(FILE_PATH):
        df = pd.read_excel(FILE_PATH)

        # Combine "Event Date" and "Event Start" if needed
        if "Event Start" not in df.columns and "Event Date" in df.columns:
            df["Event Start"] = pd.to_datetime(df["Event Date"], errors="coerce")
        elif "Event Start" in df.columns and "Event Date" in df.columns:
            df["Event Start"] = pd.to_datetime(df["Event Start"].combine_first(df["Event Date"]), errors="coerce")

        if "Event Date" in df.columns:
            df.drop(columns=["Event Date"], inplace=True)

        # Ensure all required columns
        required_cols = [
            "Event Start", "Event Location", "Post Code", "Senior Referee",
            "Referee 2", "Referee 3", "Referee 4", "Referee 5", "Referee 6"
        ]
        for col in required_cols:
            if col not in df.columns:
                df[col] = ""
        return df[required_cols]
    else:
        return pd.DataFrame(columns=[
            "Event Start", "Event Location", "Post Code", "Senior Referee",
            "Referee 2", "Referee 3", "Referee 4", "Referee 5", "Referee 6"
        ])

def save_data(df):
    df.to_excel(FILE_PATH, index=False)

def generate_pdf(dataframe):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = []

    title = Paragraph("WRPF UK Referee Planner", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    table_data = [list(dataframe.columns)]
    for row in dataframe.itertuples(index=False):
        formatted_row = []
        for cell in row:
            if isinstance(cell, pd.Timestamp):
                formatted_row.append(cell.strftime("%d/%m/%Y %H:%M"))
            else:
                formatted_row.append(str(cell) if pd.notnull(cell) else "")
        table_data.append(formatted_row)

    # Scale to page width
    page_width = landscape(A4)[0]
    num_columns = len(table_data[0])
    col_width = page_width / num_columns
    table = Table(table_data, colWidths=[col_width] * num_columns)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.black),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer

# === Streamlit Setup ===
st.set_page_config(page_title="WRPF UK Referee Planner", layout="wide")
st.title("🇬🇧 WRPF UK Referee Planner")

# === Session State ===
if "data" not in st.session_state:
    st.session_state.data = load_data()

df = st.session_state.data
df["Event Start"] = pd.to_datetime(df["Event Start"], errors="coerce")

# === Sidebar Controls ===
st.sidebar.title("⚙️ Planner Controls")

# PDF Export
st.sidebar.subheader("📄 Export to PDF")
pdf_buffer = generate_pdf(df)
st.sidebar.download_button(
    label="Download Referee Planner",
    data=pdf_buffer,
    file_name="WRPF_UK_Referee_Planner.pdf",
    mime="application/pdf"
)

# Save edits
st.sidebar.subheader("🔐 Save Edited Table")
edit_password = st.sidebar.text_input("Password to save", type="password")

# === Main Table Display ===
st.subheader("📋 Referee Assignments")
edited_df = st.data_editor(
    df,
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        "Event Start": st.column_config.DatetimeColumn(
            "Event Start", format="DD/MM/YYYY HH:mm", step=900
        )
    }
)

if st.sidebar.button("💾 Save Changes"):
    if edit_password == PASSWORD:
        save_data(edited_df)
        st.session_state.data = edited_df
        st.sidebar.success("✅ Changes saved.")
    else:
        st.sidebar.error("❌ Incorrect password.")

# Add new event
st.sidebar.subheader("➕ Add New Event")
add_password = st.sidebar.text_input("Password to add", type="password", key="add_pw")
if add_password == PASSWORD:
    with st.sidebar.form("add_event_form"):
        event_date = st.date_input("Event Date", value=date.today())
        event_time = st.time_input("Start Time", value=time(9, 0))
        event_location = st.text_input("Location")
        post_code = st.text_input("Post Code")
        senior_ref = st.text_input("Senior Referee")
        referee_2 = st.text_input("Referee 2")
        referee_3 = st.text_input("Referee 3")
        referee_4 = st.text_input("Referee 4")
        referee_5 = st.text_input("Referee 5")
        referee_6 = st.text_input("Referee 6")

        submit_event = st.form_submit_button("Add Event")
        if submit_event:
            full_datetime = datetime.combine(event_date, event_time)
            new_row = {
                "Event Start": full_datetime,
                "Event Location": event_location,
                "Post Code": post_code,
                "Senior Referee": senior_ref,
                "Referee 2": referee_2,
                "Referee 3": referee_3,
                "Referee 4": referee_4,
                "Referee 5": referee_5,
                "Referee 6": referee_6,
            }
            updated_df = pd.concat([edited_df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(updated_df)
            st.session_state.data = updated_df
            st.sidebar.success("✅ Event added.")
            st.experimental_rerun()
elif add_password:
    st.sidebar.error("❌ Incorrect password.")

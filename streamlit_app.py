import streamlit as st
import easyocr
from PIL import Image
import sqlite3
import re
from datetime import datetime

# ----------------------
# Database Setup
# ----------------------
DB_NAME = 'specials.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_specials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT,
            special_description TEXT,
            date_added TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_special(day, special_desc):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO daily_specials (day, special_description, date_added)
        VALUES (?, ?, ?)
    ''', (day, special_desc, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# ----------------------
# OCR and Parsing
# ----------------------
reader = easyocr.Reader(['en'], gpu=False)  # Initialize EasyOCR (CPU mode)

def ocr_image(image):
    """
    Use EasyOCR to read text from the given image.
    Returns a list of text lines.
    """
    results = reader.readtext(image, detail=0)  # detail=0 => text only
    return results

def parse_specials(text_lines):
    """
    Attempt to parse lines of text to extract day-based specials.
    This is a naive approach that looks for day names (Monday, Tuesday, etc.)
    and groups subsequent lines until the next day is found.
    """
    days_of_week = [
        "monday", "tuesday", "wednesday",
        "thursday", "friday", "saturday", "sunday"
    ]

    # Prepare a structure to hold {day: [list_of_special_lines]}
    parsed_data = {}
    current_day = None

    for line in text_lines:
        # Clean the line a bit
        clean_line = line.strip().lower()

        # Check if this line is a day name
        if any(day in clean_line for day in days_of_week):
            # Extract the exact day name
            for d in days_of_week:
                if d in clean_line:
                    current_day = d.capitalize()
                    parsed_data[current_day] = []
                    break
        else:
            # If we already have a current_day, append line to that day's specials
            if current_day:
                parsed_data[current_day].append(line.strip())

    # Convert lists of lines into single strings
    for day in parsed_data:
        parsed_data[day] = " | ".join(parsed_data[day])

    return parsed_data

# ----------------------
# Streamlit App
# ----------------------
def main():
    st.title("Pittsburgh Food Specials Finder (AI-powered OCR)")

    st.write("Upload an image of restaurant specials to parse and store them in a normalized format.")

    uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])

    if uploaded_file is not None:
        # Display the uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded image", use_column_width=True)

        # Run OCR
        if st.button("Extract and Parse Specials"):
            with st.spinner("Extracting text from image..."):
                text_lines = ocr_image(uploaded_file)
                st.subheader("Raw OCR Output")
                st.write(text_lines)

                # Parse out daily specials
                specials_dict = parse_specials(text_lines)
                st.subheader("Parsed Specials")
                if specials_dict:
                    for day, desc in specials_dict.items():
                        st.write(f"**{day}:** {desc}")
                else:
                    st.write("No recognizable daily specials found. Try adjusting your parsing logic.")

                # Optionally save to DB
                st.subheader("Save to Database")
                if st.button("Save All Parsed Specials"):
                    for day, desc in specials_dict.items():
                        save_special(day, desc)
                    st.success("Saved to database!")

    # Show existing specials from DB
    st.subheader("View Saved Specials")
    if st.button("Load Saved Specials"):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT day, special_description, date_added FROM daily_specials ORDER BY date_added DESC")
        rows = c.fetchall()
        conn.close()

        if rows:
            for row in rows:
                day, desc, date_added = row
                st.markdown(f"**Day**: {day}\n\n**Special**: {desc}\n\n*Added on: {date_added}*")
                st.markdown("---")
        else:
            st.info("No specials found in the database.")

if __name__ == "__main__":
    init_db()
    main()

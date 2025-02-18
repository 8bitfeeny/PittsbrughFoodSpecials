import streamlit as st
from PIL import Image
import pytesseract
import sqlite3
import re
from datetime import datetime

# --- Database Setup ---
DB_NAME = 'restaurant_specials.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Create a table for restaurants if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS specials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_name TEXT NOT NULL,
            special_details TEXT NOT NULL,
            date_added TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_special(restaurant_name, special_details):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO specials (restaurant_name, special_details, date_added)
        VALUES (?, ?, ?)
    ''', (restaurant_name, special_details, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# --- OCR Function ---
def extract_text_from_image(image):
    # Use pytesseract to extract text
    text = pytesseract.image_to_string(image)
    return text

# --- Simple Normalization ---
def extract_restaurant_name(text):
    """
    A simple (and naive) function to try to extract a restaurant name.
    Here we assume the restaurant name might be on the first line.
    """
    lines = text.strip().split('\n')
    if lines:
        # A very simple heuristic: pick the first line with alphabetical characters.
        for line in lines:
            if re.search(r'[A-Za-z]', line):
                return line.strip()
    return "Unknown Restaurant"

# --- Streamlit App ---
def main():
    st.title("Pittsburgh Food Specials Finder")
    st.write("Upload a photo of a restaurant special or paste the text details below.")

    # Option to choose input type
    input_type = st.radio("Select input type:", ["Image", "Text"])

    extracted_text = ""
    
    if input_type == "Image":
        uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)
            
            # Extract text using OCR
            if st.button("Extract Text from Image"):
                with st.spinner("Processing image..."):
                    extracted_text = extract_text_from_image(image)
                    st.text_area("Extracted Text", extracted_text, height=200)
    else:
        extracted_text = st.text_area("Paste text here", height=200)

    # If text is available, try to normalize/extract data
    if extracted_text:
        st.subheader("Normalize Data")
        # Try to extract a restaurant name from the text as a starting point.
        default_name = extract_restaurant_name(extracted_text)
        restaurant_name = st.text_input("Restaurant Name", default_name)
        special_details = st.text_area("Special Details", extracted_text)

        if st.button("Save Special"):
            if restaurant_name and special_details:
                save_special(restaurant_name, special_details)
                st.success("Special saved successfully!")
            else:
                st.error("Please provide both restaurant name and special details.")

    # Optionally, display saved records
    st.subheader("Saved Food Specials")
    if st.button("Refresh List"):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT restaurant_name, special_details, date_added FROM specials ORDER BY date_added DESC")
        rows = c.fetchall()
        conn.close()
        
        if rows:
            for row in rows:
                st.markdown(f"**{row[0]}**  \n{row[1]}  \n*Added on {row[2]}*")
                st.markdown("---")
        else:
            st.info("No specials saved yet.")

if __name__ == "__main__":
    init_db()
    main()

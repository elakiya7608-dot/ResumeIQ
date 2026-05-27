from pdf2image import convert_from_path
import easyocr
import cv2
import numpy as np
import os

# Initialize EasyOCR
reader = easyocr.Reader(['en'], gpu=False)


def extract_text_from_scanned_pdf(pdf_path):

    full_text = ""

    try:
        print("\nSTEP 1: Converting PDF to images...")

        images = convert_from_path(
            pdf_path,
            dpi=300,
            poppler_path=r"c:\Users\RAVICHANDRAN\poppler-24.08.0\Library\bin"

        )

        print(f"Total pages found: {len(images)}")

        for i, image in enumerate(images):

            print(f"\nSTEP 2: Processing page {i+1}")

            # Save image
            image_path = f"page_{i+1}.png"
            image.save(image_path, "PNG")

            print(f"Saved image: {image_path}")

            # Read image using OpenCV
            img = cv2.imread(image_path)

            # Check image loaded
            if img is None:
                print("ERROR: Image not loaded")
                continue

            print("Image loaded successfully")

            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            print("STEP 3: Running OCR...")

            result = reader.readtext(gray, detail=0)

            print("OCR Result:", result)

            extracted_text = " ".join(result)

            full_text += extracted_text + "\n"

        return full_text

    except Exception as e:
        print("OCR ERROR:", e)
        return ""
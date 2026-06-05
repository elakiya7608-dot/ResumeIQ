from pdf2image import convert_from_path
from paddleocr import PaddleOCR
import cv2
import zipfile
import tempfile
import os

# =====================================================
# INITIALIZE PADDLE OCR
# =====================================================

ocr = PaddleOCR(
    use_angle_cls=True,
    lang='en'
)

# =====================================================
# IMAGE PREPROCESSING
# =====================================================

def preprocess_image(image_path):

    img = cv2.imread(image_path)

    if img is None:

        print(f"ERROR: Cannot load image -> {image_path}")

        return None

    # =================================================
    # RESIZE IMAGE FOR BETTER OCR
    # =================================================

    img = cv2.resize(
        img,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC
    )

    # =================================================
    # CONVERT TO GRAYSCALE
    # =================================================

    gray = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2GRAY
    )

    # =================================================
    # REMOVE NOISE
    # =================================================

    gray = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    # =================================================
    # THRESHOLDING
    # =================================================

    gray = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    return gray

# =====================================================
# COMMON OCR FUNCTION
# =====================================================

def run_ocr(image_path):

    try:

        processed_image = preprocess_image(
            image_path
        )

        if processed_image is None:

            return ""

        print("Running PaddleOCR...")

        result = ocr.ocr(
            processed_image,
            cls=True
        )

        print("OCR RESULT:")
        print(result)

        extracted_text = ""

        # =================================================
        # SAFETY CHECK
        # =================================================

        if not result:

            print("No OCR result found")

            return ""

        # =================================================
        # LOOP THROUGH OCR RESULT SAFELY
        # =================================================

        for page in result:

            if page is None:

                continue

            for line in page:

                try:

                    # PaddleOCR text extraction
                    text = line[1][0]

                    extracted_text += text + " "

                except Exception as line_error:

                    print("LINE ERROR:", line_error)

                    continue

        return extracted_text.strip()

    except Exception as e:

        print("OCR ERROR:", e)

        return ""

# =====================================================
# OCR FOR SCANNED PDF
# =====================================================

def extract_text_from_scanned_pdf(pdf_path):

    full_text = ""

    try:

        print("\nSTEP 1: Converting PDF to images...")

        images = convert_from_path(
            pdf_path,
            dpi=400,
            poppler_path=r"c:\Users\RAVICHANDRAN\poppler-24.08.0\Library\bin"
        )

        print(f"Total pages found: {len(images)}")

        for i, image in enumerate(images):

            print(f"\nSTEP 2: Processing page {i+1}")

            # =================================================
            # CREATE TEMP IMAGE
            # =================================================

            temp_image = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".png"
            )

            image_path = temp_image.name

            image.save(
                image_path,
                "PNG"
            )

            print(f"Saved temp image: {image_path}")

            # =================================================
            # RUN OCR
            # =================================================

            extracted_text = run_ocr(
                image_path
            )

            print("Extracted Text:")
            print(extracted_text)

            full_text += extracted_text + "\n"

            # =================================================
            # DELETE TEMP IMAGE
            # =================================================

            os.remove(image_path)

        return full_text.strip()

    except Exception as e:

        print("PDF OCR ERROR:", e)

        return ""

# =====================================================
# OCR FOR IMAGES INSIDE DOCX
# =====================================================

def extract_text_from_docx_images(docx_path):

    full_text = ""

    try:

        print("\nSTEP 1: Extracting images from DOCX...")

        with zipfile.ZipFile(docx_path, 'r') as docx:

            image_files = [

                file for file in docx.namelist()

                if file.startswith("word/media/")
            ]

            print(f"Images found: {len(image_files)}")

            if not image_files:

                print("No images found in DOCX")

                return ""

            for i, image_file in enumerate(image_files):

                print(f"\nSTEP 2: Processing image {i+1}")

                # =============================================
                # EXTRACT IMAGE TEMPORARILY
                # =============================================

                temp_dir = tempfile.gettempdir()

                extracted_path = docx.extract(
                    image_file,
                    temp_dir
                )

                print(f"Extracted Image: {extracted_path}")

                # =============================================
                # RUN OCR
                # =============================================

                extracted_text = run_ocr(
                    extracted_path
                )

                print("Extracted Text:")
                print(extracted_text)

                full_text += extracted_text + "\n"

                # =============================================
                # DELETE EXTRACTED IMAGE
                # =============================================

                try:

                    if os.path.exists(extracted_path):

                        os.remove(extracted_path)

                except Exception as delete_error:

                    print("DELETE ERROR:", delete_error)

        return full_text.strip()

    except Exception as e:

        print("DOCX OCR ERROR:", e)

        return ""
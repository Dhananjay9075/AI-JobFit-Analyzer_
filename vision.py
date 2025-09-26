from dotenv import load_dotenv
load_dotenv()

import os
import shutil
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from PIL import Image
import pdfplumber
import pandas as pd
import google.generativeai as genai
from io import BytesIO
import easyocr
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'xlsx'}

# Setup Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize EasyOCR
reader = easyocr.Reader(['en'])

# Flask App Setup
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def retrieve_relevant_text(query, documents):
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(documents)
    query_vec = vectorizer.transform([query])
    cosine_similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
    most_relevant_idx = cosine_similarities.argmax()
    return documents[most_relevant_idx]

def get_gemini_response(prompt_text, images=None):
    try:
        if images:
            response = model.generate_content([prompt_text] + images)
        else:
            response = model.generate_content(prompt_text)
        return response.text
    except Exception as e:
        return f"❌ Error from Gemini: {e}"

@app.route("/", methods=["GET", "POST"])
def index():
    response_text = None
    selected_files = []
    preview_images = []

    if request.method == "POST":
        query = request.form.get("query")
        folder_input = request.form.get("folder_input", "")

        documents = []
        gemini_images = []

        # Process uploaded files
        uploaded_files = request.files.getlist("files")
        for file in uploaded_files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                selected_files.append(filepath)

        # Process folder input
        if folder_input:
            for folder in folder_input.split(','):
                folder = folder.strip()
                if os.path.isdir(folder):
                    for fname in os.listdir(folder):
                        if allowed_file(fname):
                            selected_files.append(os.path.join(folder, fname))

        # Analyze files
        all_pdf_text, all_excel_text, all_image_text = '', '', ''

        for filepath in selected_files:
            ext = filepath.lower().split('.')[-1]
            try:
                if ext == 'pdf':
                    with pdfplumber.open(filepath) as pdf:
                        for page in pdf.pages:
                            text = page.extract_text()
                            if text:
                                all_pdf_text += text + "\n"
                    documents.append(all_pdf_text)

                elif ext == 'xlsx':
                    df_list = pd.read_excel(filepath, sheet_name=None)
                    for sheet, df in df_list.items():
                        all_excel_text += f"Sheet: {sheet}\n{df.to_string(index=False)}\n\n"
                    documents.append(all_excel_text)

                elif ext in ['jpg', 'jpeg', 'png']:
                    image = Image.open(filepath)
                    np_image = np.array(image.convert("RGB"))
                    results = reader.readtext(np_image, detail=0)
                    extracted_text = " ".join(results)
                    all_image_text += extracted_text + "\n"
                    documents.append(all_image_text)
                    preview_images.append(filepath)
                    gemini_images.append(image)

            except Exception as e:
                print(f"Error processing {filepath}: {e}")

        if documents:
            relevant_text = retrieve_relevant_text(query, documents)
            prompt = "You are an expert in analyzing Resume with Comparing job Description.Resume and Jd is with Any Name\n"
            prompt += "Relevant Information:\n" + relevant_text + "\n\n"
            prompt += "User Query: " + query
            response_text = get_gemini_response(prompt, gemini_images if gemini_images else None)

    return render_template("index.html", response=response_text, images=preview_images)

if __name__ == "__main__":
    app.run(debug=True)
# Data Engineer – Observability & Insights Platform.pdf

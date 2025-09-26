import os
import json
import re
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
import pdfplumber
import google.generativeai as genai
from datetime import datetime

# Setup
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'pdf'}
MAX_RESUMES = 5

# Setup Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
# Try different model versions for compatibility
try:
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    print("✅ Using models/gemini-1.5-flash")
except Exception as e:
    print(f"❌ models/gemini-1.5-flash failed: {e}")
    try:
        model = genai.GenerativeModel('models/gemini-1.5-pro')
        print("✅ Using models/gemini-1.5-pro")
    except Exception as e2:
        print(f"❌ models/gemini-1.5-pro failed: {e2}")
        try:
            model = genai.GenerativeModel('models/gemini-pro')
            print("✅ Using models/gemini-pro")
        except Exception as e3:
            print(f"❌ All models failed. Last error: {e3}")
            raise Exception("No working Gemini model found. Please check your API key and model access.")

# Flask App Setup
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'your-secret-key-here'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(filepath):
    """Extract text from PDF file"""
    try:
        text = ""
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from {filepath}: {e}")
        return ""

# Helper functions removed - all data now extracted via Gemini AI in analyze_resume_match()

def analyze_resume_match(jd_text, resume_text):
    """Use Gemini to analyze resume match with JD - extract all data from LLM"""
    try:
        prompt = f"""
        You are an expert HR recruiter. Analyze this resume against the job description and provide a comprehensive comparison.

        JOB DESCRIPTION:
        {jd_text}

        CANDIDATE RESUME:
        {resume_text}

        Please provide your analysis in the following JSON format:
        {{
            "candidate_name": "Extract the candidate's full name from the resume do not extact other then full name",
            "experience_match": "Yes/No/Partially",
            "experience_analysis": "short explanation of experience match including years and relevance",
            "missing_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
            "suggestions": "Specific suggestions for improvement, concerns about JD match, and overall impact assessment in short 2-3 lines"
        }}

        Analysis Requirements:
        1. CANDIDATE NAME: Extract the full name from the resume text dont need extract all detail with name.
        2. EXPERIENCE MATCH: Compare candidate's experience with job requirements (Yes/No) in 3-4 lines only.of the experience is between the given in jd then "Yes" and not fit in between given in then "No".
        3. EXPERIENCE ANALYSIS: Detailed explanation of experience match, years of experience, and relevance
        4. MISSING KEYWORDS: List 3-5 or if more then also take key technical skills, tools, or requirements from JD that are missing from resume. take only tachnical skills not other keywords.
        5. SUGGESTIONS: Provide specific improvement suggestions and impact assessment for JD match. in just 3-4 lines only.

        Focus on:
        - Technical skills and tools mentioned in JD but not in resume
        - Experience level comparison (years and relevance)
        - Overall job fit and compatibility
        - Specific actionable suggestions for improvement
        - Any red flags or concerns about the match

        Return only valid JSON, no additional text.
        """
        
        # Add timeout for Gemini API call
        import time
        start_time = time.time()
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Log processing time
        processing_time = time.time() - start_time
        print(f"Gemini API call took {processing_time:.2f} seconds")
        
        # Clean the response to extract JSON
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "candidate_name": "Unknown Candidate",
                "experience_match": "Analysis Error",
                "experience_analysis": "Could not analyze experience match - JSON parsing failed",
                "missing_keywords": ["Analysis failed"],
                "suggestions": "Error in analysis. Please try again."
            }
            
    except Exception as e:
        print(f"Error in resume analysis: {e}")
        # Fallback analysis without AI
        return {
            "candidate_name": "Unknown Candidate",
            "experience_match": "Analysis Error",
            "experience_analysis": f"AI analysis failed: {str(e)}. Please check your API key and try again.",
            "missing_keywords": ["AI analysis unavailable"],
            "suggestions": "Unable to perform AI analysis. Please ensure your Google API key is valid and the model is accessible."
        }

@app.route("/")
def index():
    return render_template("upload.html")

@app.route("/upload", methods=["POST"])
def upload_files():
    try:
        # Check if JD file is uploaded
        jd_file = request.files.get('jd_file')
        if not jd_file or jd_file.filename == '':
            flash('Please upload a Job Description file', 'error')
            return redirect(url_for('index'))
        
        # Check if resume files are uploaded
        resume_files = request.files.getlist('resume_files')
        if not resume_files or len(resume_files) == 0:
            flash('Please upload at least one resume file', 'error')
            return redirect(url_for('index'))
        
        if len(resume_files) > MAX_RESUMES:
            flash(f'Maximum {MAX_RESUMES} resumes allowed', 'error')
            return redirect(url_for('index'))
        
        # Save JD file
        if jd_file and allowed_file(jd_file.filename):
            jd_filename = secure_filename(jd_file.filename)
            jd_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"jd_{jd_filename}")
            jd_file.save(jd_filepath)
            
            # Extract JD text
            jd_text = extract_text_from_pdf(jd_filepath)
            if not jd_text:
                flash('Could not extract text from Job Description', 'error')
                return redirect(url_for('index'))
        else:
            flash('Invalid Job Description file format', 'error')
            return redirect(url_for('index'))
        
        # Process resume files
        results = []
        for i, resume_file in enumerate(resume_files):
            if resume_file and allowed_file(resume_file.filename):
                resume_filename = secure_filename(resume_file.filename)
                resume_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"resume_{i}_{resume_filename}")
                resume_file.save(resume_filepath)
                
                # Extract resume text
                resume_text = extract_text_from_pdf(resume_filepath)
                if not resume_text:
                    continue
                
                # Analyze resume match using Gemini AI for all data
                analysis = analyze_resume_match(jd_text, resume_text)
                
                results.append({
                    'name': analysis.get('candidate_name', 'Unknown Candidate'),
                    'filename': resume_filename,
                    'analysis': analysis
                })
        
        if not results:
            flash('Could not process any resume files', 'error')
            return redirect(url_for('index'))
        
        return render_template("results.html", results=results, jd_filename=jd_filename)
        
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route("/results")
def results():
    return render_template("results.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)


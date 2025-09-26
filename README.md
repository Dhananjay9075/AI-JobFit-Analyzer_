# Resume Matcher - AI-Powered Resume Analysis

A Flask-based web application that uses Google Gemini AI to analyze and match resumes against job descriptions.

## Features

- **Dual Upload System**: Upload 1 Job Description and up to 5 Resume PDFs
- **AI-Powered Analysis**: Uses Google Gemini AI for intelligent resume matching
- **Comprehensive Results**: Four-column analysis showing:
  - Candidate Name
  - Experience Match (Yes/No/Partially)
  - Missing Keywords
  - Suggestions & Impact Analysis
- **Modern UI**: Beautiful, responsive interface with loading states
- **PDF Processing**: Automatic text extraction from PDF files

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up Google Gemini API
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Create a `.env` file in the project root:
```
GOOGLE_API_KEY=your_actual_api_key_here
```

### 3. Run the Application
```bash
python resume_matcher.py
```

The application will be available at `http://localhost:5001`

## Usage

1. **Upload Job Description**: Select a PDF file containing the job description
2. **Upload Resumes**: Select up to 5 PDF resume files
3. **Analyze**: Click "Analyze Resumes" to start the AI-powered analysis
4. **Review Results**: View detailed analysis in the results table

## Analysis Features

### Experience Matching
- Compares candidate's years of experience with job requirements
- Provides Yes/No/Partially match status
- Includes detailed analysis of experience relevance

### Keyword Analysis
- Identifies missing technical skills and keywords
- Shows which required skills are not present in the resume
- Helps identify skill gaps

### Suggestions & Impact
- Provides specific improvement suggestions
- Highlights potential concerns about job fit
- Offers actionable feedback for better matching

## File Structure

```
flask_new/
├── resume_matcher.py          # Main Flask application
├── templates/
│   ├── upload.html           # Upload page
│   └── results.html          # Results display page
├── static/
│   └── uploads/              # Uploaded files storage
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## API Endpoints

- `GET /` - Upload page
- `POST /upload` - Process uploaded files and analyze
- `GET /results` - Results page

## Requirements

- Python 3.8+
- Google Gemini API key
- PDF files for job descriptions and resumes

## Error Handling

The application includes comprehensive error handling for:
- Invalid file formats
- Missing files
- API errors
- PDF processing errors
- Network issues

## Security Features

- File type validation (PDF only)
- Secure filename handling
- Input sanitization
- Error message filtering

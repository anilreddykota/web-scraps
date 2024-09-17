from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
from flask_cors import CORS
import spacy
import pdfplumber
import docx2txt

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create the upload directory if not exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Load spaCy model
nlp = spacy.load('en_core_web_sm')

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

def extract_text_from_docx(docx_path):
    return docx2txt.process(docx_path)

def extract_info_from_text(text):
    doc = nlp(text)
    info = {
        'name': None,
        'skills': [],
    }

    # Extract name and email based on entity types
    for ent in doc.ents:
        if ent.label_ == 'PERSON' and info['name'] is None:
            info['name'] = ent.text
        elif ent.label_ == 'EMAIL' and info['email'] is None:
            info['email'] = ent.text

    # Skills list (expanded to include more terms)
    skills = ["Python", "Java", "JavaScript", "C++", "SQL", "Machine Learning", "MongoDB", "Node.js", "React.js",
              "Express.js", "NumPy", "Pandas", "Matplotlib", "Seaborn"]

    # Check each token for matching skills
    for token in doc:
        if token.text in skills and token.text not in info['skills']:
            info['skills'].append(token.text)

    return info

@app.route('/uploadresume', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({'success': False, 'message': 'No resume uploaded'}), 400

    file = request.files['resume']

    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Extract text from the resume
        try:
            if file.filename.endswith('.pdf'):
                resume_text = extract_text_from_pdf(file_path)
            elif file.filename.endswith('.docx'):
                resume_text = extract_text_from_docx(file_path)
            else:
                return jsonify({'success': False, 'message': 'Unsupported file format'}), 400

            # Extract relevant information using spaCy
            resume_data = extract_info_from_text(resume_text)
            return jsonify({'success': True, 'resumeDetails': resume_data})
        except Exception as e:
            print(f"Error parsing resume: {str(e)}")
            return jsonify({'success': False, 'message': 'Error parsing resume'}), 500

    return jsonify({'success': False, 'message': 'Invalid file type'}), 400

if _name_ == '__main__':
    app.run(debug=True)
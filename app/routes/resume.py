from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os

from app.utils.text_extraction import extract_text_from_pdf, extract_text_from_docx, extract_info_from_text

resume_bp = Blueprint('resume', __name__)

@resume_bp.route('/uploadresume', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({'success': False, 'message': 'No resume uploaded'}), 400

    file = request.files['resume']

    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            if file.filename.endswith('.pdf'):
                resume_text = extract_text_from_pdf(file_path)
            elif file.filename.endswith('.docx'):
                resume_text = extract_text_from_docx(file_path)
            else:
                return jsonify({'success': False, 'message': 'Unsupported file format'}), 400

            resume_data = extract_info_from_text(resume_text)
            return jsonify({'success': True, 'resumeDetails': resume_data})
        except Exception as e:
            print(f"Error parsing resume: {str(e)}")
            return jsonify({'success': False, 'message': 'Error parsing resume'}), 500

    return jsonify({'success': False, 'message': 'Invalid file type'}), 400

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

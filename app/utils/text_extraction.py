import pdfplumber
import docx2txt
import spacy

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
        'email': None,
        'skills': [],
    }

    for ent in doc.ents:
        if ent.label_ == 'PERSON' and info['name'] is None:
            info['name'] = ent.text
        elif ent.label_ == 'EMAIL' and info['email'] is None:
            info['email'] = ent.text

    skills = ["Python", "Java", "JavaScript", "C++", "SQL", "Machine Learning", "MongoDB", "Node.js", "React.js",
              "Express.js", "NumPy", "Pandas", "Matplotlib", "Seaborn"]

    for token in doc:
        if token.text in skills and token.text not in info['skills']:
            info['skills'].append(token.text)

    return info

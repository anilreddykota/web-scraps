from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import requests
from bs4 import BeautifulSoup
import pdfplumber
import docx2txt
import spacy
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor
import time

app = Flask(__name__)
CORS(app)

# Configuration for file uploads
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

# Function to scrape job listings (main page from GeeksGod)
def scrape_jobs_geeksgod():
    url = "https://geeksgod.com/category/off-campus-placement-drive-for-freshers/"
    response = requests.get(url)

    if response.status_code != 200:
        return [], 0

    soup = BeautifulSoup(response.text, 'html.parser')
    parent_divs = soup.find_all('div', class_='td-module-thumb')

    jobs = []
    for parent in parent_divs:
        job_link = parent.find('a', href=True)
        job_icon = parent.find('img', src=True)
        job_details = parent.find_next('div', class_='item-details')
        job_post_date = job_details.find('span', class_='td-post-date') if job_details else None
        if job_link and job_icon and job_post_date:
            jobs.append({
                'link': job_link['href'],
                'icon': job_icon['src'],
                'post_date': job_post_date.get_text(strip=True) if job_post_date else 'No date available'
            })

    return jobs

# Function to scrape job listings (main page from NCS)
def scrape_jobs_ncs():
    url = "https://www.ncs.gov.in/job-seeker/Pages/Search.aspx"
    response = requests.get(url)

    if response.status_code != 200:
        return [], 0

    soup = BeautifulSoup(response.text, 'html.parser')
    job_divs = soup.find_all('div', id='mytab')

    job_links = []
    for div in job_divs:
        link = div.find('a', onclick=True)
        if link:
            job_id = link['onclick'].split('ViewJobPopup(\'')[1].split('\')')[0]
            job_title_span = div.find('h5')
            job_company = div.find('a', class_='CheckBtn')
            extra_datas_span = div.find_all('span', class_='text-success')

            job_location = extra_datas_span[0].get_text(strip=True) if len(extra_datas_span) > 0 else "N/A"
            salary = extra_datas_span[1].get_text(strip=True) if len(extra_datas_span) > 1 else "N/A"
            skills = extra_datas_span[2].get_text(strip=True) if len(extra_datas_span) > 2 else "N/A"
            description = div.find('span', class_='ms-displayBlock wordBreak').get_text(strip=True)

            if job_title_span and job_company:
                job_title = job_title_span.get_text(strip=True)
                job_company = job_company.get_text(strip=True)
                job_links.append({
                    'title': job_title,
                    'job_location': job_location,
                    'salary': salary,
                    'skills': skills,
                    'company': job_company,
                    'url': job_id,
                    'description': description
                })

    return job_links, len(job_links)

# Function to fetch job details from a secondary page
def fetch_job_details(job):
    link = job['link']
    try:
        response = requests.get(link)
        if response.status_code != 200:
            return None

        secsoup = BeautifulSoup(response.text, 'html.parser')
        job_info = {}
        table = secsoup.find('table', class_='vk_jobInfo_table')

        if table:
            rows = table.find_all('tr')
            for row in rows:
                th = row.find('th').get_text(strip=True)
                td = row.find('td').get_text(strip=True)
                job_info[th] = td

        apply_link_tag = secsoup.select_one('p strong a[href]')
        apply_link = apply_link_tag['href'] if apply_link_tag else 'No Apply Link'

        if apply_link != 'No Apply Link':
            time.sleep(1) 
            response_tertiary = requests.get(apply_link)
            if response_tertiary.status_code == 200:
                tertiary_soup = BeautifulSoup(response_tertiary.text, 'html.parser')
                tertiary_apply_link_tag = tertiary_soup.find('a', class_='elementor-button elementor-button-link elementor-size-sm elementor-animation-shrink')
                original_apply_link = tertiary_apply_link_tag['href'] if tertiary_apply_link_tag else 'No Apply Link'
            else:
                original_apply_link = 'Failed to load tertiary page'
        else:
            original_apply_link = 'No Apply Link'

        return {
            'job_info': job_info,
            'apply_link': original_apply_link,
            'link': job['link'],
            'post_date': job['post_date'],
            'icon': job['icon']
        }
    except Exception as e:
        print(f"Error fetching job details for {link}: {e}")
        return None

@app.route('/scrapejobs', methods=['GET'])
def scrape_jobs():
    source = request.args.get('source', 'ncs')
    if source == 'geeksgod':
        job_links = scrape_jobs_geeksgod()
        page = request.args.get('page', 1, type=int)
        per_page = 10
        total_jobs = len(job_links)
        paginated_jobs = job_links[(page - 1) * per_page: page * per_page]

        with ThreadPoolExecutor() as executor:
            jobdata = list(executor.map(fetch_job_details, paginated_jobs))

        jobdata = [job for job in jobdata if job is not None]

        next_page = page + 1 if (page * per_page) < total_jobs else None
        prev_page = page - 1 if page > 1 else None

        return jsonify({
            'jobs': jobdata,
            'page': page,
            'per_page': per_page,
            'total_jobs': total_jobs,
            'next_page': next_page,
            'prev_page': prev_page
        })
    elif source == 'ncs':
        job_links, total_jobs = scrape_jobs_ncs()
        page = request.args.get('page', 1, type=int)
        per_page = 5
        paginated_jobs = job_links[(page - 1) * per_page: page * per_page]

        next_page = page + 1 if (page * per_page) < total_jobs else None
        prev_page = page - 1 if page > 1 else None

        return jsonify({
            'jobs': paginated_jobs,
            'page': page,
            'per_page': per_page,
            'total_jobs': total_jobs,
            'next_page': next_page,
            'prev_page': prev_page
        })
    else:
        return jsonify({'success': False, 'message': 'Invalid source specified'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=7000)

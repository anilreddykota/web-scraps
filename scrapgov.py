from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from flask_cors import CORS
app = Flask(__name__)
CORS(app)


# Function to scrape job listings (main page)
def scrape_jobs():
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

            # Ensure enough spans are available
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


# Pagination route with JSON response
@app.route('/')
def index():
    job_links, total_jobs = scrape_jobs()

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


if __name__ == '__main__':
    app.run(debug=True,port=7000)

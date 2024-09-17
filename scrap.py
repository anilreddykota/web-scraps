from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import time
from concurrent.futures import ThreadPoolExecutor
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

# Function to scrape job listings (main page)
def scrape_jobs():
    url = "https://geeksgod.com/category/off-campus-placement-drive-for-freshers/"
    response = requests.get(url)

    if response.status_code != 200:
        return [], 0

    soup = BeautifulSoup(response.text, 'html.parser')
    parent_divs = soup.find_all('div', class_='td-module-thumb')

    jobs = []

    # Collecting job links and icons
    for parent in parent_divs:
        job_link = parent.find('a', href=True)
        job_icon = parent.find('img', src=True)

        job_details = parent.find_next('div', class_='item-details')
        job_post_date = job_details.find('span',class_='td-post-date') if job_details else None  # Adjust as per actual HTML structure
        if job_link and job_icon and job_post_date:
            jobs.append({
                'link': job_link['href'],
                'icon': job_icon['src'],
                'post_date': job_post_date.get_text(strip=True) if job_post_date else 'No date available'
            })

    return jobs

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

# Pagination route with JSON response and parallel pipelining
@app.route('/')
def index():
    job_links = scrape_jobs()

    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of jobs per page
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

if __name__ == '__main__':
    app.run(debug=True,port=4200)

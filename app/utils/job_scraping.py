import requests
from bs4 import BeautifulSoup
import time

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

            job_link = f"https://www.ncs.gov.in/job-seeker/Pages/ViewJob.aspx?jobid={job_id}"
            job_links.append({
                'job_title': job_title_span.get_text(strip=True) if job_title_span else "N/A",
                'company': job_company.get_text(strip=True) if job_company else "N/A",
                'location': job_location,
                'salary': salary,
                'skills': skills,
                'link': job_link
            })

    return job_links, len(job_links)

def fetch_job_details(job):
    response = requests.get(job['link'])
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    job_description_div = soup.find('div', class_='job-description')

    return {
        'title': job.get('job_title'),
        'company': job.get('company'),
        'location': job.get('location'),
        'salary': job.get('salary'),
        'skills': job.get('skills'),
        'description': job_description_div.get_text(strip=True) if job_description_div else 'No description available'
    }


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


from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import time
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)


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
            time.sleep(1)  # Adding a delay for the tertiary request
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
    per_page = 5  # Number of jobs per page
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
    app.run(debug=True)

from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)


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
    app.run(debug=True)

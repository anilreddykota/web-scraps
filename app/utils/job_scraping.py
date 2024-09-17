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

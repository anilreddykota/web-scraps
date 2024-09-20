from flask import Blueprint, request, jsonify
from concurrent.futures import ThreadPoolExecutor
import time

from app.utils.job_scraping import scrape_jobs_geeksgod, scrape_jobs_ncs, fetch_job_details

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('/scrapejobs', methods=['GET'])
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

@jobs_bp.route('/scrapegovjobs', methods=['GET'])
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
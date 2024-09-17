from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Load configuration from config.py
    app.config.from_object('app.config.Config')
    
    # Register blueprints
    from app.routes.resume import resume_bp
    from app.routes.jobs import jobs_bp

    app.register_blueprint(resume_bp)
    app.register_blueprint(jobs_bp)

    return app

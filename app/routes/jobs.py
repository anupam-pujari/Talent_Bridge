from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models import Job, Application, User
from app.utils.email_helper import send_new_job_notification

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('/employee-dashboard')
@login_required
def employee_dashboard():
    # Get recent jobs
    recent_jobs = Job.query.filter_by(status='active').order_by(Job.created_at.desc()).limit(5).all()
    
    # Get user's applications
    my_applications = Application.query.filter_by(user_id=current_user.id)\
                                    .order_by(Application.applied_at.desc()).limit(5).all()
    
    return render_template('dashboard/employee_dashboard.html', 
                         recent_jobs=recent_jobs, my_applications=my_applications)

@jobs_bp.route('/hr-dashboard')
@login_required
def hr_dashboard():
    if current_user.role not in ['hr', 'manager']:
        flash('Access denied', 'danger')
        return redirect(url_for('jobs.employee_dashboard'))
    
    # Get job statistics
    total_jobs = Job.query.count()
    active_jobs = Job.query.filter_by(status='active').count()
    total_applications = Application.query.count()
    pending_applications = Application.query.filter_by(status='submitted').count()
    
    # Recent applications
    recent_applications = Application.query.order_by(Application.applied_at.desc()).limit(10).all()
    
    stats = {
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'total_applications': total_applications,
        'pending_applications': pending_applications
    }
    
    return render_template('dashboard/hr_dashboard.html', 
                         stats=stats, recent_applications=recent_applications)

@jobs_bp.route('/list')
@login_required
def job_list():
    page = request.args.get('page', 1, type=int)
    department = request.args.get('department', '')
    location = request.args.get('location', '')
    search = request.args.get('search', '')
    
    # Build query
    query = Job.query.filter_by(status='active')
    
    if department:
        query = query.filter(Job.department.ilike(f'%{department}%'))
    if location:
        query = query.filter(Job.location.ilike(f'%{location}%'))
    if search:
        query = query.filter(
            db.or_(
                Job.title.ilike(f'%{search}%'),
                Job.description.ilike(f'%{search}%'),
                Job.skills_required.ilike(f'%{search}%')
            )
        )
    
    jobs = query.order_by(Job.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # Get unique departments and locations for filters
    departments = db.session.query(Job.department.distinct()).all()
    locations = db.session.query(Job.location.distinct()).all()
    
    return render_template('jobs/job_list.html', 
                         jobs=jobs, departments=departments, locations=locations,
                         current_filters={'department': department, 'location': location, 'search': search})

@jobs_bp.route('/<int:job_id>')
@login_required
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    
    # Check if user already applied
    existing_application = None
    if current_user.role == 'employee':
        existing_application = Application.query.filter_by(
            job_id=job_id, user_id=current_user.id
        ).first()
    
    return render_template('jobs/job_detail.html', 
                         job=job, existing_application=existing_application)

@jobs_bp.route('/post', methods=['GET', 'POST'])
@login_required
def post_job():
    if current_user.role not in ['hr', 'manager']:
        flash('Access denied', 'danger')
        return redirect(url_for('jobs.job_list'))
    
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        department = request.form.get('department')
        location = request.form.get('location')
        description = request.form.get('description')
        requirements = request.form.get('requirements')
        skills_required = request.form.get('skills_required')
        salary_range = request.form.get('salary_range')
        job_type = request.form.get('job_type')
        deadline = request.form.get('deadline')
        
        # Create new job
        job = Job(
            title=title,
            department=department,
            location=location,
            description=description,
            requirements=requirements,
            skills_required=skills_required,
            salary_range=salary_range,
            job_type=job_type,
            posted_by=current_user.id
        )
        
        if deadline:
            job.deadline = datetime.strptime(deadline, '%Y-%m-%d')
        
        db.session.add(job)
        db.session.commit()
        
        # Send notification to relevant employees (optional)
        # You can implement logic to notify employees based on department/skills
        
        flash('Job posted successfully!', 'success')
        return redirect(url_for('jobs.job_detail', job_id=job.id))
    
    return render_template('jobs/post_job.html')

@jobs_bp.route('/<int:job_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)
    
    # Check permissions
    if current_user.role not in ['hr', 'manager'] and job.posted_by != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('jobs.job_detail', job_id=job_id))
    
    if request.method == 'POST':
        # Update job fields
        job.title = request.form.get('title')
        job.department = request.form.get('department')
        job.location = request.form.get('location')
        job.description = request.form.get('description')
        job.requirements = request.form.get('requirements')
        job.skills_required = request.form.get('skills_required')
        job.salary_range = request.form.get('salary_range')
        job.job_type = request.form.get('job_type')
        job.status = request.form.get('status')
        
        deadline = request.form.get('deadline')
        if deadline:
            job.deadline = datetime.strptime(deadline, '%Y-%m-%d')
        else:
            job.deadline = None
        
        job.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Job updated successfully!', 'success')
        return redirect(url_for('jobs.job_detail', job_id=job_id))
    
    return render_template('jobs/edit_job.html', job=job)

@jobs_bp.route('/<int:job_id>/delete', methods=['POST'])
@login_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    
    # Check permissions
    if current_user.role not in ['hr', 'manager'] and job.posted_by != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('jobs.job_detail', job_id=job_id))
    
    db.session.delete(job)
    db.session.commit()
    
    flash('Job deleted successfully!', 'success')
    return redirect(url_for('jobs.job_list'))

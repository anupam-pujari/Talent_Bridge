from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models import Job, Application
from app.utils.file_helper import save_uploaded_file, delete_file
from app.utils.email_helper import send_application_status_notification

applications_bp = Blueprint('applications', __name__)

@applications_bp.route('/apply/<int:job_id>', methods=['GET', 'POST'])
@login_required
def apply(job_id):
    job = Job.query.get_or_404(job_id)
    
    # Check if already applied
    existing_application = Application.query.filter_by(
        job_id=job_id, user_id=current_user.id
    ).first()
    
    if existing_application:
        flash('You have already applied to this job', 'warning')
        return redirect(url_for('jobs.job_detail', job_id=job_id))
    
    if request.method == 'POST':
        cover_letter = request.form.get('cover_letter')
        resume_file = request.files.get('resume')
        
        # Create application
        application = Application(
            job_id=job_id,
            user_id=current_user.id,
            cover_letter=cover_letter
        )
        
        # Handle resume upload
        if resume_file and resume_file.filename:
            filename = save_uploaded_file(resume_file)
            if filename:
                application.resume_filename = filename
            else:
                flash('Invalid file type. Please upload PDF, DOC, or DOCX files only.', 'danger')
                return render_template('applications/apply.html', job=job)
        
        db.session.add(application)
        db.session.commit()
        
        flash('Application submitted successfully!', 'success')
        return redirect(url_for('applications.my_applications'))
    
    return render_template('applications/apply.html', job=job)

@applications_bp.route('/my-applications')
@login_required
def my_applications():
    page = request.args.get('page', 1, type=int)
    applications = Application.query.filter_by(user_id=current_user.id)\
                                  .order_by(Application.applied_at.desc())\
                                  .paginate(page=page, per_page=10, error_out=False)
    
    return render_template('applications/my_applications.html', applications=applications)

@applications_bp.route('/manage')
@login_required
def manage_applications():
    if current_user.role not in ['hr', 'manager']:
        flash('Access denied', 'danger')
        return redirect(url_for('jobs.employee_dashboard'))
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    job_filter = request.args.get('job_id', type=int)
    
    query = Application.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    if job_filter:
        query = query.filter_by(job_id=job_filter)
    
    applications = query.order_by(Application.applied_at.desc())\
                       .paginate(page=page, per_page=20, error_out=False)
    
    # Get all jobs for filter dropdown
    jobs = Job.query.order_by(Job.title).all()
    
    return render_template('applications/manage_applications.html', 
                         applications=applications, jobs=jobs,
                         current_filters={'status': status_filter, 'job_id': job_filter})

@applications_bp.route('/<int:application_id>')
@login_required
def application_detail(application_id):
    application = Application.query.get_or_404(application_id)
    
    # Check permissions
    if current_user.role not in ['hr', 'manager'] and application.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('applications.my_applications'))
    
    return render_template('applications/application_detail.html', application=application)

@applications_bp.route('/<int:application_id>/update-status', methods=['POST'])
@login_required
def update_status(application_id):
    if current_user.role not in ['hr', 'manager']:
        flash('Access denied', 'danger')
        return redirect(url_for('applications.my_applications'))
    
    application = Application.query.get_or_404(application_id)
    new_status = request.form.get('status')
    hr_notes = request.form.get('hr_notes')
    
    old_status = application.status
    application.status = new_status
    application.hr_notes = hr_notes
    application.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    # Send notification email if status changed
    if old_status != new_status:
        send_application_status_notification(
            application.applicant.email,
            application.job.title,
            new_status
        )
    
    flash('Application status updated successfully!', 'success')
    return redirect(url_for('applications.application_detail', application_id=application_id))

@applications_bp.route('/<int:application_id>/withdraw', methods=['POST'])
@login_required
def withdraw_application(application_id):
    application = Application.query.get_or_404(application_id)
    
    # Check if user owns this application
    if application.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('applications.my_applications'))
    
    # Check if application can be withdrawn
    if application.status in ['offer', 'rejected']:
        flash('Cannot withdraw application in current status', 'warning')
        return redirect(url_for('applications.application_detail', application_id=application_id))
    
    application.status = 'withdrawn'
    application.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    flash('Application withdrawn successfully', 'info')
    return redirect(url_for('applications.my_applications'))

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models import Application, Interview
from app.utils.email_helper import send_interview_invitation

interviews_bp = Blueprint('interviews', __name__)

@interviews_bp.route('/schedule/<int:application_id>', methods=['GET', 'POST'])
@login_required
def schedule_interview(application_id):
    if current_user.role not in ['hr', 'manager']:
        flash('Access denied', 'danger')
        return redirect(url_for('jobs.employee_dashboard'))

    application = Application.query.get_or_404(application_id)

    if request.method == 'POST':
        # Get form data
        scheduled_date = request.form.get('scheduled_date')
        scheduled_time = request.form.get('scheduled_time')
        duration = int(request.form.get('duration', 60))
        interview_type = request.form.get('interview_type')
        location_or_link = request.form.get('location_or_link')
        interviewer_email = request.form.get('interviewer_email')
        notes = request.form.get('notes')

        # Combine date and time into datetime object
        try:
            interview_datetime = datetime.strptime(f"{scheduled_date} {scheduled_time}", '%Y-%m-%d %H:%M')
        except ValueError:
            flash('Invalid date or time format.', 'danger')
            return render_template('interviews/schedule.html', application=application)

        # Create Interview record
        interview = Interview(
            application_id=application.id,
            scheduled_date=interview_datetime,
            duration_minutes=duration,
            interview_type=interview_type,
            location_or_link=location_or_link,
            interviewer_email=interviewer_email,
            notes=notes,
            status='scheduled'
        )
        db.session.add(interview)

        # Update application status
        application.status = 'interview'
        application.updated_at = datetime.utcnow()

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash('Database error: unable to schedule the interview.', 'danger')
            return render_template('interviews/schedule.html', application=application)

        # Send email notification to candidate
        send_interview_invitation(
            application.applicant.email,
            application.job.title,
            interview_datetime,
            interview_type,
            location_or_link
        )

        flash('Interview scheduled successfully!', 'success')
        return redirect(url_for('applications.application_detail', application_id=application.id))

    # GET: render scheduling form
    return render_template('interviews/schedule.html', application=application)

@interviews_bp.route('/list')
@login_required
def interview_list():
    status_filter = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)

    if current_user.role == 'employee':
        # Employees see only their own interviews
        interviews = Interview.query.join(Application).filter(
            Application.user_id == current_user.id
        ).order_by(Interview.scheduled_date.asc()).all()
        return render_template('interviews/my_interviews.html', interviews=interviews)

    # HR and managers see all interviews, optionally filtered by status
    query = Interview.query
    if status_filter:
        query = query.filter_by(status=status_filter)

    interviews = query.order_by(Interview.scheduled_date.asc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('interviews/interview_list.html', interviews=interviews, current_filter=status_filter)

@interviews_bp.route('/<int:interview_id>/update', methods=['POST'])
@login_required
def update_interview(interview_id):
    if current_user.role not in ['hr', 'manager']:
        flash('Access denied', 'danger')
        return redirect(url_for('interviews.interview_list'))

    interview = Interview.query.get_or_404(interview_id)
    new_status = request.form.get('status')
    notes = request.form.get('notes')

    if new_status:
        interview.status = new_status
    if notes is not None:
        interview.notes = notes
    interview.updated_at = datetime.utcnow()

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Error updating interview.', 'danger')
        return redirect(url_for('interviews.interview_list'))

    flash('Interview updated successfully!', 'success')
    return redirect(url_for('interviews.interview_list'))

@interviews_bp.route('/<int:interview_id>/reschedule', methods=['GET', 'POST'])
@login_required
def reschedule_interview(interview_id):
    if current_user.role not in ['hr', 'manager']:
        flash('Access denied', 'danger')
        return redirect(url_for('interviews.interview_list'))

    interview = Interview.query.get_or_404(interview_id)

    if request.method == 'POST':
        scheduled_date = request.form.get('scheduled_date')
        scheduled_time = request.form.get('scheduled_time')

        try:
            new_datetime = datetime.strptime(f"{scheduled_date} {scheduled_time}", '%Y-%m-%d %H:%M')
        except ValueError:
            flash('Invalid date or time format.', 'danger')
            return render_template('interviews/reschedule.html', interview=interview)

        interview.scheduled_date = new_datetime
        interview.status = 'rescheduled'
        interview.updated_at = datetime.utcnow()

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Error rescheduling interview.', 'danger')
            return render_template('interviews/reschedule.html', interview=interview)

        # Notify candidate of rescheduled interview
        send_interview_invitation(
            interview.application.applicant.email,
            interview.application.job.title,
            new_datetime,
            interview.interview_type,
            interview.location_or_link
        )

        flash('Interview rescheduled successfully!', 'success')
        return redirect(url_for('interviews.interview_list'))

    # GET: render reschedule form
    return render_template('interviews/reschedule.html', interview=interview)

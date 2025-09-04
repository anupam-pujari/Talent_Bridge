from flask_mail import Message
from app import mail
from flask import current_app

def send_email(to, subject, template, **kwargs):
    msg = Message(
        subject=subject,
        recipients=[to] if isinstance(to, str) else to,
        html=template,
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def send_application_status_notification(user_email, job_title, status):
    subject = f"Application Status Update - {job_title}"
    template = f"""
    <h2>Application Status Update</h2>
    <p>Dear Candidate,</p>
    <p>Your application status for the position <strong>{job_title}</strong> has been updated to: <strong>{status.title()}</strong></p>
    <p>Please log in to the TalentBridge portal for more details.</p>
    <p>Best regards,<br>HR Team</p>
    """
    return send_email(user_email, subject, template)

def send_interview_invitation(user_email, job_title, interview_date, interview_type, location_or_link):
    subject = f"Interview Invitation - {job_title}"
    template = f"""
    <h2>Interview Invitation</h2>
    <p>Dear Candidate,</p>
    <p>Congratulations! You have been selected for an interview for the position <strong>{job_title}</strong>.</p>
    <p><strong>Interview Details:</strong></p>
    <ul>
        <li>Date & Time: {interview_date.strftime('%B %d, %Y at %I:%M %p')}</li>
        <li>Type: {interview_type.title()}</li>
        <li>Location/Link: {location_or_link}</li>
    </ul>
    <p>Please confirm your attendance by logging into the TalentBridge portal.</p>
    <p>Best regards,<br>HR Team</p>
    """
    return send_email(user_email, subject, template)

def send_new_job_notification(user_email, job_title, department):
    subject = f"New Job Opportunity - {job_title}"
    template = f"""
    <h2>New Job Opportunity</h2>
    <p>Dear Team Member,</p>
    <p>A new job opportunity has been posted that might interest you:</p>
    <p><strong>Position:</strong> {job_title}</p>
    <p><strong>Department:</strong> {department}</p>
    <p>Visit the TalentBridge portal to view details and apply.</p>
    <p>Best regards,<br>HR Team</p>
    """
    return send_email(user_email, subject, template)

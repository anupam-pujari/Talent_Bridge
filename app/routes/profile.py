from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.utils.file_helper import save_uploaded_file, delete_file

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/')
@login_required
def profile():
    """Display current user's profile"""
    return render_template('profile/profile.html')


@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """
    Allow users to edit their profile details and upload resume.
    """
    if request.method == 'POST':
        # Update profile fields from form data
        current_user.first_name = request.form.get('first_name', '').strip()
        current_user.last_name = request.form.get('last_name', '').strip()
        current_user.department = request.form.get('department', '').strip()
        current_user.location = request.form.get('location', '').strip()
        current_user.phone = request.form.get('phone', '').strip()
        current_user.skills = request.form.get('skills', '').strip()

        # Handle resume file upload if provided
        resume_file = request.files.get('resume')
        if resume_file and resume_file.filename:
            # Delete old resume file if exists
            if current_user.resume_filename:
                delete_file(current_user.resume_filename)

            # Save new uploaded resume
            filename = save_uploaded_file(resume_file)
            if filename:
                current_user.resume_filename = filename
            else:
                flash('Invalid file type. Please upload PDF, DOC, or DOCX only.', 'danger')
                return render_template('profile/edit_profile.html')

        # Commit changes to database
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile.profile'))
        except Exception as e:
            db.session.rollback()
            flash('There was an error updating your profile. Please try again.', 'danger')
            return render_template('profile/edit_profile.html')

    # GET request, render edit form prefilled with existing data
    return render_template('profile/edit_profile.html')


@profile_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """
    Allow user to change their password with validation.
    """
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Verify current password correctness
        if not check_password_hash(current_user.password, current_password):
            flash('Current password is incorrect.', 'danger')
            return render_template('profile/change_password.html')

        # Check new password confirmation
        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return render_template('profile/change_password.html')

        if len(new_password) < 8:
            flash('New password must be at least 8 characters long.', 'danger')
            return render_template('profile/change_password.html')

        # Update password hash in database
        current_user.password = generate_password_hash(new_password)
        try:
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('profile.profile'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to change password. Please try again.', 'danger')
            return render_template('profile/change_password.html')

    return render_template('profile/change_password.html')

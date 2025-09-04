// TalentBridge Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Form validation enhancement
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // File upload preview
    var fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function(event) {
            var file = event.target.files[0];
            var preview = document.getElementById('file-preview-' + this.id);
            
            if (file && preview) {
                var fileName = file.name;
                var fileSize = (file.size / 1024 / 1024).toFixed(2); // MB
                preview.innerHTML = `
                    <div class="alert alert-info">
                        <i class="fas fa-file"></i> ${fileName} (${fileSize} MB)
                    </div>
                `;
            }
        });
    });

    // Search functionality enhancement
    var searchInputs = document.querySelectorAll('input[type="search"], .search-input');
    searchInputs.forEach(function(input) {
        var timeout;
        input.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(function() {
                // Trigger search after 500ms of no typing
                if (input.value.length >= 3 || input.value.length === 0) {
                    // You can implement live search here
                }
            }, 500);
        });
    });

    // Confirmation dialogs
    var confirmButtons = document.querySelectorAll('[data-confirm]');
    confirmButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            var message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });

    // Status update handling
    var statusSelects = document.querySelectorAll('.status-update-select');
    statusSelects.forEach(function(select) {
        select.addEventListener('change', function() {
            var form = this.closest('form');
            if (form && confirm('Are you sure you want to update the status?')) {
                form.submit();
            }
        });
    });

    // Dynamic form fields
    var skillsInputs = document.querySelectorAll('input[name="skills_required"], input[name="skills"]');
    skillsInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            var skills = this.value.split(',');
            var preview = document.getElementById('skills-preview-' + this.name);
            
            if (preview) {
                preview.innerHTML = '';
                skills.forEach(function(skill) {
                    skill = skill.trim();
                    if (skill) {
                        var badge = document.createElement('span');
                        badge.className = 'badge bg-primary me-1 mb-1';
                        badge.textContent = skill;
                        preview.appendChild(badge);
                    }
                });
            }
        });
    });

    // Interview type field updates
    var interviewTypeSelects = document.querySelectorAll('select[name="interview_type"]');
    interviewTypeSelects.forEach(function(select) {
        select.addEventListener('change', function() {
            var locationField = document.querySelector('input[name="location_or_link"]');
            if (locationField) {
                var placeholder = '';
                switch(this.value) {
                    case 'in-person':
                        placeholder = 'Conference Room B, Building A';
                        break;
                    case 'video':
                        placeholder = 'https://zoom.us/j/123456789';
                        break;
                    case 'phone':
                        placeholder = 'Phone number or conference line';
                        break;
                }
                locationField.placeholder = placeholder;
            }
        });
    });

    // Password strength indicator
    var passwordInputs = document.querySelectorAll('input[type="password"][name="new_password"]');
    passwordInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            var strength = checkPasswordStrength(this.value);
            var indicator = document.getElementById('password-strength-' + this.name);
            
            if (indicator) {
                var strengthClass = '';
                var strengthText = '';
                
                switch(strength) {
                    case 0:
                        strengthClass = 'bg-danger';
                        strengthText = 'Very Weak';
                        break;
                    case 1:
                        strengthClass = 'bg-warning';
                        strengthText = 'Weak';
                        break;
                    case 2:
                        strengthClass = 'bg-info';
                        strengthText = 'Fair';
                        break;
                    case 3:
                        strengthClass = 'bg-primary';
                        strengthText = 'Good';
                        break;
                    case 4:
                        strengthClass = 'bg-success';
                        strengthText = 'Strong';
                        break;
                }
                
                indicator.innerHTML = `
                    <div class="progress mt-2" style="height: 5px;">
                        <div class="progress-bar ${strengthClass}" style="width: ${(strength + 1) * 20}%"></div>
                    </div>
                    <small class="text-muted">${strengthText}</small>
                `;
            }
        });
    });

    // Smooth scrolling for anchor links
    var anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(function(link) {
        link.addEventListener('click', function(event) {
            var target = document.querySelector(this.getAttribute('href'));
            if (target) {
                event.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

// Utility functions
function checkPasswordStrength(password) {
    var strength = 0;
    
    if (password.length >= 8) strength++;
    if (password.match(/[a-z]/)) strength++;
    if (password.match(/[A-Z]/)) strength++;
    if (password.match(/[0-9]/)) strength++;
    if (password.match(/[^a-zA-Z0-9]/)) strength++;
    
    return Math.min(strength, 4);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    var k = 1024;
    var sizes = ['Bytes', 'KB', 'MB', 'GB'];
    var i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function debounce(func, wait, immediate) {
    var timeout;
    return function() {
        var context = this, args = arguments;
        var later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        var callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

// Export for use in other scripts
window.TalentBridge = {
    checkPasswordStrength: checkPasswordStrength,
    formatFileSize: formatFileSize,
    debounce: debounce
};

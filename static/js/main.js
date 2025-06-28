/**
 * IntelliTutor - Main JavaScript File
 * Handles interactive features and UI enhancements
 */

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeIntelliTutor();
});

/**
 * Main initialization function
 */
function initializeIntelliTutor() {
    initializeTooltips();
    initializeProgressAnimations();
    initializeFormValidation();
    initializeAutoSave();
    initializeKeyboardShortcuts();
    initializeThemeToggle();
    initializeSearchAndFilter();
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Animate progress bars and counters
 */
function initializeProgressAnimations() {
    const progressBars = document.querySelectorAll('.progress-bar');
    const counters = document.querySelectorAll('[data-counter]');

    // Animate progress bars
    progressBars.forEach(bar => {
        const targetWidth = bar.style.width;
        bar.style.width = '0%';
        
        setTimeout(() => {
            bar.style.transition = 'width 1s ease-in-out';
            bar.style.width = targetWidth;
        }, 300);
    });

    // Animate counters
    counters.forEach(counter => {
        animateCounter(counter);
    });
}

/**
 * Animate number counters
 */
function animateCounter(element) {
    const target = parseInt(element.getAttribute('data-counter'));
    const duration = 1000;
    const step = target / (duration / 16);
    let current = 0;

    const timer = setInterval(() => {
        current += step;
        element.textContent = Math.floor(current);

        if (current >= target) {
            element.textContent = target;
            clearInterval(timer);
        }
    }, 16);
}

/**
 * Enhanced form validation
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Focus on first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                    showFieldError(firstInvalid);
                }
            }
            
            form.classList.add('was-validated');
        });

        // Real-time validation
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });

            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid')) {
                    validateField(this);
                }
            });
        });
    });
}

/**
 * Validate individual form field
 */
function validateField(field) {
    const isValid = field.checkValidity();
    
    field.classList.remove('is-valid', 'is-invalid');
    field.classList.add(isValid ? 'is-valid' : 'is-invalid');
    
    if (!isValid) {
        showFieldError(field);
    }
}

/**
 * Show field-specific error message
 */
function showFieldError(field) {
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        const fieldName = field.getAttribute('name') || 'Field';
        const errorType = field.validity;
        
        let message = 'Please check this field.';
        
        if (errorType.valueMissing) {
            message = `${fieldName} is required.`;
        } else if (errorType.typeMismatch) {
            message = `Please enter a valid ${field.type}.`;
        } else if (errorType.tooShort) {
            message = `${fieldName} must be at least ${field.minLength} characters.`;
        } else if (errorType.tooLong) {
            message = `${fieldName} must be no more than ${field.maxLength} characters.`;
        }
        
        errorDiv.textContent = message;
    }
}

/**
 * Auto-save functionality for forms
 */
function initializeAutoSave() {
    const autoSaveForms = document.querySelectorAll('[data-autosave]');
    
    autoSaveForms.forEach(form => {
        const formId = form.getAttribute('data-autosave');
        
        // Load saved data
        loadFormData(form, formId);
        
        // Save on input
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('input', debounce(() => {
                saveFormData(form, formId);
            }, 1000));
        });
        
        // Clear saved data on successful submit
        form.addEventListener('submit', function() {
            setTimeout(() => {
                clearFormData(formId);
            }, 100);
        });
    });
}

/**
 * Save form data to localStorage
 */
function saveFormData(form, formId) {
    const data = new FormData(form);
    const jsonData = {};
    
    for (let [key, value] of data.entries()) {
        jsonData[key] = value;
    }
    
    localStorage.setItem(`intellitutor_autosave_${formId}`, JSON.stringify(jsonData));
    showAutoSaveIndicator();
}

/**
 * Load form data from localStorage
 */
function loadFormData(form, formId) {
    const savedData = localStorage.getItem(`intellitutor_autosave_${formId}`);
    
    if (savedData) {
        try {
            const data = JSON.parse(savedData);
            
            Object.keys(data).forEach(key => {
                const field = form.querySelector(`[name="${key}"]`);
                if (field) {
                    field.value = data[key];
                }
            });
            
            showAutoLoadIndicator();
        } catch (e) {
            console.error('Error loading saved form data:', e);
        }
    }
}

/**
 * Clear saved form data
 */
function clearFormData(formId) {
    localStorage.removeItem(`intellitutor_autosave_${formId}`);
}

/**
 * Show auto-save indicator
 */
function showAutoSaveIndicator() {
    showToast('Draft saved automatically', 'success', 2000);
}

/**
 * Show auto-load indicator
 */
function showAutoLoadIndicator() {
    showToast('Previous draft loaded', 'info', 3000);
}

/**
 * Initialize keyboard shortcuts
 */
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(event) {
        // Ctrl/Cmd + Enter to submit forms
        if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
            const activeForm = document.querySelector('form:focus-within');
            if (activeForm) {
                const submitBtn = activeForm.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.click();
                }
            }
        }
        
        // Escape to close modals
        if (event.key === 'Escape') {
            const activeModal = document.querySelector('.modal.show');
            if (activeModal) {
                const modal = bootstrap.Modal.getInstance(activeModal);
                if (modal) {
                    modal.hide();
                }
            }
        }
        
        // Alt + D for dashboard
        if (event.altKey && event.key === 'd') {
            event.preventDefault();
            const dashboardLink = document.querySelector('a[href*="dashboard"]');
            if (dashboardLink) {
                dashboardLink.click();
            }
        }
    });
}

/**
 * Theme toggle functionality
 */
function initializeThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    
    if (themeToggle) {
        // Load saved theme
        const savedTheme = localStorage.getItem('intellitutor_theme') || 'light';
        setTheme(savedTheme);
        
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.body.getAttribute('data-theme') || 'light';
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            setTheme(newTheme);
            localStorage.setItem('intellitutor_theme', newTheme);
        });
    }
}

/**
 * Set application theme
 */
function setTheme(theme) {
    document.body.setAttribute('data-theme', theme);
    
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        const icon = themeToggle.querySelector('i');
        if (icon) {
            icon.className = theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
        }
    }
}

/**
 * Initialize search and filter functionality
 */
function initializeSearchAndFilter() {
    const searchInputs = document.querySelectorAll('[data-search]');
    
    searchInputs.forEach(input => {
        const targetSelector = input.getAttribute('data-search');
        
        input.addEventListener('input', debounce(function() {
            filterElements(this.value, targetSelector);
        }, 300));
    });
}

/**
 * Filter elements based on search term
 */
function filterElements(searchTerm, targetSelector) {
    const elements = document.querySelectorAll(targetSelector);
    const term = searchTerm.toLowerCase();
    
    elements.forEach(element => {
        const text = element.textContent.toLowerCase();
        const shouldShow = text.includes(term);
        
        element.style.display = shouldShow ? '' : 'none';
        
        // Add highlight to matching text
        if (shouldShow && term) {
            highlightText(element, term);
        } else {
            removeHighlight(element);
        }
    });
}

/**
 * Highlight matching text
 */
function highlightText(element, term) {
    const walker = document.createTreeWalker(
        element,
        NodeFilter.SHOW_TEXT,
        null,
        false
    );
    
    const textNodes = [];
    let node;
    
    while (node = walker.nextNode()) {
        textNodes.push(node);
    }
    
    textNodes.forEach(textNode => {
        const text = textNode.textContent;
        const regex = new RegExp(`(${term})`, 'gi');
        
        if (regex.test(text)) {
            const highlightedText = text.replace(regex, '<mark>$1</mark>');
            const span = document.createElement('span');
            span.innerHTML = highlightedText;
            textNode.parentNode.replaceChild(span, textNode);
        }
    });
}

/**
 * Remove text highlighting
 */
function removeHighlight(element) {
    const marks = element.querySelectorAll('mark');
    marks.forEach(mark => {
        mark.outerHTML = mark.innerHTML;
    });
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info', duration = 5000) {
    const toastContainer = getToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas fa-${getToastIcon(type)} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast, { delay: duration });
    bsToast.show();
    
    // Remove toast element after hiding
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

/**
 * Get or create toast container
 */
function getToastContainer() {
    let container = document.getElementById('toastContainer');
    
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '1060';
        document.body.appendChild(container);
    }
    
    return container;
}

/**
 * Get icon for toast type
 */
function getToastIcon(type) {
    const icons = {
        success: 'check-circle',
        error: 'exclamation-triangle',
        warning: 'exclamation-circle',
        info: 'info-circle'
    };
    
    return icons[type] || 'info-circle';
}

/**
 * Debounce function to limit function calls
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Utility function to copy text to clipboard
 */
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showToast('Copied to clipboard', 'success', 2000);
        }).catch(err => {
            console.error('Failed to copy text: ', err);
            showToast('Failed to copy text', 'error');
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showToast('Copied to clipboard', 'success', 2000);
    }
}

/**
 * Utility function to format dates
 */
function formatDate(date, options = {}) {
    const defaultOptions = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    
    const formatOptions = { ...defaultOptions, ...options };
    return new Intl.DateTimeFormat('en-US', formatOptions).format(new Date(date));
}

/**
 * Utility function to format numbers
 */
function formatNumber(number, options = {}) {
    return new Intl.NumberFormat('en-US', options).format(number);
}

/**
 * Add smooth scrolling to anchor links
 */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

/**
 * Initialize lazy loading for images
 */
function initializeLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        images.forEach(img => imageObserver.observe(img));
    } else {
        // Fallback for older browsers
        images.forEach(img => {
            img.src = img.dataset.src;
            img.classList.remove('lazy');
        });
    }
}

// Initialize lazy loading when DOM is ready
document.addEventListener('DOMContentLoaded', initializeLazyLoading);

// Export functions for use in other scripts
window.IntelliTutor = {
    showToast,
    copyToClipboard,
    formatDate,
    formatNumber,
    debounce
};

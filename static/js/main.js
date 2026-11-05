/**
 * AI Resume & Job Description Matcher
 * Client-side Interactivity & Utilities
 */

document.addEventListener('DOMContentLoaded', () => {
    // Auto-dismiss alert notifications after 5 seconds
    const alerts = document.querySelectorAll('.custom-alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });

    // Copy skill tag to clipboard on click
    const skillBadges = document.querySelectorAll('.skill-badge');
    skillBadges.forEach(badge => {
        badge.style.cursor = 'pointer';
        badge.setAttribute('title', 'Click to copy skill name');

        badge.addEventListener('click', async () => {
            const skillText = badge.textContent.trim();
            try {
                await navigator.clipboard.writeText(skillText);
                const originalHtml = badge.innerHTML;
                badge.innerHTML = `<i class="fa-solid fa-check me-1"></i> Copied!`;
                badge.style.opacity = '0.8';
                setTimeout(() => {
                    badge.innerHTML = originalHtml;
                    badge.style.opacity = '1';
                }, 1200);
            } catch (err) {
                console.error('Clipboard copy failed:', err);
            }
        });
    });

    // Validate uploaded file size (< 16 MB)
    const fileInput = document.getElementById('resumeFileInput');
    if (fileInput) {
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                const file = fileInput.files[0];
                const maxSizeBytes = 16 * 1024 * 1024;
                if (file.size > maxSizeBytes) {
                    alert(`The selected file (${(file.size / (1024 * 1024)).toFixed(2)} MB) exceeds the 16 MB limit.`);
                    fileInput.value = '';
                    const display = document.getElementById('fileSelectedDisplay');
                    if (display) display.classList.add('d-none');
                }
            }
        });
    }

    console.log('⚡ AI Resume & Job Description Matcher initialized.');
});

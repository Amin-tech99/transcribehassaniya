// Main JavaScript for Hassaniya Arabic Transcription App

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Handle audio playback controls
    setupAudioControls();
    
    // Handle tab persistence
    setupTabPersistence();
    
    // Handle form submissions
    setupFormSubmissions();
});

function setupAudioControls() {
    // Get all audio players on the page
    const audioPlayers = document.querySelectorAll('audio');
    
    // Add event listeners to each audio player
    audioPlayers.forEach(player => {
        // Reset playback rate when loading a new page
        player.playbackRate = 1.0;
        
        // Add keyboard shortcut for play/pause (handled in specific pages)
    });
}

function setupTabPersistence() {
    // Get all tab elements
    const triggerTabList = [].slice.call(document.querySelectorAll('#task-tabs button'));
    
    // Check if we have tabs on this page
    if (triggerTabList.length > 0) {
        // Get active tab from localStorage if available
        const activeTabId = localStorage.getItem('activeTab');
        
        if (activeTabId) {
            const activeTab = document.querySelector(`#${activeTabId}`);
            if (activeTab) {
                const tab = new bootstrap.Tab(activeTab);
                tab.show();
            }
        }
        
        // Store the active tab when a tab is clicked
        triggerTabList.forEach(function(triggerEl) {
            triggerEl.addEventListener('shown.bs.tab', function(event) {
                localStorage.setItem('activeTab', event.target.id);
            });
        });
    }
}

function setupFormSubmissions() {
    // Get all forms with the preventDoubleSubmission class
    const forms = document.querySelectorAll('form.prevent-double-submission');
    
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            // Disable all submit buttons in this form
            const buttons = this.querySelectorAll('button[type="submit"]');
            buttons.forEach(button => {
                const originalText = button.innerHTML;
                button.disabled = true;
                button.innerHTML = '<i class="fas fa-circle-notch fa-spin me-2"></i>Processing...';
                
                // Store original text for reference (though we'll likely navigate away)
                button.dataset.originalText = originalText;
            });
        });
    });
}

// Utility function to format time in seconds to MM:SS format
function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

// Function to handle clip assignment checkboxes
function toggleAllClips(source) {
    const checkboxes = document.getElementsByClassName('clip-checkbox');
    for (let i = 0; i < checkboxes.length; i++) {
        checkboxes[i].checked = source.checked;
    }
}

/**
 * Upload Module - File Handling
 * Contribution Truth
 */

const Upload = {
    gitFile: null,
    transcriptFile: null,

    /**
     * Initialize upload handlers
     */
    init() {
        const gitInput = document.getElementById('git-file');
        const transcriptInput = document.getElementById('transcript-file');

        if (gitInput) {
            gitInput.addEventListener('change', (e) => this.handleFileSelect(e, 'git'));
        }

        if (transcriptInput) {
            transcriptInput.addEventListener('change', (e) => this.handleFileSelect(e, 'transcript'));
        }

        // Setup drag and drop
        this.setupDragDrop('git-upload', 'git');
        this.setupDragDrop('transcript-upload', 'transcript');
    },

    /**
     * Handle file selection
     */
    handleFileSelect(event, type) {
        const file = event.target.files[0];
        if (!file) return;

        if (type === 'git') {
            this.gitFile = file;
            this.updateFileDisplay('git-upload', 'git-filename', file.name);
        } else {
            this.transcriptFile = file;
            this.updateFileDisplay('transcript-upload', 'transcript-filename', file.name);
        }

        this.updateUploadButton();
    },

    /**
     * Update file display in UI
     */
    updateFileDisplay(boxId, filenameId, name) {
        const box = document.getElementById(boxId);
        const filenameEl = document.getElementById(filenameId);

        if (box) box.classList.add('has-file');
        if (filenameEl) filenameEl.textContent = `✓ ${name}`;
    },

    /**
     * Setup drag and drop for upload boxes
     */
    setupDragDrop(boxId, type) {
        const box = document.getElementById(boxId);
        if (!box) return;

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            box.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            box.addEventListener(eventName, () => {
                box.style.borderColor = 'var(--accent-primary)';
                box.style.background = 'rgba(99, 102, 241, 0.1)';
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            box.addEventListener(eventName, () => {
                box.style.borderColor = '';
                box.style.background = '';
            });
        });

        box.addEventListener('drop', (e) => {
            const file = e.dataTransfer.files[0];
            if (!file) return;

            // Update the file input
            const input = document.getElementById(type === 'git' ? 'git-file' : 'transcript-file');
            const dt = new DataTransfer();
            dt.items.add(file);
            input.files = dt.files;

            // Trigger change event
            input.dispatchEvent(new Event('change'));
        });
    },

    /**
     * Update upload button state
     */
    updateUploadButton() {
        const btn = document.getElementById('upload-btn');
        if (btn) {
            btn.disabled = !this.gitFile && !this.transcriptFile;
        }
    },

    /**
     * Get selected files
     */
    getFiles() {
        return {
            gitFile: this.gitFile,
            transcriptFile: this.transcriptFile
        };
    },

    /**
     * Clear all files
     */
    clear() {
        this.gitFile = null;
        this.transcriptFile = null;

        ['git-upload', 'transcript-upload'].forEach(id => {
            const box = document.getElementById(id);
            if (box) box.classList.remove('has-file');
        });

        ['git-filename', 'transcript-filename'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = '';
        });

        ['git-file', 'transcript-file'].forEach(id => {
            const input = document.getElementById(id);
            if (input) input.value = '';
        });

        this.updateUploadButton();
    }
};

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Upload;
}

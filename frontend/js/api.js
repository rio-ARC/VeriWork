/**
 * API Module - Backend Communication
 * Contribution Truth
 */

const API = {
    // Auto-detect: use localhost in development, or configure the deployed backend URL
    // UPDATE THIS after deploying backend to Render!
    BASE_URL: window.location.hostname === 'localhost'
        ? 'http://localhost:8000'
        : 'https://contribution-truth-api.onrender.com',  // <-- Update after Render deploy

    /**
     * Check API health and Gemini configuration
     */
    async checkHealth() {
        try {
            const response = await fetch(`${this.BASE_URL}/health`);
            if (!response.ok) throw new Error('API not available');
            return await response.json();
        } catch (error) {
            console.error('Health check failed:', error);
            return { status: 'error', gemini_api_configured: false };
        }
    },

    /**
     * Upload evidence files (git log + transcript)
     */
    async uploadEvidence(gitLogFile, transcriptFile) {
        const formData = new FormData();

        if (gitLogFile) {
            formData.append('git_log', gitLogFile);
        }
        if (transcriptFile) {
            formData.append('transcript', transcriptFile);
        }

        const response = await fetch(`${this.BASE_URL}/api/evidence/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }

        return await response.json();
    },

    /**
     * Verify a contribution claim
     */
    async verifyClaim(claimant, claim) {
        const response = await fetch(`${this.BASE_URL}/api/verify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ claimant, claim })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Verification failed');
        }

        return await response.json();
    }
};

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = API;
}

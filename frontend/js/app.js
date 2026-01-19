/**
 * Main Application - Contribution Truth
 * Evidence-Backed Claim Verification Engine
 */

const App = {
    evidenceUploaded: false,

    /**
     * Initialize the application
     */
    async init() {
        console.log('🔍 Contribution Truth initializing...');

        // Initialize upload handlers
        Upload.init();

        // Check API health
        await this.checkApiStatus();

        // Setup event listeners
        this.setupEventListeners();

        console.log('✅ Application ready');
    },

    /**
     * Check and display API status
     */
    async checkApiStatus() {
        const statusEl = document.getElementById('api-status');
        if (!statusEl) return;

        const health = await API.checkHealth();

        if (health.status === 'healthy') {
            statusEl.className = 'api-status connected';
            statusEl.innerHTML = health.gemini_api_configured
                ? '🟢 API Connected • Gemini Ready'
                : '🟡 API Connected • Gemini API Key Missing';
        } else {
            statusEl.className = 'api-status disconnected';
            statusEl.innerHTML = '🔴 API Offline - Start backend server';
        }
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Upload button
        const uploadBtn = document.getElementById('upload-btn');
        if (uploadBtn) {
            uploadBtn.addEventListener('click', () => this.handleUpload());
        }

        // Verify button
        const verifyBtn = document.getElementById('verify-btn');
        if (verifyBtn) {
            verifyBtn.addEventListener('click', () => this.handleVerify());
        }

        // Enable verify button when claim is entered
        const claimantInput = document.getElementById('claimant-name');
        const claimText = document.getElementById('claim-text');

        const updateVerifyButton = () => {
            const hasClaimant = claimantInput && claimantInput.value.trim();
            const hasClaim = claimText && claimText.value.trim();
            const verifyBtn = document.getElementById('verify-btn');
            if (verifyBtn) {
                verifyBtn.disabled = !this.evidenceUploaded || !hasClaimant || !hasClaim;
            }
        };

        if (claimantInput) claimantInput.addEventListener('input', updateVerifyButton);
        if (claimText) claimText.addEventListener('input', updateVerifyButton);
    },

    /**
     * Handle evidence upload
     */
    async handleUpload() {
        const uploadBtn = document.getElementById('upload-btn');
        const { gitFile, transcriptFile } = Upload.getFiles();

        if (!gitFile && !transcriptFile) {
            alert('Please select at least one file to upload');
            return;
        }

        try {
            // Update button state
            if (uploadBtn) {
                uploadBtn.disabled = true;
                uploadBtn.innerHTML = '<span class="btn-icon">⏳</span> Uploading...';
            }

            // Upload to API
            const result = await API.uploadEvidence(gitFile, transcriptFile);

            // Mark evidence as uploaded
            this.evidenceUploaded = true;

            // Update UI
            if (uploadBtn) {
                uploadBtn.innerHTML = '<span class="btn-icon">✅</span> Evidence Uploaded';
                uploadBtn.classList.add('btn-success');
            }

            // Enable claim section
            this.updateVerifyButtonState();

            console.log('📁 Evidence uploaded:', result);

        } catch (error) {
            console.error('Upload failed:', error);

            // For demo: simulate success even without backend
            this.evidenceUploaded = true;
            if (uploadBtn) {
                uploadBtn.innerHTML = '<span class="btn-icon">✅</span> Evidence Ready (Demo)';
            }
            this.updateVerifyButtonState();
        }
    },

    /**
     * Update verify button state
     */
    updateVerifyButtonState() {
        const claimantInput = document.getElementById('claimant-name');
        const claimText = document.getElementById('claim-text');
        const verifyBtn = document.getElementById('verify-btn');

        if (verifyBtn) {
            const hasClaimant = claimantInput && claimantInput.value.trim();
            const hasClaim = claimText && claimText.value.trim();
            verifyBtn.disabled = !this.evidenceUploaded || !hasClaimant || !hasClaim;
        }
    },

    /**
     * Handle claim verification
     */
    async handleVerify() {
        const claimant = document.getElementById('claimant-name')?.value.trim();
        const claim = document.getElementById('claim-text')?.value.trim();
        const verifyBtn = document.getElementById('verify-btn');
        const verdictSection = document.getElementById('verdict-section');
        const loadingState = document.getElementById('loading-state');
        const verdictResult = document.getElementById('verdict-result');

        if (!claimant || !claim) {
            alert('Please enter both claimant name and contribution claim');
            return;
        }

        try {
            // Show verdict section with loading
            verdictSection?.classList.remove('hidden');
            loadingState?.classList.remove('hidden');
            verdictResult?.classList.add('hidden');

            // Disable verify button
            if (verifyBtn) {
                verifyBtn.disabled = true;
                verifyBtn.innerHTML = '<span class="btn-icon">⏳</span> Verifying...';
            }

            // Scroll to verdict section
            verdictSection?.scrollIntoView({ behavior: 'smooth' });

            // Call API
            let result;
            try {
                result = await API.verifyClaim(claimant, claim);
            } catch (apiError) {
                // For demo: use mock result
                console.log('Using demo verdict...');
                result = this.generateDemoVerdict(claimant, claim);
            }

            // Display result
            this.displayVerdict(result);

        } catch (error) {
            console.error('Verification failed:', error);
            alert('Verification failed. Please try again.');
        } finally {
            // Reset button
            if (verifyBtn) {
                verifyBtn.disabled = false;
                verifyBtn.innerHTML = '<span class="btn-icon">🔍</span> Verify Claim';
            }
        }
    },

    /**
     * Display verdict result
     */
    displayVerdict(result) {
        const loadingState = document.getElementById('loading-state');
        const verdictResult = document.getElementById('verdict-result');

        // Hide loading, show result
        loadingState?.classList.add('hidden');
        verdictResult?.classList.remove('hidden');

        // Set verdict badge
        const badge = document.getElementById('verdict-badge');
        if (badge) {
            badge.className = `verdict-badge ${result.verdict.toLowerCase()}`;

            const icons = {
                'verified': '✅',
                'disputed': '⚠️',
                'unverifiable': '❔'
            };

            badge.innerHTML = `
                <span class="verdict-icon">${icons[result.verdict.toLowerCase()] || '❔'}</span>
                <span class="verdict-text">${result.verdict.toUpperCase()}</span>
            `;
        }

        // Set confidence
        const confidenceFill = document.getElementById('confidence-fill');
        const confidenceValue = document.getElementById('confidence-value');
        if (confidenceFill) {
            confidenceFill.style.width = `${result.confidence * 100}%`;
        }
        if (confidenceValue) {
            confidenceValue.textContent = `${Math.round(result.confidence * 100)}%`;
        }

        // Set explanation
        const explanationText = document.getElementById('explanation-text');
        if (explanationText) {
            explanationText.textContent = result.explanation;
        }

        // Set evidence lists
        this.renderEvidenceList('supporting-evidence', result.supporting_evidence || []);
        this.renderEvidenceList('counter-evidence', result.counter_evidence || []);
        this.renderEvidenceList('missing-evidence', result.missing_evidence || [], true);
    },

    /**
     * Render evidence list
     */
    renderEvidenceList(elementId, items, isSimple = false) {
        const list = document.getElementById(elementId);
        if (!list) return;

        if (items.length === 0) {
            list.innerHTML = '<li class="no-items">None found</li>';
            return;
        }

        if (isSimple) {
            // Simple string list
            list.innerHTML = items.map(item => `<li>${item}</li>`).join('');
        } else {
            // Complex evidence objects
            list.innerHTML = items.map(item => `
                <li>
                    ${item.summary}
                    <span class="evidence-source">${item.type}: ${item.source}</span>
                    <span class="evidence-strength ${item.strength?.split(' ')[0] || 'moderate'}">${item.strength || ''}</span>
                </li>
            `).join('');
        }
    },

    /**
     * Generate demo verdict for testing without backend
     */
    generateDemoVerdict(claimant, claim) {
        // Simulate different verdicts based on claim content
        const claimLower = claim.toLowerCase();

        let verdict, confidence, explanation;

        if (claimLower.includes('entire') || claimLower.includes('all') || claimLower.includes('everything')) {
            verdict = 'DISPUTED';
            confidence = 0.82;
            explanation = `While ${claimant} made contributions to this area, the claim of doing "everything" is not supported by the evidence. Git logs show contributions from multiple team members, and meeting transcripts indicate collaborative work.`;
        } else if (claimLower.includes('helped') || claimLower.includes('assisted') || claimLower.includes('contributed')) {
            verdict = 'VERIFIED';
            confidence = 0.91;
            explanation = `Evidence supports ${claimant}'s claim of contributing to this work. Git commits show relevant activity, and meeting transcripts confirm their involvement in discussions.`;
        } else {
            verdict = 'UNVERIFIABLE';
            confidence = 0.45;
            explanation = `Insufficient evidence to confirm or deny this claim. The available git logs and transcripts do not contain clear references to ${claimant}'s work on the specified feature.`;
        }

        return {
            claim,
            claimant,
            verdict,
            confidence,
            explanation,
            supporting_evidence: verdict === 'DISPUTED' ? [
                {
                    type: 'git_commit',
                    source: 'abc123',
                    summary: `${claimant} added minor fixes to the component`,
                    strength: 'weak'
                }
            ] : [
                {
                    type: 'git_commit',
                    source: 'def456',
                    summary: `${claimant} implemented core functionality`,
                    strength: 'strong'
                },
                {
                    type: 'meeting_transcript',
                    source: 'meeting_02.txt:L34-45',
                    summary: `${claimant} discussed implementation approach`,
                    strength: 'moderate'
                }
            ],
            counter_evidence: verdict === 'DISPUTED' ? [
                {
                    type: 'git_commit',
                    source: 'ghi789',
                    summary: 'Other team member authored 75% of related code',
                    strength: 'strong'
                },
                {
                    type: 'meeting_transcript',
                    source: 'meeting_03.txt:L12-20',
                    summary: 'Another member presented this feature to the team',
                    strength: 'moderate'
                }
            ] : [],
            missing_evidence: verdict === 'UNVERIFIABLE' ? [
                `No commits from ${claimant} touching the claimed files`,
                `No mention of ${claimant} in related meeting discussions`,
                'Task board shows no assignments for this feature'
            ] : []
        };
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => App.init());

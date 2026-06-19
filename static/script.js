// === Toast Notifications ===
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span>${type === 'error' ? '❌' : '✅'}</span>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease-out forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

document.addEventListener('DOMContentLoaded', () => {

    // === Tabs ===
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Ignore disabled tabs
            if (tab.style.cursor === 'not-allowed') return;

            // Remove active class from all
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            // Add active class to clicked
            tab.classList.add('active');
            const target = document.getElementById(tab.dataset.tab);
            if (target) target.classList.add('active');
            
            // Save state
            localStorage.setItem('activeTab', tab.dataset.tab);
        });
    });

    // Restore active tab
    const savedTab = localStorage.getItem('activeTab');
    if (savedTab) {
        const tabElement = document.querySelector(`.tab[data-tab="${savedTab}"]`);
        if (tabElement) tabElement.click();
    }

    loadConfig();
    startPerformanceMonitoring();

    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');

    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--accent)';
        dropZone.style.background = 'rgba(30, 41, 59, 0.8)';
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--border)';
        dropZone.style.background = 'rgba(30, 41, 59, 0.5)';
    });

    dropZone.addEventListener('drop', e => {
        e.preventDefault();
        dropZone.style.border = '2px dashed var(--border)';
        if (e.dataTransfer.files.length) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    // === EXP Tab Drop Zone ===
    const expDropZone = document.getElementById('exp-drop-zone');
    const expFileInput = document.getElementById('exp-file-upload');

    if (expDropZone && expFileInput) {
        expDropZone.addEventListener('click', () => expFileInput.click());

        expDropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            expDropZone.style.borderColor = 'var(--accent)';
            expDropZone.style.background = 'rgba(30, 41, 59, 0.8)';
        });

        expDropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            expDropZone.style.borderColor = 'var(--border)';
            expDropZone.style.background = 'transparent';
        });

        expDropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            expDropZone.style.borderColor = 'var(--border)';
            expDropZone.style.background = 'transparent';
            
            if (e.dataTransfer.files.length) {
                expFileInput.files = e.dataTransfer.files;
                uploadExpPdf();
            }
        });
    }
});

async function loadConfig() {
    try {
        const res = await fetch('/api/config');
        const config = await res.json();
        
        document.getElementById('llm-provider').value = config.LLM_PROVIDER;
        document.getElementById('llm-base-url').value = config.LLM_BASE_URL;
        document.getElementById('words-extract').value = config.WORDS_TO_EXTRACT;
        document.getElementById('extractor-system-prompt').value = config.EXTRACTOR_SYSTEM_PROMPT || "";
        document.getElementById('ocr-chunk-size').value = config.OCR_CHUNK_WORDS || 2000;
        document.getElementById('ocr-overlap-size').value = config.OCR_OVERLAP_WORDS || 50;
        
        await updateModels(config.LLM_MODEL_NAME);
        calculateTotalChunks();
    } catch (e) {
        console.error('Failed to load config', e);
    }
}

async function saveConfig() {
    const provider = document.getElementById('llm-provider').value;
    const baseUrl = document.getElementById('llm-base-url').value;
    const model = document.getElementById('llm-model').value;
    const words = document.getElementById('words-extract').value;
    const prompt = document.getElementById('extractor-system-prompt').value;
    const chunkSize = document.getElementById('ocr-chunk-size').value;
    const overlapSize = document.getElementById('ocr-overlap-size').value;

    const configData = {
        LLM_PROVIDER: provider,
        LLM_BASE_URL: baseUrl,
        LLM_MODEL_NAME: model,
        WORDS_TO_EXTRACT: parseInt(words),
        EXTRACTOR_SYSTEM_PROMPT: prompt,
        OCR_CHUNK_WORDS: parseInt(chunkSize),
        OCR_OVERLAP_WORDS: parseInt(overlapSize)
    };

    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(configData)
        });
        const data = await response.json();
        if (data.status === 'success') {
            showToast('Configuration saved successfully!');
        } else {
            showToast('Failed to save configuration', 'error');
        }
    } catch (e) {
        console.error('Failed to save config', e);
        showToast('Failed to save configuration', 'error');
    }
}

async function updateModels(selectedModel = null) {
    // Save current provider temporarily to backend to fetch models correctly without overwriting model
    const provider = document.getElementById('llm-provider').value;
    const baseUrl = document.getElementById('llm-base-url').value;
    await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ LLM_PROVIDER: provider, LLM_BASE_URL: baseUrl })
    });

    const modelSelect = document.getElementById('llm-model');
    modelSelect.innerHTML = '<option>Loading...</option>';
    
    try {
        const res = await fetch('/api/models');
        const data = await res.json();
        
        modelSelect.innerHTML = '';
        data.models.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m;
            opt.textContent = m;
            if (m === selectedModel) {
                opt.selected = true;
            }
            modelSelect.appendChild(opt);
        });
    } catch (e) {
        console.error('Failed to load models', e);
        modelSelect.innerHTML = '<option>Error loading models</option>';
    }
}

function startPerformanceMonitoring() {
    setInterval(async () => {
        try {
            const res = await fetch('/api/performance');
            const stats = await res.json();
            
            document.getElementById('stat-cpu').textContent = stats.cpu_usage_percent.toFixed(1) + '%';
            
            const ramPct = ((stats.ram_usage_mb / stats.ram_total_mb) * 100).toFixed(1);
            document.getElementById('stat-ram').textContent = `${stats.ram_usage_mb.toFixed(0)} / ${stats.ram_total_mb.toFixed(0)} MB (${ramPct}%)`;
            
            document.getElementById('stat-gpu').textContent = stats.gpu_usage_percent !== null ? stats.gpu_usage_percent.toFixed(1) + '%' : 'N/A';
            
            if (stats.vram_usage_mb !== null && stats.vram_total_mb !== null) {
                const vramPct = ((stats.vram_usage_mb / stats.vram_total_mb) * 100).toFixed(1);
                document.getElementById('stat-vram').textContent = `${stats.vram_usage_mb.toFixed(0)} / ${stats.vram_total_mb.toFixed(0)} MB (${vramPct}%)`;
            } else {
                document.getElementById('stat-vram').textContent = 'N/A';
            }
        } catch (e) {
            // silent fail
        }
    }, 2000);
}

async function handleFileUpload(file) {
    document.getElementById('drop-zone').style.display = 'none';
    const statusContainer = document.getElementById('status-container');
    const statusText = document.getElementById('status-text');
    statusContainer.style.display = 'block';
    document.getElementById('results-container').style.display = 'none';
    statusText.textContent = `Uploading and extracting ${file.name}...`;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/api/upload_book', {
            method: 'POST',
            body: formData
        });
        
        const result = await res.json();
        
        if (result.status === 'success') {
            displayResults(result.project);
            showToast('File extracted successfully! You can now edit the text or Ask the LLM.', 'success');
            document.getElementById('btn-ask-llm').style.display = 'inline-block';
        } else {
            throw new Error(result.message || 'Extraction failed');
        }
    } catch (e) {
        console.error('Error:', e);
        statusText.textContent = `Error: ${e.message || 'Processing failed'}`;
        showToast(e.message || 'Processing failed', 'error');
    } finally {
        document.getElementById('drop-zone').style.display = 'block';
        document.getElementById('status-container').style.display = 'none';
    }
}

function displayResults(data) {
    document.getElementById('results-container').style.display = 'flex';
    
    // Performance
    if (data.performance) {
        document.getElementById('res-time').textContent = data.performance.total_time_seconds.toFixed(2) + ' s';
        document.getElementById('res-tps').textContent = data.performance.tokens_per_second.toFixed(1);
        document.getElementById('res-sent').textContent = data.performance.tokens_sent;
        document.getElementById('res-recv').textContent = data.performance.tokens_received;
    } else {
        document.getElementById('res-time').textContent = '-';
        document.getElementById('res-tps').textContent = '-';
        document.getElementById('res-sent').textContent = '-';
        document.getElementById('res-recv').textContent = '-';
    }
    
    // Metadata
    document.getElementById('current-project-id').value = data.id;
    const m = data.book_metadata || {};
    
    const lang = m.provided_language || m.original_language || "?";
    const trans = m.is_translation ? "Translation" : "Original";
    const author = m.author || "?";
    const title = m.title || data.filename || 'Unknown Title';
    const year = m.publish_date || "?";
    const genre = m.genre || "?";
    
    let displayLabel = "";
    if (Object.keys(m).length > 0) {
        displayLabel = `[${lang}][${trans}] ${author} - ${title} - ${year} - ${genre}`;
    } else {
        displayLabel = `[Unprocessed] ${data.filename || title}`;
    }
    
    document.getElementById('global-active-book').textContent = displayLabel;
    
    document.getElementById('meta-title').value = m.title || '';
    document.getElementById('meta-author').value = m.author || '';
    
    // Calculate total raw word count
    const wordCount = data.extracted_text ? data.extracted_text.trim().split(/\s+/).length : 0;
    document.getElementById('meta-word-count').value = wordCount.toLocaleString() + ' words';
    // Also update OCR tab
    document.getElementById('ocr-stat-words').textContent = wordCount.toLocaleString();
    
    document.getElementById('meta-publish-date').value = m.publish_date || '';
    document.getElementById('meta-genre').value = m.genre || '';
    document.getElementById('meta-style').value = m.style || '';
    document.getElementById('meta-target-audience').value = m.target_audience || '';
    document.getElementById('meta-original-language').value = m.original_language || '';
    document.getElementById('meta-provided-language').value = m.provided_language || '';
    document.getElementById('meta-is-translation').checked = !!m.is_translation;
    document.getElementById('meta-translator').value = m.translator || '';
    document.getElementById('meta-details').value = m.details || '';
    
    // Corrected Text
    // Handle LLM Box Previews
    let textSent = data.extracted_text || '';
    const wordLimit = data.settings?.words_extracted || 1000;
    const words = textSent.trim().split(/\s+/);
    if (words.length > wordLimit) {
        textSent = words.slice(0, wordLimit).join(" ") + "\n\n...[TRUNCATED FOR BOOK INFO EXTRACTION]...";
    }
    
    document.getElementById('res-text-sent').value = textSent;
    document.getElementById('res-text-recv').value = data.corrected_text || '';
    
    // Show ask LLM button if we have text but no corrected text
    if (data.extracted_text && !data.corrected_text) {
        document.getElementById('btn-ask-llm').style.display = 'inline-block';
    } else {
        document.getElementById('btn-ask-llm').style.display = 'none';
    }
    
    calculateTotalChunks();
}

function calculateTotalChunks() {
    const rawCountStr = document.getElementById('ocr-stat-words').textContent;
    const totalWords = parseInt(rawCountStr.replace(/\D/g, '')) || 0;
    if (totalWords === 0) {
        document.getElementById('ocr-stat-chunks-total').textContent = '--';
        return;
    }
    
    const chunkWords = parseInt(document.getElementById('ocr-chunk-size').value) || 2000;
    const overlapWords = parseInt(document.getElementById('ocr-overlap-size').value) || 50;
    
    if (chunkWords <= overlapWords) {
        document.getElementById('ocr-stat-chunks-total').textContent = 'Invalid Config';
        return;
    }
    
    let chunks = 0;
    let i = 0;
    while (i < totalWords) {
        chunks++;
        if (i + chunkWords >= totalWords) break;
        i += (chunkWords - overlapWords);
    }
    
    document.getElementById('ocr-stat-chunks-total').textContent = chunks;
}

async function askLLM() {
    const projectId = document.getElementById('current-project-id').value;
    if (!projectId) {
        showToast('No active project. Extract a file first.', 'error');
        return;
    }
    
    const statusContainer = document.getElementById('status-container');
    const statusText = document.getElementById('status-text');
    statusContainer.style.display = 'block';
    statusText.textContent = `Asking LLM for book metadata... this might take a while.`;
    document.getElementById('btn-ask-llm').disabled = true;

    try {
        const res = await fetch(`/api/project/${projectId}/ask_llm`, { method: 'POST' });
        const result = await res.json();
        
        if (result.status === 'success') {
            displayResults(result.project);
            showToast('LLM Processing successful!', 'success');
        } else {
            throw new Error(result.message || 'LLM Processing failed');
        }
    } catch (e) {
        console.error('Error:', e);
        showToast(e.message || 'LLM Processing failed', 'error');
    } finally {
        statusContainer.style.display = 'none';
        document.getElementById('btn-ask-llm').disabled = false;
    }
}

// === LLM Controls ===

async function checkConnection() {
    showToast('Checking connection...', 'success');
    try {
        const res = await fetch('/api/llm/check');
        const data = await res.json();
        if (data.status === 'success' && data.connected) {
            showToast('Connection to LLM is successful!', 'success');
        } else {
            showToast('Failed to connect to LLM.', 'error');
        }
    } catch (e) {
        console.error(e);
        showToast('Connection check failed.', 'error');
    }
}

async function requestModels() {
    showToast('Requesting models...', 'success');
    try {
        const res = await fetch('/api/models');
        const data = await res.json();
        if (data.status === 'success' && data.models) {
            const select = document.getElementById('llm-model');
            const current = select.value;
            select.innerHTML = '';
            data.models.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m;
                opt.textContent = m;
                select.appendChild(opt);
            });
            if (data.models.includes(current)) {
                select.value = current;
            }
            showToast(`Loaded ${data.models.length} models.`, 'success');
        } else {
            showToast('Failed to load models.', 'error');
        }
    } catch (e) {
        console.error(e);
        showToast('Failed to fetch models.', 'error');
    }
}

async function unloadModel() {
    showToast('Unloading model...', 'success');
    try {
        const res = await fetch('/api/llm/unload', { method: 'POST' });
        const data = await res.json();
        if (data.status === 'success') {
            showToast('Model unloaded successfully!', 'success');
        } else {
            showToast('Failed to unload model.', 'error');
        }
    } catch (e) {
        console.error(e);
        showToast('Error unloading model.', 'error');
    }
}

function openSettings() {
    showToast('Settings panel not yet implemented. (Coming soon)', 'success');
}

function toggleTextLayout() {
    const container = document.getElementById('text-comparison-container');
    if (container.classList.contains('text-comparison-flex')) {
        container.classList.remove('text-comparison-flex');
        container.classList.add('text-comparison-col');
    } else {
        container.classList.remove('text-comparison-col');
        container.classList.add('text-comparison-flex');
    }
}

async function saveBookDetails() {
    const projectId = document.getElementById('current-project-id').value;
    if (!projectId) {
        showToast('No active project. Extract a file first.', 'error');
        return;
    }

    const metadata = {
        title: document.getElementById('meta-title').value,
        author: document.getElementById('meta-author').value,
        publish_date: document.getElementById('meta-publish-date').value,
        genre: document.getElementById('meta-genre').value,
        style: document.getElementById('meta-style').value,
        target_audience: document.getElementById('meta-target-audience').value,
        original_language: document.getElementById('meta-original-language').value,
        provided_language: document.getElementById('meta-provided-language').value,
        is_translation: document.getElementById('meta-is-translation').checked,
        translator: document.getElementById('meta-translator').value,
        details: document.getElementById('meta-details').value
    };

    try {
        const res = await fetch(`/api/project/${projectId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(metadata)
        });
        const result = await res.json();
        if (result.status === 'success') {
            showToast('Book details saved successfully!');
        } else {
            showToast('Failed to save details.', 'error');
        }
    } catch (e) {
        showToast('Error saving details.', 'error');
    }
}

async function openLoadProjectModal() {
    document.getElementById('load-project-modal').style.display = 'flex';
    const select = document.getElementById('project-dropdown');
    select.innerHTML = '<option value="">Loading...</option>';

    try {
        const res = await fetch('/api/projects');
        const data = await res.json();
        select.innerHTML = '';
        if (data.projects && data.projects.length > 0) {
            // Sort by created_at descending
            data.projects.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
            
            data.projects.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.id;
                
                let label = "";
                if (p.book_metadata && Object.keys(p.book_metadata).length > 0) {
                    const m = p.book_metadata;
                    const lang = m.provided_language || m.original_language || "?";
                    const trans = m.is_translation ? "Translation" : "Original";
                    const author = m.author || "?";
                    const title = m.title || p.filename;
                    const year = m.publish_date || "?";
                    const genre = m.genre || "?";
                    label = `[${lang}][${trans}] ${author} - ${title} - ${year} - ${genre}`;
                } else {
                    label = `[Unprocessed] ${p.filename}`;
                }
                
                opt.textContent = label;
                select.appendChild(opt);
            });
        } else {
            select.innerHTML = '<option value="">No previous extractions found.</option>';
        }
    } catch (e) {
        select.innerHTML = '<option value="">Error loading projects.</option>';
    }
}

function closeLoadProjectModal() {
    document.getElementById('load-project-modal').style.display = 'none';
}

// --- Tabs Logic ---
function switchTab(tabId) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => {
        c.classList.remove('active');
        c.style.display = 'none';
    });
    
    document.querySelector(`.tab[data-tab="${tabId}"]`).classList.add('active');
    const content = document.getElementById(tabId);
    if (content) {
        content.classList.add('active');
        content.style.display = 'block';
    }
}

// --- Full Book OCR Logic ---
let ocrPollInterval = null;

async function startFullOCR() {
    const projectId = document.getElementById('current-project-id').value;
    if (!projectId) {
        showToast('Please load or upload a book first.', 'error');
        return;
    }
    
    const systemPrompt = document.getElementById('ocr-system-prompt').value;
    
    try {
        const res = await fetch(`/api/project/${projectId}/ocr_start`, { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ system_prompt: systemPrompt })
        });
        const data = await res.json();
        if (data.status === 'success') {
            showToast('Full Book OCR started!', 'success');
            document.getElementById('ocr-job-status').textContent = 'Running...';
            document.getElementById('ocr-progress-bar').style.width = '0%';
            document.getElementById('ocr-corrections-list').innerHTML = '<li>Processing...</li>';
            
            if (ocrPollInterval) clearInterval(ocrPollInterval);
            ocrPollInterval = setInterval(pollOCRStatus, 2000);
        } else {
            showToast(data.message, 'error');
        }
    } catch (e) {
        showToast('Failed to start OCR.', 'error');
    }
}

async function stopFullOCR() {
    const projectId = document.getElementById('current-project-id').value;
    if (!projectId) return;
    try {
        await fetch(`/api/project/${projectId}/ocr_stop`, { method: 'POST' });
        showToast('Stop signal sent.', 'success');
    } catch (e) {}
}

async function pollOCRStatus() {
    const projectId = document.getElementById('current-project-id').value;
    if (!projectId) return;
    
    try {
        const res = await fetch(`/api/project/${projectId}/ocr_status`);
        const status = await res.json();
        
        if (status.status === 'none') return;
        
        const statusText = document.getElementById('ocr-job-status');
        const progressBar = document.getElementById('ocr-progress-bar');
        
        statusText.textContent = status.status.charAt(0).toUpperCase() + status.status.slice(1);
        
        if (status.status === 'running') {
            const total = status.total_chunks || 0;
            const recv = status.chunks_received || 0;
            
            const pct = total > 0 ? (recv / total) * 100 : 0;
            progressBar.style.width = pct + '%';
            
            document.getElementById('ocr-stat-chunks-total').textContent = total;
            document.getElementById('ocr-stat-chunks-done').textContent = recv;
            
            if (status.eta_seconds > 0) {
                document.getElementById('ocr-stat-eta').textContent = Math.round(status.eta_seconds) + 's';
            } else {
                document.getElementById('ocr-stat-eta').textContent = 'Calculating...';
            }

            if (status.llm_stats) {
                document.getElementById('ocr-stat-curr-tokens').textContent = status.llm_stats.tokens_received || '--';
                document.getElementById('ocr-stat-curr-speed').textContent = status.llm_stats.speed_tps ? status.llm_stats.speed_tps.toFixed(1) + ' t/s' : '--';
                document.getElementById('ocr-stat-curr-time').textContent = status.llm_stats.elapsed ? status.llm_stats.elapsed.toFixed(1) + 's' : '--';
            }
        }
        
        if (status.corrections && status.corrections.length > 0) {
            const list = document.getElementById('ocr-corrections-list');
            list.innerHTML = '';
            status.corrections.forEach(c => {
                const li = document.createElement('li');
                li.textContent = c;
                list.appendChild(li);
            });
            // auto scroll to bottom
            list.scrollTop = list.scrollHeight;
        }
        
        if (status.status === 'completed' || status.status === 'stopped' || status.status === 'error') {
            clearInterval(ocrPollInterval);
            if (status.status === 'error') {
                showToast(status.error_msg || 'OCR Error', 'error');
            } else if (status.status === 'completed') {
                showToast('OCR completely finished and saved to database!', 'success');
            }
        }
    } catch (e) {}
}

async function loadSelectedProject() {
    const id = document.getElementById('project-dropdown').value;
    if (!id) return;
    loadProject(id);
}

async function deleteSelectedProject() {
    const id = document.getElementById('project-dropdown').value;
    if (!id) return;
    
    if (!confirm('Are you sure you want to delete this extraction permanently?')) return;
    
    try {
        const res = await fetch(`/api/project/${id}`, { method: 'DELETE' });
        const result = await res.json();
        if (result.status === 'success') {
            showToast('Project deleted successfully.');
            // Reload the dropdown list
            openLoadProjectModal();
        } else {
            showToast('Failed to delete.', 'error');
        }
    } catch (e) {
        showToast('Error deleting.', 'error');
    }
}

async function loadProject(id) {
    closeLoadProjectModal();
    showToast('Loading project...', 'success');
    try {
        const res = await fetch(`/api/project/${id}`);
        const result = await res.json();
        if (result.status === 'success') {
            displayResults(result.project);
            showToast('Project loaded!');
        } else {
            showToast('Failed to load project.', 'error');
        }
    } catch (e) {
        showToast('Error loading project.', 'error');
    }
}
// ---------------------------------------------------------
// INTERNATIONALIZATION (i18n)
// ---------------------------------------------------------
const translations = {
    en: {
        app_title: "Storycrafter Lite",
        config_title: "Configuration",
        llm_provider: "LLM Provider",
        base_url: "Base URL",
        api_key: "API Key",
        model: "Model",
        save_config: "Save Configuration",
        llm_controls: "LLM Controls",
        check_conn: "Check Connection",
        req_models: "Request Models",
        unload_model: "Unload Model",
        sys_perf: "System Performance",
        cpu: "CPU:",
        ram: "RAM:",
        gpu: "GPU:",
        vram: "VRAM:",
        active_book: "Active Book:",
        no_book: "None (Please load or upload a book)",
        upload_new: "Upload New Book",
        load_lib: "Load from Library",
        tab_info: "Book Information Extractor",
        tab_ocr: "Full Book OCR",
        ext_desc: "Extract metadata from the active book.",
        ask_llm: "Ask LLM for Information ✨",
        sys_prompt: "System Prompt (Instructions to LLM) ⚙️",
        words_extract: "Words to Extract",
        save_settings: "Save Settings",
        drag_drop: "Drag & Drop your file here",
        or_click: "or click to browse",
        processing: "Processing...",
        time_taken: "Time Taken",
        tps: "Tokens/sec",
        tokens_sent: "Tokens Sent",
        tokens_recv: "Tokens Received",
        metadata_ext: "Metadata Extracted",
        save_details: "Save Book Details",
        lbl_title: "Title",
        lbl_author: "Author",
        lbl_words: "Total Words (Raw File)",
        lbl_date: "Publish Date",
        lbl_genre: "Genre",
        lbl_style: "Style",
        lbl_audience: "Target Audience",
        lbl_orig_lang: "Original Language",
        lbl_prov_lang: "Provided Language",
        lbl_is_trans: "Is Translation",
        lbl_translator: "Translator",
        lbl_details: "Details",
        txt_process: "Text Processing",
        toggle_sbs: "Toggle Side-by-Side",
        sent_llm: "Sent to LLM (Raw Extract)",
        recv_llm: "Received from LLM (Corrected)",
        ocr_desc: "Runs asynchronously over the entire book to perfectly correct scanning errors and typos.",
        ocr_chunk: "OCR Chunk Size (Words)",
        ocr_overlap: "OCR Overlap (Words)",
        start_ocr: "Start Full Book OCR",
        stop_job: "Stop Job",
        ready: "Ready",
        tot_words: "Total Words:",
        tot_chunks: "Total Chunks:",
        chunks_done: "Chunks Done:",
        eta: "ETA:",
        chunk_tok: "Chunk Tokens:",
        chunk_spd: "Chunk Speed:",
        chunk_time: "Chunk Time:",
        corr_log: "Corrections Log",
        no_corr: "No corrections made yet.",
        load_prev: "Load Previous Extractions",
        btn_load: "Load",
        btn_delete: "Delete",
        
        // Tooltips
        tip_llm_provider: "Select the local or cloud AI engine.",
        tip_base_url: "API endpoint for the selected provider.",
        tip_model: "The AI model to use for extractions and corrections.",
        tip_check_conn: "Test if the AI server is reachable.",
        tip_req_models: "Refresh the list of available models.",
        tip_unload_model: "Unload model from VRAM.",
        tip_upload_new: "Upload a PDF, EPUB, DOCX, or TXT file.",
        tip_load_lib: "Load a previously extracted book.",
        tip_ask_llm: "Send the first X words to the LLM to extract title, author, and genre automatically.",
        tip_sys_prompt: "Instructions given to the AI for extracting metadata.",
        tip_words_extract: "Number of words from the beginning of the book to analyze.",
        tip_save_details: "Save the fields below to the database.",
        tip_toggle_sbs: "Change the layout of the text boxes below.",
        tip_ocr_prompt: "Instructions given to the AI for fixing OCR errors.",
        tip_chunk: "Number of words to process at a time.",
        tip_overlap: "Overlap between chunks to maintain context.",
        tip_start_ocr: "Begin the automated correction process for the entire book.",
        tip_stop_job: "Abort the current OCR job."
    },
    tr: {
        app_title: "Storycrafter Lite",
        config_title: "Yapılandırma",
        llm_provider: "LLM Sağlayıcısı",
        base_url: "Temel URL",
        api_key: "API Anahtarı",
        model: "Model",
        save_config: "Yapılandırmayı Kaydet",
        llm_controls: "LLM Kontrolleri",
        check_conn: "Bağlantıyı Kontrol Et",
        req_models: "Modelleri İste",
        unload_model: "Modeli Kaldır",
        sys_perf: "Sistem Performansı",
        cpu: "CPU:",
        ram: "RAM:",
        gpu: "GPU:",
        vram: "VRAM:",
        active_book: "Aktif Kitap:",
        no_book: "Yok (Lütfen bir kitap yükleyin)",
        upload_new: "Yeni Kitap Yükle",
        load_lib: "Kütüphaneden Yükle",
        tab_info: "Kitap Bilgi Çıkarıcı",
        tab_ocr: "Tam Kitap OCR",
        ext_desc: "Aktif kitaptan meta verileri çıkarın.",
        ask_llm: "LLM'ye Bilgi Sor ✨",
        sys_prompt: "Sistem İstemi (LLM Talimatları) ⚙️",
        words_extract: "Çıkarılacak Kelime Sayısı",
        save_settings: "Ayarları Kaydet",
        drag_drop: "Dosyanızı buraya sürükleyip bırakın",
        or_click: "veya göz atmak için tıklayın",
        processing: "İşleniyor...",
        time_taken: "Geçen Süre",
        tps: "Token/sn",
        tokens_sent: "Gönderilen Token",
        tokens_recv: "Alınan Token",
        metadata_ext: "Çıkarılan Meta Veriler",
        save_details: "Kitap Detaylarını Kaydet",
        lbl_title: "Başlık",
        lbl_author: "Yazar",
        lbl_words: "Toplam Kelime (Ham Dosya)",
        lbl_date: "Yayın Tarihi",
        lbl_genre: "Tür",
        lbl_style: "Stil",
        lbl_audience: "Hedef Kitle",
        lbl_orig_lang: "Orijinal Dil",
        lbl_prov_lang: "Sağlanan Dil",
        lbl_is_trans: "Çeviri mi?",
        lbl_translator: "Çevirmen",
        lbl_details: "Detaylar",
        txt_process: "Metin İşleme",
        toggle_sbs: "Yan Yana Görünümü Değiştir",
        sent_llm: "LLM'ye Gönderilen (Ham Çıktı)",
        recv_llm: "LLM'den Alınan (Düzeltilmiş)",
        ocr_desc: "Tarama hatalarını ve yazım yanlışlarını kusursuzca düzeltmek için tüm kitap üzerinde asenkron olarak çalışır.",
        ocr_chunk: "OCR Parça Boyutu (Kelime)",
        ocr_overlap: "OCR Örtüşmesi (Kelime)",
        start_ocr: "Tam Kitap OCR Başlat",
        stop_job: "İşi Durdur",
        ready: "Hazır",
        tot_words: "Toplam Kelime:",
        tot_chunks: "Toplam Parça:",
        chunks_done: "Tamamlanan Parça:",
        eta: "Kalan Süre:",
        chunk_tok: "Parça Tokenleri:",
        chunk_spd: "Parça Hızı:",
        chunk_time: "Parça Süresi:",
        corr_log: "Düzeltme Günlüğü",
        no_corr: "Henüz bir düzeltme yapılmadı.",
        load_prev: "Önceki Çıkarımları Yükle",
        btn_load: "Yükle",
        btn_delete: "Sil",

        // Tooltips
        tip_llm_provider: "Yerel veya bulut AI motorunu seçin.",
        tip_base_url: "Seçili sağlayıcı için API uç noktası.",
        tip_model: "Çıkarım ve düzeltmeler için kullanılacak AI modeli.",
        tip_check_conn: "AI sunucusuna ulaşılıp ulaşılamadığını test eder.",
        tip_req_models: "Kullanılabilir modeller listesini yeniler.",
        tip_unload_model: "Modeli VRAM'den kaldırır.",
        tip_upload_new: "PDF, EPUB, DOCX veya TXT dosyası yükleyin.",
        tip_load_lib: "Daha önce çıkarılmış bir kitabı yükleyin.",
        tip_ask_llm: "Başlık, yazar ve türü otomatik çıkarmak için ilk X kelimeyi LLM'ye gönderir.",
        tip_sys_prompt: "Meta veri çıkarma için AI'ya verilen talimatlar.",
        tip_words_extract: "Kitabın başından itibaren analiz edilecek kelime sayısı.",
        tip_save_details: "Aşağıdaki alanları veritabanına kaydeder.",
        tip_toggle_sbs: "Aşağıdaki metin kutularının düzenini değiştirir.",
        tip_ocr_prompt: "OCR hatalarını düzeltmek için AI'ya verilen talimatlar.",
        tip_chunk: "Tek seferde işlenecek kelime sayısı.",
        tip_overlap: "Bağlamı korumak için parçalar arasındaki örtüşme miktarı.",
        tip_start_ocr: "Tüm kitap için otomatik düzeltme sürecini başlatır.",
        tip_stop_job: "Mevcut OCR işini iptal eder."
    }
};

function changeLanguage(lang) {
    const dict = translations[lang];
    if (!dict) return;

    // Update text elements
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (dict[key]) {
            el.textContent = dict[key];
        }
    });

    // Update tooltips
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        if (dict[key]) {
            el.setAttribute('title', dict[key]);
        }
    });
}

window.changeLanguage = changeLanguage;

async function handleProviderChange() {
    const provider = document.getElementById('llm-provider').value;
    const baseUrlInput = document.getElementById('llm-base-url');
    const baseUrlLabel = document.querySelector('[data-i18n="base_url"]') || document.querySelector('[data-i18n="api_key"]');

    if (provider === 'lmstudio') {
        baseUrlInput.value = 'http://localhost:1234/v1';
        if (baseUrlLabel) baseUrlLabel.setAttribute('data-i18n', 'base_url');
    } else if (provider === 'ollama') {
        baseUrlInput.value = 'http://localhost:11434';
        if (baseUrlLabel) baseUrlLabel.setAttribute('data-i18n', 'base_url');
    } else if (provider === 'gemini') {
        baseUrlInput.value = '';
        if (baseUrlLabel) baseUrlLabel.setAttribute('data-i18n', 'api_key');
        baseUrlInput.placeholder = 'Enter Gemini API Key';
    } else {
        baseUrlInput.placeholder = '';
    }

    // Refresh language for the label change
    const lang = document.getElementById('lang-selector')?.value || 'en';
    changeLanguage(lang);

    await updateModels();
}
window.handleProviderChange = handleProviderChange;

// Set default language on load
document.addEventListener('DOMContentLoaded', () => {
    changeLanguage('en');
});

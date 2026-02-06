// YouTube Clipper - Frontend JavaScript

// Tab switching
document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        // Update nav
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Update tabs
        const tabId = btn.dataset.tab;
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.getElementById(tabId).classList.add('active');
    });
});

// Console output
const consoleOutput = document.getElementById('console-output');

function log(message, type = '') {
    consoleOutput.className = type;
    consoleOutput.textContent = message;
    consoleOutput.scrollTop = consoleOutput.scrollHeight;
}

function clearConsole() {
    consoleOutput.textContent = 'Siap digunakan...';
    consoleOutput.className = '';
}

// Native file picker handler
function handleFileSelect(fileInput, textInputId) {
    const textInput = document.getElementById(textInputId);
    if (fileInput.files.length > 0) {
        // Get full path (for display) - browsers only give filename for security
        const file = fileInput.files[0];
        textInput.value = file.name;
        // Store full path in data attribute (if available via webkitRelativePath)
        textInput.dataset.fullPath = file.name;
    }
}

// API call helper
async function callApi(endpoint, data, button) {
    button.classList.add('loading');
    button.disabled = true;
    log('Memproses...');

    try {
        const response = await fetch(`/api/${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        log(result.output, result.success ? 'success' : 'error');
        return result;
    } catch (error) {
        log('Error: ' + error.message, 'error');
        return { success: false };
    } finally {
        button.classList.remove('loading');
        button.disabled = false;
    }
}

// Form handlers
document.getElementById('full-auto-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const data = {
        url: form.url.value,
        api_key: form.api_key.value,
        model: form.model.value,
        watermark: form.watermark.value,
        burn_subtitle: form.burn_subtitle.checked
    };

    // Show progress section
    const progressSection = document.getElementById('progress-section');
    const progressBar = document.getElementById('progress-bar');
    const progressStep = document.getElementById('progress-step');
    const progressPercent = document.getElementById('progress-percent');
    const progressStatus = document.getElementById('progress-status');

    progressSection.style.display = 'block';
    progressBar.style.width = '0%';
    progressStep.textContent = 'Step 0/5';
    progressPercent.textContent = '0%';
    progressStatus.textContent = '🚀 Memulai proses...';

    // Custom handling for long process
    const btn = form.querySelector('button');
    btn.classList.add('loading');
    btn.disabled = true;
    log('🚀 Memulai Full Automation Pipeline...', '');

    try {
        // Start the job
        const response = await fetch('/api/full-auto', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (!result.success || !result.job_id) {
            progressStatus.textContent = '❌ Gagal memulai job!';
            log(result.output || 'Failed to start job', 'error');
            btn.classList.remove('loading');
            btn.disabled = false;
            return;
        }

        const jobId = result.job_id;
        log(`📋 Job started: ${jobId}`, '');

        // Poll for status
        let polling = true;
        while (polling) {
            await new Promise(resolve => setTimeout(resolve, 1500)); // Poll every 1.5s

            try {
                const statusRes = await fetch(`/api/job-status/${jobId}`);
                const statusData = await statusRes.json();

                if (statusData.success) {
                    const step = statusData.step;
                    const total = statusData.total_steps;
                    const percent = Math.round((step / total) * 100);

                    progressStep.textContent = `Step ${step}/${total}`;
                    progressPercent.textContent = `${percent}%`;
                    progressBar.style.width = `${percent}%`;
                    progressStatus.textContent = statusData.message;

                    // Update console with output
                    if (statusData.output) {
                        log(statusData.output, '');
                    }

                    if (statusData.status === 'done') {
                        progressBar.style.width = '100%';
                        progressStep.textContent = 'Step 5/5';
                        progressPercent.textContent = '100%';
                        progressStatus.textContent = '✅ Selesai!';
                        log('✅ Automation Complete!', 'success');
                        polling = false;
                    } else if (statusData.status === 'error') {
                        progressStatus.textContent = '❌ Gagal!';
                        log(statusData.output || 'Job failed', 'error');
                        polling = false;
                    }
                }
            } catch (pollError) {
                console.error('Polling error:', pollError);
                // Continue polling on network errors
            }
        }
    } catch (error) {
        progressStatus.textContent = '❌ Error!';
        log('Error: ' + error.message, 'error');
    } finally {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
});

document.getElementById('download-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const data = { url: form.url.value };
    await callApi('download', data, form.querySelector('button'));
});

document.getElementById('download-sub-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const data = {
        url: form.url.value,
        lang: form.lang.value,
        auto: form.auto.value
    };
    await callApi('download-subtitle', data, form.querySelector('button'));
});

document.getElementById('analyze-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const data = { file: form.file.value };
    await callApi('analyze', data, form.querySelector('button'));
});

document.getElementById('auto-clip-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const data = {
        file: form.file.value,
        api_key: form.api_key.value,
        model: form.model.value
    };

    // Custom handling for auto-clip to format JSON
    const btn = form.querySelector('button');
    btn.classList.add('loading');
    btn.disabled = true;
    log('🤖 Mengirim ke Kie.ai... mohon tunggu...', '');

    try {
        const response = await fetch('/api/auto-map', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success && result.chapters) {
            let output = "✅ Berhasil Membuat Chapter:\n\n";
            result.chapters.forEach((chap, i) => {
                output += `${i + 1}. ${chap.title}\n`;
                output += `   Start: ${chap.start} | End: ${chap.end}\n`;
                output += `   Alasan: ${chap.reason}\n\n`;
            });
            output += "👉 Gunakan waktu di atas pada tab 'Clip Video'";
            log(output, 'success');
        } else {
            // Fallback for raw output or error
            const msg = result.output || JSON.stringify(result, null, 2);
            log(msg, result.success ? 'success' : 'error');
        }
    } catch (error) {
        log('Error: ' + error.message, 'error');
    } finally {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
});

document.getElementById('clip-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const data = {
        video: form.video.value,
        start: form.start.value,
        end: form.end.value,
        output: form.output.value
    };
    await callApi('clip', data, form.querySelector('button'));
});

document.getElementById('extract-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const data = {
        subtitle: form.subtitle.value,
        start: form.start.value,
        end: form.end.value,
        output: form.output.value
    };
    await callApi('extract-subtitle', data, form.querySelector('button'));
});

document.getElementById('burn-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const data = {
        video: form.video.value,
        subtitle: form.subtitle.value,
        output: form.output.value
    };
    await callApi('burn', data, form.querySelector('button'));
});

// File Browser
let currentFilePicker = null;

async function loadFiles(path = '') {
    const fileList = document.getElementById('file-list');
    const pathDisplay = document.getElementById('current-path');

    try {
        const response = await fetch(`/api/files?path=${encodeURIComponent(path)}`);
        const data = await response.json();

        if (!data.success) {
            fileList.innerHTML = '<div class="file-item">Error loading files</div>';
            return;
        }

        pathDisplay.textContent = data.current_path;

        let html = '';

        // Parent directory
        if (data.parent_path) {
            html += `
                <div class="file-item" onclick="loadFiles('${escapeHtml(data.parent_path)}')">
                    <span class="file-icon">📁</span>
                    <span class="file-name">..</span>
                </div>
            `;
        }

        // Files and folders
        data.files.forEach(file => {
            const icon = file.is_dir ? '📁' : getFileIcon(file.ext);
            const size = file.is_dir ? '' : formatSize(file.size);
            const onclick = file.is_dir
                ? `loadFiles('${escapeHtml(file.path)}')`
                : `selectFile('${escapeHtml(file.name)}')`;

            html += `
                <div class="file-item" onclick="${onclick}">
                    <span class="file-icon">${icon}</span>
                    <span class="file-name">${escapeHtml(file.name)}</span>
                    <span class="file-size">${size}</span>
                </div>
            `;
        });

        fileList.innerHTML = html || '<div class="file-item">Empty folder</div>';
    } catch (error) {
        fileList.innerHTML = '<div class="file-item">Error: ' + error.message + '</div>';
    }
}

function showFilePicker(formId, fieldName, filterExt) {
    currentFilePicker = { formId, fieldName, filterExt };
    document.getElementById('file-panel').classList.add('open');
    loadFiles();
}

function closeFilePicker() {
    document.getElementById('file-panel').classList.remove('open');
    currentFilePicker = null;
}

function selectFile(filename) {
    if (currentFilePicker) {
        const form = document.getElementById(currentFilePicker.formId + '-form');
        const input = form.querySelector(`[name="${currentFilePicker.fieldName}"]`);
        input.value = filename;
        closeFilePicker();
    }
}

// Open folder in Explorer
async function openFolder() {
    await fetch('/api/open-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: '' })
    });
}

// Helpers
function getFileIcon(ext) {
    const icons = {
        '.mp4': '🎬',
        '.webm': '🎬',
        '.mkv': '🎬',
        '.vtt': '📝',
        '.srt': '📝',
        '.txt': '📄',
        '.json': '📋'
    };
    return icons[ext] || '📄';
}

function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/'/g, "\\'").replace(/"/g, '\\"');
}

// YouTube Clipper - Frontend JavaScript

// SVG Icons for File Browser
const ICONS = {
    folder: `<svg class="w-5 h-5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20"><path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"></path></svg>`,
    video: `<svg class="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>`,
    subtitle: `<svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>`,
    file: `<svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 2H7a2 2 0 00-2 2v15a2 2 0 002 2z"></path></svg>`,
    back: `<svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 15l-3-3m0 0l3-3m-3 3h8M3 12a9 9 0 1118 0 9 9 0 01-18 0z"></path></svg>`
};

// Tab switching
document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        // Update nav styles
        document.querySelectorAll('.nav-btn').forEach(b => {
            b.classList.remove('active', 'text-white', 'bg-hover');
            const icon = b.querySelector('svg');
            if (icon) icon.classList.remove('text-accent');
        });

        btn.classList.add('active', 'text-white', 'bg-hover');
        const activeIcon = btn.querySelector('svg');
        if (activeIcon) activeIcon.classList.add('text-accent');

        // Update tabs visibility
        const tabId = btn.dataset.tab;
        document.querySelectorAll('.tab').forEach(t => t.classList.add('hidden'));
        const targetTab = document.getElementById(tabId);
        if (targetTab) {
            targetTab.classList.remove('hidden');
            // Scroll main area to top when switching
            document.getElementById('main-scroll-area').scrollTop = 0;
        }
    });
});

// Console output
const consoleOutput = document.getElementById('console-output');

// Helper to copy timestamp to form
window.copyTimestamp = function (element) {
    const time = element.textContent.replace(/[\[\]]/g, ''); // Remove []
    const startInput = document.querySelector('#clip-form input[name="start"]');
    const endInput = document.querySelector('#clip-form input[name="end"]');

    // Auto-switch to Clip tab
    const clipTabBtn = document.querySelector('.nav-btn[data-tab="clip"]');
    if (clipTabBtn && !clipTabBtn.classList.contains('active')) {
        clipTabBtn.click();
    }

    // Simple logic: If start is empty, fill start. If start full, fill end.
    if (!startInput.value || (startInput.value && endInput.value)) {
        startInput.value = time;
        endInput.value = ''; // Reset end if starting new clip
        // Visual feedback
        element.classList.add('text-green-400');
        setTimeout(() => element.classList.remove('text-green-400'), 200);
    } else {
        endInput.value = time;
        // Visual feedback
        element.classList.add('text-accent');
        setTimeout(() => element.classList.remove('text-accent'), 200);
    }
};

function log(message, type = '') {
    // Reset classes but keep base layout
    consoleOutput.className = 'flex-1 p-4 overflow-y-auto font-mono text-xs whitespace-pre-wrap selection:bg-accent selection:text-white';

    if (type === 'success') {
        consoleOutput.classList.add('text-green-400');
    } else if (type === 'error') {
        consoleOutput.classList.add('text-red-400');
    } else {
        consoleOutput.classList.add('text-gray-400');
    }

    // Escape HTML first
    let safeMessage = escapeHtml(message);

    // Make timestamps clickable [00:00:00] or [00:00:00.000]
    safeMessage = safeMessage.replace(/(\[\d{2}:\d{2}:\d{2}(?:\.\d+)?\])/g,
        '<span class="cursor-pointer hover:text-white hover:underline transition-colors text-accent" onclick="copyTimestamp(this)" title="Click to set Start/End time">$1</span>');

    consoleOutput.innerHTML = safeMessage;
    consoleOutput.scrollTop = consoleOutput.scrollHeight;
}

function clearConsole() {
    consoleOutput.textContent = 'Siap digunakan...';
    consoleOutput.className = 'flex-1 p-4 overflow-y-auto font-mono text-xs text-gray-400 whitespace-pre-wrap selection:bg-accent selection:text-white';
}

// Native file picker handler
function handleFileSelect(fileInput, textInputId) {
    const textInput = document.getElementById(textInputId);
    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        textInput.value = file.name;
    }
}

// API call helper
async function callApi(endpoint, data, button) {
    const spinner = button.querySelector('.spinner');
    if (spinner) spinner.classList.remove('hidden');

    button.disabled = true;
    button.classList.add('opacity-75', 'cursor-not-allowed');
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
        if (spinner) spinner.classList.add('hidden');
        button.disabled = false;
        button.classList.remove('opacity-75', 'cursor-not-allowed');
    }
}

// Form handlers
document.getElementById('full-auto-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    // Map Checkbox manually
    const burnSubtitle = document.getElementById('burn-subtitle-check').checked;

    const data = {
        url: form.url.value,
        api_key: form.api_key.value,
        model: form.model.value,
        watermark: form.watermark.value,
        burn_subtitle: burnSubtitle,
        analysis_method: form.analysis_method.value
    };

    // UI Updates
    const progressSection = document.getElementById('progress-section');
    const progressBar = document.getElementById('progress-bar');
    const progressStep = document.getElementById('progress-step');
    const progressPercent = document.getElementById('progress-percent');
    const progressStatus = document.getElementById('progress-status');
    const btn = form.querySelector('button');
    const spinner = btn.querySelector('.spinner');

    progressSection.classList.remove('hidden');
    progressBar.style.width = '0%';
    progressStep.textContent = 'Step 0/5';
    progressPercent.textContent = '0%';
    progressStatus.textContent = '🚀 Memulai proses...';

    if (spinner) spinner.classList.remove('hidden');
    btn.disabled = true;
    btn.classList.add('opacity-75', 'cursor-not-allowed');

    log('🚀 Memulai Full Automation Pipeline...', '');

    try {
        const response = await fetch('/api/full-auto', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (!result.success || !result.job_id) {
            progressStatus.textContent = '❌ Gagal memulai job!';
            log(result.output || 'Failed to start job', 'error');
            if (spinner) spinner.classList.add('hidden');
            btn.disabled = false;
            btn.classList.remove('opacity-75', 'cursor-not-allowed');
            return;
        }

        const jobId = result.job_id;
        log(`📋 Job started: ${jobId}`, '');

        let polling = true;
        while (polling) {
            await new Promise(resolve => setTimeout(resolve, 1500));

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

                    if (statusData.output) {
                        log(statusData.output, '');
                    }

                    if (statusData.status === 'done') {
                        progressBar.style.width = '100%';
                        progressStep.textContent = 'Step 5/5';
                        progressPercent.textContent = '100%';
                        progressStatus.textContent = '✅ Selesai!';
                        progressStatus.classList.add('text-green-400');
                        log('✅ Automation Complete!', 'success');
                        polling = false;
                    } else if (statusData.status === 'error') {
                        progressStatus.textContent = '❌ Gagal!';
                        progressStatus.classList.add('text-red-400');
                        log(statusData.output || 'Job failed', 'error');
                        polling = false;
                    }
                }
            } catch (pollError) {
                console.error('Polling error:', pollError);
            }
        }
    } catch (error) {
        progressStatus.textContent = '❌ Error!';
        log('Error: ' + error.message, 'error');
    } finally {
        if (spinner) spinner.classList.add('hidden');
        btn.disabled = false;
        btn.classList.remove('opacity-75', 'cursor-not-allowed');
    }
});

// Generic Listeners
['download-form', 'download-sub-form', 'analyze-form', 'clip-form', 'extract-form', 'burn-form'].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
        el.addEventListener('submit', async (e) => {
            e.preventDefault();
            const form = e.target;
            const btn = form.querySelector('button[type="submit"]');

            // Build data object from inputs
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());

            // Map endpoint based on form ID
            let endpoint = '';
            if (id === 'download-form') endpoint = 'download';
            if (id === 'download-sub-form') endpoint = 'download-subtitle';
            if (id === 'analyze-form') endpoint = 'analyze';
            if (id === 'clip-form') endpoint = 'clip';
            if (id === 'extract-form') endpoint = 'extract-subtitle';
            if (id === 'burn-form') endpoint = 'burn';

            await callApi(endpoint, data, btn);
        });
    }
});

// Auto Clip Form specific (handle JSON output)
document.getElementById('auto-clip-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const btn = form.querySelector('button');

    const data = {
        file: form.file.value,
        api_key: form.api_key.value,
        model: form.model.value
    };

    const spinner = btn.querySelector('.spinner');
    if (spinner) spinner.classList.remove('hidden');
    btn.disabled = true;
    btn.classList.add('opacity-75');

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
            const msg = result.output || JSON.stringify(result, null, 2);
            log(msg, result.success ? 'success' : 'error');
        }
    } catch (error) {
        log('Error: ' + error.message, 'error');
    } finally {
        if (spinner) spinner.classList.add('hidden');
        btn.disabled = false;
        btn.classList.remove('opacity-75');
    }
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
            fileList.innerHTML = '<div class="p-2 text-red-400">Error loading files</div>';
            return;
        }

        pathDisplay.textContent = data.current_path;

        let html = '';

        // Parent directory
        if (data.parent_path) {
            html += `
                <div class="flex items-center gap-3 p-2 rounded hover:bg-hover cursor-pointer group" onclick="loadFiles('${escapeHtml(data.parent_path)}')">
                    <span>${ICONS.back}</span>
                    <span class="text-xs font-mono group-hover:text-white">..</span>
                </div>
            `;
        }

        // Files and folders
        data.files.forEach(file => {
            const icon = file.is_dir ? ICONS.folder : getFileIcon(file.ext);
            const size = file.is_dir ? '' : `<span class="text-xs text-gray-500">${formatSize(file.size)}</span>`;
            const onclick = file.is_dir
                ? `loadFiles('${escapeHtml(file.path)}')`
                : `selectFile('${escapeHtml(file.name)}')`;

            html += `
                <div class="flex items-center gap-3 p-2 rounded hover:bg-hover cursor-pointer group" onclick="${onclick}">
                    <span class="flex-shrink-0">${icon}</span>
                    <span class="flex-1 text-xs truncate group-hover:text-white font-mono" title="${escapeHtml(file.name)}">${escapeHtml(file.name)}</span>
                    ${size}
                </div>
            `;
        });

        fileList.innerHTML = html || '<div class="p-4 text-gray-500 text-center text-xs">Empty folder</div>';
    } catch (error) {
        fileList.innerHTML = '<div class="p-2 text-red-400">Error: ' + error.message + '</div>';
    }
}

function showFilePicker(formId, fieldName, filterExt) {
    currentFilePicker = { formId, fieldName, filterExt };
    // Tailwind toggle
    const panel = document.getElementById('file-panel');
    panel.classList.remove('translate-x-full');
    loadFiles();
}

function closeFilePicker() {
    const panel = document.getElementById('file-panel');
    panel.classList.add('translate-x-full');
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
    if (['.mp4', '.webm', '.mkv'].includes(ext)) return ICONS.video;
    if (['.vtt', '.srt'].includes(ext)) return ICONS.subtitle;
    return ICONS.file;
}

function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function escapeHtml(text) {
    // Replace backslashes first, then quotes
    return text.replace(/\\/g, "\\\\").replace(/'/g, "\\'").replace(/"/g, '\\"');
}

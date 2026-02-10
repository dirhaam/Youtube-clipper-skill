
// Toggle AI fields based on Analysis Method
const analysisMethodSelect = document.getElementById('analysis-method');
const apiKeyInput = document.getElementById('api-key-input');
const modelSelect = document.querySelector('select[name="model"]');

if (analysisMethodSelect) {
    analysisMethodSelect.addEventListener('change', (e) => {
        const isAI = e.target.value === 'ai';
        const apiKeyContainer = apiKeyInput.closest('.space-y-2');
        const modelContainer = modelSelect.closest('.space-y-2');

        if (isAI) {
            apiKeyContainer.classList.remove('hidden', 'opacity-50', 'pointer-events-none');
            modelContainer.classList.remove('hidden', 'opacity-50', 'pointer-events-none');
            apiKeyInput.required = true;
        } else {
            apiKeyContainer.classList.add('opacity-50', 'pointer-events-none'); // Dim instead of hide to avoid layout shift
            modelContainer.classList.add('opacity-50', 'pointer-events-none');
            apiKeyInput.required = false;
        }
    });
}

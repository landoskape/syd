document.addEventListener('DOMContentLoaded', function () {
    const mode = localStorage.getItem('view-mode') || 'notebook';
    document.body.dataset.viewMode = mode;

    const toggle = document.createElement('div');
    toggle.id = 'view-mode-toggle';
    toggle.innerHTML = `
        <button id="notebook-mode" class="notebook-button">Notebook</button>
        <button id="browser-mode" class="browser-button">Browser</button>
    `;
    document.body.prepend(toggle);

    document.getElementById(`${mode}-mode`).classList.add('active');

    document.getElementById('notebook-mode').onclick = () => setMode('notebook');
    document.getElementById('browser-mode').onclick = () => setMode('browser');

    function setMode(mode) {
        localStorage.setItem('view-mode', mode);
        document.body.dataset.viewMode = mode;
        document.querySelectorAll('#view-mode-toggle button').forEach(btn => btn.classList.remove('active'));
        document.getElementById(`${mode}-mode`).classList.add('active');
    }
});

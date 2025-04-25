/**
 * Update the status display
 */
export function updateStatus(message) {
    const statusElement = document.getElementById('status-display');
    if (statusElement) {
        statusElement.innerHTML = `<b>Syd Controls</b> <span class="status-message">Status: ${message}</span>`;
    }
}

/**
 * Format parameter name as a label (capitalize each word)
 */
export function formatLabel(name) {
    return name
        .replace(/_/g, ' ')  // Replace underscores with spaces
        .replace(/\w\S*/g, function(txt) {
            return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        });
}

/**
 * Create and cache the slow loading image
 */
let slowLoadingImageCache = null; // Cache for slow loading image
export function createSlowLoadingImage() {
    if (slowLoadingImageCache) {
        return slowLoadingImageCache;
    }

    const canvas = document.createElement('canvas');
    canvas.width = 1200;
    canvas.height = 900;
    const ctx = canvas.getContext('2d');

    // Fill background
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Add loading text
    ctx.fillStyle = '#000000';
    ctx.font = 'bold 16px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('waiting for next figure...', canvas.width/2, canvas.height/2);

    slowLoadingImageCache = canvas.toDataURL();
    return slowLoadingImageCache;
}

import { state } from './state.js';
import { updateThreshold } from './config.js';
import { updateStatus, createSlowLoadingImage } from './utils.js';

let loadingTimeout = null; // Timeout for showing loading state

/**
 * Update the plot with current state
 */
export function updatePlot() {
    const plotImage = document.getElementById('plot-image');
    if (!plotImage) {
        console.warn("Plot image element not found");
        return;
    }

    // Clear any existing loading timeout
    if (loadingTimeout) {
        clearTimeout(loadingTimeout);
        loadingTimeout = null; // Reset timeout variable
    }

    // Show loading state after threshold
    loadingTimeout = setTimeout(() => {
        const slowLoadingDataURL = createSlowLoadingImage(); // Get cached or create new
        plotImage.src = slowLoadingDataURL;
        plotImage.style.opacity = '0.5';
        updateStatus('Generating plot...'); // Update status during loading
    }, updateThreshold * 1000);

    // Build query string from state
    const queryParams = new URLSearchParams();
    for (const [name, value] of Object.entries(state)) {
        if (Array.isArray(value) || typeof value === 'object') {
            // Ensure complex objects/arrays are properly stringified for URL
            queryParams.append(name, JSON.stringify(value));
        } else {
            queryParams.append(name, value);
        }
    }

    // Set the image source to the plot endpoint with parameters
    const url = `/plot?${queryParams.toString()}`;

    // Use an Image object to preload and handle load/error events
    const newImage = new Image();

    newImage.onload = function() {
        // Clear loading timeout if it hasn't fired yet
        if (loadingTimeout) {
            clearTimeout(loadingTimeout);
            loadingTimeout = null;
        }
        // Update the actual image source and reset opacity
        plotImage.src = url;
        plotImage.style.opacity = 1;
        // Don't necessarily set status to Ready here, as state updates might happen
        // Let the calling function (updateParameter or initial load) handle final status
    };

    newImage.onerror = function() {
        // Clear loading timeout
        if (loadingTimeout) {
            clearTimeout(loadingTimeout);
            loadingTimeout = null;
        }
        updateStatus('Error loading plot');
        plotImage.style.opacity = 1; // Reset opacity even on error
        // Optionally display an error image/message
        // plotImage.src = 'path/to/error/image.png';
    };

    // Start loading the new image
    newImage.src = url;
}

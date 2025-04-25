export let updateThreshold = 1.0;  // Default update threshold

// Config object parsed from HTML data attributes
export const config = {
    controlsPosition: document.getElementById('viewer-config')?.dataset.controlsPosition || 'left',
    controlsWidthPercent: parseInt(document.getElementById('viewer-config')?.dataset.controlsWidthPercent || 20),
    plotMarginPercent: parseInt(document.getElementById('viewer-config')?.dataset.plotMarginPercent || 15)
};

// Function to update threshold, needed by system controls
export function setUpdateThreshold(value) {
    updateThreshold = value;
}

// Function to update config values, needed by system controls
export function setConfigValue(key, value) {
    if (key in config) {
        config[key] = value;
    } else {
        console.warn(`Attempted to set unknown config key: ${key}`);
    }
}

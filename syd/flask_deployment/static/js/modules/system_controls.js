import { config, updateThreshold, setUpdateThreshold, setConfigValue } from './config.js';
// Import createFloatController - we assume it will be exported from ui_controls.js
import { createFloatController } from './ui_controls.js';

/**
 * Create system controls (width, threshold, margin)
 * @param {HTMLElement} container - The DOM element to append controls to.
 */
export function createSystemControls(container) {
    // Create controls width slider
    const widthControl = createFloatController('controls_width', {
        type: 'float',
        value: config.controlsWidthPercent,
        min: 10,
        max: 50,
        step: 1
    });
    widthControl.className = 'numeric-control system-control';

    // Add label for width control
    const widthLabel = document.createElement('span');
    widthLabel.className = 'control-label';
    widthLabel.textContent = 'Controls Width %';

    const widthGroup = document.createElement('div');
    widthGroup.className = 'control-group';
    widthGroup.appendChild(widthLabel);
    widthGroup.appendChild(widthControl);

    // Create update threshold slider
    const thresholdControl = createFloatController('update_threshold', {
        type: 'float',
        value: updateThreshold,
        min: 0.1,
        max: 10.0,
        step: 0.1
    });
    thresholdControl.className = 'numeric-control system-control';

    // Add label for threshold control
    const thresholdLabel = document.createElement('span');
    thresholdLabel.className = 'control-label';
    thresholdLabel.textContent = 'Update Threshold';

    const thresholdGroup = document.createElement('div');
    thresholdGroup.className = 'control-group';
    thresholdGroup.appendChild(thresholdLabel);
    thresholdGroup.appendChild(thresholdControl);

    // Create plot margin slider
    const plotMarginControl = createFloatController('plot_margin', {
        type: 'float',
        value: config.plotMarginPercent,
        min: 0,
        max: 50,
        step: 1
    });
    plotMarginControl.className = 'numeric-control system-control';

    // Add label for margin control
    const marginLabel = document.createElement('span');
    marginLabel.className = 'control-label';
    marginLabel.textContent = 'Plot Margin %';

    const marginGroup = document.createElement('div');
    marginGroup.className = 'control-group';
    marginGroup.appendChild(marginLabel);
    marginGroup.appendChild(plotMarginControl);

    // Add custom event listeners
    // Width Control Listeners
    function updateControlsWidth(width) {
        setConfigValue('controlsWidthPercent', width); // Use setter from config.js

        // Update the root containers using querySelector for classes
        const rootContainer = document.querySelector('.viewer-container');
        const controlsContainer = document.querySelector('.controls-container'); // Select the outer div by class
        const plotContainer = document.querySelector('.plot-container');

        if (rootContainer && controlsContainer && plotContainer) {
            if (config.controlsPosition === 'left' || config.controlsPosition === 'right') {
                controlsContainer.style.width = `${width}%`;
                plotContainer.style.width = `${100 - width}%`;
            }
        }

        // Ensure slider/input values match
        widthSlider.value = width;
        widthInput.value = width;
    }
    
    const widthSlider = widthControl.querySelector('input[type="range"]');
    const widthInput = widthControl.querySelector('input[type="number"]');

    widthSlider.addEventListener('input', function() { // Real-time update for number input
        updateControlsWidth(this.value);
    });

    widthInput.addEventListener('change', function() {
        updateControlsWidth(this.value);
    });

    // Threshold Control Listeners
    const thresholdSlider = thresholdControl.querySelector('input[type="range"]');
    const thresholdInput = thresholdControl.querySelector('input[type="number"]');

    thresholdSlider.addEventListener('input', function() { // Real-time update for number input
        thresholdInput.value = this.value;
    });

    thresholdSlider.addEventListener('change', function() {
        const newThreshold = parseFloat(this.value);
        setUpdateThreshold(newThreshold); // Use setter from config.js
        thresholdInput.value = newThreshold; // Ensure input matches final value
        thresholdSlider.value = newThreshold; // Ensure slider matches final value
    });

    // Plot Margin Control Listeners
    const marginSlider = plotMarginControl.querySelector('input[type="range"]');
    const marginInput = plotMarginControl.querySelector('input[type="number"]');
    const plotContainer = document.querySelector('.plot-container');

    // Function to apply margin and adjust size of the plot image
    function applyPlotMargin(marginPercent) {
        const plotImage = document.getElementById('plot-image'); // Get the image element
        if (plotImage) {
            const effectiveMargin = parseFloat(marginPercent); // Ensure it's a number
            // Apply margin to the image
            plotImage.style.margin = `${effectiveMargin}%`;
            // Adjust width and height to account for the margin
            plotImage.style.width = `calc(100% - ${2 * effectiveMargin}%)`;
            plotImage.style.height = `calc(100% - ${2 * effectiveMargin}%)`;
            // Reset container padding just in case
            if (plotContainer) {
                 plotContainer.style.padding = '0';
            }
            setConfigValue('plotMarginPercent', effectiveMargin); // Update config using setter
        } else {
            console.warn('Plot image element not found when applying margin.');
        }
    }

    marginSlider.addEventListener('input', function() { // Real-time update for number input
        marginInput.value = this.value;
    });

    marginSlider.addEventListener('change', function() {
        const margin = parseFloat(this.value);
        marginInput.value = margin; // Ensure input matches final value
        marginSlider.value = margin; // Ensure slider matches final value
        applyPlotMargin(margin);
    });

    // Add wheel event listener to plot container for margin control
    if (plotContainer) {
        plotContainer.addEventListener('wheel', function(event) {
            event.preventDefault(); // Prevent page scrolling

            const currentValue = parseFloat(marginSlider.value);
            const step = parseFloat(marginSlider.step) || 1;
            const min = parseFloat(marginSlider.min);
            const max = parseFloat(marginSlider.max);

            let newValue;
            if (event.deltaY < 0) {
                // Scrolling up (or zoom in) -> decrease margin
                newValue = currentValue - step;
            } else {
                // Scrolling down (or zoom out) -> increase margin
                newValue = currentValue + step;
            }

            // Clamp the value within min/max bounds
            newValue = Math.max(min, Math.min(max, newValue));

            // Only update if the value actually changed
            if (newValue !== currentValue) {
                marginSlider.value = newValue;
                marginInput.value = newValue;
                applyPlotMargin(newValue);
            }
        }, { passive: false }); // Need passive: false to call preventDefault()
    }

    // Apply initial margin
    applyPlotMargin(config.plotMarginPercent);

    container.appendChild(widthGroup);
    container.appendChild(thresholdGroup);
    container.appendChild(marginGroup);
}
/**
 * Syd Viewer JavaScript for Flask deployment
 * Handles dynamic creation of UI components and interaction with the Flask backend
 */

// State object to store current values
let state = {};
let paramInfo = {};

// Config object parsed from HTML data attributes
const config = {
    figureWidth: parseFloat(document.getElementById('viewer-config').dataset.figureWidth || 8.0),
    figureHeight: parseFloat(document.getElementById('viewer-config').dataset.figureHeight || 6.0),
    controlsPosition: document.getElementById('viewer-config').dataset.controlsPosition || 'left',
    controlsWidthPercent: parseInt(document.getElementById('viewer-config').dataset.controlsWidthPercent || 30)
};

// Track whether we're currently in an update operation
let isUpdating = false;

// Initialize the viewer
document.addEventListener('DOMContentLoaded', function() {
    // Fetch initial parameter information from server
    fetch('/init-data')
        .then(response => response.json())
        .then(data => {
            paramInfo = data.params;
            
            // Initialize state from parameter info
            for (const [name, param] of Object.entries(paramInfo)) {
                state[name] = param.value;
            }
            
            // Create UI controls for each parameter
            createControls();
            
            // Generate initial plot
            updatePlot();
        })
        .catch(error => {
            console.error('Error initializing viewer:', error);
        });
});

/**
 * Create UI controls based on parameter types
 */
function createControls() {
    const controlsContainer = document.getElementById('controls-container');
    
    // Clear any existing controls
    controlsContainer.innerHTML = '';
    
    // Create controls for each parameter
    for (const [name, param] of Object.entries(paramInfo)) {
        // Create control group
        const controlGroup = createControlGroup(name, param);
        
        // Add to container
        if (controlGroup) {
            controlsContainer.appendChild(controlGroup);
        }
    }
}

/**
 * Create a control group for a parameter
 */
function createControlGroup(name, param) {
    // Skip if param type is unknown
    if (!param.type || param.type === 'unknown') {
        console.warn(`Unknown parameter type for ${name}`);
        return null;
    }
    
    // Create control group div
    const controlGroup = document.createElement('div');
    controlGroup.className = 'control-group';
    controlGroup.id = `control-group-${name}`;
    
    // Add label
    const label = document.createElement('span');
    label.className = 'control-label';
    label.textContent = formatLabel(name);
    controlGroup.appendChild(label);
    
    // Create specific control based on parameter type
    const control = createControl(name, param);
    if (control) {
        controlGroup.appendChild(control);
    }
    
    return controlGroup;
}

/**
 * Create a specific control based on parameter type
 */
function createControl(name, param) {
    switch (param.type) {
        case 'text':
            return createTextControl(name, param);
        case 'boolean':
            return createBooleanControl(name, param);
        case 'integer':
            return createIntegerControl(name, param);
        case 'float':
            return createFloatControl(name, param);
        case 'selection':
            return createSelectionControl(name, param);
        case 'multiple-selection':
            return createMultipleSelectionControl(name, param);
        case 'integer-range':
            return createIntegerRangeControl(name, param);
        case 'float-range':
            return createFloatRangeControl(name, param);
        case 'unbounded-integer':
            return createUnboundedIntegerControl(name, param);
        case 'unbounded-float':
            return createUnboundedFloatControl(name, param);
        case 'button':
            return createButtonControl(name, param);
        default:
            console.warn(`No control implementation for type: ${param.type}`);
            return null;
    }
}

/**
 * Create text input control
 */
function createTextControl(name, param) {
    const input = document.createElement('input');
    input.type = 'text';
    input.id = `${name}-input`;
    input.value = param.value || '';
    
    input.addEventListener('change', function() {
        updateParameter(name, this.value);
    });
    
    return input;
}

/**
 * Create boolean checkbox control
 */
function createBooleanControl(name, param) {
    const container = document.createElement('div');
    container.className = 'checkbox-container';
    
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.id = `${name}-checkbox`;
    checkbox.checked = param.value === true;
    
    checkbox.addEventListener('change', function() {
        updateParameter(name, this.checked);
    });
    
    container.appendChild(checkbox);
    return container;
}

/**
 * Create integer control with slider and number input
 */
function createIntegerControl(name, param) {
    const container = document.createElement('div');
    container.className = 'numeric-control';
    
    // Create slider
    const slider = document.createElement('input');
    slider.type = 'range';
    slider.id = `${name}-slider`;
    slider.min = param.min;
    slider.max = param.max;
    slider.step = param.step || 1;
    slider.value = param.value;
    
    // Create number input
    const input = document.createElement('input');
    input.type = 'number';
    input.id = `${name}-input`;
    input.min = param.min;
    input.max = param.max;
    input.step = param.step || 1;
    input.value = param.value;
    
    // Add event listeners
    slider.addEventListener('input', function() {
        const value = parseInt(this.value, 10);
        input.value = value;
        updateParameter(name, value);
    });
    
    input.addEventListener('change', function() {
        const value = parseInt(this.value, 10);
        if (!isNaN(value) && value >= param.min && value <= param.max) {
            slider.value = value;
            updateParameter(name, value);
        } else {
            this.value = state[name]; // Revert to current state
        }
    });
    
    container.appendChild(slider);
    container.appendChild(input);
    return container;
}

/**
 * Create float control with slider and number input
 */
function createFloatControl(name, param) {
    const container = document.createElement('div');
    container.className = 'numeric-control';
    
    // Create slider
    const slider = document.createElement('input');
    slider.type = 'range';
    slider.id = `${name}-slider`;
    slider.min = param.min;
    slider.max = param.max;
    slider.step = param.step || 0.01;
    slider.value = param.value;
    
    // Create number input
    const input = document.createElement('input');
    input.type = 'number';
    input.id = `${name}-input`;
    input.min = param.min;
    input.max = param.max;
    input.step = param.step || 0.01;
    input.value = param.value;
    
    // Add event listeners
    slider.addEventListener('input', function() {
        const value = parseFloat(this.value);
        input.value = value;
        updateParameter(name, value);
    });
    
    input.addEventListener('change', function() {
        const value = parseFloat(this.value);
        if (!isNaN(value) && value >= param.min && value <= param.max) {
            slider.value = value;
            updateParameter(name, value);
        } else {
            this.value = state[name]; // Revert to current state
        }
    });
    
    container.appendChild(slider);
    container.appendChild(input);
    return container;
}

/**
 * Create selection dropdown control
 */
function createSelectionControl(name, param) {
    const select = document.createElement('select');
    select.id = `${name}-select`;
    
    // Add options
    param.options.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option;
        optionElement.textContent = formatLabel(String(option));
        // Store the original type information as a data attribute
        optionElement.dataset.originalType = typeof option;
        // For float values, also store the original value for exact comparison
        if (typeof option === 'number') {
            optionElement.dataset.originalValue = option;
        }
        select.appendChild(optionElement);
    });
    
    // Set default value
    select.value = param.value;
    
    // Add event listener
    select.addEventListener('change', function() {
        // Get the selected option element
        const selectedOption = this.options[this.selectedIndex];
        let valueToSend = this.value;
        
        // Convert back to the original type if needed
        if (selectedOption.dataset.originalType === 'number') {
            // Use the original value from the dataset for exact precision with floats
            if (selectedOption.dataset.originalValue) {
                valueToSend = parseFloat(selectedOption.dataset.originalValue);
            } else {
                valueToSend = parseFloat(valueToSend);
            }
        }
        
        updateParameter(name, valueToSend);
    });
    
    return select;
}

/**
 * Create multiple selection control
 */
function createMultipleSelectionControl(name, param) {
    const container = document.createElement('div');
    container.className = 'multiple-selection-container';
    
    // Create select element
    const select = document.createElement('select');
    select.id = `${name}-select`;
    select.className = 'multiple-select';
    select.multiple = true;
    
    // Add options
    param.options.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option;
        optionElement.textContent = formatLabel(String(option));
        
        // Check if this option is selected
        if (param.value.includes(option)) {
            optionElement.selected = true;
        }
        
        select.appendChild(optionElement);
    });
    
    // Helper text
    const helperText = document.createElement('div');
    helperText.className = 'helper-text';
    helperText.textContent = 'Ctrl+click to select multiple';
    
    // Add event listener
    select.addEventListener('change', function() {
        // Get all selected options
        const selectedValues = Array.from(this.selectedOptions).map(option => option.value);
        updateParameter(name, selectedValues);
    });
    
    container.appendChild(select);
    container.appendChild(helperText);
    return container;
}

/**
 * Create integer range control with dual sliders
 */
function createIntegerRangeControl(name, param) {
    return createRangeControl(name, param, parseInt);
}

/**
 * Create float range control with dual sliders
 */
function createFloatRangeControl(name, param) {
    return createRangeControl(name, param, parseFloat);
}

/**
 * Generic range control creator
 */
function createRangeControl(name, param, converter) {
    const container = document.createElement('div');
    container.className = 'range-container';
    
    // Create inputs container
    const inputsContainer = document.createElement('div');
    inputsContainer.className = 'range-inputs';
    
    // Create min input
    const minInput = document.createElement('input');
    minInput.type = 'number';
    minInput.id = `${name}-min-input`;
    minInput.className = 'range-input';
    minInput.min = param.min;
    minInput.max = param.max;
    minInput.step = param.step || 1;
    minInput.value = param.value[0];
    
    // Create slider container
    const sliderContainer = document.createElement('div');
    sliderContainer.className = 'range-slider-container';
    
    // Create min slider
    const minSlider = document.createElement('input');
    minSlider.type = 'range';
    minSlider.id = `${name}-min-slider`;
    minSlider.className = 'range-slider min-slider';
    minSlider.min = param.min;
    minSlider.max = param.max;
    minSlider.step = param.step || 1;
    minSlider.value = param.value[0];
    
    // Create max slider
    const maxSlider = document.createElement('input');
    maxSlider.type = 'range';
    maxSlider.id = `${name}-max-slider`;
    maxSlider.className = 'range-slider max-slider';
    maxSlider.min = param.min;
    maxSlider.max = param.max;
    maxSlider.step = param.step || 1;
    maxSlider.value = param.value[1];
    
    // Create max input
    const maxInput = document.createElement('input');
    maxInput.type = 'number';
    maxInput.id = `${name}-max-input`;
    maxInput.className = 'range-input';
    maxInput.min = param.min;
    maxInput.max = param.max;
    maxInput.step = param.step || 1;
    maxInput.value = param.value[1];
    
    // Range display
    const rangeDisplay = document.createElement('div');
    rangeDisplay.className = 'range-display';
    rangeDisplay.id = `${name}-range-display`;
    rangeDisplay.textContent = `Range: ${param.value[0]} - ${param.value[1]}`;
    
    // Add event listeners
    minSlider.addEventListener('input', function() {
        const minVal = converter(this.value);
        const maxVal = converter(maxSlider.value);
        
        if (minVal <= maxVal) {
            state[name] = [minVal, maxVal];
            minInput.value = minVal;
            updateRangeDisplay(rangeDisplay, minVal, maxVal);
            updateParameter(name, [minVal, maxVal]);
        } else {
            this.value = maxVal;
        }
    });
    
    maxSlider.addEventListener('input', function() {
        const minVal = converter(minSlider.value);
        const maxVal = converter(this.value);
        
        if (maxVal >= minVal) {
            state[name] = [minVal, maxVal];
            maxInput.value = maxVal;
            updateRangeDisplay(rangeDisplay, minVal, maxVal);
            updateParameter(name, [minVal, maxVal]);
        } else {
            this.value = minVal;
        }
    });
    
    minInput.addEventListener('change', function() {
        const minVal = converter(this.value);
        const maxVal = converter(maxInput.value);
        
        if (!isNaN(minVal) && minVal >= param.min && minVal <= maxVal) {
            state[name] = [minVal, maxVal];
            minSlider.value = minVal;
            updateRangeDisplay(rangeDisplay, minVal, maxVal);
            updateParameter(name, [minVal, maxVal]);
        } else {
            this.value = state[name][0];
        }
    });
    
    maxInput.addEventListener('change', function() {
        const minVal = converter(minInput.value);
        const maxVal = converter(this.value);
        
        if (!isNaN(maxVal) && maxVal <= param.max && maxVal >= minVal) {
            state[name] = [minVal, maxVal];
            maxSlider.value = maxVal;
            updateRangeDisplay(rangeDisplay, minVal, maxVal);
            updateParameter(name, [minVal, maxVal]);
        } else {
            this.value = state[name][1];
        }
    });
    
    // Assemble the control
    inputsContainer.appendChild(minInput);
    inputsContainer.appendChild(maxInput);
    
    sliderContainer.appendChild(minSlider);
    sliderContainer.appendChild(maxSlider);
    
    container.appendChild(inputsContainer);
    container.appendChild(sliderContainer);
    container.appendChild(rangeDisplay);
    
    return container;
}

/**
 * Update range display text
 */
function updateRangeDisplay(displayElement, min, max) {
    displayElement.textContent = `Range: ${min} - ${max}`;
}

/**
 * Create unbounded integer control
 */
function createUnboundedIntegerControl(name, param) {
    const input = document.createElement('input');
    input.type = 'number';
    input.id = `${name}-input`;
    input.value = param.value;
    input.step = 1;
    
    input.addEventListener('change', function() {
        const value = parseInt(this.value, 10);
        if (!isNaN(value)) {
            updateParameter(name, value);
        } else {
            this.value = state[name];
        }
    });
    
    return input;
}

/**
 * Create unbounded float control
 */
function createUnboundedFloatControl(name, param) {
    const input = document.createElement('input');
    input.type = 'number';
    input.id = `${name}-input`;
    input.value = param.value;
    input.step = param.step || 'any';
    
    input.addEventListener('change', function() {
        const value = parseFloat(this.value);
        if (!isNaN(value)) {
            updateParameter(name, value);
        } else {
            this.value = state[name];
        }
    });
    
    return input;
}

/**
 * Create button control
 */
function createButtonControl(name, param) {
    const button = document.createElement('button');
    button.id = `${name}-button`;
    button.textContent = param.label || name;
    
    button.addEventListener('click', function() {
        // Show button as active
        button.classList.add('active');
        
        // Send action to the server
        fetch('/update-param', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: name,
                value: null, // Value is not used for buttons
                action: true
            }),
        })
        .then(response => response.json())
        .then(data => {
            // Remove active class
            button.classList.remove('active');
            
            if (data.error) {
                console.error('Error:', data.error);
            } else {
                // Update state with any changes from callbacks
                updateStateFromServer(data.state);
                // Update plot if needed
                updatePlot();
            }
        })
        .catch(error => {
            // Remove active class
            button.classList.remove('active');
            console.error('Error:', error);
        });
    });
    
    return button;
}

/**
 * Update a parameter value and send to server
 */
function updateParameter(name, value) {
    // Prevent recursive updates
    if (isUpdating) {
        return;
    }
    
    // Update local state
    state[name] = value;
    
    // Send update to server
    fetch('/update-param', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            name: name,
            value: value
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error:', data.error);
        } else {
            // Update state with any changes from callbacks
            updateStateFromServer(data.state);
            // Update plot
            updatePlot();
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

/**
 * Update local state from server response
 */
function updateStateFromServer(serverState) {
    // Set updating flag to prevent recursive updates
    isUpdating = true;
    
    try {
        // Update any parameters that changed due to callbacks
        for (const [name, value] of Object.entries(serverState)) {
            if (JSON.stringify(state[name]) !== JSON.stringify(value)) {
                state[name] = value;
                updateControlValue(name, value);
            }
        }
    } finally {
        // Clear updating flag
        isUpdating = false;
    }
}

/**
 * Update a control's value in the UI
 */
function updateControlValue(name, value) {
    if (!paramInfo[name]) return;
    
    const param = paramInfo[name];
    
    switch (param.type) {
        case 'text':
            document.getElementById(`${name}-input`).value = value;
            break;
        case 'boolean':
            document.getElementById(`${name}-checkbox`).checked = value === true;
            break;
        case 'integer':
        case 'float':
            document.getElementById(`${name}-slider`).value = value;
            document.getElementById(`${name}-input`).value = value;
            break;
        case 'selection':
            document.getElementById(`${name}-select`).value = value;
            break;
        case 'multiple-selection':
            const select = document.getElementById(`${name}-select`);
            if (select) {
                Array.from(select.options).forEach(option => {
                    option.selected = value.includes(option.value);
                });
            }
            break;
        case 'integer-range':
        case 'float-range':
            document.getElementById(`${name}-min-slider`).value = value[0];
            document.getElementById(`${name}-max-slider`).value = value[1];
            document.getElementById(`${name}-min-input`).value = value[0];
            document.getElementById(`${name}-max-input`).value = value[1];
            const display = document.getElementById(`${name}-range-display`);
            if (display) {
                updateRangeDisplay(display, value[0], value[1]);
            }
            break;
        case 'unbounded-integer':
        case 'unbounded-float':
            document.getElementById(`${name}-input`).value = value;
            break;
    }
}

/**
 * Format parameter name as a label (capitalize each word)
 */
function formatLabel(name) {
    return name
        .replace(/_/g, ' ')  // Replace underscores with spaces
        .replace(/\w\S*/g, function(txt) {
            return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        });
}

/**
 * Update the plot with current state
 */
function updatePlot() {
    // Build query string from state
    const queryParams = new URLSearchParams();
    
    for (const [name, value] of Object.entries(state)) {
        // Handle arrays and special types by serializing to JSON
        if (Array.isArray(value) || typeof value === 'object') {
            queryParams.append(name, JSON.stringify(value));
        } else {
            queryParams.append(name, value);
        }
    }
    
    // Set the image source to the plot endpoint with parameters
    const url = `/plot?${queryParams.toString()}`;
    const plotImage = document.getElementById('plot-image');
    
    // Show loading indicator
    plotImage.style.opacity = 0.5;
    
    // Create a new image object
    const newImage = new Image();
    newImage.onload = function() {
        plotImage.src = url;
        plotImage.style.opacity = 1;
    };
    newImage.src = url;
} 
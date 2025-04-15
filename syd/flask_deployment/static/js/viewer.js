let state = {};
let paramInfo = {};
let paramOrder = [];
let isUpdating = false;

// Config object parsed from HTML data attributes
const config = {
    controlsPosition: document.getElementById('viewer-config').dataset.controlsPosition || 'left',
    controlsWidthPercent: parseInt(document.getElementById('viewer-config').dataset.controlsWidthPercent || 20)
};

// Initialize the viewer
document.addEventListener('DOMContentLoaded', function() {
    // Fetch initial parameter information from server
    fetch('/init-data')
        .then(response => response.json())
        .then(data => {
            paramInfo = data.params;
            paramOrder = data.param_order;
            
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
    
    // Create controls for each parameter in the order specified by the viewer
    paramOrder.forEach(name => {
        const param = paramInfo[name];
        if (!param) {
            console.warn(`Parameter info not found for ${name} during control creation.`);
            return; // Skip if param info is missing for some reason
        }
        
        // Create control group
        const controlGroup = createControlGroup(name, param);
        
        // Add to container
        if (controlGroup) {
            controlsContainer.appendChild(controlGroup);
        }
    });
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
    slider.addEventListener('change', function() {
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
    slider.addEventListener('change', function() {
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
    minInput.step = param.step || (converter === parseInt ? 1 : 0.01); // Default step
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
    minSlider.step = param.step || (converter === parseInt ? 1 : 0.01); // Default step
    minSlider.value = param.value[0];
    
    // Create max slider
    const maxSlider = document.createElement('input');
    maxSlider.type = 'range';
    maxSlider.id = `${name}-max-slider`;
    maxSlider.className = 'range-slider max-slider';
    maxSlider.min = param.min;
    maxSlider.max = param.max;
    maxSlider.step = param.step || (converter === parseInt ? 1 : 0.01); // Default step
    maxSlider.value = param.value[1];
    
    // Create max input
    const maxInput = document.createElement('input');
    maxInput.type = 'number';
    maxInput.id = `${name}-max-input`;
    maxInput.className = 'range-input';
    maxInput.min = param.min;
    maxInput.max = param.max;
    maxInput.step = param.step || (converter === parseInt ? 1 : 0.01); // Default step
    maxInput.value = param.value[1];
    
    // Add event listeners
    minSlider.addEventListener('change', function() {
        const minVal = converter(this.value);
        const maxVal = converter(maxSlider.value);
        
        if (minVal <= maxVal) {
            state[name] = [minVal, maxVal];
            minInput.value = minVal;
            updateSliderGradient(minSlider, maxSlider, sliderContainer); // Update gradient
            updateParameter(name, [minVal, maxVal]);
        } else {
            this.value = maxVal; // Snap to maxVal if crossing
            minInput.value = maxVal; // Also update input
            updateSliderGradient(minSlider, maxSlider, sliderContainer); // Update gradient
        }
    });
    
    maxSlider.addEventListener('change', function() {
        const minVal = converter(minSlider.value);
        const maxVal = converter(this.value);
        
        if (maxVal >= minVal) {
            state[name] = [minVal, maxVal];
            maxInput.value = maxVal;
            updateSliderGradient(minSlider, maxSlider, sliderContainer); // Update gradient
            updateParameter(name, [minVal, maxVal]);
        } else {
            this.value = minVal; // Snap to minVal if crossing
            maxInput.value = minVal; // Also update input
            updateSliderGradient(minSlider, maxSlider, sliderContainer); // Update gradient
        }
    });
    
    minInput.addEventListener('change', function() {
        const minVal = converter(this.value);
        const maxVal = converter(maxInput.value);
        
        if (!isNaN(minVal) && minVal >= param.min && minVal <= maxVal) {
            state[name] = [minVal, maxVal];
            minSlider.value = minVal;
            updateSliderGradient(minSlider, maxSlider, sliderContainer); // Update gradient
            updateParameter(name, [minVal, maxVal]);
        } else {
            // Revert input value and ensure gradient matches state
            this.value = state[name][0]; 
            minSlider.value = state[name][0];
            updateSliderGradient(minSlider, maxSlider, sliderContainer); 
        }
    });
    
    maxInput.addEventListener('change', function() {
        const minVal = converter(minInput.value);
        const maxVal = converter(this.value);
        
        if (!isNaN(maxVal) && maxVal <= param.max && maxVal >= minVal) {
            state[name] = [minVal, maxVal];
            maxSlider.value = maxVal;
            updateSliderGradient(minSlider, maxSlider, sliderContainer); // Update gradient
            updateParameter(name, [minVal, maxVal]);
        } else {
            // Revert input value and ensure gradient matches state
            this.value = state[name][1];
            maxSlider.value = state[name][1];
            updateSliderGradient(minSlider, maxSlider, sliderContainer);
        }
    });
    
    // Assemble the control
    inputsContainer.appendChild(minInput);
    inputsContainer.appendChild(maxInput);
    
    sliderContainer.appendChild(minSlider);
    sliderContainer.appendChild(maxSlider);
    
    container.appendChild(inputsContainer);
    container.appendChild(sliderContainer);
    
    // Set initial gradient state
    updateSliderGradient(minSlider, maxSlider, sliderContainer);
    
    return container;
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
                updateStateFromServer(data.state, data.params);
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
            value: value,
            action: false
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error:', data.error);
        } else {
            // Update state with any changes from callbacks
            updateStateFromServer(data.state, data.params);
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
function updateStateFromServer(serverState, serverParamInfo) {
    // Set updating flag to prevent recursive updates
    isUpdating = true;
    
    try {
        // Update any parameters that changed due to callbacks
        for (const [name, value] of Object.entries(serverState)) {
            if (JSON.stringify(state[name]) !== JSON.stringify(value) || JSON.stringify(paramInfo[name]) !== JSON.stringify(serverParamInfo[name])) {
                state[name] = value;
                updateControlValue(name, value, serverParamInfo[name]);
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
function updateControlValue(name, value, param) {
    if (!paramInfo[name]) return;

    switch (param.type) {
        case 'text':
            document.getElementById(`${name}-input`).value = value;
            break;
        case 'boolean':
            document.getElementById(`${name}-checkbox`).checked = value === true;
            break;
        case 'integer':
        case 'float':
            const slider = document.getElementById(`${name}-slider`);
            slider.value = value;
            slider.min = param.min;
            slider.max = param.max;
            slider.step = param.step;
            const input = document.getElementById(`${name}-input`);
            input.value = value;
            input.min = param.min;
            input.max = param.max;
            input.step = param.step;
            break;
        case 'selection':
            const selectElement = document.getElementById(`${name}-select`);
            if (selectElement) {
                // 1. Clear existing options
                selectElement.innerHTML = '';

                // 2. Add new options from the updated param info
                if (param.options && Array.isArray(param.options)) {
                    param.options.forEach(option => {
                        const optionElement = document.createElement('option');
                        optionElement.value = option;
                        optionElement.textContent = formatLabel(String(option));
                        // Store original type/value info
                        optionElement.dataset.originalType = typeof option;
                        if (typeof option === 'number') {
                            optionElement.dataset.originalValue = option;
                        }
                        selectElement.appendChild(optionElement);
                    });
                } else {
                    console.warn(`No options found or options is not an array for parameter: ${name}`);
                }

                selectElement.value = value;
            } else {
                console.warn(`No select element found for parameter: ${name}`);
            }
            break;
        case 'multiple-selection':
            const multiSelect = document.getElementById(`${name}-select`);
            if (multiSelect) {
                multiSelect.innerHTML = '';

                if (param.options && Array.isArray(param.options)) {
                    param.options.forEach(option => {
                        const optionElement = document.createElement('option');
                        optionElement.value = option;
                        optionElement.textContent = formatLabel(String(option));
                        multiSelect.appendChild(optionElement);
                    });
                } else {
                    console.warn(`No options found or options is not an array for parameter: ${name}`);
                }

                Array.from(multiSelect.options).forEach(option => {
                    option.selected = value.includes(option.value);
                });
            }
            break;
        case 'integer-range':
        case 'float-range':
            const minSlider = document.getElementById(`${name}-min-slider`);
            const maxSlider = document.getElementById(`${name}-max-slider`);
            const minInput = document.getElementById(`${name}-min-input`);
            const maxInput = document.getElementById(`${name}-max-input`);

            minSlider.min = param.min;
            minSlider.max = param.max;
            minSlider.step = param.step;
            maxSlider.min = param.min;
            maxSlider.max = param.max;
            maxSlider.step = param.step;
            minInput.min = param.min;
            minInput.max = param.max;
            minInput.step = param.step;
            maxInput.min = param.min;
            maxInput.max = param.max;
            maxInput.step = param.step;
            
            minSlider.value = value[0];
            maxSlider.value = value[1];
            minInput.value = value[0];
            maxInput.value = value[1];
            
            // Update the gradient background
            const sliderContainer = minSlider ? minSlider.closest('.range-slider-container') : null;
            if (sliderContainer) {
                updateSliderGradient(minSlider, maxSlider, sliderContainer);
            } else {
                 console.warn(`Could not find slider container for range control: ${name}`);
            }
            break;
        case 'unbounded-integer':
        case 'unbounded-float':
            document.getElementById(`${name}-input`).value = value;
            break;
    }
}

/**
 * Updates the background gradient for the dual range slider.
 * @param {HTMLInputElement} minSlider - The minimum value slider element.
 * @param {HTMLInputElement} maxSlider - The maximum value slider element.
 * @param {HTMLElement} container - The container element holding the sliders.
 */
function updateSliderGradient(minSlider, maxSlider, container) {
    const rangeMin = parseFloat(minSlider.min);
    const rangeMax = parseFloat(minSlider.max);
    const minVal = parseFloat(minSlider.value);
    const maxVal = parseFloat(maxSlider.value);
    
    // Calculate percentages
    const range = rangeMax - rangeMin;
    // Prevent division by zero if min === max
    const minPercent = range === 0 ? 0 : ((minVal - rangeMin) / range) * 100; 
    const maxPercent = range === 0 ? 100 : ((maxVal - rangeMin) / range) * 100;
    
    // Update CSS custom properties
    container.style.setProperty('--min-pos', `${minPercent}%`);
    container.style.setProperty('--max-pos', `${maxPercent}%`);
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
import { paramOrder, paramInfo, state, updateParameter } from './state.js';
import { formatLabel } from './utils.js';
import { handleButtonClick } from './api.js';

/**
 * Create UI controls based on parameter types
 */
export function createControls() {
    const paramControlsContainer = document.getElementById('parameter-controls');
    if (!paramControlsContainer) {
        console.error("Element with ID 'parameter-controls' not found.");
        return;
    }

    // Clear any existing parameter controls first
    // Add Parameters header
    const paramHeader = document.createElement('div');
    paramHeader.className = 'section-header';
    paramHeader.innerHTML = '<b>Parameters</b>';
    paramControlsContainer.innerHTML = ''; // Clear container AFTER getting header content
    paramControlsContainer.appendChild(paramHeader);

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
            paramControlsContainer.appendChild(controlGroup);
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
 * Create selection dropdown control
 */
function createSelectionControl(name, param) {
    const select = document.createElement('select');
    select.id = `${name}-select`;

    // Add options
    if (param.options && Array.isArray(param.options)) {
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
    } else {
         console.warn(`No options or invalid options format for selection parameter: ${name}`);
    }

    // Set default value
    select.value = param.value;

    // Add event listener
    select.addEventListener('change', function() {
        // Get the selected option element
        const selectedOption = this.options[this.selectedIndex];
        let valueToSend = this.value;

        // Convert back to the original type if needed
        if (selectedOption && selectedOption.dataset.originalType === 'number') {
            // Use the original value from the dataset for exact precision with floats
            if (selectedOption.dataset.originalValue) {
                valueToSend = parseFloat(selectedOption.dataset.originalValue);
            } else {
                // Fallback if originalValue wasn't stored (shouldn't happen)
                valueToSend = parseFloat(valueToSend);
            }
        }
        // No conversion needed for string, boolean already handled by value

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

            // Check if this option is selected in the initial value array
            if (Array.isArray(param.value) && param.value.includes(option)) {
                optionElement.selected = true;
            }

            select.appendChild(optionElement);
        });
    } else {
         console.warn(`No options or invalid options format for multi-selection parameter: ${name}`);
    }

    // Helper text
    const helperText = document.createElement('div');
    helperText.className = 'helper-text';
    helperText.textContent = 'Ctrl+click to select multiple';

    // Add event listener
    select.addEventListener('change', function() {
        // Get all selected options
        const selectedValues = Array.from(this.selectedOptions).map(option => {
             let value = option.value;
             // Convert back to original type if needed
             if (option.dataset.originalType === 'number') {
                 value = option.dataset.originalValue ? parseFloat(option.dataset.originalValue) : parseFloat(value);
             }
             return value;
         });
        updateParameter(name, selectedValues);
    });

    container.appendChild(select);
    container.appendChild(helperText);
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
        input.value = this.value;
    });

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
            // Revert to current state value if input is invalid
            this.value = state[name];
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
    // Use the shared controller creator
    const container = createFloatController(name, param);
    const slider = container.querySelector('input[type="range"]');
    const input = container.querySelector('input[type="number"]');

    // Add event listeners specific to parameter updates
    slider.addEventListener('input', function() {
        input.value = this.value;
    });

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
            // Revert to current state value if input is invalid
            this.value = state[name];
        }
    });

    return container;
}

/**
 * Create float controller object (container with slider and number input).
 * Exported because it's also used by system_controls.js
 * @param {string} name - Base name for element IDs.
 * @param {object} param - Parameter info (min, max, step, value).
 */
export function createFloatController(name, param) {
    const container = document.createElement('div');
    container.className = 'numeric-control';

    // Create slider
    const slider = document.createElement('input');
    slider.type = 'range';
    slider.id = `${name}-slider`;
    slider.min = param.min;
    slider.max = param.max;
    slider.step = param.step || 0.01; // Default step for float
    slider.value = param.value;

    // Create number input
    const input = document.createElement('input');
    input.type = 'number';
    input.id = `${name}-input`;
    input.min = param.min;
    input.max = param.max;
    input.step = param.step || 0.01; // Default step for float
    input.value = param.value;

    container.appendChild(slider);
    container.appendChild(input);
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

    // Create max input
    const maxInput = document.createElement('input');
    maxInput.type = 'number';
    maxInput.id = `${name}-max-input`;
    maxInput.className = 'range-input';
    maxInput.min = param.min;
    maxInput.max = param.max;
    maxInput.step = param.step || (converter === parseInt ? 1 : 0.01);
    maxInput.value = param.value[1];
    
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
    minSlider.step = param.step || (converter === parseInt ? 1 : 0.01);
    minSlider.value = param.value[0];

    // Create max slider
    const maxSlider = document.createElement('input');
    maxSlider.type = 'range';
    maxSlider.id = `${name}-max-slider`;
    maxSlider.className = 'range-slider max-slider';
    maxSlider.min = param.min;
    maxSlider.max = param.max;
    maxSlider.step = param.step || (converter === parseInt ? 1 : 0.01);
    maxSlider.value = param.value[1];

    // --- Event Listeners --- 

    // Input listeners (for real-time updates of linked elements and gradient)
    minSlider.addEventListener('input', function() {
        const minVal = converter(this.value);
        const maxVal = converter(maxSlider.value);
        if (minVal <= maxVal) {
            minInput.value = minVal;
        } else {
            // Prevent slider crossing visually, update input to maxVal
            this.value = maxVal; 
            minInput.value = maxVal;
        }
        updateSliderGradient(minSlider, maxSlider, sliderContainer);
    });

    maxSlider.addEventListener('input', function() {
        const minVal = converter(minSlider.value);
        const maxVal = converter(this.value);
        if (maxVal >= minVal) {
            maxInput.value = maxVal;
        } else {
            // Prevent slider crossing visually, update input to minVal
            this.value = minVal;
            maxInput.value = minVal;
        }
        updateSliderGradient(minSlider, maxSlider, sliderContainer);
    });

    // Change listeners (for updating state and triggering backend calls)
    minSlider.addEventListener('change', function() {
        const minVal = converter(this.value);
        const maxVal = converter(maxSlider.value);

        // Ensure min doesn't exceed max after potential adjustment during 'input'
        if (minVal <= maxVal) {
            minInput.value = minVal;
            updateSliderGradient(minSlider, maxSlider, sliderContainer);
            updateParameter(name, [minVal, maxVal]);
        } else {
            // If somehow it crossed, snap it back and update state
            this.value = maxVal;
            minInput.value = maxVal;
            updateSliderGradient(minSlider, maxSlider, sliderContainer);
            updateParameter(name, [maxVal, maxVal]);
        }
    });

    maxSlider.addEventListener('change', function() {
        const minVal = converter(minSlider.value);
        const maxVal = converter(this.value);

        // Ensure max doesn't go below min after potential adjustment during 'input'
        if (maxVal >= minVal) {
            maxInput.value = maxVal;
            updateSliderGradient(minSlider, maxSlider, sliderContainer);
            updateParameter(name, [minVal, maxVal]);
        } else {
            // If somehow it crossed, snap it back and update state
            this.value = minVal;
            maxInput.value = minVal;
            updateSliderGradient(minSlider, maxSlider, sliderContainer);
            updateParameter(name, [minVal, minVal]);
        }
    });

    minInput.addEventListener('change', function() {
        const minVal = converter(this.value);
        const maxVal = converter(maxInput.value); // Use current max input value

        if (!isNaN(minVal) && minVal >= param.min && minVal <= maxVal) {
            minSlider.value = minVal;
            updateSliderGradient(minSlider, maxSlider, sliderContainer);
            updateParameter(name, [minVal, maxVal]);
        } else {
            // Revert input value to current state and update slider/gradient
            this.value = state[name][0]; 
            minSlider.value = state[name][0];
            updateSliderGradient(minSlider, maxSlider, sliderContainer);
        }
    });

    maxInput.addEventListener('change', function() {
        const minVal = converter(minInput.value); // Use current min input value
        const maxVal = converter(this.value);

        if (!isNaN(maxVal) && maxVal <= param.max && maxVal >= minVal) {
            maxSlider.value = maxVal;
            updateSliderGradient(minSlider, maxSlider, sliderContainer);
            updateParameter(name, [minVal, maxVal]);
        } else {
            // Revert input value to current state and update slider/gradient
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
            // Revert to current state if input is not a valid integer
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
    input.step = param.step || 'any'; // Allow any decimal

    input.addEventListener('change', function() {
        const value = parseFloat(this.value);
        if (!isNaN(value)) {
            updateParameter(name, value);
        } else {
            // Revert to current state if input is not a valid float
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
    button.textContent = param.label || formatLabel(name); // Use formatLabel for default
    button.className = 'button-control'; // Add a class for styling

    button.addEventListener('click', function() {
        // Call the handler from api.js
        handleButtonClick(name);
    });

    return button;
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

    // Update CSS custom properties on the container
    container.style.setProperty('--min-pos', `${minPercent}%`);
    container.style.setProperty('--max-pos', `${maxPercent}%`);
}

/**
 * Update a control's value in the UI based on state changes.
 * Exported because it's called from state.js
 * @param {string} name - The name of the parameter.
 * @param {*} value - The new value.
 * @param {object} param - The parameter's info (potentially updated, includes type, min, max, options etc.).
 */
export function updateControlValue(name, value, param) {
    // Check if param info is available
    if (!param) {
        console.warn(`No parameter info found for ${name} during UI update.`);
        return;
    }

    // Helper function to safely update element properties
    const safeUpdate = (element, property, newValue) => {
        if (element && element[property] !== newValue) {
            element[property] = newValue;
        }
    };

    // Helper function to update min/max/step for numeric inputs/sliders
    const updateNumericProps = (element, param) => {
        if (element) {
             safeUpdate(element, 'min', param.min);
             safeUpdate(element, 'max', param.max);
             safeUpdate(element, 'step', param.step || (param.type === 'integer' ? 1 : (param.type === 'integer-range' ? 1 : 0.01)));
         }
    };

    switch (param.type) {
        case 'text':
        case 'unbounded-integer':
        case 'unbounded-float':
            const inputElem = document.getElementById(`${name}-input`);
            safeUpdate(inputElem, 'value', value);
            // Update step for unbounded types if provided
            if (param.type !== 'text') {
                safeUpdate(inputElem, 'step', param.step || (param.type === 'unbounded-integer' ? 1 : 'any'));
            }
            break;
        case 'boolean':
            const checkboxElem = document.getElementById(`${name}-checkbox`);
            safeUpdate(checkboxElem, 'checked', value === true);
            break;
        case 'integer':
        case 'float':
            const sliderElem = document.getElementById(`${name}-slider`);
            const numInputElem = document.getElementById(`${name}-input`);
            updateNumericProps(sliderElem, param);
            updateNumericProps(numInputElem, param);
            safeUpdate(sliderElem, 'value', value);
            safeUpdate(numInputElem, 'value', value);
            break;
        case 'selection':
            const selectElem = document.getElementById(`${name}-select`);
            if (selectElem) {
                // Rebuild options if they might have changed (param object might be new)
                if (param.options && Array.isArray(param.options)) {
                    let optionsChanged = selectElem.options.length !== param.options.length;
                    if (!optionsChanged) {
                         // Quick check if values differ
                         for(let i=0; i < param.options.length; i++) {
                             if (selectElem.options[i].value !== String(param.options[i])) {
                                 optionsChanged = true;
                                 break;
                             }
                         }
                    }

                    if (optionsChanged) {
                        selectElem.innerHTML = ''; // Clear existing
                        param.options.forEach(option => {
                            const optionElement = document.createElement('option');
                            optionElement.value = option;
                            optionElement.textContent = formatLabel(String(option));
                            optionElement.dataset.originalType = typeof option;
                            if (typeof option === 'number') {
                                optionElement.dataset.originalValue = option;
                            }
                            selectElem.appendChild(optionElement);
                        });
                    }
                }
                // Update the selected value
                safeUpdate(selectElem, 'value', value);
            } else {
                console.warn(`Select element not found for ${name}`);
            }
            break;
        case 'multiple-selection':
            const multiSelectElem = document.getElementById(`${name}-select`);
             if (multiSelectElem) {
                 // Similar logic to rebuild options if necessary
                 if (param.options && Array.isArray(param.options)) {
                     let optionsChanged = multiSelectElem.options.length !== param.options.length;
                     if (!optionsChanged) {
                         for(let i=0; i < param.options.length; i++) {
                             if (multiSelectElem.options[i].value !== String(param.options[i])) {
                                 optionsChanged = true;
                                 break;
                             }
                         }
                    }

                     if (optionsChanged) {
                        multiSelectElem.innerHTML = ''; // Clear existing
                        param.options.forEach(option => {
                            const optionElement = document.createElement('option');
                            optionElement.value = option;
                            optionElement.textContent = formatLabel(String(option));
                            optionElement.dataset.originalType = typeof option;
                            if (typeof option === 'number') {
                                optionElement.dataset.originalValue = option;
                            }
                            multiSelectElem.appendChild(optionElement);
                        });
                    }
                 }
                 // Update selected status for all options
                 const valueArray = Array.isArray(value) ? value : [value]; // Ensure value is array
                 Array.from(multiSelectElem.options).forEach(option => {
                     // Check against original value if available, otherwise string value
                     const optionValue = option.dataset.originalValue ? parseFloat(option.dataset.originalValue) : option.value;
                     const shouldBeSelected = valueArray.some(val => val == optionValue); // Use loose equality for comparison after potential type conversion
                     safeUpdate(option, 'selected', shouldBeSelected);
                 });
             } else {
                 console.warn(`Multi-select element not found for ${name}`);
             }
            break;
        case 'integer-range':
        case 'float-range':
            const minSliderElem = document.getElementById(`${name}-min-slider`);
            const maxSliderElem = document.getElementById(`${name}-max-slider`);
            const minInputElem = document.getElementById(`${name}-min-input`);
            const maxInputElem = document.getElementById(`${name}-max-input`);

            updateNumericProps(minSliderElem, param);
            updateNumericProps(maxSliderElem, param);
            updateNumericProps(minInputElem, param);
            updateNumericProps(maxInputElem, param);

            if (Array.isArray(value) && value.length === 2) {
                safeUpdate(minSliderElem, 'value', value[0]);
                safeUpdate(maxSliderElem, 'value', value[1]);
                safeUpdate(minInputElem, 'value', value[0]);
                safeUpdate(maxInputElem, 'value', value[1]);

                // Update the gradient background
                const sliderContainer = minSliderElem ? minSliderElem.closest('.range-slider-container') : null;
                if (sliderContainer && minSliderElem && maxSliderElem) {
                    updateSliderGradient(minSliderElem, maxSliderElem, sliderContainer);
                } else {
                    console.warn(`Could not find elements for updating range slider gradient: ${name}`);
                }
            } else {
                console.warn(`Invalid value format for range control ${name}:`, value);
            }
            break;
        case 'button':
            // Buttons don't have a 'value' to update in the traditional sense.
            // We might update the label if param.label changed, but that's less common.
            const buttonElem = document.getElementById(`${name}-button`);
            if (param.label) {
                 safeUpdate(buttonElem, 'textContent', param.label);
             }
            break;
        default:
             // Type was already checked earlier, but good to have a default
             break;
    }
}

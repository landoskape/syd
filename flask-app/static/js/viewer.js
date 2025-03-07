// State object to store current values
let state = {};
let paramInfo = {};

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
    });

// Function to create UI controls based on parameter types
function createControls() {
    const controlsContainer = document.getElementById('controls-container');
    
    // Clear any existing controls
    controlsContainer.innerHTML = '';
    
    // Create controls for each parameter
    for (const [name, param] of Object.entries(paramInfo)) {
        // Create control group div
        const controlGroup = document.createElement('div');
        controlGroup.className = 'control-group';
        
        // Add label
        const label = document.createElement('span');
        label.className = 'control-label';
        label.textContent = formatLabel(name) + ':';
        controlGroup.appendChild(label);
        
        if (param.type === 'float') {
            // Create slider and number input for float parameters
            
            // Create slider
            const slider = document.createElement('input');
            slider.type = 'range';
            slider.id = `${name}-slider`;
            slider.min = param.min;
            slider.max = param.max;
            slider.step = param.step;
            slider.value = param.value;
            
            // Create number input
            const numberInput = document.createElement('input');
            numberInput.type = 'number';
            numberInput.id = `${name}-input`;
            numberInput.min = param.min;
            numberInput.max = param.max;
            numberInput.step = param.step;
            numberInput.value = param.value;
            
            // Add event listeners for slider
            slider.addEventListener('input', function() {
                const value = parseFloat(this.value);
                state[name] = value;
                numberInput.value = value;
                updatePlot();
            });
            
            // Add event listeners for number input
            numberInput.addEventListener('change', function() {
                const value = parseFloat(this.value);
                if (!isNaN(value) && value >= param.min && value <= param.max) {
                    state[name] = value;
                    slider.value = value;
                    updatePlot();
                }
            });
            
            // Add elements to control group
            controlGroup.appendChild(slider);
            controlGroup.appendChild(numberInput);
            
        } else if (param.type === 'integer') {
            // Create slider and number input for integer parameters
            
            // Create slider
            const slider = document.createElement('input');
            slider.type = 'range';
            slider.id = `${name}-slider`;
            slider.min = param.min;
            slider.max = param.max;
            slider.step = 1; // Integer steps
            slider.value = param.value;
            
            // Create number input
            const numberInput = document.createElement('input');
            numberInput.type = 'number';
            numberInput.id = `${name}-input`;
            numberInput.min = param.min;
            numberInput.max = param.max;
            numberInput.step = 1; // Integer steps
            numberInput.value = param.value;
            
            // Add event listeners for slider
            slider.addEventListener('input', function() {
                const value = parseInt(this.value, 10);
                state[name] = value;
                numberInput.value = value;
                updatePlot();
            });
            
            // Add event listeners for number input
            numberInput.addEventListener('change', function() {
                const value = parseInt(this.value, 10);
                if (!isNaN(value) && value >= param.min && value <= param.max) {
                    state[name] = value;
                    slider.value = value;
                    updatePlot();
                }
            });
            
            // Add elements to control group
            controlGroup.appendChild(slider);
            controlGroup.appendChild(numberInput);
            
        } else if (param.type === 'float-range' || param.type === 'integer-range') {
            // Create range container
            const rangeContainer = document.createElement('div');
            rangeContainer.className = 'range-container';
            
            // Create min input
            const minInput = document.createElement('input');
            minInput.type = 'number';
            minInput.id = `${name}-min-input`;
            minInput.className = 'range-input';
            minInput.min = param.min;
            minInput.max = param.max;
            minInput.step = param.step;
            minInput.value = param.value[0];
            
            // Create range slider container
            const sliderContainer = document.createElement('div');
            sliderContainer.className = 'range-slider-container';
            
            // Create min slider (lower bound)
            const minSlider = document.createElement('input');
            minSlider.type = 'range';
            minSlider.id = `${name}-min-slider`;
            minSlider.className = 'range-slider min-slider';
            minSlider.min = param.min;
            minSlider.max = param.max;
            minSlider.step = param.step;
            minSlider.value = param.value[0];
            
            // Create max slider (upper bound)
            const maxSlider = document.createElement('input');
            maxSlider.type = 'range';
            maxSlider.id = `${name}-max-slider`;
            maxSlider.className = 'range-slider max-slider';
            maxSlider.min = param.min;
            maxSlider.max = param.max;
            maxSlider.step = param.step;
            maxSlider.value = param.value[1];
            
            // Create max input
            const maxInput = document.createElement('input');
            maxInput.type = 'number';
            maxInput.id = `${name}-max-input`;
            maxInput.className = 'range-input';
            maxInput.min = param.min;
            maxInput.max = param.max;
            maxInput.step = param.step;
            maxInput.value = param.value[1];
            
            // Create range display
            const rangeDisplay = document.createElement('div');
            rangeDisplay.className = 'range-display';
            rangeDisplay.id = `${name}-display`;
            
            // Convert to integer if needed
            const converter = param.type === 'integer-range' ? parseInt : parseFloat;
            
            // Handle min slider change
            minSlider.addEventListener('input', function() {
                const minVal = converter(this.value);
                const maxVal = converter(maxSlider.value);
                
                // Ensure min doesn't exceed max
                if (minVal <= maxVal) {
                    state[name] = [minVal, maxVal];
                    minInput.value = minVal;
                    updateRangeDisplay(name, minVal, maxVal);
                    updatePlot();
                } else {
                    this.value = maxVal;
                }
            });
            
            // Handle max slider change
            maxSlider.addEventListener('input', function() {
                const minVal = converter(minSlider.value);
                const maxVal = converter(this.value);
                
                // Ensure max doesn't go below min
                if (maxVal >= minVal) {
                    state[name] = [minVal, maxVal];
                    maxInput.value = maxVal;
                    updateRangeDisplay(name, minVal, maxVal);
                    updatePlot();
                } else {
                    this.value = minVal;
                }
            });
            
            // Handle min input change
            minInput.addEventListener('change', function() {
                const minVal = converter(this.value);
                const maxVal = converter(maxInput.value);
                
                // Validate input
                if (!isNaN(minVal) && minVal >= param.min && minVal <= maxVal) {
                    state[name] = [minVal, maxVal];
                    minSlider.value = minVal;
                    updateRangeDisplay(name, minVal, maxVal);
                    updatePlot();
                } else {
                    this.value = state[name][0];
                }
            });
            
            // Handle max input change
            maxInput.addEventListener('change', function() {
                const minVal = converter(minInput.value);
                const maxVal = converter(this.value);
                
                // Validate input
                if (!isNaN(maxVal) && maxVal <= param.max && maxVal >= minVal) {
                    state[name] = [minVal, maxVal];
                    maxSlider.value = maxVal;
                    updateRangeDisplay(name, minVal, maxVal);
                    updatePlot();
                } else {
                    this.value = state[name][1];
                }
            });
            
            // Initialize range display
            function updateRangeDisplay(name, min, max) {
                const display = document.getElementById(`${name}-display`);
                if (display) {
                    display.textContent = `Range: ${min} - ${max}`;
                }
            }
            
            // Add elements to containers
            sliderContainer.appendChild(minSlider);
            sliderContainer.appendChild(maxSlider);
            
            rangeContainer.appendChild(minInput);
            rangeContainer.appendChild(sliderContainer);
            rangeContainer.appendChild(maxInput);
            
            controlGroup.appendChild(rangeContainer);
            controlGroup.appendChild(rangeDisplay);
            
            // Initialize display
            updateRangeDisplay(name, param.value[0], param.value[1]);
            
        } else if (param.type === 'selection') {
            // Create dropdown for selection parameters
            const select = document.createElement('select');
            select.id = `${name}-select`;
            select.className = 'color-dropdown';
            
            // Add options to dropdown - handle both string and object formats
            param.options.forEach(option => {
                const optionElement = document.createElement('option');
                
                // Check if the option is a string or an object
                if (typeof option === 'string') {
                    // Simple string option
                    optionElement.value = option;
                    optionElement.textContent = option;
                } else {
                    // Object with name/value properties
                    optionElement.value = option.value;
                    optionElement.textContent = option.name;
                }
                
                select.appendChild(optionElement);
            });
            
            // Set default value
            select.value = param.value;
            
            // Add event listener
            select.addEventListener('change', function() {
                state[name] = this.value;
                updatePlot();
            });
            
            // Add select to control group
            controlGroup.appendChild(select);
            
        } else if (param.type === 'multiple-selection') {
            // Create multiple selection dropdown
            const select = document.createElement('select');
            select.id = `${name}-select`;
            select.className = 'multiple-select';
            select.multiple = true; // Allow multiple selections
            
            // Add options to dropdown - handle both string and object formats
            param.options.forEach(option => {
                const optionElement = document.createElement('option');
                
                // Check if the option is a string or an object
                if (typeof option === 'string') {
                    // Simple string option
                    optionElement.value = option;
                    optionElement.textContent = option;
                } else {
                    // Object with name/value properties
                    optionElement.value = option.value;
                    optionElement.textContent = option.name;
                }
                
                // Check if this option is in the selected values
                if (param.value.includes(optionElement.value)) {
                    optionElement.selected = true;
                }
                
                select.appendChild(optionElement);
            });
            
            // Add helper text
            const helperText = document.createElement('div');
            helperText.className = 'helper-text';
            helperText.textContent = 'Ctrl+click to select multiple';
            
            // Add event listener
            select.addEventListener('change', function() {
                // Get all selected options
                const selectedValues = Array.from(this.selectedOptions).map(option => option.value);
                state[name] = selectedValues;
                updatePlot();
            });
            
            // Add select and helper text to control group
            controlGroup.appendChild(select);
            controlGroup.appendChild(helperText);
        }
        
        // Add control group to container
        controlsContainer.appendChild(controlGroup);
    }
}

// Function to format parameter name as a label (capitalize first letter)
function formatLabel(name) {
    return name.charAt(0).toUpperCase() + name.slice(1);
}

// Function to update the sine wave plot
function updatePlot() {
    // Build query string from state
    const queryParams = new URLSearchParams();
    
    for (const [name, value] of Object.entries(state)) {
        // Handle arrays (for MultipleSelectionParam) and range values
        if (Array.isArray(value)) {
            queryParams.append(name, JSON.stringify(value));
        } else {
            queryParams.append(name, value);
        }
    }
    
    const url = `/plot?${queryParams.toString()}`;
    document.getElementById('plot-image').src = url;
} 
// State object to store current values
let state = {
    frequency: 1.0,
    amplitude: 1.0,
    offset: 0.0,
    color: "#FF0000"
};

// Fetch initial default values from server
fetch('/init-data')
    .then(response => response.json())
    .then(data => {
        // Update state with defaults from server
        state.frequency = data.default_frequency;
        state.amplitude = data.default_amplitude;
        state.offset = data.default_offset;
        state.color = data.default_color;
        
        // Update UI elements with default values
        document.getElementById('frequency-slider').value = state.frequency;
        document.getElementById('frequency-input').value = state.frequency;
        document.getElementById('amplitude-slider').value = state.amplitude;
        document.getElementById('amplitude-input').value = state.amplitude;
        document.getElementById('offset-slider').value = state.offset;
        document.getElementById('offset-input').value = state.offset;
        document.getElementById('color-input').value = state.color;
        
        // Generate initial plot
        updatePlot();
    });

// Function to update the sine wave plot
function updatePlot() {
    const url = `/plot?frequency=${state.frequency}&amplitude=${state.amplitude}&offset=${state.offset}&color=${encodeURIComponent(state.color)}`;
    document.getElementById('plot-image').src = url;
}

// Event listeners for frequency control
document.getElementById('frequency-slider').addEventListener('input', function() {
    const value = parseFloat(this.value);
    state.frequency = value;
    document.getElementById('frequency-input').value = value;
    updatePlot();
});

document.getElementById('frequency-input').addEventListener('change', function() {
    const value = parseFloat(this.value);
    if (!isNaN(value) && value >= 0.1) {
        state.frequency = value;
        document.getElementById('frequency-slider').value = value;
        updatePlot();
    }
});

// Event listeners for amplitude control
document.getElementById('amplitude-slider').addEventListener('input', function() {
    const value = parseFloat(this.value);
    state.amplitude = value;
    document.getElementById('amplitude-input').value = value;
    updatePlot();
});

document.getElementById('amplitude-input').addEventListener('change', function() {
    const value = parseFloat(this.value);
    if (!isNaN(value) && value >= 0.1) {
        state.amplitude = value;
        document.getElementById('amplitude-slider').value = value;
        updatePlot();
    }
});

// Event listeners for offset control
document.getElementById('offset-slider').addEventListener('input', function() {
    const value = parseFloat(this.value);
    state.offset = value;
    document.getElementById('offset-input').value = value;
    updatePlot();
});

document.getElementById('offset-input').addEventListener('change', function() {
    const value = parseFloat(this.value);
    if (!isNaN(value)) {
        state.offset = value;
        document.getElementById('offset-slider').value = value;
        updatePlot();
    }
});

// Event listener for color control
document.getElementById('color-input').addEventListener('change', function() {
    state.color = this.value;
    updatePlot();
}); 
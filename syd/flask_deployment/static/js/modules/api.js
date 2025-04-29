import { updateStatus } from './utils.js';
import { initializeState, updateStateFromServer } from './state.js';
import { updatePlot } from './plot.js';
import { setUpdateThreshold } from './config.js';

/**
 * Fetch initial parameter information from the server.
 * Initializes the state and gets configuration.
 */
export async function fetchInitialData() {
    try {
        const response = await fetch('/init-data');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        setUpdateThreshold(data.config.update_threshold); // Set initial threshold
        initializeState(data); // Initialize state

        return data; // Return data in case the caller needs it
    } catch (error) {
        console.error('Error initializing viewer:', error);
        updateStatus('Error initializing viewer');
        throw error; // Re-throw the error to signal failure
    }
}

/**
 * Send parameter update to the server.
 * @param {string} name - The name of the parameter.
 * @param {*} value - The new value of the parameter.
 * @param {boolean} [action=false] - Whether this is a button action.
 */
export async function updateParameterOnServer(name, value, action = false) {
    try {
        const response = await fetch('/update-param', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: name,
                value: value,
                action: action
            }),
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json(); // Return the server response
    } catch (error) {
        console.error('Error updating parameter:', error);
        updateStatus('Error updating parameter');
        throw error; // Re-throw error
    }
}

/**
 * Handles button click actions by sending to the server.
 * @param {string} name - The name of the button parameter.
 */
export function handleButtonClick(name) {
    const button = document.getElementById(`${name}-button`);
    if (!button) return;

    button.classList.add('active'); // Show button as active
    updateStatus(`Processing ${name}...`);

    updateParameterOnServer(name, null, true) // Send action=true
        .then(data => {
            button.classList.remove('active');
            if (data.error) {
                console.error('Error:', data.error);
                updateStatus(`Error processing ${name}`);
            } else {
                // Update state with any changes from callbacks
                updateStateFromServer(data.state, data.params);
                if (data.replot) {
                    updatePlot();
                }
                updateStatus('Ready!');
            }
        })
        .catch(error => {
            button.classList.remove('active');
            console.error('Error during button action:', error);
            updateStatus(`Error processing ${name}`);
        });
}

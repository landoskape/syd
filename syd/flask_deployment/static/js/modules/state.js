import { updateControlValue } from './ui_controls.js';
import { updatePlot } from './plot.js';
import { updateParameterOnServer } from './api.js';
import { updateStatus } from './utils.js';

export let state = {};
export let paramInfo = {};
export let paramOrder = [];
let isUpdating = false;

// Function to initialize state (called after fetching initial data)
export function initializeState(initialData) {
    paramInfo = initialData.params;
    paramOrder = initialData.param_order;
    // Initialize state from parameter info
    for (const [name, param] of Object.entries(paramInfo)) {
        state[name] = param.value;
    }
}

/**
 * Update a parameter value and send to server
 */
export function updateParameter(name, value) {
    // Prevent recursive updates
    if (isUpdating) {
        return;
    }
    // Indicate status update
    updateStatus('Updating ' + name + '...');

    // Update local state
    state[name] = value;

    // Send update to server (from api.js)
    updateParameterOnServer(name, value)
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

    // Indicate status update
    updateStatus('Ready!');
}

/**
 * Update local state from server response
 */
export function updateStateFromServer(serverState, serverParamInfo) {
    // Set updating flag to prevent recursive updates
    isUpdating = true;

    try {
        // Update global paramInfo first if it changed
        if (serverParamInfo) {
            // Basic check: update if stringified versions differ. Might need deeper comparison.
            if(JSON.stringify(paramInfo) !== JSON.stringify(serverParamInfo)) {
                paramInfo = serverParamInfo;
                 // TODO: Potentially re-create controls if param info structure changed significantly?
                 // For now, we only update values below.
            }
        }

        // Update any parameters that changed due to callbacks
        for (const [name, value] of Object.entries(serverState)) {
            // Check if state value changed OR if paramInfo for this specific param changed
            const currentParamInfoStr = paramInfo[name] ? JSON.stringify(paramInfo[name]) : undefined;
            const serverParamInfoStr = serverParamInfo && serverParamInfo[name] ? JSON.stringify(serverParamInfo[name]) : undefined;

            if (JSON.stringify(state[name]) !== JSON.stringify(value) || currentParamInfoStr !== serverParamInfoStr) {
                state[name] = value;
                // Pass the potentially updated paramInfo for this specific control
                updateControlValue(name, value, serverParamInfo ? serverParamInfo[name] : paramInfo[name]);
            }
        }
    } finally {
        // Clear updating flag
        isUpdating = false;
    }
}

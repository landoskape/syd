import { fetchInitialData } from './modules/api.js';
import { createControls } from './modules/ui_controls.js';
import { createSystemControls } from './modules/system_controls.js';
import { config } from './modules/config.js';
import { updateStatus } from './modules/utils.js';
import { updatePlot } from './modules/plot.js';

document.addEventListener('DOMContentLoaded', async () => {
    updateStatus('Initializing...');

    // Get the main container where controls will be placed (assuming it exists in HTML)
    const mainContainer = document.getElementById('controls-container');
    if (!mainContainer) {
        console.error("Fatal Error: Element with ID 'controls-container' not found.");
        updateStatus("Error: Main controls container missing.");
        return; // Stop execution if main container is missing
    }

    // --- Create the necessary sub-containers dynamically --- 
    // Create parameter controls section
    const paramControls = document.createElement('div');
    paramControls.id = 'parameter-controls';
    paramControls.className = 'parameter-controls';
    // Header will be added by createControls() later

    // Create system controls section
    const systemControls = document.createElement('div');
    systemControls.id = 'system-controls';
    systemControls.className = 'system-controls';

    // Create status element (needs to exist before first updateStatus call potentially)
    const statusElement = document.createElement('div');
    statusElement.id = 'status-display';
    statusElement.className = 'status-display';
    systemControls.appendChild(statusElement); // Add status display to system controls container

    // Add sections to main container in the desired order
    mainContainer.appendChild(paramControls); // Add parameter controls container
    mainContainer.appendChild(systemControls); // Add system controls container
    // --- End of dynamic container creation ---

    try {
        // Now fetch data and create controls, the containers exist
        await fetchInitialData();
        createControls(); // Populates #parameter-controls
        if (['left', 'right'].includes(config.controlsPosition)) {
            createSystemControls(systemControls); // Populates #system-controls
        }
        updatePlot();
        updateStatus('Ready!');
    } catch (error) {
        console.error("Initialization failed:", error);
        updateStatus('Initialization failed.');
    }
});

class SydViewer {
    constructor(config) {
        this.config = {
            controlsPosition: 'left',
            continuous: false,
            updateInterval: 200,
            ...config
        };

        this.form = document.getElementById('controls-form');
        this.plot = document.getElementById('plot');
        this.updateTimer = null;
        this.setupEventListeners();
        this.updatePlot();
    }

    setupEventListeners() {
        // Handle all form input changes
        this.form.addEventListener('input', (event) => {
            const input = event.target;
            if (input.dataset.continuous === 'true' || this.config.continuous) {
                this.debounceUpdate(() => this.handleInputChange(input));
            }
        });

        // Handle form changes for non-continuous updates
        this.form.addEventListener('change', (event) => {
            const input = event.target;
            if (input.dataset.continuous !== 'true' && !this.config.continuous) {
                this.handleInputChange(input);
            }
        });

        // Handle button clicks
        this.form.querySelectorAll('button[type="button"]').forEach(button => {
            button.addEventListener('click', () => this.handleButtonClick(button));
        });
    }

    debounceUpdate(callback) {
        if (this.updateTimer) {
            clearTimeout(this.updateTimer);
        }
        this.updateTimer = setTimeout(callback, this.config.updateInterval);
    }

    async handleInputChange(input) {
        let value = this.getInputValue(input);
        const name = input.name;

        try {
            const response = await fetch(`/update/${name}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ value }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            await this.updatePlot();
        } catch (error) {
            console.error('Error updating parameter:', error);
        }
    }

    async handleButtonClick(button) {
        const name = button.name;
        try {
            const response = await fetch(`/update/${name}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ value: null }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            await this.updatePlot();
        } catch (error) {
            console.error('Error handling button click:', error);
        }
    }

    getInputValue(input) {
        switch (input.type) {
            case 'checkbox':
                return input.checked;
            case 'number':
                return parseFloat(input.value);
            case 'range':
                if (input.name.endsWith('_low')) {
                    const high = document.getElementById(input.id.replace('_low', '_high')).value;
                    return [parseFloat(input.value), parseFloat(high)];
                } else if (input.name.endsWith('_high')) {
                    const low = document.getElementById(input.id.replace('_high', '_low')).value;
                    return [parseFloat(low), parseFloat(input.value)];
                }
                return parseFloat(input.value);
            case 'select-multiple':
                return Array.from(input.selectedOptions).map(option => {
                    const value = option.value;
                    return !isNaN(value) ? parseFloat(value) : value;
                });
            default:
                const value = input.value;
                return !isNaN(value) ? parseFloat(value) : value;
        }
    }

    async updatePlot() {
        try {
            const response = await fetch('/plot');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }

            this.plot.src = `data:image/png;base64,${data.image}`;
        } catch (error) {
            console.error('Error updating plot:', error);
        }
    }

    async updateState() {
        try {
            const response = await fetch('/state');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const state = await response.json();
            this.syncFormWithState(state);
        } catch (error) {
            console.error('Error updating state:', error);
        }
    }

    syncFormWithState(state) {
        for (const [name, value] of Object.entries(state)) {
            const input = this.form.elements[name];
            if (!input) continue;

            if (input.type === 'checkbox') {
                input.checked = value;
            } else if (input.type === 'select-multiple') {
                Array.from(input.options).forEach(option => {
                    option.selected = value.includes(option.value);
                });
            } else if (input.type === 'range' && Array.isArray(value)) {
                const [low, high] = value;
                document.getElementById(`param_${name}_low`).value = low;
                document.getElementById(`param_${name}_high`).value = high;
                document.querySelector(`output[for="param_${name}_low"]`).value = low;
                document.querySelector(`output[for="param_${name}_high"]`).value = high;
            } else {
                input.value = value;
                if (input.type === 'range') {
                    document.querySelector(`output[for="${input.id}"]`).value = value;
                }
            }
        }
    }
} 
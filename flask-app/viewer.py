import matplotlib as mpl
from typing import Any

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


class FloatParam:
    def __init__(self, value: float, min: float, max: float, step: float):
        self.value = value
        self.min = min
        self.max = max
        self.step = step

    def __call__(self):
        return self.value

    def update_value(self, new_value):
        if self.min <= new_value <= self.max:
            self.value = new_value
        else:
            raise ValueError(f"Invalid value: {new_value}")


class SelectionParam:
    def __init__(self, value: str, options: list[str]):
        self.value = value
        self.options = options

    def __call__(self):
        return self.value

    def update_value(self, new_value):
        if new_value in self.options:
            self.value = new_value
        else:
            raise ValueError(f"Invalid value: {new_value}")


class SineWaveViewer:
    # Define a list of color options with name and hex value
    COLOR_OPTIONS = [
        {"name": "Red", "value": "#FF0000"},
        {"name": "Blue", "value": "#0000FF"},
        {"name": "Green", "value": "#00AA00"},
        {"name": "Purple", "value": "#800080"},
        {"name": "Orange", "value": "#FFA500"},
        {"name": "Teal", "value": "#008080"},
        {"name": "Magenta", "value": "#FF00FF"},
        {"name": "Gold", "value": "#FFD700"},
    ]

    DEFAULT_COLOR = "#FF0000"  # Red as default

    def __init__(self, frequency=1.0, amplitude=1.0, offset=0.0, color=None):
        self.params = {}

        self.register_param("frequency", FloatParam(frequency, 0.1, 10.0, 0.1))
        self.register_param("amplitude", FloatParam(amplitude, 0.1, 5.0, 0.1))
        self.register_param("offset", FloatParam(offset, -5.0, 5.0, 0.1))
        self.register_param("color", SelectionParam(color, self.COLOR_OPTIONS))

    def register_param(self, name: str, param: FloatParam | SelectionParam):
        self.params[name] = param

    def update_parameters(self, state: dict[str, Any]):
        # Update parameters if provided, otherwise keep existing values
        for name, param in self.params.items():
            if name in state:
                param.update_value(state[name])

        print(f"Updated parameters from: {state}")

    def plot(self):
        frequency = self.params["frequency"].value
        amplitude = self.params["amplitude"].value
        offset = self.params["offset"].value
        color = self.params["color"].value

        fig, ax = plt.subplots(figsize=(10, 6))
        x = np.linspace(0, 2 * np.pi, 1000)
        y = amplitude * np.sin(frequency * x) + offset

        # Plot the sine wave
        ax.plot(x, y, color=color, linewidth=2)

        # Add grid and labels
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_title(f"Sine Wave: A={amplitude}, f={frequency}, offset={offset}")

        # Set y-axis limits based on amplitude and offset
        y_margin = max(1, amplitude) * 1.2
        ax.set_ylim(offset - y_margin, offset + y_margin)

        print("Plotting sine wave!")
        return fig

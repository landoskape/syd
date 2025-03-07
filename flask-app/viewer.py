import matplotlib as mpl
from typing import Any, List, Union, Tuple

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


class IntegerParam:
    def __init__(self, value: int, min: int, max: int):
        self.value = value
        self.min = min
        self.max = max

    def __call__(self):
        return self.value

    def update_value(self, new_value):
        new_value = int(new_value)
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


class MultipleSelectionParam:
    def __init__(self, value: List[str], options: list[str]):
        self.value = value if value else []
        self.options = options

    def __call__(self):
        return self.value

    def update_value(self, new_value):
        # Handle both single string and list inputs
        if isinstance(new_value, str):
            if new_value in self.options:
                self.value = [new_value]
            else:
                raise ValueError(f"Invalid value: {new_value}")
        elif isinstance(new_value, list):
            # Validate all values in the list
            for val in new_value:
                if val not in self.options:
                    raise ValueError(f"Invalid value in list: {val}")
            self.value = new_value
        else:
            raise ValueError(
                f"Invalid type for MultipleSelectionParam: {type(new_value)}"
            )


class FloatRangeParam:
    def __init__(self, value: Tuple[float, float], min: float, max: float, step: float):
        self.value = value  # (min_value, max_value)
        self.min = min  # Absolute minimum for the range
        self.max = max  # Absolute maximum for the range
        self.step = step

        # Validate the initial value
        if not (self.min <= value[0] <= value[1] <= self.max):
            raise ValueError(f"Invalid range: {value}. Must be within [{min}, {max}]")

    def __call__(self):
        return self.value

    def update_value(self, new_value):
        # Ensure the value is a tuple/list of exactly 2 floats
        if not isinstance(new_value, (list, tuple)) or len(new_value) != 2:
            raise ValueError(f"Invalid range format: {new_value}. Must be [min, max]")

        min_val, max_val = float(new_value[0]), float(new_value[1])

        # Validate the range values
        if not (self.min <= min_val <= max_val <= self.max):
            raise ValueError(
                f"Invalid range: {new_value}. Must be within [{self.min}, {self.max}]"
            )

        self.value = (min_val, max_val)


class IntegerRangeParam:
    def __init__(self, value: Tuple[int, int], min: int, max: int):
        self.value = value  # (min_value, max_value)
        self.min = min  # Absolute minimum for the range
        self.max = max  # Absolute maximum for the range

        # Validate the initial value
        if not (self.min <= value[0] <= value[1] <= self.max):
            raise ValueError(f"Invalid range: {value}. Must be within [{min}, {max}]")

    def __call__(self):
        return self.value

    def update_value(self, new_value):
        # Ensure the value is a tuple/list of exactly 2 integers
        if not isinstance(new_value, (list, tuple)) or len(new_value) != 2:
            raise ValueError(f"Invalid range format: {new_value}. Must be [min, max]")

        min_val, max_val = int(new_value[0]), int(new_value[1])

        # Validate the range values
        if not (self.min <= min_val <= max_val <= self.max):
            raise ValueError(
                f"Invalid range: {new_value}. Must be within [{self.min}, {self.max}]"
            )

        self.value = (min_val, max_val)


class SineWaveViewer:
    # Define a list of color options with name and hex value
    COLOR_OPTIONS = [
        "black",
        "red",
        "blue",
        "green",
        "purple",
        "orange",
        "teal",
        "magenta",
        "gold",
    ]

    def __init__(self):
        self.params = {}
        # Register basic sine wave parameters
        self.register_param("frequency", FloatParam(1.0, 0.1, 10.0, 0.1))
        self.register_param("amplitude", FloatParam(1.0, 0.1, 5.0, 0.1))
        self.register_param("offset", FloatParam(0.0, -5.0, 5.0, 0.1))
        self.register_param(
            "color", SelectionParam(self.COLOR_OPTIONS[0], self.COLOR_OPTIONS)
        )

        # Register new parameter types for demonstration
        self.register_param("num_cycles", IntegerParam(2, 1, 10))
        self.register_param(
            "visible_components",
            MultipleSelectionParam(
                ["sine"], ["sine", "cosine", "tangent", "reference"]
            ),
        )

        # Add range parameter examples
        self.register_param(
            "x_display_range", FloatRangeParam((0.0, 6.28), 0.0, 20.0, 0.1)
        )
        self.register_param("harmonic_range", IntegerRangeParam((1, 3), 1, 10))

    def register_param(
        self,
        name: str,
        param: Union[
            FloatParam,
            IntegerParam,
            SelectionParam,
            MultipleSelectionParam,
            FloatRangeParam,
            IntegerRangeParam,
        ],
    ):
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
        num_cycles = self.params["num_cycles"].value
        visible_components = self.params["visible_components"].value
        x_range = self.params["x_display_range"].value
        harmonic_range = self.params["harmonic_range"].value

        fig, ax = plt.subplots(figsize=(10, 6))

        # Generate x values based on the x range
        x = np.linspace(x_range[0], x_range[1], 1000)

        # Plot different components based on selection
        if "sine" in visible_components:
            y_sine = amplitude * np.sin(frequency * x) + offset
            ax.plot(x, y_sine, color=color, linewidth=2, label="Sine")

            # Add harmonics if selected
            for harmonic in range(harmonic_range[0], harmonic_range[1] + 1):
                if harmonic > 1:  # Skip the fundamental which we already plotted
                    harmonic_amp = amplitude / harmonic
                    y_harmonic = (
                        harmonic_amp * np.sin(harmonic * frequency * x) + offset
                    )
                    ax.plot(
                        x,
                        y_harmonic,
                        color=color,
                        linewidth=1,
                        alpha=0.5,
                        linestyle="--",
                        label=f"Sine H{harmonic}",
                    )

        if "cosine" in visible_components:
            y_cosine = amplitude * np.cos(frequency * x) + offset
            ax.plot(
                x, y_cosine, color="blue", linewidth=2, linestyle="--", label="Cosine"
            )

        if "tangent" in visible_components:
            # Limit tangent to avoid extreme values
            y_tangent = amplitude * np.tan(frequency * x)
            # Clip extreme values
            y_tangent = np.clip(y_tangent, -5, 5) + offset
            ax.plot(
                x,
                y_tangent,
                color="green",
                linewidth=1,
                linestyle=":",
                label="Tangent (clipped)",
            )

        if "reference" in visible_components:
            # Plot a reference line at the offset
            ax.axhline(
                y=offset, color="gray", linestyle="-.", linewidth=1, label="Reference"
            )

        # Add grid and labels
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.set_xlabel("x")
        ax.set_ylabel("y")

        # Create title based on parameters
        components_str = ", ".join(visible_components)
        ax.set_title(
            f"Wave Components: {components_str} (A={amplitude}, f={frequency}, offset={offset})"
        )

        # Show legend if there are multiple components
        if len(visible_components) > 1:
            ax.legend()

        # Set y-axis limits based on amplitude and offset
        y_margin = max(1, amplitude) * 1.5
        ax.set_ylim(offset - y_margin, offset + y_margin)

        print("Plotting wave components!")
        return fig

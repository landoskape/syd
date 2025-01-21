Quick Start Guide
===============

Creating Your First Interactive Plot
---------------------------------

1. Create a viewer class that inherits from ``InteractiveViewer``
2. Implement the ``plot()`` method to create your visualization
3. Add parameters to control your plot
4. Register callbacks to update the plot when parameters change

Here's a complete example. You can run the complete example 
`here <https://github.com/landoskape/syd/blob/main/docs/examples/example_notebook.ipynb>`_ 
or run it yourself in colab:

.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/landoskape/syd/blob/main/docs/examples/example_notebook.ipynb
   :alt: Open In Colab


.. code-block:: python

    import numpy as np
    import matplotlib.pyplot as plt
    from syd import InteractiveViewer

    class SimpleWaveformViewer(InteractiveViewer):
        """A simple example viewer that shows an interactive waveform."""
        
        def __init__(self):            
            # Add parameters
            self.add_float("frequency", value=1.0, min_value=0.1, max_value=5.0)
            self.add_float("sine_amplitude", value=1.0, min_value=0.1, max_value=2.0)
            self.add_float("square_amplitude", value=1.0, min_value=0.1, max_value=2.0)
            self.add_float("sawtooth_amplitude", value=1.0, min_value=0.1, max_value=2.0)
            self.add_selection("sine_color", value="red", options=["red", "blue", "green"])
            self.add_selection("square_color", value="blue", options=["red", "blue", "green"])
            self.add_selection("sawtooth_color", value="green", options=["red", "blue", "green"])
            self.add_multiple_selection("waveform_type", value=["sine", "square", "sawtooth"], options=["sine", "square", "sawtooth"])
            self.add_boolean("show_legend", value=True)
            self.add_boolean("show_grid", value=True)

        def plot(self, state):
            """Plot the waveform based on current parameters."""
            t = np.linspace(0, 2*np.pi, 1000)

            ymin = float("inf")
            ymax = float("-inf")

            fig, ax = plt.subplots()
            if "sine" in state["waveform_type"]:    
                ax.plot(t, state["sine_amplitude"] * np.sin(state["frequency"] * t), color=state["sine_color"], label="Sine")
                ymin = min(ymin, -state["sine_amplitude"])
                ymax = max(ymax, state["sine_amplitude"])
            if "square" in state["waveform_type"]:
                ax.plot(t, state["square_amplitude"] * np.sign(np.sin(state["frequency"] * t)), color=state["square_color"], label="Square")
                ymin = min(ymin, -state["square_amplitude"])
                ymax = max(ymax, state["square_amplitude"])
            if "sawtooth" in state["waveform_type"]:
                ax.plot(t, state["sawtooth_amplitude"] * (t % (2*np.pi/state["frequency"])) * (state["frequency"] / 2 / np.pi), color=state["sawtooth_color"], label="Sawtooth")
                ymin = min(ymin, -state["sawtooth_amplitude"])
                ymax = max(ymax, state["sawtooth_amplitude"])

            ax.set_xlabel("Time")
            ax.set_ylabel("Amplitude")
            ax.grid(state["show_grid"])
            ax.set_ylim(ymin*1.1, ymax*1.1)
            if state["show_legend"]:
                ax.legend()
            return fig
        

    viewer = SimpleWaveformViewer()
    viewer.deploy(continuous_update=True)

.. image:: ../examples/assets/simple_waveform_viewer.png
   :alt: Simple Waveform Viewer
   :align: center


Available Parameter Types
-----------------------

- Text input (``add_text``)
- Checkboxes (``add_boolean``)
- Dropdown menus (``add_selection``)
- Multi-select menus (``add_multiple_selection``)
- Integer sliders (``add_integer``)
- Float sliders (``add_float``)
- Range sliders (``add_integer_range``, ``add_float_range``)
- Unbounded numeric inputs (``add_unbounded_integer``, ``add_unbounded_float``) 
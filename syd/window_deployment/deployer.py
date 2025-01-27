import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class WindowDeployment:
    """
    A deployment system for InteractiveViewer in standalone windows using tkinter.
    Parallels the NotebookDeployment class but for window-based deployment.
    """

    def __init__(
        self,
        viewer: "InteractiveViewer",
        controls_position: str = "left",
        figure_width: float = 8.0,
        figure_height: float = 6.0,
        controls_width_percent: int = 30,
        window_title: str = "Interactive Viewer",
    ):
        self.viewer = viewer
        self.config = LayoutConfig(
            controls_position=controls_position,
            figure_width=figure_width,
            figure_height=figure_height,
            controls_width_percent=controls_width_percent,
        )

        # Initialize tkinter window
        self.root = tk.Tk()
        self.root.title(window_title)

        # Create main containers
        self.controls_frame = ttk.Frame(self.root)
        self.plot_frame = ttk.Frame(self.root)

        # Initialize widget containers
        self.parameter_widgets = {}
        self._create_parameter_widgets()

        # Store current figure
        self._current_figure = None
        self._canvas = None

    def _create_parameter_widgets(self):
        """Create tkinter widgets for all parameters."""
        for name, param in self.viewer.parameters.items():
            if isinstance(param, TextParameter):
                widget = self._create_text_widget(param)
            elif isinstance(param, BooleanParameter):
                widget = self._create_boolean_widget(param)
            # Add other parameter types...

            self.parameter_widgets[name] = widget

    def _create_text_widget(self, param):
        """Create a text entry widget."""
        frame = ttk.Frame(self.controls_frame)
        label = ttk.Label(frame, text=param.name)
        entry = ttk.Entry(frame)
        entry.insert(0, param.value)

        def on_change(*args):
            self.viewer.set_parameter_value(param.name, entry.get())
            self._update_plot()

        entry.bind("<Return>", on_change)

        label.pack(side=tk.LEFT)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        frame.pack(fill=tk.X, padx=5, pady=2)

        return entry

    def _create_boolean_widget(self, param):
        """Create a checkbox widget."""
        var = tk.BooleanVar(value=param.value)
        checkbox = ttk.Checkbutton(
            self.controls_frame,
            text=param.name,
            variable=var,
            command=lambda: self._handle_widget_change(param.name, var.get()),
        )
        checkbox.pack(anchor=tk.W, padx=5, pady=2)
        return checkbox

    def _handle_widget_change(self, name: str, value: Any):
        """Handle changes to widget values."""
        self.viewer.set_parameter_value(name, value)
        self._update_plot()

    def _update_plot(self):
        """Update the plot with current state."""
        if self._canvas is not None:
            self._canvas.get_tk_widget().destroy()

        state = self.viewer.get_state()
        self._current_figure = self.viewer.plot(state)

        self._canvas = FigureCanvasTkAgg(self._current_figure, self.plot_frame)
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def deploy(self):
        """Deploy the interactive viewer in a standalone window."""
        # Set up layout
        if self.config.controls_position == "left":
            self.controls_frame.pack(side=tk.LEFT, fill=tk.Y)
            self.plot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        else:  # top
            self.controls_frame.pack(side=tk.TOP, fill=tk.X)
            self.plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Create initial plot
        self._update_plot()

        # Start the tkinter event loop
        self.root.mainloop()

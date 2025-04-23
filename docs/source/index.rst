Welcome to Syd's documentation!
===============================

Syd is a Python library for creating interactive matplotlib visualizations with just a few lines of code. It 
allows you to make interactive GUIs for data science as easy as possible. No boilerplate, no complicated GUI
management, just a few extra lines of code to define interactive components, and Syd will handle the rest.

Example
-------

This example is just to show how easy it is to make an interactive plot with Syd. We'll make a simple sine wave
plot where we can control the frequency, amplitude, and color of the wave. All you have to do is define the plot
function, create a viewer object, define a few parameters (here they're called ``frequency``, ``amplitude``, and
``color``), and then call ``viewer.show()`` to view the plot in a jupyter notebook or ``viewer.share()`` to view
it in a web browser. 

To understand the mechanics of how it works, check out a thorough explanation of the sine-wave viewer in the 
:ref:`quickstart` section or learn more in the :ref:`tutorial`. 

.. tabs::
   .. tab:: Notebook

      .. code-block:: python

         from syd import make_viewer
         import matplotlib.pyplot as plt
         import numpy as np

         def plot(state):
            """Plot the waveform based on current parameters."""
            t = np.linspace(0, 2*np.pi, 1000)
            y = np.sin(state["frequency"] * t) * state["amplitude"]
            fig = plt.figure()
            ax = plt.gca()
            ax.plot(t, y, color=state["color"])
            return fig

         viewer = make_viewer(plot)
         viewer.add_float("frequency", value=1.0, min=0.1, max=5.0)
         viewer.add_float("amplitude", value=1.0, min=0.1, max=2.0)
         viewer.add_selection("color", value="red", options=["red", "blue", "green"])
         viewer.show() # for viewing in a jupyter notebook
   
      .. image:: ../assets/viewer_screenshots/1-simple_example.png
        :alt: Quick Start Example
        :align: center

   .. tab:: Browser

      .. code-block:: python

         from syd import make_viewer
         import matplotlib.pyplot as plt
         import numpy as np

         def plot(state):
            """Plot the waveform based on current parameters."""
            t = np.linspace(0, 2*np.pi, 1000)
            y = np.sin(state["frequency"] * t) * state["amplitude"]
            fig = plt.figure()
            ax = plt.gca()
            ax.plot(t, y, color=state["color"])
            return fig

         viewer = make_viewer(plot)
         viewer.add_float("frequency", value=1.0, min=0.1, max=5.0)
         viewer.add_float("amplitude", value=1.0, min=0.1, max=2.0)
         viewer.add_selection("color", value="red", options=["red", "blue", "green"])
         viewer.share() # for viewing in a web browser

Installation
============

You can install Syd using pip:

.. code-block:: bash

   pip install syd

Requirements
------------

- Python 3.9+ (it might work on older versions but it isn't tested on them!)
- matplotlib
- ipywidgets
- ipympl
- ipykernel
- flask


Table of Contents
=================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   components
   tutorial
   api/index
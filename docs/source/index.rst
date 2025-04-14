Welcome to Syd's documentation!
===============================

Syd is a Python library for creating interactive matplotlib visualizations with minimal boilerplate.
Add GUI controls to your plots with just a few lines of code!

.. code-block:: python

   from syd import make_viewer
   import matplotlib.pyplot as plt
   import numpy as np

   def plot(state):
      x = np.linspace(0, 2*np.pi, 100)
      y = np.sin(x * state["frequency"])
      fig = plt.figure()
      plt.plot(x, y)
      return fig

   viewer = make_viewer(plot)
   viewer.add_float('frequency', value=1.0, min=0, max=3.0)
   viewer.deploy(continuous=True)


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


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   components
   tutorial
   api/index
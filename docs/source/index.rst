Welcome to Syd's documentation!
===============================

Syd is a Python library for creating interactive matplotlib visualizations with minimal boilerplate.
Add GUI controls to your plots with just a few lines of code!

.. code-block:: python

   from syd import InteractiveViewer
   import matplotlib.pyplot as plt

   class MyViewer(InteractiveViewer):
       def plot(self, state):
           fig = plt.figure()
           plt.plot([0, state['x']])
           return fig

   viewer = MyViewer()
   viewer.add_float('x', value=1.0, min_value=0, max_value=10)


Installation
============

You can install Syd using pip:

.. code-block:: bash

   pip install syd

Requirements
------------

- Python 3.7+
- matplotlib
- ipywidgets (for Jupyter notebook support) 


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   api/index 
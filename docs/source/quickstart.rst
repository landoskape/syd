Quick Start Guide
===============

Creating Your First Interactive Plot
---------------------------------

1. Create a viewer class that inherits from ``InteractiveViewer``
2. Implement the ``plot()`` method to create your visualization
3. Add parameters to control your plot
4. Register callbacks to update the plot when parameters change

Here's a complete example:

.. code-block:: python

   from syd import InteractiveViewer
   import matplotlib.pyplot as plt
   import numpy as np

   class SineViewer(InteractiveViewer):
       def plot(self, state):
           fig = plt.figure()
           x = np.linspace(0, 10, 1000)
           y = np.sin(state['frequency'] * x)
           plt.plot(x, y)
           plt.title(state['title'])
           plt.grid(state['show_grid'])
           return fig

        def toggle_grid(self, state):
            self.update_boolean('show_grid', value=not state['show_grid'])

   viewer = SineViewer()

   # Add controls
   viewer.add_float('frequency', value=1.0, min_value=0.1, max_value=5.0, step=0.1)
   viewer.add_text('title', value='Sine Wave')
   viewer.add_boolean('show_grid', value=True)

   # Update plot when any parameter changes
   viewer.on_change(['frequency', 'title', 'show_grid'], self.toggle_grid)

Available Parameter Types
-----------------------

- Text input (``add_text``)
- Checkboxes (``add_boolean``)
- Dropdown menus (``add_selection``)
- Multi-select (``add_multiple_selection``)
- Integer sliders (``add_integer``)
- Float sliders (``add_float``)
- Range sliders (``add_integer_range``, ``add_float_range``)
- Unbounded numeric inputs (``add_unbounded_integer``, ``add_unbounded_float``) 
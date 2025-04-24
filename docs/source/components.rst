Components
==========

Available Parameter Types
-------------------------

The SYD package offers a rich variety of parameter types to make your interactive visualizations! Here's your toolkit:

.. list-table:: 
   :widths: 40 40 40
   :header-rows: 1

   * - Parameter Type
     - Description
     - Use Cases
   * - Text input
     - A classic text field for any string input
     - Labels, names, free-form text
   * - Checkboxes
     - Simple true/false decisions
     - Toggle features, settings
   * - Dropdown menus
     - Choose one option from a list
     - Single selection, filters
   * - Multi-select menus
     - Select multiple options
     - Multiple filters, combined options
   * - Integer sliders
     - Slide through whole numbers
     - Range selection, adjustments
   * - Float sliders
     - Smooth sailing through decimal values
     - Precision adjustments, fine-tuning
   * - Integer Range sliders
     - Pick two integers to define bounds
     - Range limits, boundary settings
   * - Float Range sliders
     - Select a continuous range with decimal precision
     - Continuous range selection, precision limits
   * - Unbounded integer inputs
     - Any whole number input
     - Large number inputs, calculations
   * - Unbounded float inputs
     - Decimal values without bounds
     - Scientific calculations, precise measurements
   * - Button
     - Trigger actions (not associated with a value)
     - Great for saving the figure, for example!

Info about each parameter
-------------------------

For more information about each parameter type, open the dropdowns below. In each, you'll learn:

* What the parameter is for
* How to use it
* What it returns
* Documentation for the add & update methods to create or update the parameter.

.. dropdown:: Text input
  :class-title: bg-primary text-white
  :class-body: bg-light

  Text input parameters are used to get a string input from the user. 
  
  Their format is a simple text field and they return strings. You can use them
  for whatever you want as long as you can represent it as a string!

  .. image:: ../assets/component_screenshots/text_input.png
    :alt: Text Input
    :align: center

  .. automethod:: syd.viewer.Viewer.add_text
    :no-index:

  .. automethod:: syd.viewer.Viewer.update_text
    :no-index:

.. dropdown:: Checkboxes
  :class-title: bg-primary text-white
  :class-body: bg-light  

  Checkbox parameters are used to get a boolean input from the user. 
  
  Their format is a checkbox and they return booleans. They're great for toggling features
  on and off or changing the state of something. 
  
  For example, you could use a checkbox to toggle whether a certain plot is shown or not - 
  or whether to show an average with a line plot vs the raw data with a scatter plot. 

  .. image:: ../assets/component_screenshots/checkbox.png
    :alt: Checkbox
    :align: center

  .. automethod:: syd.viewer.Viewer.add_boolean
    :no-index:

  .. automethod:: syd.viewer.Viewer.update_boolean
    :no-index:
  
.. dropdown:: Dropdown menus
  :class-title: bg-primary text-white
  :class-body: bg-light  

  Dropdown menu parameters are used to choose a single option from a list. 
  
  Dropdown menus accept a list of options, and the value of the parameter is the selected option.
  What you put in the list is completely up to you, as long as you can find it in the list with a
  standard ``==`` comparison.
  
  These are great for situations where you need to choose from a few options. For example, you might
  want to show data from a particular session, where the "options" are the names of each session. They
  can also be used to show different plots or different calculations, etc etc etc. 

  .. image:: ../assets/component_screenshots/dropdown.png
    :alt: Dropdown Menu
    :align: center

  .. automethod:: syd.viewer.Viewer.add_selection
    :no-index:

  .. automethod:: syd.viewer.Viewer.update_selection
    :no-index:

.. dropdown:: Multi-select menus
  :class-title: bg-primary text-white
  :class-body: bg-light  

  Multi-select menu parameters are used to choose multiple options from a list. 

  Multi-select menus accept a list of options, and the value of the parameter a list of the currently selected
  options. What you put in the list is completely up to you, as long as you can find it in the list with a
  standard ``==`` comparison.
  
  These are great for situations where you need to select groups of things. For example, you might want to select
  multiple sessions to include in a plot, or multiple channels to include in a calculation. Maybe you have a plot
  that shows the same data in a variety of ways, and you want to decide which parts to show overlaid on top of
  each other. 

  .. image:: ../assets/component_screenshots/multiselect.png
    :alt: Multi-select Menu
    :align: center

  .. automethod:: syd.viewer.Viewer.add_multiple_selection
    :no-index:

  .. automethod:: syd.viewer.Viewer.update_multiple_selection
    :no-index:


.. dropdown:: Integer sliders
  :class-title: bg-primary text-white
  :class-body: bg-light  

  Integer slider parameters are used to select a single integer value within a defined range.
  
  Their format is a slider that snaps to whole numbers, and they return integers. These are perfect
  for situations where you need to select from a sequence of numbers, like choosing how many items
  to display, selecting a specific frame number in a sequence, or adjusting discrete quantities.
  
  For example, you might use an integer slider to select which trial number to display in an
  experiment, or to adjust the number of bins in a histogram.

  **NOTE:** You can change the value by dragging the slider or by typing in the value in the text field!

  .. image:: ../assets/component_screenshots/integer.png
    :alt: Integer Slider
    :align: center

  .. automethod:: syd.viewer.Viewer.add_integer
    :no-index:

  .. automethod:: syd.viewer.Viewer.update_integer
    :no-index:


.. dropdown:: Float sliders
  :class-title: bg-primary text-white
  :class-body: bg-light  

  Float slider parameters are used to select a decimal value within a defined range.
  
  Their format is a smooth slider that allows for decimal values, and they return floats. These are
  ideal for continuous adjustments where precision matters, like setting thresholds, adjusting
  scaling factors, or fine-tuning visual parameters. You can set the step size of the slider to be
  as small or as large as you want for extra control over the values. 
  
  For example, you might use a float slider to adjust the transparency of a plot overlay, set a
  correlation threshold, or control the smoothing factor in a data processing step.

  **NOTE:** You can change the value by dragging the slider or by typing in the value in the text field!

  .. image:: ../assets/component_screenshots/float.png
    :alt: Float Slider
    :align: center

  .. automethod:: syd.viewer.Viewer.add_float
    :no-index:

  .. automethod:: syd.viewer.Viewer.update_float
    :no-index:


.. dropdown:: Integer Range sliders
  :class-title: bg-primary text-white
  :class-body: bg-light  

  Integer range slider parameters are used to select a range between two integer values.
  
  Their format is a dual-handle slider that snaps to whole numbers, and they return a tuple of
  integers (start, end). These are perfect for defining discrete intervals or bounds, like
  selecting a range of frames, specifying trial numbers, or setting count-based limits.
  
  For example, you might use an integer range slider to select a span of time points in a
  recording, or to specify the start and end indices for a data subset.

  **NOTE:** You can change the value by dragging the slider or by typing in the values in the text field!

  .. image:: ../assets/component_screenshots/integer_range.png
    :alt: Integer Range Slider
    :align: center

  .. automethod:: syd.viewer.Viewer.add_integer_range
    :no-index:

  .. automethod:: syd.viewer.Viewer.update_integer_range
    :no-index:


.. dropdown:: Float Range sliders
  :class-title: bg-primary text-white
  :class-body: bg-light  

  Float range slider parameters are used to select a continuous range between two decimal values.
  
  Their format is a dual-handle slider that allows for decimal values, and they return a tuple of
  floats (start, end). These are ideal for defining continuous intervals where precision matters,
  like specifying frequency bands, setting value thresholds, or defining time windows.
  
  For example, you might use a float range slider to select a specific frequency band for
  filtering, or to define minimum and maximum values for data normalization.

  In addition, float sliders are a great way to control the xlim or ylim of a plot if you want it to
  be persistent when you are updating the other parameters!!!

  **NOTE:** You can change the value by dragging the slider or by typing in the values in the text field!

  .. image:: ../assets/component_screenshots/float_range.png
    :alt: Float Range Slider
    :align: center

  .. automethod:: syd.viewer.Viewer.add_float_range
    :no-index:

  .. automethod:: syd.viewer.Viewer.update_float_range
    :no-index:


.. dropdown:: Unbounded integer inputs
  :class-title: bg-primary text-white
  :class-body: bg-light  

  Unbounded integer input parameters are used when you need to input any whole number without
  range restrictions.
  
  Their format is a simple number input field that only accepts integers, and they return integers.
  These are perfect for situations where you can't predict the range of values needed, like
  entering large numbers, IDs, or counts that could vary widely.
  
  For example, you might use an unbounded integer input to specify a random seed for
  reproducibility, enter a specific trial number in a large dataset, or input a timestamp.

  .. image:: ../assets/component_screenshots/unbounded_integer.png
    :alt: Unbounded Integer Input
    :align: center

  .. automethod:: syd.viewer.Viewer.add_unbounded_integer
    :no-index:

  .. automethod:: syd.viewer.Viewer.update_unbounded_integer
    :no-index:


.. dropdown:: Unbounded float inputs  
  :class-title: bg-primary text-white
  :class-body: bg-light  

  Unbounded float input parameters are used when you need to input any decimal number without
  range restrictions.
  
  Their format is a simple number input field that accepts decimal values, and they return floats.
  These are ideal for situations where you need precise numerical input without constraints, like
  entering scientific measurements, custom scaling factors, or exact values for calculations.
  
  For example, you might use an unbounded float input to enter a specific frequency value,
  provide a custom threshold, or input exact coordinates for visualization.

  .. image:: ../assets/component_screenshots/unbounded_float.png
    :alt: Unbounded Float Input
    :align: center

  .. automethod:: syd.viewer.Viewer.add_unbounded_float
    :no-index:

  .. automethod:: syd.viewer.Viewer.update_unbounded_float
    :no-index:

.. dropdown:: Button
  :class-title: bg-primary text-white
  :class-body: bg-light  

  Button parameters are used to trigger actions.
  
  They don't return anything, but they are great for triggering actions like saving the figure,
  running a calculation, or performing an operation. 
  
  For example, suppose you're using Syd to look at example data to pick which one you want to use
  as the main example in your paper. You could use a button to save a reference to the current selection
  so that you can save it for later!

  .. image:: ../assets/component_screenshots/button.png
    :alt: Button
    :align: center

  .. automethod:: syd.viewer.Viewer.add_button
    :no-index:

  .. automethod:: syd.viewer.Viewer.update_button
    :no-index:

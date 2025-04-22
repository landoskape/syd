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

Adding and updating parameters
------------------------------

Each parameter type has a corresponding method in the viewer class. For example, to add a float parameter, you can use ``add_float()``.
The methods have conveniently simple and obvious names, the format is always ``add_<parameter_type>``.

.. list-table:: 
   :widths: 60 60 60
   :header-rows: 1

   * - Parameter Type
     - Add Method
     - Update Method
   * - Text input
     - :meth:`~syd.viewer.Viewer.add_text`
     - :meth:`~syd.viewer.Viewer.update_text`
   * - Checkboxes
     - :meth:`~syd.viewer.Viewer.add_boolean`
     - :meth:`~syd.viewer.Viewer.update_boolean`
   * - Dropdown menus
     - :meth:`~syd.viewer.Viewer.add_selection`
     - :meth:`~syd.viewer.Viewer.update_selection`
   * - Multi-select menus
     - :meth:`~syd.viewer.Viewer.add_multiple_selection`
     - :meth:`~syd.viewer.Viewer.update_multiple_selection`
   * - Integer sliders
     - :meth:`~syd.viewer.Viewer.add_integer`
     - :meth:`~syd.viewer.Viewer.update_integer`
   * - Float sliders
     - :meth:`~syd.viewer.Viewer.add_float`
     - :meth:`~syd.viewer.Viewer.update_float`
   * - Integer Range sliders
     - :meth:`~syd.viewer.Viewer.add_integer_range`
     - :meth:`~syd.viewer.Viewer.update_integer_range`
   * - Float Range sliders
     - :meth:`~syd.viewer.Viewer.add_float_range`
     - :meth:`~syd.viewer.Viewer.update_float_range`
   * - Unbounded integer inputs
     - :meth:`~syd.viewer.Viewer.add_unbounded_integer`
     - :meth:`~syd.viewer.Viewer.update_unbounded_integer`
   * - Unbounded float inputs
     - :meth:`~syd.viewer.Viewer.add_unbounded_float`
     - :meth:`~syd.viewer.Viewer.update_unbounded_float`
    

Components
==========

Available Parameter Types
-------------------------

The SYD package offers a rich variety of parameter types to make your interactive visualizations! Here's your toolkit:

Text & Numbers
"""""""""""""""""
* **Text Input**
    - Your classic text field for any string input
    - Perfect for labels, names, or free-form text

* **Unbounded Inputs**
    - **Integer**: When you need any whole number under the sun
    - **Float**: For those decimal values that know no bounds

Sliders & Ranges
"""""""""""""""""""
* **Single-Value Sliders**
    - **Integer Slider**: Slide through whole numbers with style
    - **Float Slider**: Smooth sailing through decimal values

* **Range Sliders**
    - **Integer Range**: Pick two integers to define your bounds
    - **Float Range**: Select a continuous range with decimal precision

Selection Controls
"""""""""""""""""""""
* **Dropdown Menu**
    - Choose one option from your curated list
    - Keep your interface clean and choices clear

* **Multi-Select Menu**
    - Why choose one when you can have many?
    - Perfect for multiple filters or combined options

Toggle Controls
"""""""""""""""""""
* **Checkbox**
    - Simple true/false decisions
    - Toggle features on and off with a click


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
     - :meth:`~syd.interactive_viewer.InteractiveViewer.add_text`
     - :meth:`~syd.interactive_viewer.InteractiveViewer.update_text`
   * - Checkboxes
     - :meth:`~syd.interactive_viewer.InteractiveViewer.add_boolean`
     - :meth:`~syd.interactive_viewer.InteractiveViewer.update_boolean`
   * - Dropdown menus
     - :meth:`~syd.interactive_viewer.InteractiveViewer.add_selection`
     - :meth:`~syd.interactive_viewer.InteractiveViewer.update_selection`
   * - Multi-select menus
     - :meth:`~syd.interactive_viewer.InteractiveViewer.add_multiple_selection`
     - :meth:`~syd.interactive_viewer.InteractiveViewer.update_multiple_selection`
   * - Integer sliders
     - :meth:`~syd.interactive_viewer.InteractiveViewer.add_integer`
     - :meth:`~syd.interactive_viewer.InteractiveViewer.update_integer`
   * - Float sliders
     - :meth:`~syd.interactive_viewer.InteractiveViewer.add_float`
     - :meth:`~syd.interactive_viewer.InteractiveViewer.update_float`
   * - Integer Range sliders
     - :meth:`~syd.interactive_viewer.InteractiveViewer.add_integer_range`
     - :meth:`~syd.interactive_viewer.InteractiveViewer.update_integer_range`
   * - Float Range sliders
     - :meth:`~syd.interactive_viewer.InteractiveViewer.add_float_range`
     - :meth:`~syd.interactive_viewer.InteractiveViewer.update_float_range`
   * - Unbounded integer inputs
     - :meth:`~syd.interactive_viewer.InteractiveViewer.add_unbounded_integer`
     - :meth:`~syd.interactive_viewer.InteractiveViewer.update_unbounded_integer`
   * - Unbounded float inputs
     - :meth:`~syd.interactive_viewer.InteractiveViewer.add_unbounded_float`
     - :meth:`~syd.interactive_viewer.InteractiveViewer.update_unbounded_float`
    

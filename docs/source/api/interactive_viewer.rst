Interactive Viewer
==================

.. currentmodule:: syd.interactive_viewer

InteractiveViewer
-----------------

.. autoclass:: InteractiveViewer
   :members:
   :inherited-members:
   :special-members: __init__

   .. rubric:: Methods

   .. autosummary::
      :nosignatures:

      plot
      get_state
      on_change
      set_parameter_value

   .. rubric:: Parameter Registration

   .. autosummary::
      :nosignatures:

      add_text
      add_boolean
      add_selection
      add_multiple_selection
      add_integer
      add_float
      add_integer_range
      add_float_range
      add_unbounded_integer
      add_unbounded_float

   .. rubric:: Parameter Updates

   .. autosummary::
      :nosignatures:

      update_text
      update_boolean
      update_selection
      update_multiple_selection
      update_integer
      update_float
      update_integer_range
      update_float_range
      update_unbounded_integer
      update_unbounded_float 
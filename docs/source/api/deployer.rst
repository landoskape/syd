Deployer
========

.. currentmodule:: syd.deployer

Deployer Base Class
-------------------

.. autoclass:: Deployer
   :members:
   :inherited-members:
   :special-members: __init__

   .. rubric:: Methods

   .. autosummary::
      :nosignatures:

      deploy
      handle_component_engagement
      sync_components_with_state
      update_plot

   .. rubric:: Abstract Methods (for Subclasses)

   .. autosummary::
      :nosignatures:

      display_new_plot
      build_components
      build_layout
      display

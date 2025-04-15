Support
=======

.. currentmodule:: syd.support

Overview
--------

The `syd.support` module provides essential backend support for parameter operations within the syd framework. It includes custom exceptions and singleton classes that facilitate error handling and state management in parameter updates and initializations. This module is crucial for developers working with the syd framework, as it ensures robust and predictable behavior when parameters are added or updated. If you are just trying to use Syd for your project, you can probably ignore this module!

Singletons
----------

The `syd.support` module defines two singleton classes, `NoUpdate` and `NoInitialValue`, which are used throughout the syd framework to represent specific states in parameter operations.

.. autoclass:: NoUpdate
   :members:
   :show-inheritance:

   The `NoUpdate` singleton is used to signify that a parameter should not be updated. It is used throughout each parameter's ``update_*`` method where updating an attribute of a parameter is optional. The reason for a singleton rather than the more conventional ``None`` is that ``None`` is a valid value for some parameters, and we want to be able to distinguish between a parameter that has not been updated and a parameter that has been updated to ``None``.

.. autoclass:: NoInitialValue
   :members:
   :show-inheritance:

   The `NoInitialValue` singleton represents the absence of an initial value for a parameter. It is used throughout each parameter's ``add_*`` method where specifying the initial value is optional. The reason for using a singleton rather than the more conventional ``None`` is that ``None`` is a valid value for some parameters, and we want to be able to distinguish between a parameter that has not been initialized and a parameter that has been initialized to ``None``.
   

Exceptions
----------

.. autoexception:: ParameterAddError
   :members:
   :show-inheritance:

.. autoexception:: ParameterUpdateError
   :members:
   :show-inheritance: 


Warnings
--------

.. autoexception:: ParameterUpdateWarning
   :members:
   :show-inheritance:

    The `ParameterUpdateWarning` is used to warn the user that a parameter has been updated to a new value behind the scenes. This occurs in cases where a callback leads to the parameters attributes changing which can invalidate the current parameter's value. We fire off a warning so they are aware of the change. 


.. autofunction:: warn_parameter_update

   We include a specific function for firing off ``ParameterUpdateWarning`` warnings so that it is easier to suppress the warnings if desired. 


High-level Parameter Handling
-----------------------------

.. autoclass:: ParameterMeta
   :show-inheritance:

   The `ParameterMeta` class is a metaclass that is used to stereotype the parameter classes. Syd often checks if an object is of a particular parameter type, and will raise an error when it isn't. This is a nightmare for module reloading in jupyter notebooks, which is one of the primary use areas for Syd. So, the `ParameterMeta` class is used to store the parameter types in a way that makes sure module reloading doesn't break the type checking. 


.. autofunction:: get_parameter_attributes

   The `get_parameter_attributes` function is used to get the attributes of a parameter. It is used for checking parameter updates and for testing. 

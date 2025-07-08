Frequently Asked Questions
==========================

This section contains a list of explanations for common issues and questions about Syd. If you 
think something should be added here, please `open an issue <https://github.com/landoskape/syd/issues>`_.

How do I add a parameter to a viewer? 
-------------------------------------

All parameters are added using their respective ``add_{parameter_type}`` method. For example, to add a
boolean parameter, you would use ``viewer.add_boolean()``. For a full list of parameters, see the 
:doc:`components` section.

Each parameter type has it's own set of attributes that are usually required to be set when you add it. 
For example, the ``add_float`` method has the following required attributes:

* ``name``: The name of the parameter.
* ``min``: The minimum value of the parameter.
* ``max``: The maximum value of the parameter.

In addition to the optional attributes:

* ``value``: The initial value of the parameter (defaults to ``min``).
* ``step``: The step size of the parameter (defaults to ``0.001``).

This is what it looks like in action:

.. tabs::

    .. tab:: Factory-based

        .. code-block:: python

            from syd import make_viewer

            viewer = make_viewer()
            viewer.add_float("my_float", value=3, min=0, max=10, step=0.1)

    .. tab:: Subclass-based

        .. code-block:: python

            from syd import Viewer

            class MyViewer(Viewer):
                def __init__(self):
                    self.add_float("my_float", value=3, min=0, max=10, step=0.1)

How do I update a parameter? 
----------------------------

All parameters are updated using their respective ``update_{parameter_type}`` method. For example, to update a
float parameter, you would use :meth:`update_float() <syd.Viewer.update_float>`. For a full list of update methods, see the dropdown
menus in the :doc:`components` section.

For simplicity, update methods have the same API as the corresponding ``add_{parameter_type}`` method, but every
input is optional (except for ``name``, which is required to specify which parameter you want to update).

You can use the ``update_{parameter_type}`` methods whenever you want, but they are most commonly used in the 
context of a callback function that is triggered by some other change (see below). 

.. note::
    Syd attempts to fail gracefully if an update is inconsistent. For example, if you have a selection parameter 
    with ``value="a"`` and ``options=["a", "b", "c"]``, and you try to set ``options=[1, 2, 3]``, Syd will recognize
    that the current value is not in the new options, and will change the value to the first of the new options (e.g. ``1``). 

    However, if a graceful failure is not possible, Syd will raise an error (like if you try to change it to ``value=1`` and 
    ``options=["a", "b", "c"]``).

This is what it looks like in action:

.. tabs::

    .. tab:: Factory-based

        .. code-block:: python

            from syd import make_viewer

            viewer = make_viewer()
            viewer.add_float("my_float", value=3, min=0, max=10, step=0.1)

            # Change the value and leave the min/max/step the same
            viewer.update_float("my_float", value=4)

    .. tab:: Subclass-based

        .. code-block:: python

            from syd import Viewer

            class MyViewer(Viewer):
                def __init__(self):
                    self.add_float("my_float", value=3, min=0, max=10, step=0.1)
                    
                    # Change the value and leave the min/max/step the same
                    self.update_float("my_float", value=4)

How do I change the axis limits of a plot and keep them there?
--------------------------------------------------------------

If you use ``%matplotlib widget`` mode in a notebook, (e.g. with the ``viewer.show()`` method), then you should be able
to change the axis limits of the plot, but it won't be persistent if you change a parameter of the GUI. 

However, you can use a ``FloatRangeParameter`` to control axis limits using the Syd interface. This way, you can change
the axis limits and they'll stay where they are even when you change some other parameter of the GUI.

This is what it looks like in action:

.. tabs::

    .. tab:: Factory-based

        .. code-block:: python

            from syd import make_viewer

            viewer = make_viewer()
            viewer.add_float_range("x_limits", value=(0, 10), min=0, max=10)
            viewer.add_float_range("y_limits", value=(0, 10), min=0, max=10)

            def plot(state):
                x = np.linspace(0, 10, 100)
                y = np.linspace(0, 10, 100)
                plt.plot(x, y)
                plt.xlim(state["x_limits"])
                plt.ylim(state["y_limits"])
                return plt.gcf()

    .. tab:: Subclass-based

        .. code-block:: python

            from syd import Viewer

            class MyViewer(Viewer):
                def __init__(self):
                    self.add_float_range("x_limits", value=(0, 10), min=0, max=10)
                    self.add_float_range("y_limits", value=(0, 10), min=0, max=10)  

                def plot(state):
                    x = np.linspace(0, 10, 100)
                    y = np.linspace(0, 10, 100)
                    plt.plot(x, y)
                    plt.xlim(state["x_limits"])
                    plt.ylim(state["y_limits"])
                    return plt.gcf()

But like, how does Syd have access to my data?
----------------------------------------------

Thinking about how to get your data into a Syd viewer is a common question that isn't always 
perfectly intuitive. Ultimately, Syd only needs to know what your plot function is, and as long
as the plot function knows how to get the data, then Syd will be able to plot it!

For example, suppose you are have a numpy array ``data`` that you want to plot. You can do the following:

.. tabs::

    .. tab:: Factory-based

        .. code-block:: python

            import numpy as np
            import matplotlib.pyplot as plt
            from syd import make_viewer

            # As long as the data is defined, it will be available to the plot function.
            data = np.random.randn(100, 1000)

            def plot(state):
                fig = plt.figure()
                plt.plot(data[state["index"]])
                return fig

            # The viewer will call the plot function, which will access the data.
            viewer = make_viewer(plot)
            viewer.add_integer("index", min=0, max=data.shape[0] - 1)
            viewer.show()

    .. tab:: Subclass-based

        .. code-block:: python

            import numpy as np
            import matplotlib.pyplot as plt
            from syd import Viewer

            # As long as the data is defined, it will be available to the plot function.
            data = np.random.randn(100, 1000)

            class MyViewer(Viewer):
                def __init__(self):
                    self.add_integer("index", min=0, max=data.shape[0] - 1)

                def plot(state):
                    fig = plt.figure()
                    plt.plot(data[state["index"]])
                    return fig

            # The viewer will call the plot function, which will access the data.
            viewer = MyViewer()
            viewer.show()

.. seealso::

    For a fully fleshed out example, see the `data-loading-example notebook <https://github.com/landoskape/syd/blob/main/examples/3-data_loading.ipynb>`_
    or |colab|.

.. |colab| image:: https://colab.research.google.com/assets/colab-badge.svg
    :target: https://colab.research.google.com/github/landoskape/syd/blob/main/examples/3-data_loading.ipynb
    :alt: Open In Colab


Syd is slow! What can I do? (Cache your data!)
----------------------------------------------

Syd is actually quite fast because there's very little work Syd has to do behind the scenes. The main reason you'll get slow
performance is when *your plot function is slow*. The best way to speed things up is to cache as much as you can so you don't
have to do much processing in the plot function. It's easiest to handle a cache in an object-oriented way, so the example below
will exclusively use the subclass-based approach. 

Suppose you have some large dataset composed of 10 neuropixels recordings (if you aren't familiar, neuropixels data is huge and 
usually slow to load). You want to be able to pick the recording, then do some Syd controlled processing on the data from each
recording. If your plot function loads the recording from disk every time, it'll be slow. But if you cache the recording, it'll
only have to load from disk once (or every time you change the recording you're looking at). 

Here's an example of how to handle this situation:

.. code-block:: python

    import numpy as np
    import matplotlib.pyplot as plt
    from time import sleep
    from syd import Viewer

    def data_loading_function(recording_name):
        # This is a placeholder for some data loading function.
        # For example, it might load data from disk, or download it from a server, etc.
        sleep(2) # simulate slow loading...
        return np.random.randn(100, 1000)

    # This viewer will allow you to pick a recording, then plot data from the recording.
    # Each recording is a numpy array with shape (num_neurons, num_samples).
    # We can use the xlims/ylims float ranges to control which part of the data is shown.
    class MyViewer(Viewer):
        def __init__(self):
            recording_names = [r"recording_{i}" for i in range(10)]
            self.add_selection("recording", options=recording_names)
            self.add_integer("neuron", min=0, max=999)
            self.add_float_range("xlims", value=(0, 10), min=0, max=100)
            self.add_float_range("ylims", value=(0, 10), min=0, max=100)
            self.add_color("color", value="black", options=["black", "red", "blue", "green"])

            self.data_cache = None

            # Whenever the recording changes, we run the cache_data callback. 
            # This will load the data and store it as an attribute of the viewer object.
            self.on_change("recording", self.cache_data)

        def cache_data(self, state):
            # Load the data with your data loading function and store it as an 
            # attribute of the viewer object you made. 
            self.data_cache = data_loading_function(state["recording"])

            # Each recording might have a different number of neurons, so we need to update the max
            # of the neuron parameter to the number of neurons in the new recording.
            self.update_integer("neuron", max=self.data_cache.shape[0] - 1)

        def plot(state):
            # Instead of reloading the data, we use the cached data!!
            data = self.data_cache
            fig = plt.figure()
            ax = fig.add_subplot(111)
            ax.plot(data[state["neuron"]], color=state["color"])
            ax.set_xlim(state["xlims"])
            ax.set_ylim(state["ylims"])
            return fig

The above example demonstrates how you can bypass a slow dataloading function by caching the data. You'll
notice that the data is loaded from disk every time you change the recording, but the data is cached so that
the data is not loaded from disk again if you change the neuron or the x/ylims or the color. This means that
you've limited the bottleneck to a single parameter. 

See the next FAQ for more explanation of callback / plot behavior. 

.. note::

    Caching is a powerful technique and if memory isn't an issue, you can also do lazy loading and save everything.
    This way, it'll be slow the *first time* you load each recording, but then it'll be fast afterwards. 

    .. code-block:: python

        # Instead of a single data cache, use a dictionary to remember every recording. 
        self.data_cache = {name: None for name in recording_names}

        def cache_data(self, state):
            # In your cache data method, check if the data is cached in your cache dictionary, 
            # if it isn't get it, and then return it. 
            if self.data_cache[state["recording"]] is None:
                self.data_cache[state["recording"]] = data_loading_function(state["recording"])
            return self.data_cache[state["recording"]]


Wait, when are callbacks and plot functions called?
---------------------------------------------------

Syd has a very simple and streamlined system for handling callbacks and updates to the plot function. 

Whenever a parameter change is initiated by interaction with the GUI, a few things happen:

1. The parameter value is updated in the viewer object.
2. The viewer object checks if the parameter is associated with any callbacks. If it is, they are called. 
3. If a callback initiated by one parameter caused a change to any *other* parameters, then the GUI will be updated to reflect the new parameter values.
4. The plot function is called with the new viewer state.

.. note::
    Callbacks are called in the order they were added!

.. note::
    Any other parameters that are changed by a callback *will not* trigger additional callbacks.


My syd viewer isn't showing, what's wrong?
------------------------------------------

There's probably a variety of reasons that can cause this. Some common issues relate to python / conda environment management 
and to the "environment" that your viewer is displayed in. So - if you are attached to your python environment -- try using the
alternative syd deployment option (if using ``show()``, try ``share()`` instead). Or - if you are comfortable rebuilding your 
conda environment, try that again with with a fresh install of syd in a clean background.

.. note::
    If you have trouble and are able to successfully debug it - please tell us by opening an issue on the `github issues page <https://github.com/landoskape/syd/issues>`_.


How do I make the plots in a Syd viewer interactive?
----------------------------------------------------

Syd is built on top of matplotlib, and matplotlib enables interactive plots within jupyter notebooks using the ``%matplotlib widget``
magic command. So, if you are using a jupyter notebook, you can use the following:

.. code-block:: python

    %matplotlib widget

    # ... then build your viewer as usual ...
   
This should work for any kind of plot in a notebook. Due to the way we handle the webbrowser view, it *won't work* in the ``viewer.share()`` mode. If this is something that you'd like, please let us know by opening an issue on the `github issues page <https://github.com/landoskape/syd/issues>`_.

Note, updating axis limits with the ``%matplotlib widget`` method will not be persistent when you update any parameters. See the above FAQ for a better way to handle this titled "How do I change the axis limits of a plot and keep them there?".


I want to use Seaborn in my Syd viewer, how do I do that?
---------------------------------------------------------

Just make a seaborn plot and return the ``figure`` object! Since Syd is built on top of matplotlib, any plotting package that is built on top of matplotlib will work. This includes seaborn!

There are a few tricks that show up occasionally depending on the type of Seaborn plot you're making.

Seaborn plots that allow / require you to set the ``ax`` object.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For seaborn plots that allow you to set the ``ax`` object, your job will be to make a ``fig, ax``, tell seaborn to use your desired ``ax``, and then return the ``fig`` object.

.. code-block:: python

    import seaborn as sns
    import matplotlib.pyplot as plt

    def plot(state):
        fig, ax = plt.subplots()
        sns.scatterplot(x=x, y=y, ax=ax)
        return fig

Seaborn plots that create a new figure.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For seaborn plots that create a new figure internally, you have to retrieve the figure object that it created and return that. For example, the ``jointplot`` function returns a ``JointGrid`` object, which you can then use to get the ``figure`` object. Each seaborn plot function is different, so you'll have to look up the correct way to get the figure object for the plot you're making.

.. code-block:: python

    import seaborn as sns
    import matplotlib.pyplot as plt

    def plot(state):
        joint_grid = sns.jointplot(x=x, y=y)
        fig = joint_grid._figure
        return fig






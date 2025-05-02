# Syd

[![PyPI version](https://badge.fury.io/py/syd.svg)](https://badge.fury.io/py/syd)
[![Tests](https://github.com/landoskape/syd/actions/workflows/tests.yml/badge.svg)](https://github.com/landoskape/syd/actions/workflows/tests.yml)
[![Documentation Status](https://readthedocs.org/projects/shareyourdata/badge/?version=stable)](https://shareyourdata.readthedocs.io/en/stable/?badge=stable)
[![codecov](https://codecov.io/gh/landoskape/syd/branch/main/graph/badge.svg)](https://codecov.io/gh/landoskape/syd)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


<div>
    <img src="./docs/assets/syd-logo-white.png" alt="Syd" width="350" align="right"/>
</div>

A package to help you share your data!

Have you ever wanted to look through all your data really quickly interactively? Of course you have. Mo data mo problems, but only if you don't know what to do with it. And that's why Syd stands for show your data! 

Syd is a system for creating a data viewing GUI that you can view in a jupyter notebook or in a web browser. And guess what? Since it can open in a web browser, you can even open it on any other computer on your local network! For example, your PI's computer. Gone are the days of single random examples that they make infinitely stubborn conclusions about. Now, you can look at all the examples, quickly and easily, on their computer. And that's why Syd stands for share your data!

Okay, so what is it? Syd is an automated system to convert some basic python plotting code into an interactive GUI. This means you only have to think about _**what you want to plot**_ and _**which parameters**_ you want to be interactive. Syd handles all the behind-the-scenes action required to make an interface. And guess what? That means you get to _**spend your time thinking**_ about your data, rather than writing code to look at it. And that's why Syd stands for Science, Yes! Dayummmm!

## Installation
It's easy, just use pip install. The dependencies are light so it should work in most environments.
```bash
pip install syd
```

## Documentation
The full documentation is available [here](https://shareyourdata.readthedocs.io/). It includes a quick start guide, a comprehensive tutorial, and an API reference for the different elements of Syd. If you have any questions or want to suggest improvements to the docs, please let us know on the [github issues page](https://github.com/landoskape/syd/issues)!

## Quick Start
This is an example of a sine wave viewer which is about as simple as it gets. You can choose which env to use - if you use ``env="notebook"`` then the GUI will deploy as the output of a jupyter cell (this only works in jupyter!). If you use ``env="browser"`` then the GUI will open a page in your default web browser and you can interact with the data there (works in jupyter notebooks and also from python scripts!).

```python
import numpy as np
import matplotlib.pyplot as plt
from syd import make_viewer
def plot(state):
    # Here's a simple plot function that plots a sine wave
    fig = plt.figure()
    t = np.linspace(0, 2 * np.pi, 1000)
    ax = plt.gca()
    ax.plot(t, state["amplitude"] * np.sin(state["frequency"] * t), color=state["color"])
    return fig

viewer = make_viewer(plot)
viewer.add_float("amplitude", value=1.0, min=0.1, max=2.0)
viewer.add_float("frequency", value=1.0, min=0.1, max=5.0)
viewer.add_selection("color", value="red", options=["red", "blue", "green", "black"])

viewer.show() # for viewing in a jupyter notebook
# viewer.share() # for viewing in a web browser
```

![Quick Start Viewer](./docs/assets/viewer_screenshots/readme_example_gif.gif)

### More Examples
We have several examples of more complex viewers with detailed explanations in the comments. Here are the links and descriptions to each of them:

| Example | Description | Try It! |
|---------|-------------|---------------|
| [Basic Tutorial](examples/1-simple_example.ipynb) | A good starting point with detailed explanations of how to use the core elements of Syd. | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/landoskape/syd/blob/main/examples/1-simple_example.ipynb) |
| [Comprehensive](examples/2a-complex_example.ipynb) | Showcases just about everything you can do with Syd. | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/landoskape/syd/blob/main/examples/2a-complex_example.ipynb) |
| [Making a Viewer Class](examples/2b-subclass_example.ipynb) | Rewrites the comprehensive example as a class, which is useful when you have complex data processing or callbacks. | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/landoskape/syd/blob/main/examples/2b-subclass_example.ipynb) |
| [Data Loading](examples/3-data_loading.ipynb) | Showcases different ways to get your data into a Syd viewer. | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/landoskape/syd/blob/main/examples/3-data_loading.ipynb) |
| [Hierarchical Callbacks](examples/4-hierarchical_callbacks.ipynb) | Demonstrates how to handle complicated callback situations. | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/landoskape/syd/blob/main/examples/4-hierarchical_callbacks.ipynb) |


### Data loading
Thinking about how to get data into a Syd viewer can be non-intuitive. For some examples that showcase different ways to get your data into a Syd viewer, check out the [data loading example](examples/3-data_loading.ipynb). Or, if you just want a quick and fast example, check this one out:
```python
import numpy as np
from matplotlib import pyplot as plt
from syd import make_viewer

# Suppose you computed some data somewhere (in a script or in a jupyter notebook)
data = np.random.randn(100, 1000)

# When you write a plot function like this, it'll be able to access the data variable
def plot(state):
    fig = plt.figure()
    ax = fig.add_subplot(111)

    # plot indexes to the data that you created outside the plot function
    ax.imshow(data[state["index"]])
    return fig

# Since plot "knows" about the data variable, all you need to do is pass the plot
# function to the syd viewer and it'll be able to access the data once deployed!
viewer = make_viewer(plot)
viewer.show()
```

### Handling Hierarchical Callbacks
Syd dramatically reduces the amount of work you need to do to build a GUI for viewing your data. However, it can still be a bit complicated to think about callbacks. Below is a quick demonstration. To try it yourself, check out the full example [here](examples/4-hierarchical_callbacks.ipynb) or open it in colab [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/landoskape/syd/blob/main/examples/4-hierarchical_callbacks.ipynb).

For example, suppose your dataset is composed of electrophysiology recordings from 3 mice, where each mouse has a different number of sesssions, and each session has a different number of neurons. You want to build a viewer to view a particular neuron from a particular session from a particular mouse. But the viewer will break if you try to index to session 5 for mouse 2 when mouse 2 has less than 5 sessions!

This is where hierarchical callbacks come in. There's a straightforward pattern to handling this kind of situation that you can follow. You can write a callback for each **level** of the hierarchy. Then, each callback can **update** the state and call the next callback in the hierarchy once it's finished. It looks like this: 
```python
import numpy as np
from syd import Viewer # Much easier to build a Viewer class for hierarchical callbacks

class MouseViewer(Viewer):
    def __init__(self, mice_names):
        self.mice_names = mice_names

        self.add_selection("mouse", options=list(mice_names))

        # We don't know how many sessions or neurons to pick from yet,
        # so just set the max to 1 for now.
        self.add_integer("session", min=0, max=1)
        self.add_integer("neuron", min=0, max=1)
        
        # Any time the mouse changes, update the sessions to pick from!
        self.on_change("mouse", self.update_mouse)

        # Any time the session changes, update the neurons to pick from!
        self.on_change("session", self.update_session)

        # Since we built callbacks for setting the range of the session
        # and neuron parameters, we can use them here so the viewer is
        # fully ready and up to date.

        # To get the state, use self.state, which is the current
        # state of the viewer (in the init function, it'll just be the
        # default value for each parameter you've added already).
        self.update_mouse(self.state)

    def update_mouse(self, state):
        # Pseudo code for getting the number of sessions for a given mouse
        num_sessions = get_num_sessions(state["mouse"])

        # Now we update the number of sessions to pick from
        self.update_integer("session", max=num_sessions - 1)

        # Now we need to update the neurons to choose from ....

        # But! Updating the session parameter's max value might trigger a change
        # to the current session value. This ~won't be reflected~ in the state 
        # dictionary that was passed to this function.
        
        # So, we need to load the ~NEW~ state dictionary, which is always 
        # accessible as self.state (or viewer.state if you're not using a class).
        new_state = self.state

        # Then perform the session update callback!
        self.update_session(new_state)

    def update_session(self, state):
        # Pseudo code for getting the number of neurons for a given mouse and session
        num_neurons = get_num_neurons(state["mouse"], state["session"])

        # Now we update the number of neurons to pick from
        self.update_integer("neuron", max=num_neurons - 1)

    def plot(self, state):
        # Pseudo code for plotting the data
        data = get_data(state["mouse"], state["session"], state["neuron"])
        fig = plot_the_data(data)
        return fig

# Now we can create a viewer and deploy it
viewer = MouseViewer(["Mouse 1", "Mouse 2", "Mouse 3"])
viewer.show()
```

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! If you have an idea for an improvement or a bug report, please let us know by opening an
issue on the [github issues page](https://github.com/landoskape/syd/issues). You can also contribute code by submitting
a pull request. Here are some guidelines for contributing:

### 1. Reporting Bugs
If you find a bug, (e.g. any error or strange behavior that is not expected), please let us know by opening an issue on the [github issues page](https://github.com/landoskape/syd/issues).

### 2. Suggesting Features
If you have an idea for a feature or improvement, please let tell us. Opening an issue on the [github issues page](https://github.com/landoskape/syd/issues).

### 3. Improvements to the Documentation
A package is only as good as its documentation. If you think the documentation is missing something, confusing, or could be improved in any way, please let us know by opening an issue on the [github issues page](https://github.com/landoskape/syd/issues).

### 4. Contributing Code
If you want to contribute code (good for you!), here's how you can do it:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run the tests (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request online

Please make sure to update tests as appropriate and adhere to the existing coding style (black, line-length=88, other style guidelines not capture by black, generally following pep8 guidelines). Try to make the code coverage report improve or stay the same rather than decrease (right now the deployment system isn't covered by tests). There aren't any precommit hooks or anything so you're responsible for checking this yourself. You can process the code with black as follows:
```bash
pip install black
black . # from the root directory of the repo
```

## To-Do List
This section doubles as a checklist for things I think could be useful and _a place to get feedback about what users think is useful_. If you think something in this is critical and should be prioritized, or if you think something is missing, please let me know by submitting an issue on the [github issues page](https://github.com/landoskape/syd/issues).
- Layout controls
  - [ ] Add a "save" button that saves the current state of the viewer to a json file
  - [ ] Add a "load" button that loads the viewer state from a json file
  - [ ] Add a "freeze" button that allows the user to update state variables without updating the plot until unfreezing
  - [ ] Add a window for capturing any error messages that might be thrown by the plot function. Maybe we could have a little interface for looking at each one (up to a point) and the user could press a button to throw an error for the traceback. 
- [ ] Consider "app_deployed" context for each deployer...
- Export options:
  - [ ] Export lite: export the viewer as a HTML/Java package that contains an incomplete set of renderings of figures -- using a certain set of parameters.
  - [ ] Export full: export the viewer in a way that contains the data to give full functionality.
- [ ] Idea for sharing: https://github.com/analyticalmonk/awesome-neuroscience, https://github.com/fasouto/awesome-dataviz
- [ ] The handling of value in Selection parameters is kind of weird.... I think we need to think more about what to do for fails!!!!
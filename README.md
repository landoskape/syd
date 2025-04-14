# syd

[![PyPI version](https://badge.fury.io/py/syd.svg)](https://badge.fury.io/py/syd)
[![Tests](https://github.com/landoskape/syd/actions/workflows/tests.yml/badge.svg)](https://github.com/landoskape/syd/actions/workflows/tests.yml)
[![Documentation Status](https://readthedocs.org/projects/shareyourdata/badge/?version=stable)](https://shareyourdata.readthedocs.io/en/stable/?badge=stable)
[![codecov](https://codecov.io/gh/landoskape/syd/branch/main/graph/badge.svg)](https://codecov.io/gh/landoskape/syd)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


A package to help you share your data!

Have you ever wanted to look through all your data really quickly interactively? Of course you have. Mo data mo problems, but only if you don't know what to do with it. And that starts with looking at your data. And that's why syd stands for show your data! 

Syd is a system for creating a data viewing GUI that you can view on a web-browser (or in a jupyter notebook). And guess what? Since it opens on a web browser, you can even open it on any other computer on your local network! For example, your PI's computer. Gone are the days of single random examples that they make infinitely stubborn conclusions about. Now, you can look at all the examples, quickly and easily, on their computer. And that's why syd stands for share your data!

Okay, so what is it? Syd is an automated system to convert some basic python plotting code into an interactive GUI. This means you only have to think about _**what**_ you want to plot and _**which**_ parameters you want to be interactive. Syd handles all the behind-the-scenes action required to make an interface. And do you know what that means? It means you get to spend your time _thinking_ about your data, rather than writing code to look at it. And that's why syd stands for Science, Yes! Dayummmm!

## Installation
It's easy, just use pip install. The dependencies are light so it should work in most environments.
```bash
pip install syd
```

## Quick Start
This is an example of a sine wave viewer which is about as simple as it gets. You can choose which env to use - if you use ``env="notebook"`` then the GUI will deploy as the output of a jupyter cell (this only works in jupyter!). If you use ``env="browser"`` then the GUI will open a page in your default web browser and you can interact with the data there (works in jupyter notebooks and also from python scripts!).
```python
import matplotlib.pyplot as plt
import numpy as np
from syd import make_viewer
def plot(viewer, state):
    fig, ax = plt.subplots()
    x = np.linspace(0, 10, 1000)
    y = state['amplitude'] * np.sin(state['frequency'] * x)
    ax.plot(x, y)
    return fig
        
viewer = make_viewer()
viewer.set_plot(plot)
viewer.add_float('amplitude', value=1.0, min=0, max=2)
viewer.add_float('frequency', value=1.0, min=0.1, max=5)

# env = "notebook" # for viewing within a jupyter notebook
env = "browser" # for viewing in a web browser
viewer.deploy(env=env)
```

We have several examples of more complex viewers in the [examples](examples) folder. A good one to start with is the [simple example](examples/1-simple_example.ipynb) because this has detailed explanations of how to use the core elements of SYD. To see an example that showcases everything you can do with SYD, try [complex example](examples/2a-complex_example.ipynb). And to see what the same viewer looks like when written as a class, check out [subclass example](examples/2b-subclass_example.ipynb). This format is pretty useful when you want complex functionality - for example if you want to add extra supporting methods for processing data and updating parameters that require more complex logic or if your data processing requires some clever preprocessing to make plotting fast. 

For some examples on how to handle data loading for syd viewers, check out the [data loading example](examples/3-data_loading.ipynb).

## Documentation

Full documentation is available at [shareyourdata.readthedocs.io](https://shareyourdata.readthedocs.io/).

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run the tests (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request online

Please make sure to update tests as appropriate and adhere to the existing coding style (black, line-length=88, other style guidelines not capture by black, generally following pep8 guidelines).


## To-Do List
- Layout controls
  - [ ] Improve the display and make it look better
  - [ ] Add a "save" button that saves the current state of the viewer to a json file
  - [ ] Add a "load" button that loads the viewer state from a json file
  - [ ] Add a "freeze" button that allows the user to update state variables without updating the plot until unfreezing
  - [ ] Add a window for capturing any error messages that might be thrown by the plot function. Maybe we could have a little interface for looking at each one (up to a point) and the user could press a button to throw an error for the traceback. 
- [ ] Consider "app_deployed" context for each deployer...
- [ ] Consider the error messages and if they can be more informative and less opaque -- especially when debugging (e.g. when we always get routed to the decorators that check things...)
- Notebook deployment debouncer: 
  - [ ] Probably make this dependent on whether the user is in %matplotlib widget mode or not
  - [ ] Also probably make it dependent on whether the deployer is in continuous mode or not
  - [ ] Potentially make the wait_time dynamic depending on how fast the plot method is and how frequently the no comm messages show up... (if we can catch them)
- [ ] Consider adding a step to the integer parameter...
- Idea for figure management:
  - [ ] We could make fig=?, ax=? arguments optional for the plot function and add a
    "recycle_figure: bool = False" flag be part of the deploy API. This way, an
    advanced user that wants snappy responsivity or complex figure management can
    do so, but the default is for the user to generate a new figure object each time.
- Export options:
  - [ ] Export lite: export the viewer as a HTML/Java package that contains an incomplete set of renderings of figures -- using a certain set of parameters.
  - [ ] Export full: export the viewer in a way that contains the data to give full functionality.
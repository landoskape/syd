# syd

[![PyPI version](https://badge.fury.io/py/syd.svg)](https://badge.fury.io/py/syd)
[![Tests](https://github.com/landoskape/syd/actions/workflows/tests.yml/badge.svg)](https://github.com/landoskape/syd/actions/workflows/tests.yml)
[![Documentation Status](https://readthedocs.org/projects/shareyourdata/badge/?version=stable)](https://shareyourdata.readthedocs.io/en/stable/?badge=stable)
[![codecov](https://codecov.io/gh/landoskape/syd/branch/main/graph/badge.svg)](https://codecov.io/gh/landoskape/syd)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


A package to help you share your data!

Have you ever wanted to look through all your data really quickly interactively? Of course you have. Mo data mo problems, but only if you don't know what to do with it. And that starts with looking at your data. And that's why syd stands for show your data! 

Syd is a system for creating a data viewing GUI that you can view on a web-browser (feature coming soon, right now only in jupyter notebooks). And guess what? Since it opens on a web browser, you can even open it on any other computer on your local network! For example, your PI's computer. Gone are the days of single random examples that they make infinitely stubborn conclusions about. Now, you can look at all the examples, quickly and easily, on their computer. And that's why syd stands for share your data!

Okay, so what is it? Syd is an automated system to convert some basic python plotting code into an interactive GUI. This is great, because it means you only have to think about what you want to plot and which parameters you want to be interactive. Syd handles all the behind-the-scenes boilerplate code required to make an interface. You know what that means? It means you get to focus on _thinking_ about your data, rather than spending time writing code to look at it. And that's why syd stands for Science, Yes! Dayummmm!

## Installation
It's easy, just use pip install. The dependencies are light so it should work in most environments.
```bash
pip install syd
```

## Quick Start
Right now the only way to use it is in a jupyter notebook. More deployment options coming soon!
This is an example of a sine wave viewer which is about as simple as it gets. 
```python
# In a notebook! 
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
viewer.add_float('amplitude', value=1.0, min_value=0, max_value=2)
viewer.add_float('frequency', value=1.0, min_value=0.1, max_value=5)
viewer.deploy(continuous=True)
```

We have several examples of more complex viewers in the [examples](examples) folder. A good one
to start with is the [first example](examples/first_example.ipynb) because this has detailed 
explanations of how to use the core elements of SYD. To see what the exact same viewer looks like
when written as a class, see the [subclass example](examples/subclass_example.ipynb). This format
is pretty useful when you want complex functionality - for example if you want to add extra
supporting methods for processing data and updating parameters that require more complex logic.

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
- Notebook deployment debouncer: 
  - Probably make this dependent on whether the user is in %matplotlib widget mode or not
  - Also probably make it dependent on whether the deployer is in continuous mode or not
  - Potentially make the wait_time dynamic depending on how fast the plot method is and how
  - frequently the no comm messages show up... (if we can catch them)
- Consider the class method "of this class" function permissions.... (and write tests...)
- Think about whether there's alternatives to creating new figures each time...
- Consider adding a step to the integer parameter...
- Idea!
  - We could make fig=?, ax=? arguments optional for the plot function and add a
    "recycle_figure: bool = False" flag be part of the deploy API. This way, an
    advanced user that wants snappy responsivity or complex figure management can
    do so, but the default is for the user to generate a new figure object each time.
- I've updated some rules for parameters -- need to make tests for empty options on selection / multiple selections
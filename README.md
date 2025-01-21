# syd

[![PyPI version](https://badge.fury.io/py/syd.svg)](https://badge.fury.io/py/syd)
[![Tests](https://github.com/landoskape/syd/actions/workflows/tests.yml/badge.svg)](https://github.com/landoskape/syd/actions/workflows/tests.yml)
[![Documentation Status](https://readthedocs.org/projects/shareyourdata/badge/?version=latest)](https://shareyourdata.readthedocs.io/en/latest/?badge=latest)
[![codecov](https://codecov.io/gh/landoskape/syd/branch/main/graph/badge.svg)](https://codecov.io/gh/landoskape/syd)

A package to help you share your data!

Have you ever wanted to look through all your data really quickly interactively? Of course you have. Mo data mo problems, but only if you don't know what to do with it. And that starts with looking at your data. And that's why syd stands for show your data! 

Syd is a system for creating a data viewing GUI that you can view on a web-browser. And guess what? Since it opens on a web browser, you can even open it on any other computer on your local network! For example, your PI. Gone are the days of single random examples that they make infinitely stubborn conclusions about. Now, you can look at all the examples, quickly and easily, on their computer. And that's why syd stands for share your data!

Okay, so what is it? Syd is an automated system to convert some basic python plotting code into an interactive GUI. This is great, because it means you only have to think about what you want to plot and what you want to be interactive, syd does the work to make an interface. There's some small overhead for learning how to prepare your data to work with syd, but we provide some templates to make it easy. You know what that means? That means you get to focus on _thinking_ about your data, rather than spending time writing code to look at it. And that's why syd stands for Science, Yes! Datum!

## Installation

```bash
pip install syd
```

## Quick Start
Right now the only way to use it is in a jupyter notebook. More deployments coming soon!
```python
# In a notebook! 
from syd import InteractiveViewer
import matplotlib.pyplot as plt
import numpy as np
class WaveViewer(InteractiveViewer):
    def __init__(self):
        self.add_float('amplitude', value=1.0, min_value=0, max_value=2)
        self.add_float('frequency', value=1.0, min_value=0.1, max_value=5)

    def plot(self, state):
        fig, ax = plt.subplots()
        x = np.linspace(0, 10, 1000)
        y = state['amplitude'] * np.sin(state['frequency'] * x)
        ax.plot(x, y)
        return fig

viewer = WaveViewer()
viewer.deploy()
```

## Documentation

Full documentation is available at [shareyourdata.readthedocs.io](https://shareyourdata.readthedocs.io/).

Key features:
- Create interactive matplotlib visualizations with minimal code
- Support for various parameter types (sliders, dropdowns, checkboxes, etc.)
- Real-time updates as parameters change
- Works in Jupyter notebooks and can be shared over local network

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
7. Open a Pull Request

Please make sure to update tests as appropriate and adhere to the existing coding style.
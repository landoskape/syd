import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


class SineWaveViewer:
    def __init__(self, frequency=1.0, amplitude=1.0, offset=0.0, color="#FF0000"):
        self.frequency = frequency
        self.amplitude = amplitude
        self.offset = offset
        self.color = color

    def plot(self):
        fig, ax = plt.subplots()
        x = np.linspace(0, 2 * np.pi, 1000)
        y = self.amplitude * np.sin(self.frequency * x) + self.offset
        ax.plot(x, y, color=self.color)
        return fig

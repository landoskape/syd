import time
import numpy as np
import matplotlib.pyplot as plt
from syd import Viewer


class ViewerWithData(Viewer):
    def __init__(self):
        # In the object constructor, we load the data as an attribute.
        # This way the data is "ready" once you've created the viewer object.
        self.dataset = [np.random.randn(100, 10000) for _ in range(10)]

        # simulate a slow dataload... (1 second is enough delay to notice but not be super annoying for the example....)
        time.sleep(3)

        # Add the syd parameters as usual
        self.add_integer(
            "dataset_index",
            value=0,
            min=0,
            max=len(self.dataset) - 1,
        )
        self.add_integer(
            "sample_index",
            value=0,
            min=0,
            max=self.dataset[0].shape[0] - 1,
        )

    def filter_data(self, c_sample):
        # You might want to do some processing of the data here. Filtering is fast, but
        # can be slow if you have a lot of data. Filtering on-demand is a great way to
        # get good quick viewer performance while not having to load and filter the data
        # upfront!! (You can imagine this is useful for all kinds of data processing!)
        return c_sample[c_sample > 0]

    def plot(self, state):
        # Now that we're using the class version -- self.dataset is available from the plot function.
        c_data = self.dataset[state["dataset_index"]]
        c_sample = c_data[state["sample_index"]]
        filtered_sample = self.filter_data(c_sample)
        fig = plt.figure(figsize=(4, 4))
        ax = plt.gca()

        # HELLO USER
        # TRY CHANGING THE COLOR OF THE LINE AND REDEPLOYING WITHOUT CONSTRUCTING THE NEW VIEWER OBJECT!!!
        # (for 3-data_loading.ipynb)
        ax.plot(filtered_sample, color="k")
        return fig

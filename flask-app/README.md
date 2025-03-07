# Sine Wave Visualizer

A simple Flask web application that allows users to visualize and customize sine waves by adjusting frequency, amplitude, offset, and color parameters.

## Features

- Interactive controls for customizing sine wave parameters:
  - Frequency (0.1 to 10)
  - Amplitude (0.1 to 5)
  - Offset (-5 to 5)
  - Color (any valid HTML color)
- Real-time plot updates as parameters change
- Responsive design that works on various screen sizes

## Requirements

- Python 3.6+
- Flask
- Matplotlib
- NumPy

## Installation

1. Clone this repository or navigate to the project directory
2. Install the required packages:

```
pip install flask matplotlib numpy
```

## Running the Application

From the project root directory, run:

```
python -m flask
```

Or alternatively:

```
cd flask
python app.py
```

Then open your web browser and navigate to http://localhost:5000

## How It Works

- The Flask backend generates matplotlib plots of sine waves based on user-specified parameters
- The frontend provides a user-friendly interface with sliders and input fields for adjusting the parameters
- When parameter values change, an AJAX request is sent to the server to generate a new plot
- The server returns the plot as a PNG image that is displayed in real-time 
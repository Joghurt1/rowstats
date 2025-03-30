# Stroke Data Analyzer

A Python tool for processing and visualizing rowing stroke data from CSV files. It reads raw data, processes movement direction, and generates an interactive visualization for performance analysis.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage Guide](#usage-guide)
- [Hacking Guide](#hacking-guide)
- [License](#license)

## Features

✅ Reads stroke data from CSV files  
✅ Cleans and processes data automatically  
✅ Identifies boat movement direction (up/down)  
✅ Generates an interactive HTML visualization  
✅ Works with multiple CSV files  

## Installation

1. Install [Python](https://www.python.org/) (version 3.8 or later).  
2. Download or clone this repository:
   ```sh
   git clone https://github.com/derdilla/rowstats.git
   cd stroke-data-analyzer
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Usage Guide

1. Place your CSV files inside the `csv-samples/` directory.  
2. Run the program:
   ```sh
   python main.py
   ```
3. After the script finishes, open `index.html` in a web browser to view the results.

## Hacking Guide

Want to modify or improve the tool? Here’s how:

### Understanding the Code Structure

- `main.py` → The main script that processes data and generates the visualization.
- `requirements.txt` → Lists all required dependencies.
- `csv-samples/` → Folder where you should place your CSV files.
- `index.html` → The output visualization file.

### Making Changes

#### 1. Modify the Data Processing Logic
- Open `main.py` and locate the `split_frames()` function.
- This function determines the boat’s movement direction and applies filtering.
- Modify it to adjust stroke rate thresholds, data cleaning logic, or direction detection.

#### 2. Customize the Visualization
- Locate the `draw()` function in `main.py`.
- Modify the Altair chart settings to change colors, axes, or tooltips.
- Save changes and re-run `python main.py`.

#### 3. Add New Features
- Want to add extra analysis, like heart rate trends? Find the section where `get_table()` extracts CSV data.
- Extend the code to include new metrics in the visualization.

### Debugging & Testing
- If something goes wrong, check for error messages in the console.
- Use `print()` statements or Python’s built-in `logging` module to debug.
- Test your changes with sample CSV files before running large datasets.

## License

This project is licensed under the MIT License. Feel free to use, modify, and distribute it as you like!


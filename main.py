import logging
import os
from datetime import datetime
from io import StringIO
from typing import List

import altair as alt
import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def get_table(file_path: str) -> pd.DataFrame:
    """
    Reads the provided CSV file and returns a DataFrame containing the table after the
    'Per-Stroke Data:' header line.

    Args:
        file_path: Path to the CSV file.

    Returns:
        A pandas DataFrame with the parsed data.

    Raises:
        ValueError: If the expected header is not found.
    """
    logging.info(f"Reading file {file_path}")
    try:
        with open(file_path, "r") as f:
            content = f.read()
        # Ensure the split text is present
        marker = 'Per-Stroke Data:\n'
        if marker not in content:
            raise ValueError(f"Expected marker '{marker}' not found in {file_path}")
        # Read the portion after the marker into a DataFrame
        csv_content = content.split(marker, 1)[1]
        df = pd.read_csv(StringIO(csv_content))

        # Remove data that is never read
        df = df.drop(columns=['Power','Catch','Slip','Finish','Wash','Work', "Distance (IMP)", "Split (IMP)", "Speed (IMP)", "Distance/Stroke (IMP)", "Heart Rate", "Force Avg", "Force Max", "Max Force Angle", "GPS Lat.", "GPS Lon."])

        return df
    except Exception as e:
        logging.error(f"Error processing file {file_path}: {e}")
        raise


def split_frames(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processes the DataFrame by adding a 'dir' column to indicate the boat's movement direction
    ('up', 'down', or 'turning'). Rows marked as 'turning' are removed, and numeric columns are
    cleaned based on specific criteria.

    Args:
        df: DataFrame containing raw stroke data.

    Returns:
        A cleaned DataFrame with a new 'dir' column and numeric conversions.
    """
    logging.info(f"Splitting dataframes with {df.shape[0]} rows")

    directions = []
    is_up = True
    pending_transition = True
    elements_since_transition = 0

    # Process each row and determine direction based on the 'Split (GPS)' time
    for idx, row in df.iterrows():
        try:
            split_time = datetime.strptime(row['Split (GPS)'], '%H:%M:%S.%f')
        except (ValueError, KeyError) as e:
            logging.error(f"Row {idx}: Invalid or missing 'Split (GPS)' value: {row.get('Split (GPS)', None)}")
            directions.append('turning')
            continue

        if split_time.minute > 12 and not pending_transition:
            pending_transition = True
        elif split_time.minute <= 12 and pending_transition:
            if elements_since_transition >= 8:
                is_up = not is_up
            elements_since_transition = 0
            pending_transition = False

        if pending_transition:
            directions.append('turning')
        else:
            elements_since_transition += 1
            directions.append('up' if is_up else 'down')

    df = df.copy()
    df['dir'] = directions
    # Filter out rows where direction is 'turning'
    df = df[df['dir'] != 'turning'].copy()

    # Convert columns to numeric, coercing errors to NaN
    df['Distance (GPS)'] = pd.to_numeric(df['Distance (GPS)'], errors='coerce')
    df['Stroke Rate'] = pd.to_numeric(df['Stroke Rate'], errors='coerce')

    # Insert NaN where gaps are too large or stroke rates are out of acceptable bounds
    df.loc[df['Distance (GPS)'].diff() > 100, ['Distance (GPS)', 'Stroke Rate']] = np.nan
    df.loc[df['Stroke Rate'] < 10, ['Distance (GPS)', 'Stroke Rate']] = np.nan
    df.loc[df['Stroke Rate'] > 34, ['Distance (GPS)', 'Stroke Rate']] = np.nan

    return df


def create_joined_dataset(file_names: List[str]) -> pd.DataFrame:
    """
    Reads multiple CSV files, processes each using the get_table and split_frames functions, and
    concatenates them into a single DataFrame. A 'file_name' column is added to track the source.

    Args:
        file_names: List of CSV file paths.

    Returns:
        A concatenated pandas DataFrame of all processed files.
    """
    logging.info(f"Processing {len(file_names)} files:")
    datasets = []
    for file_path in file_names:
        try:
            parsed_data = get_table(file_path)
            # Remove header row if needed (assuming first row is unwanted)
            parsed_data = parsed_data.iloc[1:].copy()
            parsed_data = split_frames(parsed_data)
            parsed_data['file_name'] = os.path.basename(file_path)
            datasets.append(parsed_data)
        except Exception as e:
            logging.error(f"Skipping file {file_path} due to error: {e}")

    if not datasets:
        raise ValueError("No valid datasets were created from the provided files.")
    
    logging.info(f"Successfully created unified dataset from {len(datasets)} files")
    return pd.concat(datasets, ignore_index=True)


def draw(data: pd.DataFrame) -> None:
    """
    Generates and saves an interactive Altair visualization with two components:
      - A faceted line chart showing stroke rate vs. GPS distance by boat direction.
      - A bar chart summarizing the maximum GPS distance per file.

    Args:
        data: DataFrame containing the processed stroke data.
    """
    alt.renderers.enable("html")

    # Selection for interactive toggling by file_name
    multi = alt.selection_point(fields=['file_name'])

    # Faceted line chart
    line_chart = (
        alt.Chart(data)
        .mark_line(strokeWidth=2)
        .add_params(multi)
        .encode(
            x=alt.X('Distance (GPS):Q', title='Distance (m)', scale=alt.Scale(domain=[0, 14000]), axis=alt.Axis(labelAngle=-45)),
            y=alt.Y('Stroke Rate:Q', title='Stroke Rate (spm)', scale=alt.Scale(domain=[10, 35])),
            tooltip=alt.Tooltip('Stroke Rate:Q', title='Stroke Rate (spm)'),
            color=alt.condition(multi, 'file_name:N', alt.value('lightgray')),
            detail='group:N'
        )
        .properties(width=1200, height=250)
        .facet(row=alt.Row('dir:N', title="Direction"))
    )

    # Bar chart for maximum GPS distance by file
    bar_chart = (
        alt.Chart(data)
        .mark_bar(size=30)
        .encode(
            y=alt.Y('file_name:N', title='File Name', sort='-y'),
            x=alt.X('max(Distance (GPS)):Q', title='Distance (m)', scale=alt.Scale(zero=True)),
            color=alt.Color('file_name:N', legend=None, scale=alt.Scale(scheme='tableau20')),
            tooltip=[alt.Tooltip('file_name:N', title='File Name'), alt.Tooltip('max(Distance (GPS)):Q', title='Max GPS Distance (m)')]
        )
        .add_params(multi)
        .properties(width=1200, height=400, title="Max GPS Distance by File")
    )

    # Save the composed chart as an HTML file with SVG renderer embedded
    (line_chart & bar_chart).save('index.html', embed_options={'renderer': 'svg'})
    logging.info("Visualization saved to 'index.html'")


def main() -> None:
    """
    Main function that aggregates CSV files from the 'csv-samples' directory,
    processes them, and generates visualizations.
    """
    directory = 'csv-samples'
    try:
        files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.csv')]
    except FileNotFoundError:
        logging.error(f"Directory '{directory}' not found.")
        return

    if not files:
        logging.error("No CSV files found in the specified directory.")
        return

    try:
        data = create_joined_dataset(files)
        draw(data)
    except Exception as e:
        logging.error(f"An error occurred during processing: {e}")


if __name__ == '__main__':
    main()

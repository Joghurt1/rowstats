from datetime import datetime
from io import StringIO
from typing import List

import altair as alt
import pandas as pd
import numpy as np
import os


def get_table(file):
    with open(file, "r") as file:
        content = file.read()
    content = content.split('Per-Stroke Data:\n')[1]
    content = pd.read_csv(StringIO(content))
    return content
 
def split_frames(df):
    """
    Add a 'direction' column to the dataframe indicating whether the boat is going 'up', 'down', or 'turning'.
    """
    is_up = True
    pending_transition = True
    elements_since_transition = 0
 
    # Process each row
    for i, row in df.iterrows():
        split_time = datetime.strptime(row['Split (GPS)'], '%H:%M:%S.%f')
 
        if split_time.minute > 12 and not pending_transition:
            pending_transition = True
        elif split_time.minute <= 12 and pending_transition:
            if elements_since_transition >= 8:
                is_up = not is_up
            elements_since_transition = 0
            pending_transition = False
        if pending_transition:
            df.at[i, 'dir'] = 'turning'
        else:
            elements_since_transition += 1
            df.at[i, 'dir'] = 'up' if is_up else 'down'

    # remove turning columns
    df = df[df['dir'] != 'turning']

    # insert nan where distance gap is to big
    pd.options.mode.copy_on_write = True
    df['Distance (GPS)'] = pd.to_numeric(df['Distance (GPS)'])
    df['Stroke Rate'] = pd.to_numeric(df['Stroke Rate'])
    df.loc[df['Distance (GPS)'].diff() > 100, ['Distance (GPS)', 'Stroke Rate']] = np.nan
    df.loc[df['Stroke Rate'] < 10 , ['Distance (GPS)', 'Stroke Rate']] = np.nan
    df.loc[df['Stroke Rate'] > 34 , ['Distance (GPS)', 'Stroke Rate']] = np.nan
    return df

def create_joined_dataset(file_names: List[str]) -> pd.DataFrame:
    results = []
    for file in file_names:
        parsed_data = get_table(file)
        parsed_data = parsed_data[1:]
        parsed_data = split_frames(parsed_data)
        # set 'file_name' column
        parsed_data['file_name'] = file
        results.append(parsed_data)
    return pd.concat(results, ignore_index=True)

def draw(data):
    alt.renderers.enable("html")

    # draw 2 lines allow toggling depending on 'dir' parameter and limit the size
    multi = alt.selection_point(fields=['file_name'])
    chart = alt.Chart(data).mark_line(
        strokeWidth=2
    ).add_params(
        multi
    ).encode(
        x=alt.X('Distance (GPS)', title='Distance (m)', scale=alt.Scale(domain=[0, 14000]), axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('Stroke Rate', title='Stroke Rate (spm)', scale=alt.Scale(domain=[10, 35])), # alt.Y('Split (GPS)', title='Split (GPS)'),
        tooltip=alt.Tooltip('Stroke Rate', title='Stroke Rate (spm)'),
        # set the color based on the 'file_name' column, allowing selection
        color=alt.condition(multi, 'file_name:N', alt.value('lightgray')),
        detail='group:N'
    ).properties(
        width=1200,
        height=250,
    ).facet(
        row='dir:N'  # Creates separate charts for 'up' and 'down'
    )

    length = alt.Chart(data).mark_bar(size=30).encode(
        y=alt.Y('file_name:N', title='File Name', sort='-y'),  # Sort by distance
        x=alt.X('max(Distance (GPS)):Q', title='Distance (m)', scale=alt.Scale(zero=True)),  
        color=alt.Color('file_name:N', legend=None, scale=alt.Scale(scheme='tableau20')),  
        tooltip=['file_name:N', 'max(Distance (GPS)):Q']  # Add tooltips
    ).add_params(
        multi
    ).properties(
        width=1200,
        height=400,
        title="Max GPS Distance by File"
    )

    (chart & length).save('index.html', embed_options={'renderer':'svg'})

 
def main():
    # Interval,     Distance (GPS),     Distance (IMP),     Elapsed Time,Split (GPS),Speed (GPS),Split (IMP),Speed (IMP),Stroke Rate,Total Strokes,Distance/Stroke (GPS),Distance/Stroke (IMP),Heart Rate,Power,Catch,Slip,Finish,Wash,Force Avg,Work,Force Max,Max Force Angle,GPS Lat.,GPS Lon.
    # (Interval),   (Meters),           (Meters),           (HH:MM:SS.tenths),(/500),(M/S),(/500),(M/S),(SPM),(Strokes),(Meters),(Meters),(BPM),(Watts),(Degrees),(Degrees),(Degrees),(Degrees),(Newtons),(Joules),(Newtons),(Degrees),(Degrees),(Degrees)
    
    # get a list of all files in csv-samples
    files = ['csv-samples/' + f for f in os.listdir('csv-samples') if f.endswith('.csv')]

    # create a dataset of all files in csv-samples, by indexing the dir
    data = create_joined_dataset(files)
    draw(data)

 
if __name__ == '__main__':
    main()

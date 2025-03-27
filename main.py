from datetime import datetime
from io import StringIO
from typing import List

import altair as alt
import pandas as pd


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
    chart = alt.Chart(data).mark_line().encode(
        x=alt.X('Distance (GPS)', title='Distance (m)', axis=alt.Axis(
            values=range(0, 1000, 100),
            labelAngle=0  # Keep labels horizontal (optional)
        )),
        y=alt.Y('Stroke Rate', title='Stroke Rate (spm)'), # alt.Y('Split (GPS)', title='Split (GPS)'),
        tooltip=alt.Tooltip('Stroke Rate', title='Stroke Rate (spm)'),
        # set the color based on the 'file_name' column
        color='file_name:N',
    ).properties(
        width=800,
        height=400,
    ).facet(
        column='dir:N'  # Creates separate charts for 'up' and 'down'
    )

    chart.save('index.html', embed_options={'renderer':'svg'})

 
def main():
    # Interval,     Distance (GPS),     Distance (IMP),     Elapsed Time,Split (GPS),Speed (GPS),Split (IMP),Speed (IMP),Stroke Rate,Total Strokes,Distance/Stroke (GPS),Distance/Stroke (IMP),Heart Rate,Power,Catch,Slip,Finish,Wash,Force Avg,Work,Force Max,Max Force Angle,GPS Lat.,GPS Lon.
    # (Interval),   (Meters),           (Meters),           (HH:MM:SS.tenths),(/500),(M/S),(/500),(M/S),(SPM),(Strokes),(Meters),(Meters),(BPM),(Watts),(Degrees),(Degrees),(Degrees),(Degrees),(Newtons),(Joules),(Newtons),(Degrees),(Degrees),(Degrees)
    data = create_joined_dataset(['csv-samples/SpdCoach 3039416 20250307 1205PM.csv', 'csv-samples/SpdCoach 3039416 20250308 0240PM.csv'])
    draw(data)

 
if __name__ == '__main__':
    main()

import pandas as pd
from typing import Dict, List, Any, Union
from datetime import datetime
from pprint import pprint
from io import StringIO
 
def get_table(file):
    content = ''
    with open(file, "r") as file:
        content = file.read()
    content = content.split('Per-Stroke Data:\n')[1]
    content = pd.read_csv(StringIO(content))
    return content
 
def split_frames(df):
    '''Create 2 dataframes depending on whether the boat is going up or down'''
    is_up = True
    up_df = pd.DataFrame()
    down_df = pd.DataFrame()
    pending_transition = False
    elements_since_transition = 0
 
    # Process each row
    for _, row in df.iterrows():
        split_time = datetime.strptime(row['Split (GPS)'], '%H:%M:%S.%f')
 
        if split_time.minute > 10 and not pending_transition:
            pending_transition = True
        elif split_time.minute <= 10 and pending_transition:
            if elements_since_transition >= 5:
                is_up = not is_up
            elements_since_transition = 0
            pending_transition = False
 
        if not pending_transition:
            elements_since_transition +=1
            if is_up:
                up_df = pd.concat([up_df, row.to_frame().T], ignore_index=True)
            else:
                down_df = pd.concat([down_df, row.to_frame().T], ignore_index=True)
    return (up_df, down_df)
 
 
def session_stats(data):
    duration_min = distance_m = stroke_count = 0
    for x in data:
 
 
def main():
    # Interval,     Distance (GPS),     Distance (IMP),     Elapsed Time,Split (GPS),Speed (GPS),Split (IMP),Speed (IMP),Stroke Rate,Total Strokes,Distance/Stroke (GPS),Distance/Stroke (IMP),Heart Rate,Power,Catch,Slip,Finish,Wash,Force Avg,Work,Force Max,Max Force Angle,GPS Lat.,GPS Lon.
    # (Interval),   (Meters),           (Meters),           (HH:MM:SS.tenths),(/500),(M/S),(/500),(M/S),(SPM),(Strokes),(Meters),(Meters),(BPM),(Watts),(Degrees),(Degrees),(Degrees),(Degrees),(Newtons),(Joules),(Newtons),(Degrees),(Degrees),(Degrees)
    parsed_data = get_table('data/csv/SpdCoach 3039416 20250307 1205PM.csv')
    parsed_data = parsed_data[1:]
    up,down = split_frames(parsed_data)
    print(f'Parsed data: {len(up)} up / {len(down)} down.')
 
 
if __name__ == '__main__':
    main()

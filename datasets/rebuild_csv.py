import pandas as pd

df = pd.read_csv('vanet_traffic_data.csv')

# Remove old emergency_vehicle column if exists
if 'emergency_vehicle' in df.columns:
    df.drop(columns=['emergency_vehicle'], inplace=True)

# Add fresh emergency_vehicle column — all 0 by default
df['emergency_vehicle'] = 0

# 5 emergency vehicles, one every 3 minutes
# Dataset has 12 rows; simulation_interval = 1000ms = 1 tick/sec
# 3 min = 180 ticks → but dataset is small (12 rows), so we spread 5 across 12 rows
# Place at rows 0, 2, 5, 7, 10 (roughly every 2-3 rows apart)
ev_indices = [0, 2, 5, 7, 10]
for i in ev_indices:
    df.at[i, 'emergency_vehicle'] = 1

df.to_csv('vanet_traffic_data.csv', index=False)
print("Done. Emergency vehicle column added with 5 vehicles.")
print(df[['timestamp', 'road_segment_id', 'emergency_vehicle']].to_string())

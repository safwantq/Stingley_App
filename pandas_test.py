import pandas as pd
import sqlite3

# time conversion using dataframes (from 24 system to 12 system)

conn = sqlite3.connect('/home/safwanpi/databases/test3_microphone_data.db')

query = f"SELECT time FROM Table_1"
query2 = f"SELECT mic_reading FROM Table_1"

df = pd.read_sql_query(query, conn)
df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S')
df['time_12'] = df['time'].dt.strftime('%I:%M:%S %p')

conn.close()

print(df)

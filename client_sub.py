from datetime import datetime
import paho.mqtt.client as mqtt
import sqlite3
import os

db_path = '/home/safwanpi/databases/test3_microphone_data.db'

MQTT_ADDRESS = '10.42.0.1'
MQTT_TOPIC_ALL = 'test/#'
table = 0
noise_level = 0
avg_noise_level = 0
mx = 0
mn = 0

def insert_data(table_name, mic_reading):
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for i in range(1, 19):
        new_table = f'Table_{i}'
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {new_table} (
            time TEXT,
            date TEXT,
            mic_reading REAL
        );
        ''')
        # Commit the changes and close the connection
        conn.commit()
    # Get current time and date
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    current_date = now.strftime("%Y-%m-%d")
    
    # Prepare the SQL query to insert data
    query = f"INSERT INTO {table_name} (time, date, mic_reading) VALUES (?, ?, ?)"
    data_tuple = (current_time, current_date, mic_reading)
    try:
        # Execute the query
        cursor.execute(query, data_tuple)
        # Commit the transaction
        conn.commit()
        print(f"Data inserted into {table_name}: {data_tuple}")
    except sqlite3.Error as error:
        print(f"Failed to insert data into {table_name}: {error}")
    finally:
        # Close the connection
        conn.close()

def on_connect(client, userdata, flags, rc):
    print('Connected with result code ' + str(rc))
    client.subscribe(MQTT_TOPIC_ALL)

def on_message(client, userdata, msg):
    print(msg.topic + ' ' + str(msg.payload))
    print(datetime.now())
    message = msg.payload.decode('utf-8')
    split_message = message.split()
    for i in range(1, len(split_message), 2):
        split_message[i] = split_message[i].replace(',', ' ')
        split_message[i] = split_message[i].replace('\'', ' ')
        print(split_message[i])
    table_number = f"Table_{split_message[1]}"
    print(table_number)
    noise_level = int(split_message[3])
    print("Noise Level: " + split_message[3])
    avg_noise_level = int(split_message[5])
    print("Average: " + split_message[5])
    mx = int(split_message[7])
    print("Maximum: " + split_message[7])
    mn = int(split_message[9])
    print("Minimum: " + split_message[9])
    insert_data(table_number, noise_level)

def main():
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    mqtt_client.connect(MQTT_ADDRESS, 1883)
    mqtt_client.loop_forever()

if __name__ == '__main__':
    print('MQTT to SQLite DB bridge')
    main()

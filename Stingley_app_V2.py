import sqlite3
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import threading
import numpy as np
import pandas as pd

# Specify the y-values for the horizontal dashed lines
# noisy state is around 800
maximum_threshold = 850  # Rename threshold_value to maximum_threshold 
moderate_threshold = 400   # Add moderate_threshold
# Global variable to store the selected database path
db_path = None
root = None  # Initialize root as a global variable
# Connect to the database (initialize only, not create it)
def connect_db():
    if db_path is None:
        raise ValueError("Database path is not set.")
    return sqlite3.connect(db_path)

# Convert 12-hour format to 24-hour format for database queries
def convert_to_24_hour(hour, minute, period):
    if period == "PM" and hour != 12:
        hour += 12
    elif period == "AM" and hour == 12:
        hour = 0
    return f"{hour:02}:{minute:02}:00"

# Query the database based on the table and date range
def query_data(table, start_datetime, end_datetime, callback):
    conn = connect_db()
    cursor = conn.cursor()

    query = f"SELECT time, date, mic_reading FROM {table} WHERE datetime(date || ' ' || time) BETWEEN ? AND ?"
    cursor.execute(query, (start_datetime, end_datetime))
    data = cursor.fetchall()

    conn.close()
    callback(data, table)

# Plot data for individual or multiple tables
def plot_data(data, table, message_label, multiple_tables=False, all_data=None):
    if not data and not multiple_tables:
        message_label.config(text="No data found for the selected range.", fg="red")
        return

    if multiple_tables:
        # Create a single plot for multiple tables with different colors
        plt.figure(figsize=(9, 6))
        plt.title('Microphone Readings for Selected Tables', fontsize=16)

        # Get a colormap with enough distinct colors
        num_colors = len(all_data)
        cmap = plt.get_cmap('tab20')  # Or any other suitable colormap
        colors = [cmap(i) for i in np.linspace(0, 1, num_colors)]

        for idx, (data, table) in enumerate(all_data):
            if not data:
                continue
            # Extract times and mic_readings for each table
            times = [datetime.strptime(f'{row[1]} {row[0]}', '%Y-%m-%d %H:%M:%S') for row in data]
            mic_readings = [row[2] for row in data]

            # Plot each table's data with a different color
            plt.plot(times, mic_readings, label=f'{table}', color=colors[idx % len(colors)], linewidth=1)

        # **Add the horizontal dashed lines**
        plt.axhline(y=maximum_threshold, color='red', linestyle='--', linewidth=1, label=f'Maximum Threshold ({maximum_threshold})')
        plt.axhline(y=moderate_threshold, color='orange', linestyle='--', linewidth=1, label=f'Moderate Threshold ({moderate_threshold})')

        # Formatting the x-axis
        plt.xlabel('Date and Time', fontsize=12)
        plt.ylabel('Microphone Levels', fontsize=12)
        plt.grid(True)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.gcf().autofmt_xdate()

        # Add a legend to identify each table
        plt.legend(loc='upper right', fontsize=10, title="Tables and Thresholds", title_fontsize=12)

        # Show the plot
        plt.tight_layout()
        plt.show()
        return

    # Single table plot
    message_label.config(text="Plotting data...", fg="green")
    times = [datetime.strptime(f'{row[1]} {row[0]}', '%Y-%m-%d %H:%M:%S') for row in data]

    mic_readings = [row[2] for row in data]

    plt.figure(figsize=(9, 6))
    plt.plot(times, mic_readings, label=f'{table} Mic Levels')

    # **Add the horizontal dashed lines**
    plt.axhline(y=maximum_threshold, color='red', linestyle='--', linewidth=1, label=f'Maximum Threshold ({maximum_threshold})')
    plt.axhline(y=moderate_threshold, color='orange', linestyle='--', linewidth=1, label=f'Moderate Threshold ({moderate_threshold})')

    plt.xlabel('Date and Time')
    plt.ylabel('Microphone Levels')
    plt.title(f'Microphone Readings for {table}')
    plt.grid(True)
    plt.gcf().autofmt_xdate()
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.legend()
    plt.show()

# Export the plot
def export_plot(data, table, message_label, multiple_tables=False, all_data=None):
    if not data and not multiple_tables:
        message_label.config(text="No data to export.", fg="red")
        return

    if multiple_tables:
        # File dialog to save the plot as a PNG file
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")], title="Save plot")
        if file_path:
            plt.figure(figsize=(9, 6))
            plt.title('Microphone Readings for Selected Tables', fontsize=16)

            # Get a colormap with enough distinct colors
            num_colors = len(all_data)
            cmap = plt.get_cmap('tab20')  # Or any other suitable colormap
            colors = [cmap(i) for i in np.linspace(0, 1, num_colors)]

            for idx, (data, table) in enumerate(all_data):
                if not data:
                    continue
                # Extract times and mic_readings for each table
                times = [datetime.strptime(f'{row[1]} {row[0]}', '%Y-%m-%d %H:%M:%S') for row in data]
                mic_readings = [row[2] for row in data]

                # Plot each table's data with a different color
                plt.plot(times, mic_readings, label=f'{table}', color=colors[idx % len(colors)], linewidth=1)

            # **Add the horizontal dashed lines**
            plt.axhline(y=maximum_threshold, color='red', linestyle='--', linewidth=1, label=f'Maximum Threshold ({maximum_threshold})')
            plt.axhline(y=moderate_threshold, color='orange', linestyle='--', linewidth=1, label=f'Moderate Threshold ({moderate_threshold})')

            # Formatting the x-axis
            plt.xlabel('Date and Time', fontsize=12)
            plt.ylabel('Microphone Levels', fontsize=12)
            plt.grid(True)
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
            plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
            plt.gcf().autofmt_xdate()

            # Add a legend to identify each table
            plt.legend(loc='upper right', fontsize=10, title="Tables and Thresholds", title_fontsize=12)

            # Save the plot
            plt.tight_layout()
            plt.savefig(file_path)
            message_label.config(text=f"Plot saved as {file_path}", fg="green")
        return

    # Single table export
    file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")], title=f"Save plot for {table}")
    if file_path:
        times = [datetime.strptime(f'{row[1]} {row[0]}', '%Y-%m-%d %H:%M:%S') for row in data]
        mic_readings = [row[2] for row in data]

        plt.figure(figsize=(9, 6))
        plt.plot(times, mic_readings, label=f'{table} Mic Levels')

        # **Add the horizontal dashed lines**
        plt.axhline(y=maximum_threshold, color='red', linestyle='--', linewidth=1, label=f'Maximum Threshold ({maximum_threshold})')
        plt.axhline(y=moderate_threshold, color='orange', linestyle='--', linewidth=1, label=f'Moderate Threshold ({moderate_threshold})')

        plt.xlabel('Date and Time')
        plt.ylabel('Microphone Levels')
        plt.title(f'Microphone Readings for {table}')
        plt.grid(True)
        plt.gcf().autofmt_xdate()
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        plt.legend()
        plt.savefig(file_path)
        message_label.config(text=f"Plot saved as {file_path}", fg="green")

# Safely update the GUI on the main thread
def safe_update_gui(root, callback, data, table, message_label, multiple_tables=False, all_data=None, tables_to_process=None):
    root.after(0, callback, data, table, message_label, multiple_tables, all_data, tables_to_process)

# Function to run a background query
def run_query_in_background(root, table, start_datetime, end_datetime, callback, message_label, multiple_tables=False, all_data=None, tables_to_process=None):
    def thread_func():
        query_data(table, start_datetime, end_datetime, lambda data, table: safe_update_gui(root, callback, data, table, message_label, multiple_tables, all_data, tables_to_process))
    threading.Thread(target=thread_func).start()

# Function to let the user select the database file
def select_database():
    global db_path
    db_path = filedialog.askopenfilename(title="Select Database", filetypes=[("SQLite Database", "*.db")])
    if db_path:
        message_label.config(text=f"Database selected: {db_path}", fg="green")
    else:
        message_label.config(text="No database selected.", fg="red")

def create_datetime_selector(root, row, label_text, default_datetime=None):
    label = tk.Label(root, text=label_text)
    label.grid(row=row, column=0, sticky='w')

    # If default_datetime is provided, use it; else, set fields to empty
    if default_datetime is not None:
        # Date fields for year, month, day
        year_var = tk.StringVar(value=str(default_datetime.year))
        month_var = tk.StringVar(value=str(default_datetime.month).zfill(2))
        day_var = tk.StringVar(value=str(default_datetime.day).zfill(2))

        # Time picker (12-hour format)
        hour_24 = default_datetime.hour
        hour_12 = hour_24 % 12
        if hour_12 == 0:
            hour_12 = 12
        hour_var = tk.StringVar(value=f'{hour_12:02}')
        minute_var = tk.StringVar(value=f'{default_datetime.minute:02}')
        period = 'AM' if hour_24 < 12 else 'PM'
        period_var = tk.StringVar(value=period)
    else:
        # Set variables to empty strings
        year_var = tk.StringVar(value='')
        month_var = tk.StringVar(value='')
        day_var = tk.StringVar(value='')
        hour_var = tk.StringVar(value='')
        minute_var = tk.StringVar(value='')
        period_var = tk.StringVar(value='AM')  # Default to 'AM' for period

    # Create the widgets
    year_entry = tk.Entry(root, textvariable=year_var, width=5)
    year_entry.grid(row=row, column=1)
    year_label = tk.Label(root, text="Year")
    year_label.grid(row=row, column=2)

    month_entry = tk.Entry(root, textvariable=month_var, width=3)
    month_entry.grid(row=row, column=3)
    month_label = tk.Label(root, text="Month")
    month_label.grid(row=row, column=4)

    day_entry = tk.Entry(root, textvariable=day_var, width=3)
    day_entry.grid(row=row, column=5)
    day_label = tk.Label(root, text="Day")
    day_label.grid(row=row, column=6)

    # Time picker (12-hour format)
    hour_dropdown = ttk.Combobox(root, textvariable=hour_var, width=3, values=[f'{i:02}' for i in range(1, 13)])
    hour_dropdown.grid(row=row, column=7)

    minute_dropdown = ttk.Combobox(root, textvariable=minute_var, width=3, values=[f'{i:02}' for i in range(60)])
    minute_dropdown.grid(row=row, column=8)

    period_dropdown = ttk.Combobox(root, textvariable=period_var, width=3, values=["AM", "PM"])
    period_dropdown.grid(row=row, column=9)

    return (year_var, month_var, day_var), hour_var, minute_var, period_var
# Create the GUI
def create_gui():
    global message_label
    global root
    root = tk.Tk()
    root.title("Stingley's Plotter")
    # root.iconbitmap('path_to_icon.ico')
    
    window_width = 900
    window_height = 400
    
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    center_x = int(screen_width/2 - window_width/2)
    center_y = int(screen_height/2 - window_height/2)
    
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    
    style = ttk.Style(root)
    style.theme_use('clam')  # Options include 'clam', 'alt', 'default', 'classic'
    
    
    # Button to select the database file
    db_button = tk.Button(root, text="Select Database", command=select_database)
    db_button.grid(row=0, column=0, padx=10, pady=10, sticky='w')

    # Create checkboxes for table selection
    table_label = tk.Label(root, text="Select Tables:")
    table_label.grid(row=1, column=0, sticky='w', padx=10, pady=5)

     # Get the current datetime
    current_datetime = datetime.now()

     # Option 2: Both start and end times are set to the current time
    start_date_vars, start_hour_var, start_minute_var, start_period_var = create_datetime_selector(root, 5, "Start Date and Time",current_datetime - timedelta(weeks=1))
    end_date_vars, end_hour_var, end_minute_var, end_period_var = create_datetime_selector(root, 6, "End Date and Time", default_datetime=current_datetime)

    table_vars = []
    num_columns = 6
    for i in range(18):
        var = tk.IntVar()
        cb = tk.Checkbutton(root, text=f'Table_{i+1}', variable=var)
        table_vars.append(var)
        row = 2 + i // num_columns  # Rows 2 to 4
        col = i % num_columns       # Columns 0 to 5
        cb.grid(row=row, column=col, sticky='w', padx=5, pady=5)

    # Add a "Select All" checkbox
    select_all_var = tk.IntVar()
    def select_all_tables():
        state = select_all_var.get()
        for var in table_vars:
            var.set(state)
    select_all_cb = tk.Checkbutton(root, text="Select All Tables", variable=select_all_var, command=select_all_tables)
    select_all_cb.grid(row=1, column=1, sticky='w', padx=10, pady=5)

    # Message label to display status
    message_label = tk.Label(root, text="")
    message_label.grid(row=7, columnspan=6)

    # Callback function to process the queried data
    def process_data(data, table, message_label, multiple_tables=False, all_data=None, tables_to_process=None):
        if multiple_tables:
            all_data.append((data, table))
            if len(all_data) == len(tables_to_process):  # All data has been gathered
                plot_data(None, None, message_label, multiple_tables=True, all_data=all_data)
        else:
            plot_data(data, table, message_label)

    # Callback function to process the exported data
    def export_data(data, table, message_label, multiple_tables=False, all_data=None, tables_to_process=None):
        if multiple_tables:
            all_data.append((data, table))
            if len(all_data) == len(tables_to_process):  # All data has been gathered
                export_plot(None, None, message_label, multiple_tables=True, all_data=all_data)
        else:
            export_plot(data, table, message_label)

    # Function to handle plot button click
    def on_plot_click():

        if db_path is None:
            message_label.config(text="Error: No database selected.", fg="red")
            return

        if not all([start_date_vars[0].get(), start_date_vars[1].get(), start_date_vars[2].get(),
                    start_hour_var.get(), start_minute_var.get(), start_period_var.get(),
                    end_date_vars[0].get(), end_date_vars[1].get(), end_date_vars[2].get(),
                    end_hour_var.get(), end_minute_var.get(), end_period_var.get()]):
            message_label.config(text="Error: Start and End times must be fully selected.", fg="red")
            return

        # Collect selected tables
        selected_tables = [f'Table_{i+1}' for i, var in enumerate(table_vars) if var.get() == 1]

        if not selected_tables:
            message_label.config(text="Error: No tables selected.", fg="red")
            return

        # Construct the start date and time
        start_year, start_month, start_day = start_date_vars
        start_date = f"{start_year.get()}-{start_month.get().zfill(2)}-{start_day.get().zfill(2)}"
        start_hour = int(start_hour_var.get())
        start_minute = int(start_minute_var.get())
        start_period = start_period_var.get()
        start_time = convert_to_24_hour(start_hour, start_minute, start_period)
        start_datetime = f"{start_date} {start_time}"

        # Construct the end date and time
        end_year, end_month, end_day = end_date_vars
        end_date = f"{end_year.get()}-{end_month.get().zfill(2)}-{end_day.get().zfill(2)}"
        end_hour = int(end_hour_var.get())
        end_minute = int(end_minute_var.get())
        end_period = end_period_var.get()
        end_time = convert_to_24_hour(end_hour, end_minute, end_period)
        end_datetime = f"{end_date} {end_time}"

        if len(selected_tables) == 1:
            # Handle single table
            table = selected_tables[0]
            run_query_in_background(root, table, start_datetime, end_datetime, process_data, message_label)
        else:
            # Gather data from selected tables
            all_data = []
            tables_to_process = selected_tables.copy()
            for table_name in selected_tables:
                run_query_in_background(root, table_name, start_datetime, end_datetime, process_data, message_label,
                                        multiple_tables=True, all_data=all_data, tables_to_process=tables_to_process)

    # Function to handle export button click
    def on_export_click():

        if db_path is None:
            message_label.config(text="Error: No database selected.", fg="red")
            return

        if not all([start_date_vars[0].get(), start_date_vars[1].get(), start_date_vars[2].get(),
                    start_hour_var.get(), start_minute_var.get(), start_period_var.get(),
                    end_date_vars[0].get(), end_date_vars[1].get(), end_date_vars[2].get(),
                    end_hour_var.get(), end_minute_var.get(), end_period_var.get()]):
            message_label.config(text="Error: Start and End times must be fully selected.", fg="red")
            return

        # Collect selected tables
        selected_tables = [f'Table_{i+1}' for i, var in enumerate(table_vars) if var.get() == 1]

        if not selected_tables:
            message_label.config(text="Error: No tables selected.", fg="red")
            return

        # Construct the start date and time
        start_year, start_month, start_day = start_date_vars
        start_date = f"{start_year.get()}-{start_month.get().zfill(2)}-{start_day.get().zfill(2)}"
        start_hour = int(start_hour_var.get())
        start_minute = int(start_minute_var.get())
        start_period = start_period_var.get()
        start_time = convert_to_24_hour(start_hour, start_minute, start_period)
        start_datetime = f"{start_date} {start_time}"

        # Construct the end date and time
        end_year, end_month, end_day = end_date_vars
        end_date = f"{end_year.get()}-{end_month.get().zfill(2)}-{end_day.get().zfill(2)}"
        end_hour = int(end_hour_var.get())
        end_minute = int(end_minute_var.get())
        end_period = end_period_var.get()
        end_time = convert_to_24_hour(end_hour, end_minute, end_period)
        end_datetime = f"{end_date} {end_time}"

        if len(selected_tables) == 1:
            # Handle single table
            table = selected_tables[0]
            run_query_in_background(root, table, start_datetime, end_datetime, export_data, message_label)
        else:
            # Gather data from selected tables
            all_data = []
            tables_to_process = selected_tables.copy()
            for table_name in selected_tables:
                run_query_in_background(root, table_name, start_datetime, end_datetime, export_data, message_label,
                                        multiple_tables=True, all_data=all_data, tables_to_process=tables_to_process)

    # Buttons for generating plot and exporting
    plot_button = tk.Button(root, text="View Data", command=on_plot_click)
    plot_button.grid(row=8, column=0, padx=10, pady=10, sticky='w')

    export_button = tk.Button(root, text="Export a picture", command=on_export_click)
    export_button.grid(row=8, column=1, padx=10, pady=10, sticky='w')

    root.mainloop()


if __name__ == "__main__":
    create_gui()

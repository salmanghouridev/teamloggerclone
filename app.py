import tkinter as tk
from tkinter import messagebox
import requests
from datetime import datetime, timedelta

# WordPress configuration
WP_URL = "http://wocommercetest.local/wp-json/utl/v1/log"
WP_USER = "admin"
WP_APPLICATION_PASSWORD = "aeYl o1yw 7eMt FsFv cz2P XfdR"

# Initialize global variables
start_time = None
break_start_time = None
current_task = None
current_project = None
is_running = False
update_interval = 1000  # in milliseconds

# Function to start the timer
def start_timer():
    global start_time, current_task, current_project, is_running
    start_time = datetime.now()
    current_task = task_entry.get() or "Default Task"
    current_project = project_entry.get() or "Default Project"
    project_label.config(text=f"Current Project: {current_project}")
    task_label.config(text=f"Current Task: {current_task}")
    update_status(f"Timer started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    start_button.config(state=tk.DISABLED)
    break_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.NORMAL)
    is_running = True
    update_timer()

# Function to take a break
def take_break():
    global break_start_time, is_running
    break_start_time = datetime.now()
    update_status(f"Break started at: {break_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    break_button.config(state=tk.DISABLED)
    resume_button.config(state=tk.NORMAL)
    is_running = False

# Function to resume work after a break
def resume_work():
    global start_time, break_start_time, is_running
    break_end_time = datetime.now()
    break_duration = break_end_time - break_start_time
    start_time += break_duration  # Adjust start time to account for the break
    update_status(f"Resumed work at: {break_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    resume_button.config(state=tk.DISABLED)
    break_button.config(state=tk.NORMAL)
    is_running = True
    update_timer()

# Function to stop the timer and calculate the duration
def stop_timer():
    global is_running
    try:
        end_time = datetime.now()
        duration = end_time - start_time
        hours, remainder = divmod(duration.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        duration_str = '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))
        update_status(f"Timer stopped at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\nDuration: {duration_str}")
        log_time_to_wordpress(start_time.strftime('%Y-%m-%d %H:%M:%S'), end_time.strftime('%Y-%m-%d %H:%M:%S'), duration_str)
        start_button.config(state=tk.NORMAL)
        stop_button.config(state=tk.DISABLED)
        break_button.config(state=tk.DISABLED)
        resume_button.config(state=tk.DISABLED)
        is_running = False
        total_duration_label.config(text=f"Total Duration: {fetch_total_duration()}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

# Function to log time to WordPress
def log_time_to_wordpress(start_time, end_time, duration):
    try:
        data = {
            'project_name': current_project,
            'task_name': current_task,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration
        }
        response = requests.post(WP_URL, json=data, auth=(WP_USER, WP_APPLICATION_PASSWORD))
        if response.status_code == 200:
            messagebox.showinfo("Success", "Time log entry created successfully in WordPress.")
        else:
            messagebox.showerror("Error", f"Failed to create time log entry: {response.text}")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to connect to WordPress: {e}")

# Function to fetch total duration from WordPress
def fetch_total_duration():
    try:
        response = requests.get(f"{WP_URL}/total", auth=(WP_USER, WP_APPLICATION_PASSWORD))
        if response.status_code == 200:
            return response.json().get('total_duration', '00:00:00')
        else:
            return '00:00:00'
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch total duration: {e}")
        return '00:00:00'

# Function to update the status label
def update_status(message):
    status_label.config(text=message)

# Function to update the real-time timer
def update_timer():
    if is_running:
        elapsed_time = datetime.now() - start_time
        hours, remainder = divmod(elapsed_time.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        timer_label.config(text='Elapsed Time: {:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds)))
        root.after(update_interval, update_timer)

# Create the main window
root = tk.Tk()
root.title("Team Logger")

# Set up fonts and padding
default_font = ("Arial", 12)
padding = {'padx': 10, 'pady': 5}

# Create frames for better layout management
project_frame = tk.Frame(root)
project_frame.pack(fill="x", **padding)

task_frame = tk.Frame(root)
task_frame.pack(fill="x", **padding)

button_frame = tk.Frame(root)
button_frame.pack(fill="x", **padding)

status_frame = tk.Frame(root)
status_frame.pack(fill="x", **padding)

timer_frame = tk.Frame(root)
timer_frame.pack(fill="x", **padding)

total_duration_frame = tk.Frame(root)
total_duration_frame.pack(fill="x", **padding)

# Project and Task Entry
tk.Label(project_frame, text="Project:", font=default_font).pack(side="left", **padding)
project_entry = tk.Entry(project_frame, font=default_font)
project_entry.pack(side="left", fill="x", expand=True, **padding)

tk.Label(task_frame, text="Task:", font=default_font).pack(side="left", **padding)
task_entry = tk.Entry(task_frame, font=default_font)
task_entry.pack(side="left", fill="x", expand=True, **padding)

# Current Project and Task Labels
project_label = tk.Label(root, text="Current Project: Default Project", font=default_font)
project_label.pack(**padding)

task_label = tk.Label(root, text="Current Task: Default Task", font=default_font)
task_label.pack(**padding)

# Timer label
timer_label = tk.Label(timer_frame, text="Elapsed Time: 00:00:00", font=("Arial", 16), fg="green")
timer_label.pack(**padding)

# Total duration label
total_duration_label = tk.Label(total_duration_frame, text=f"Total Duration: {fetch_total_duration()}", font=("Arial", 16), fg="blue")
total_duration_label.pack(**padding)

# Add start button
start_button = tk.Button(button_frame, text="Start Timer", command=start_timer, font=default_font)
start_button.pack(side="left", **padding)

# Add break and resume buttons
break_button = tk.Button(button_frame, text="Take a Break", command=take_break, font=default_font)
break_button.pack(side="left", **padding)
break_button.config(state=tk.DISABLED)

resume_button = tk.Button(button_frame, text="Resume Work", command=resume_work, font=default_font)
resume_button.pack(side="left", **padding)
resume_button.config(state=tk.DISABLED)

# Add stop button
stop_button = tk.Button(button_frame, text="Stop Timer", command=stop_timer, font=default_font)
stop_button.pack(side="left", **padding)
stop_button.config(state=tk.DISABLED)

# Add status label
status_label = tk.Label(status_frame, text="Timer not started.", font=default_font)
status_label.pack(fill="x", **padding)

# Start the Tkinter event loop
root.mainloop()

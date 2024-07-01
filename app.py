import tkinter as tk
from tkinter import messagebox, simpledialog
import requests
from datetime import datetime, timedelta
import configparser
import os
import random
from PIL import ImageGrab

# Configuration file
CONFIG_FILE = 'config.ini'

# Initialize global variables
start_time = None
break_start_time = None
current_task = None
current_project = None
is_running = False
update_interval = 1000  # in milliseconds
screenshot_intervals = [3, 12, 20, 90, 30, 40]  # in seconds
next_screenshot_time = None

# Load configuration
config = configparser.ConfigParser()
if os.path.exists(CONFIG_FILE):
    config.read(CONFIG_FILE)
else:
    config['wordpress'] = {
        'WP_URL': 'https://retrov.cutacut.co.uk/ab/wp-json/utl/v1/log',
        'WP_USER': 'admin',
        'WP_APPLICATION_PASSWORD': 'gzhu akH5 P95P 3CXI alp8 Vupu',
        'WP_MEDIA_URL': 'https://retrov.cutacut.co.uk/ab/wp-json/wp/v2/media'
    }
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

# Ensure all necessary keys are present in the configuration
if 'wordpress' not in config:
    config['wordpress'] = {}

wordpress_config_defaults = {
    'WP_URL': 'https://retrov.cutacut.co.uk/ab/wp-json/utl/v1/log',
    'WP_USER': 'admin',
    'WP_APPLICATION_PASSWORD': 'EWKE ZhoJ dIvW ZDmo 6lbb P3ag',
    'WP_MEDIA_URL': 'https://retrov.cutacut.co.uk/ab/wp-json/wp/v2/media'
}

for key, value in wordpress_config_defaults.items():
    if key not in config['wordpress']:
        config['wordpress'][key] = value

# Save updated configuration if any defaults were added
with open(CONFIG_FILE, 'w') as configfile:
    config.write(configfile)

# WordPress configuration
WP_URL = config['wordpress']['WP_URL']
WP_USER = config['wordpress']['WP_USER']
WP_APPLICATION_PASSWORD = config['wordpress']['WP_APPLICATION_PASSWORD']
WP_MEDIA_URL = config['wordpress']['WP_MEDIA_URL']

# Function to check WordPress connection and set status
def check_wordpress_connection():
    try:
        response = requests.get(WP_URL, auth=(WP_USER, WP_APPLICATION_PASSWORD))
        if response.status_code == 200:
            online_status_label.config(text="Status: Online", fg="green")
        else:
            online_status_label.config(text="Status: Offline", fg="red")
    except requests.exceptions.RequestException:
        online_status_label.config(text="Status: Offline", fg="red")

# Function to start the timer
def start_timer():
    global start_time, current_task, current_project, is_running, next_screenshot_time
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
    next_screenshot_time = start_time + timedelta(seconds=random.choice(screenshot_intervals))
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
            print(f"Failed to create time log entry: {response.text}")
            messagebox.showerror("Error", f"Failed to create time log entry: {response.status_code} {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to WordPress: {e}")
        messagebox.showerror("Error", f"Failed to connect to WordPress: {e}")

# Function to fetch total duration from WordPress
def fetch_total_duration():
    try:
        response = requests.get(f"{WP_URL}/total", auth=(WP_USER, WP_APPLICATION_PASSWORD))
        if response.status_code == 200:
            return response.json().get('total_duration', '00:00:00')
        else:
            print(f"Failed to fetch total duration: {response.text}")
            return '00:00:00'
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch total duration: {e}")
        messagebox.showerror("Error", f"Failed to fetch total duration: {e}")
        return '00:00:00'

# Function to update the status label
def update_status(message):
    status_label.config(text=message)

# Function to capture and upload a screenshot
def capture_and_upload_screenshot():
    global next_screenshot_time
    screenshot_path = f'screenshot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    ImageGrab.grab().save(screenshot_path)
    upload_screenshot_to_wordpress(screenshot_path)
    next_screenshot_time = datetime.now() + timedelta(seconds=random.choice(screenshot_intervals))

# Function to upload screenshot to WordPress
def upload_screenshot_to_wordpress(screenshot_path):
    try:
        with open(screenshot_path, 'rb') as img:
            media = {
                'file': img,
                'caption': f'Screenshot taken on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            }
            response = requests.post(WP_MEDIA_URL, files=media, auth=(WP_USER, WP_APPLICATION_PASSWORD))
            if response.status_code != 201:
                print(f"Failed to upload screenshot: {response.text}")
                messagebox.showerror("Error", f"Failed to upload screenshot: {response.status_code} {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to WordPress: {e}")
        messagebox.showerror("Error", f"Failed to connect to WordPress: {e}")

# Function to update the real-time timer
def update_timer():
    if is_running:
        elapsed_time = datetime.now() - start_time
        hours, remainder = divmod(elapsed_time.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        timer_label.config(text='Elapsed Time: {:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds)))
        
        if datetime.now() >= next_screenshot_time:
            capture_and_upload_screenshot()
        
        root.after(update_interval, update_timer)

# Function to open settings window
def open_settings():
    settings_window = tk.Toplevel(root)
    settings_window.title("Settings")

    def save_settings():
        global WP_URL, WP_USER, WP_APPLICATION_PASSWORD, WP_MEDIA_URL
        config['wordpress']['WP_URL'] = wp_url_entry.get()
        config['wordpress']['WP_USER'] = wp_user_entry.get()
        config['wordpress']['WP_APPLICATION_PASSWORD'] = wp_password_entry.get()
        config['wordpress']['WP_MEDIA_URL'] = wp_media_url_entry.get()
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        WP_URL = config['wordpress']['WP_URL']
        WP_USER = config['wordpress']['WP_USER']
        WP_APPLICATION_PASSWORD = config['wordpress']['WP_APPLICATION_PASSWORD']
        WP_MEDIA_URL = config['wordpress']['WP_MEDIA_URL']
        check_wordpress_connection()  # Update the online status
        settings_window.destroy()

    tk.Label(settings_window, text="WordPress URL:", font=default_font).grid(row=0, column=0, padx=10, pady=5, sticky='e')
    wp_url_entry = tk.Entry(settings_window, width=40)
    wp_url_entry.insert(0, WP_URL)
    wp_url_entry.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(settings_window, text="WordPress Username:", font=default_font).grid(row=1, column=0, padx=10, pady=5, sticky='e')
    wp_user_entry = tk.Entry(settings_window, width=40)
    wp_user_entry.insert(0, WP_USER)
    wp_user_entry.grid(row=1, column=1, padx=10, pady=5)

    tk.Label(settings_window, text="WordPress Application Password:", font=default_font).grid(row=2, column=0, padx=10, pady=5, sticky='e')
    wp_password_entry = tk.Entry(settings_window, show='*', width=40)
    wp_password_entry.insert(0, WP_APPLICATION_PASSWORD)
    wp_password_entry.grid(row=2, column=1, padx=10, pady=5)

    tk.Label(settings_window, text="WordPress Media URL:", font=default_font).grid(row=3, column=0, padx=10, pady=5, sticky='e')
    wp_media_url_entry = tk.Entry(settings_window, width=40)
    wp_media_url_entry.insert(0, WP_MEDIA_URL)
    wp_media_url_entry.grid(row=3, column=1, padx=10, pady=5)

    tk.Button(settings_window, text="Save", command=save_settings, font=default_font).grid(row=4, column=1, padx=10, pady=10, sticky='e')

# Initialize the main window
root = tk.Tk()
root.title("Time Tracker")
default_font = ('Helvetica', 12)

# Create and place widgets
tk.Label(root, text="Project:", font=default_font).grid(row=0, column=0, padx=10, pady=5, sticky='e')
project_entry = tk.Entry(root, width=40)
project_entry.grid(row=0, column=1, padx=10, pady=5)

tk.Label(root, text="Task:", font=default_font).grid(row=1, column=0, padx=10, pady=5, sticky='e')
task_entry = tk.Entry(root, width=40)
task_entry.grid(row=1, column=1, padx=10, pady=5)

start_button = tk.Button(root, text="Start", command=start_timer, font=default_font)
start_button.grid(row=2, column=0, padx=10, pady=10)

break_button = tk.Button(root, text="Break", command=take_break, state=tk.DISABLED, font=default_font)
break_button.grid(row=2, column=1, padx=10, pady=10)

resume_button = tk.Button(root, text="Resume", command=resume_work, state=tk.DISABLED, font=default_font)
resume_button.grid(row=2, column=2, padx=10, pady=10)

stop_button = tk.Button(root, text="Stop", command=stop_timer, state=tk.DISABLED, font=default_font)
stop_button.grid(row=2, column=3, padx=10, pady=10)

project_label = tk.Label(root, text="Current Project: None", font=default_font)
project_label.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky='w')

task_label = tk.Label(root, text="Current Task: None", font=default_font)
task_label.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky='w')

timer_label = tk.Label(root, text="Elapsed Time: 00:00:00", font=default_font)
timer_label.grid(row=5, column=0, columnspan=2, padx=10, pady=5, sticky='w')

status_label = tk.Label(root, text="", font=default_font, fg='blue')
status_label.grid(row=6, column=0, columnspan=4, padx=10, pady=5, sticky='w')

total_duration_label = tk.Label(root, text=f"Total Duration: {fetch_total_duration()}", font=default_font)
total_duration_label.grid(row=7, column=0, columnspan=4, padx=10, pady=5, sticky='w')

settings_button = tk.Button(root, text="Settings", command=open_settings, font=default_font)
settings_button.grid(row=8, column=0, columnspan=4, padx=10, pady=10)

username_label = tk.Label(root, text=f"Username: {WP_USER}", font=default_font)
username_label.grid(row=9, column=0, columnspan=4, padx=10, pady=5, sticky='w')

online_status_label = tk.Label(root, text="Status: Offline", font=default_font, fg="red")
online_status_label.grid(row=10, column=0, columnspan=4, padx=10, pady=5, sticky='w')

check_wordpress_connection()  # Check the connection status on startup

root.mainloop()

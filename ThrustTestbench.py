import os
import time
import random
import keyboard
import threading
import pyautogui
import matplotlib
import numpy as np
import configparser
import tkinter as tk
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
from tkinter import scrolledtext
from tkinter import simpledialog
from matplotlib.figure import Figure
from serial_sniffer import serial_ports
from serial_communicator import Serial_Communications
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Display Debug Messages
matplotlib.use("TkAgg")
sp = serial_ports()
print(sp)
currentDIR = os.getcwd()
connected = False
expanded = True  # Changed to True for default expanded serial monitor
kill = False
autolog = True
serial_thread = None
serial_thread_running = False
calibrate_state = False  # Did you calibrate the esc
static_image = None
PWM = 0
cf1 = 0
cf2 = 0
cf3 = 0
gif_frames = []
gif_index = 0
gif_animation = None
image_label = None
raw_reading = 0
test_name = ""
data = ""
data_map = { # all data for a run
    'Time': [],
    'PWM': [],
    'Current': [],
    'RPM': [],
    'Thrust': [],
    'Torque': []
}

# Flag to track if manual motor control is active (for initial 'i' command)
manual_control_session_active = False # Renamed for clarity

# Global variable for loadcell_var
loadcell_var = None

# Dark Mode Colors
DARK_MODE_BG = '#2e2e2e'
DARK_MODE_FG = '#ffffff'
DARK_MODE_FILL_COLOR = '#444444'
DARK_MODE_BORDER_COLOR = '#6a6a6a'
DARK_MODE_HOVER_COLOR = '#888888'
DARK_MODE_PRESS_COLOR = '#aaaaaa'

# Light Mode Colors (original)
LIGHT_MODE_BG = '#dddddd'
LIGHT_MODE_FG = '#001122'
LIGHT_MODE_FILL_COLOR = '#001122'
LIGHT_MODE_BORDER_COLOR = "#5b3065"
LIGHT_MODE_HOVER_COLOR = "#ba5da3"
LIGHT_MODE_PRESS_COLOR = "#fffaaa"

# Configuration file handling
TEST_CONFIG_FILE = "config_test.ini"
DATA_CONFIG_FILE = "config_data.ini"
LOADCELLS_CONFIG_FILE = "config_loadcells.ini"

def load_test_config():
    config = configparser.ConfigParser()
    if os.path.exists(TEST_CONFIG_FILE):
        config.read(TEST_CONFIG_FILE)
        return config
    else:
        # Create default config
        config['TEST'] = {
            'pwm_step': '5',
            'pwm_start': '0',
            'pwm_end': '100',
            'Timestep': '2'
        }
        with open(TEST_CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        return config

def load_data_config():
    config = configparser.ConfigParser()
    if os.path.exists(DATA_CONFIG_FILE):
        config.read(DATA_CONFIG_FILE)
        return config
    else:
        # Create default config
        config['GRAPH'] = {
            'x_axis': 'Time',
            'y_axis': 'Thrust'
        }
        config['GENERAL'] = {
            'autolog': 'True',
            'dark_mode': 'True' # Default to dark mode
        }
        with open(DATA_CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        return config

def load_loadcells_config():
    config = configparser.ConfigParser()
    if os.path.exists(LOADCELLS_CONFIG_FILE):
        config.read(LOADCELLS_CONFIG_FILE)
        return config
    else:
        # Create default config
        config['Calibration Factors'] = {
            'loadcell1': '7050',
            'loadcell2': '7050',
            'loadcell3': '7050'
        }
        with open(LOADCELLS_CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        return config

def save_test_config():
    global settings
    config = configparser.ConfigParser()
    config['TEST'] = {
        'pwm_step': str(settings[0]),
        'pwm_start': str(settings[1]),
        'pwm_end': str(settings[2]),
        'Timestep': str(settings[3]),
        # 'test_name': test_name # Removed automatic saving of test_name
    }
    with open(TEST_CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

def save_data_config():
    global graph_x, graph_y, autolog, dark_mode_enabled
    config = configparser.ConfigParser()
    config['GRAPH'] = {
        'x_axis': graph_x,
        'y_axis': graph_y
    }
    config['GENERAL'] = {
        'autolog': str(autolog),
        'dark_mode': str(dark_mode_enabled)
    }
    with open(DATA_CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

def save_loadcells_config():
    global cf1, cf2, cf3, calibrations
    config = configparser.ConfigParser()
    config['Calibration Factors'] = {
            'loadcell1': str(calibrations[0]), # Ensure these are saved as strings
            'loadcell2': str(calibrations[1]),
            'loadcell3': str(calibrations[2])
    }
    with open(LOADCELLS_CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

# Load configuration at startup
config_test = load_test_config()
config_data = load_data_config()
config_loadcells = load_loadcells_config()

graph_x = config_data['GRAPH'].get('x_axis', 'Time')
graph_y = config_data['GRAPH'].get('y_axis', 'Thrust')
autolog = config_data['GENERAL'].getboolean('autolog', True)
dark_mode_enabled = config_data['GENERAL'].getboolean('dark_mode', True) # Load dark mode setting

settings = [
    float(config_test['TEST'].get('pwm_step', '5')),
    float(config_test['TEST'].get('pwm_start', '0')),
    float(config_test['TEST'].get('pwm_end', '100')),
    float(config_test['TEST'].get('Timestep', '2'))
]
calibrations = [
    float(config_loadcells['Calibration Factors'].get('loadcell1', '430')),
    float(config_loadcells['Calibration Factors'].get('loadcell2', '430')),
    float(config_loadcells['Calibration Factors'].get('loadcell3', '430'))
]
test_name = config_test['TEST'].get('test_name', '') # Load initial test name from config
#Serial Communication
#------------------------------------------------
def Send(a):  # Send to Serial Port func
    global Serial
    try:
        Serial.send(f"{a}")
    except AttributeError:
        print("Serial port not connected.")

def Send_text(event=None):  # Send to Serial Port from user input
    try:
        Serial.send(serial_sender.get())  # serial_sender is the textbox
        serial_sender.delete(0, tk.END)
    except AttributeError:
        print("Serial port not connected.")

def refreshSerialPorts(event=None):  # checks if a serial port is connected or disconnected while connected
    global sp
    sp = serial_ports()
    SerialPorts['values'] = (sp)

def serial_read_start():
    global serial_thread, serial_thread_running
    if not serial_thread_running:
        serial_thread_running = True
        serial_thread = threading.Thread(target=SerialRefresh)
        serial_thread.daemon = True  # Terminate when main exits
        serial_thread.start()

def SerialRefresh():
    global Serial, data, serial_thread_running, data_map, calibrations, raw_reading,serial_thread
    while serial_thread_running:
        try:
            readings = Serial.read()
            if readings != "" and readings != '\n' and readings != None:
                data += readings
                # Check if we have a complete reading
                if '$' in data:
                    parts = data.split('$')
                    # Process all complete readings
                    for part in parts[:-1]:
                        if part.strip() == "":
                            continue
                        values = part.split(',')
                        if len(values) == 6:  # We have all 6 values
                            try:
                                # Update data storage
                                data_map['Time'].append(float(values[0]))
                                data_map['PWM'].append(float(values[1]))
                                data_map['Current'].append(float(values[2]))
                                data_map['RPM'].append(float(values[3]))
                                raw_reading = float(values[4])
                                try:
                                    data_map['Thrust'].append(float(values[4])*calibrations[0])
                                except Exception as e:
                                    print(e)
                                data_map['Torque'].append(float(values[5]))
                                # Update graph in real-Time
                                root.after(0, update_graph)
                            except ValueError:
                                print("Data Mismatch or incomplete data received")
                        else:
                            SerialMonitorInsert(f"Incomplete data packet: {part}")
                    # Keep the last (incomplete) part
                    data = parts[-1]
                else:
                    SerialMonitorInsert(data)
        except Exception as e:
            print(f"Error reading from serial: {e}")
            serial_thread_running = False # Stop thread on error
            serial_thread=False
            break


# Button Functions
#------------------------------------------------
def connect_clicked():
    global connected, serial_thread_running, Serial,serial_thread
    refreshSerialPorts()
    if connected:
        print('stopped')
        Send('e')
        connect.itemconfig(connect_toggle_text, text='Disconnected')
        connected = False
        Serial.close()
        serial_thread_running = False  # Signal thread to stop
        if serial_thread and serial_thread.is_alive():
            serial_thread.join()  # Wait for thread to finish
    else:
        try:
            COM = SerialPorts.get()
            if not COM:
                print("No serial port selected.")
                return
            Serial = Serial_Communications(COM, 115200)
            connected = True
            print('started')
            connect.itemconfig(connect_toggle_text, text='Connected')
            fix_autostart() # RESTORED: fix_autostart() was missing
            serial_read_start()
        except Exception as e:
            print(f'Error While Opening Serial Port: {e}')
            connected = False

def start_clicked():
    global kill, connected, gif_animation
    if connected:
        if start.itemconfig(start_toggle_text)['text'][4] == 'Start Test':
            kill = False  # Reset kill flag
            testThread = threading.Thread(target=test_loop)
            testThread.start()
            start.itemconfig(start_toggle_text, text='Stop Test')
            start.itemconfig(startB, outline=red)
            if gif_frames:
                if gif_animation:
                    root.after_cancel(gif_animation) # Cancel any previous animation
                animate_gif() # Start new animation
        # If button says "Stop Test"
        else:
            kill = True  # Set kill flag to stop the loop
            Send("e")
            start.itemconfig(start_toggle_text, text='Start Test')
            start.itemconfig(startB, outline=green)
            # Stop GIF animation when test is stopped
            if gif_animation:
                root.after_cancel(gif_animation)
            if static_image and image_label:
                image_label.config(image=static_image)

def apply_current_settings():
    global settings, test_name

    test_name = test_name_var_display.get() # Get from entry
    # Test_Name_Label.config(text=f'Test Name: {test_name}') # This will be updated by update_test_settings_display

    try:
        new_pwm_step = float(pwm_step_var_display.get())
        new_pwm_start = float(pwm_start_var_display.get())
        new_pwm_end = float(pwm_end_var_display.get())
        new_timestep = float(timestep_var_display.get())
        settings = [new_pwm_step, new_pwm_start, new_pwm_end, new_timestep]
        print("Settings applied successfully:", settings)
        update_test_settings_display() # Update display labels
        # save_test_config() # REMOVED: Test name no longer automatically saved
        # Do NOT call toggle_edit_mode here, it's called after this from the button release
    except ValueError:
        print("Error: Please enter valid numbers for PWM settings.")
        # Optionally, show a message box

def toggle_edit_mode():
    global settings, test_name

    current_mode_text = edit_test_button.itemcget(edit_test_button_text, "text") # Renamed 'edit_settings_button' to 'edit_test_button'

    if current_mode_text == "Edit Test":
        # Switch to edit mode
        edit_test_button.itemconfig(edit_test_button_text, text="Done Editing")

        # Hide display labels
        Test_Name_Label.grid_forget()
        pwm_step_label.grid_forget()
        pwm_start_label.grid_forget()
        pwm_end_label.grid_forget()
        timestep_label.grid_forget()

        # Place input labels and entries within settings_display_frame
        edit_test_name_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        test_name_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)

        edit_pwm_step_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        pwm_step_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=5)

        edit_pwm_start_label.grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        pwm_start_entry.grid(row=2, column=1, sticky='ew', padx=5, pady=5)

        edit_pwm_end_label.grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        pwm_end_entry.grid(row=3, column=1, sticky='ew', padx=5, pady=5)

        edit_timestep_label.grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        timestep_entry.grid(row=4, column=1, sticky='ew', padx=5, pady=5)

        # Populate entries with current values
        test_name_var_display.set(test_name)
        pwm_step_var_display.set(str(settings[0]))
        pwm_start_var_display.set(str(settings[1]))
        pwm_end_var_display.set(str(settings[2]))
        timestep_var_display.set(str(settings[3]))

        # Show Save and Set as Default buttons
        save_settings_button.grid(row=5, column=4, pady=5, padx=5, sticky='ew')
        set_default_settings_button.grid(row=5, column=5, pady=5, padx=5, sticky='ew')

        # Ensure column 1 in settings_display_frame expands for entries
        settings_display_frame.grid_columnconfigure(1, weight=1)

    else: # Currently "Done Editing"
        # Before switching back, apply current settings
        apply_current_settings() # FIX: Call apply_current_settings here to save changes
        save_test_config() # Save settings to config file (excluding test_name)

        # Hide input labels and entries
        edit_test_name_label.grid_forget()
        test_name_entry.grid_forget()
        edit_pwm_step_label.grid_forget()
        pwm_step_entry.grid_forget()
        edit_pwm_start_label.grid_forget()
        pwm_start_entry.grid_forget()
        edit_pwm_end_label.grid_forget()
        pwm_end_entry.grid_forget()
        edit_timestep_label.grid_forget()
        timestep_entry.grid_forget()

        # Hide Save and Set as Default buttons
        save_settings_button.grid_forget()
        set_default_settings_button.grid_forget()

        # Re-grid display labels
        Test_Name_Label.grid(row=0, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        pwm_step_label.grid(row=1, column=0, columnspan=2, sticky='w', padx=5, pady=1)
        pwm_start_label.grid(row=2, column=0, columnspan=2, sticky='w', padx=5, pady=1)
        pwm_end_label.grid(row=3, column=0, columnspan=2, sticky='w', padx=5, pady=1)
        timestep_label.grid(row=4, column=0, columnspan=2, sticky='w', padx=5, pady=1)

        # Reset column weight
        settings_display_frame.grid_columnconfigure(1, weight=0)

        update_test_settings_display() # Ensure labels show current settings

# Data Config Panel (Advanced Mode)
def toggle_advanced_mode_panel():
    if data_config_frame.winfo_ismapped(): # Check if it's currently visible
        data_config_frame.grid_forget() # Hide it
        manual_control_frame.grid_forget() # Also hide manual control if visible
    else:
        # Hide serial monitor if data config is shown to avoid overlap
        if serial_frame.winfo_ismapped():
            SerialMonitor() # Call to hide serial monitor

        # Show Advanced Mode frame
        data_config_frame.grid(row=5, column=0, columnspan=4, sticky='nsew', padx=5, pady=5)
        # Show Manual Control frame next to it
        manual_control_frame.grid(row=5, column=4, columnspan=3, sticky='nsew', padx=5, pady=5)
        # Ensure initial state of calibration section within advanced mode
        show_default_calibration_options()

def set_autolog_in_main_window(value):
    global autolog
    autolog = value
    save_data_config() # Save the change immediately

def update_axes_in_main_window(x, y):
    global graph_x, graph_y
    graph_x = x
    graph_y = y
    update_graph()
    save_data_config() # Save graph axis preference

# Manual Speed Control Functions
def send_manual_speed_on_slider_move(val): # val is passed by tk.Scale
    global manual_control_session_active
    if manual_control_session_active: # Only send command if session is active
        # This will be called by slider movement if manual_control_session_active is True
        # It sends only the speed, 'i' is only sent once by the "Manual Test" button
        Send(str(int(val)))
        print(f"Slider moved, sent speed: {int(val)}")

def send_manual_test_start(): # This function is called only by the "Manual Test" button
    global manual_control_session_active, data_map

    if not connected:
        print("Serial port not connected. Cannot start manual test.")
        return

    if not manual_control_session_active:
        # Start a new manual control session
        Send('i') # Initialize motor control
        manual_control_session_active = True
        # Clear graph data for new manual test
        for key in data_map:
            data_map[key] = []
        update_graph() # Clear the plot
        print("Manual control session started. Graph reset. Initial speed sent.")
        # Send initial speed from slider
        Send(str(int(motor_speed_slider.get())))
    else:
        print("Manual control session already active. Use slider to change speed or 'Stop & Log'.")


def stop_manual_control_and_log():
    global manual_control_session_active
    if connected:
        Send('e') # End motor control
        print("Motor stopped.")
    else:
        print("Serial port not connected. No motor to stop.")

    logger_clicked() # Log data
    manual_control_session_active = False # Reset flag for next manual session

# Calibration Functions integrated into Advanced Mode
#------------------------------------------------
def show_default_calibration_options():
    # Hide all loadcell calibration elements explicitly
    # Un-grid all elements that belong to the detailed loadcell calibration view
    loadcell_picker_label.grid_forget()
    loadcell_picker.grid_forget()
    zero_loadcell_button.grid_forget()
    known_mass_label.grid_forget()
    known_mass_entry.grid_forget()
    calibrate_loadcell_action_button.grid_forget()
    back_to_adv_calibration_button.grid_forget()

    # Show initial calibration buttons within calibration_container
    calibration_main_label.grid(row=0, column=0, columnspan=2, pady=10, sticky='ew') # Ensure title is gridded
    calibrate_esc_button_adv.grid(row=1, column=0, columnspan=2, pady=5, padx=5, sticky='ew') # Column 0, spanning 2 columns
    calibrate_loadcell_button_adv.grid(row=2, column=0, columnspan=2, pady=5, padx=5, sticky='ew') # Column 0, spanning 2 columns
    # Reset column weight
    calibration_container.grid_columnconfigure(1, weight=0)


def calibrate_esc_func():
    # Visual feedback for the button within Advanced Mode
    calibrate_esc_button_adv.itemconfig(calibrate_esc_button_rect_adv, outline=red)
    Send('c')
    time.sleep(4)
    calibrate_esc_button_adv.itemconfig(calibrate_esc_button_rect_adv, outline=green)
    print("ESC Calibration Done!")
    calibrate_esc_button_adv.itemconfig(calibrate_esc_button_rect_adv, outline=current_normal_color) # Reset color

def show_loadcell_calibration_menu_adv():
    # Hide general calibration options within Advanced Mode
    calibration_main_label.grid_forget()
    calibrate_esc_button_adv.grid_forget()
    calibrate_loadcell_button_adv.grid_forget()

    # Show loadcell calibration elements within calibration_container
    loadcell_picker_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')
    loadcell_picker.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
    zero_loadcell_button.grid(row=1, column=0, columnspan=2, pady=5, padx=5, sticky='ew')
    known_mass_label.grid(row=2, column=0, padx=5, pady=5, sticky='w')
    known_mass_entry.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
    calibrate_loadcell_action_button.grid(row=3, column=0, columnspan=2, pady=5, padx=5, sticky='ew')
    back_to_adv_calibration_button.grid(row=4, column=0, columnspan=2, pady=5, padx=5, sticky='ew')
    # Ensure column 1 of calibration_container is expandable for loadcell_picker/entry
    calibration_container.grid_columnconfigure(1, weight=1)

def zero_loadcell_func():
    selected_loadcell = loadcell_var.get()
    if not selected_loadcell:
        print("Error: Please select a loadcell to zero.")
        return
    Send(f"zl{selected_loadcell}")
    print(f"Zero command sent for Loadcell {selected_loadcell}")

def calibrate_loadcell_func():
    global raw_reading, calibrations
    selected_loadcell = loadcell_var.get()
    known_mass_str = known_mass_entry.get()
    try:
        known_mass = float(known_mass_str)
        # Convert selected_loadcell to an integer index (1-based to 0-based)
        loadcell_index = int(selected_loadcell) - 1
        if 0 <= loadcell_index < len(calibrations):
            if raw_reading is not None and raw_reading != 0:
                calibrations[loadcell_index] = known_mass * 9.81 / raw_reading
                print(f"Loadcell {selected_loadcell} calibrated. New factor: {calibrations[loadcell_index]}")
                save_loadcells_config() # Save updated calibration factors
            else:
                print("Error: Raw reading is not available or is zero. Perform a reading with known mass.")
        else:
            print("Error: Invalid loadcell selected.")
    except ValueError:
        print("Error: Known mass must be a number.")
    except Exception as e:
        print(f"An error occurred during loadcell calibration: {e}")

def back_to_adv_calibration_menu():
    # Hide loadcell calibration elements by forgetting their grid placement
    loadcell_picker_label.grid_forget()
    loadcell_picker.grid_forget()
    zero_loadcell_button.grid_forget()
    known_mass_label.grid_forget()
    known_mass_entry.grid_forget()
    calibrate_loadcell_action_button.grid_forget()
    back_to_adv_calibration_button.grid_forget()

    # Show default calibration options
    show_default_calibration_options()
    # Reset column weight
    calibration_container.grid_columnconfigure(1, weight=0)


def SerialMonitor(): # Serial monitor tkinter button
    global expanded
    if expanded:
        expanded=False
        root.grid_rowconfigure(5, weight=0) # Collapse serial monitor row (row 5 for serial frame)
        root.grid_rowconfigure(6, weight=0) # Collapse serial sender row (row 6 for serial sender)
        serial_frame.grid_forget()
        serial_sender.grid_forget()
        # Restore main content row weights
        root.grid_rowconfigure(0, weight=5)
        root.grid_rowconfigure(1, weight=5)
        root.grid_rowconfigure(2, weight=5)
    else:
        expanded=True
        # Main content rows remain with weight 5
        root.grid_rowconfigure(0, weight=5)
        root.grid_rowconfigure(1, weight=5)
        root.grid_rowconfigure(2, weight=5)
        root.grid_rowconfigure(5, weight=1) # Serial frame will expand vertically
        root.grid_rowconfigure(6, weight=0) # Serial sender will be fixed height

        serial_frame.grid(row=5, column=0, columnspan=7, sticky='nsew', padx=5, pady=5)
        serial_monitor.pack(padx=4, pady=4, fill='both', expand=True) # Allow vertical expansion
        serial_sender.grid(row=6, column=0, columnspan=7, sticky='ew', padx=5, pady=5)

# RunTime Functions
#------------------------------------------------
def SerialMonitorInsert(readings): # Refresh Serial monitor
    serial_monitor.insert(tk.END, readings+'\n')
    serial_monitor.see(tk.END)

def fix_autostart():
    Send("i")
    Send("0")
    Send("e")

def test_loop():
    global kill, settings, data, autolog, PWM
    # Reset data storage at start of test
    for key in data_map:
        data_map[key] = []
    Send('i')  # INIT TEST START
    start.itemconfig(start_toggle_text, text='Testing')
    start.itemconfig(startB, outline=red) # Visual feedback
    pwm_step = settings[0]
    pwm_start = settings[1]
    pwm_end = settings[2]
    Timestep = settings[3]
    PWM = pwm_start
    while PWM <= pwm_end and not kill:
        Send(PWM)  # PWM signal Once
        time.sleep(Timestep)
        PWM += pwm_step
    Send('e')  # End Test
    if autolog:
        logger_clicked()
    if gif_animation: # Always cancel animation on test end/stop
        root.after_cancel(gif_animation)
    if static_image and image_label: # Always show static image on test end/stop
        image_label.config(image=static_image)
    if kill:
        print("Test stopped")
        kill = True
        start.itemconfig(start_toggle_text, text='Start Test')
        start.itemconfig(startB, outline=green) # Visual feedback
    else:
        print("Test completed, automatically logged")
        kill = True
        start.itemconfig(start_toggle_text, text='Start Test')
        start.itemconfig(startB, outline=green) # Visual feedback

def update_graph():
    global data_map, graph_x, graph_y, axis, fig1

    # Clear previous plot
    axis.clear()

    # Get data for selected axes
    x_data = data_map.get(graph_x, []) # Use .get with default empty list to avoid KeyError if data_map is empty
    y_data = data_map.get(graph_y, [])

    # Only plot if we have data
    if x_data and y_data and len(x_data) == len(y_data): # Ensure lengths match
        axis.plot(x_data, y_data, 'b-')
        axis.set_title(f"{graph_y} vs {graph_x}", color=current_fg_color)
        axis.set_xlabel(graph_x, color=current_fg_color)
        axis.set_ylabel(graph_y, color=current_fg_color)
    else:
        # If no data or mismatch, still set title and labels but clear plot
        axis.set_title(f"{graph_y} vs {graph_x}", color=current_fg_color)
        axis.set_xlabel(graph_x, color=current_fg_color)
        axis.set_ylabel(graph_y, color=current_fg_color)


    # Set grid and background based on current theme
    axis.grid(True)
    axis.set_facecolor(current_bg_color_plot)
    axis.tick_params(axis='x', colors=current_fg_color)
    axis.tick_params(axis='y', colors=current_fg_color)

    # Redraw canvas
    fig1.draw_idle()

def set_autolog(value):
    global autolog
    autolog = value

def update_axes(x, y):
    global graph_x, graph_y
    graph_x = x
    graph_y = y
    update_graph()

def toggle_dark_mode(enable_dark_mode):
    global dark_mode_enabled, current_bg_color, current_fg_color, current_fill_color, current_normal_color, current_hover_color, current_press_color, current_bg_color_plot

    dark_mode_enabled = enable_dark_mode
    save_data_config() # Save the dark mode setting

    if dark_mode_enabled:
        current_bg_color = DARK_MODE_BG
        current_fg_color = DARK_MODE_FG
        current_fill_color = DARK_MODE_FILL_COLOR
        current_normal_color = DARK_MODE_BORDER_COLOR
        current_hover_color = DARK_MODE_HOVER_COLOR
        current_press_color = DARK_MODE_PRESS_COLOR
        current_bg_color_plot = '#3a3a3a' # Slightly different for plot background
    else:
        current_bg_color = LIGHT_MODE_BG
        current_fg_color = LIGHT_MODE_FG
        current_fill_color = LIGHT_MODE_FILL_COLOR
        current_normal_color = LIGHT_MODE_BORDER_COLOR
        current_hover_color = LIGHT_MODE_HOVER_COLOR
        current_press_color = LIGHT_MODE_PRESS_COLOR
        current_bg_color_plot = '#dddddd' # Back to original

    apply_theme()

def apply_theme():
    # Update root window
    root.config(bg=current_bg_color)

    # Update ttk styles (only for widgets that are ttk)
    s.configure("TCombobox", fieldbackground=current_bg_color, background=current_bg_color, foreground=current_fg_color)
    s.map("TCombobox", fieldbackground=[('readonly', current_bg_color)])
    s.map("TCombobox", selectbackground=[('readonly', current_bg_color)])
    s.map("TCombobox", selectforeground=[('readonly', current_fg_color)])
    s.configure("TButton", background=current_fill_color, foreground=current_fg_color)
    s.map('TButton', background=[('active', current_hover_color), ('pressed', current_press_color)],
                     foreground=[('active', current_fg_color), ('pressed', current_fg_color)])

    # Update Checkbutton selectcolor for general checkbuttons and those in config window
    checkbutton_options = {'bg': current_bg_color, 'fg': current_fg_color, 'selectcolor': current_fill_color}


    # Update settings display frame (tk.LabelFrame)
    settings_display_frame.config(bg=current_bg_color, fg=current_fg_color,
                                  highlightbackground=current_normal_color) # Update highlightbackground for border

    # Update display labels in settings frame
    Test_Name_Label.config(bg=current_bg_color, fg=current_fg_color)
    pwm_step_label.config(bg=current_bg_color, fg=current_fg_color)
    pwm_start_label.config(bg=current_bg_color, fg=current_fg_color)
    pwm_end_label.config(bg=current_bg_color, fg=current_fg_color)
    timestep_label.config(bg=current_bg_color, fg=current_fg_color)

    # Update settings entry widgets and their labels in settings frame
    edit_test_name_label.config(bg=current_bg_color, fg=current_fg_color)
    test_name_entry.config(bg=current_bg_color, fg=current_fg_color, insertbackground=current_fg_color)
    edit_pwm_step_label.config(bg=current_bg_color, fg=current_fg_color)
    pwm_step_entry.config(bg=current_bg_color, fg=current_fg_color, insertbackground=current_fg_color)
    edit_pwm_start_label.config(bg=current_bg_color, fg=current_fg_color)
    pwm_start_entry.config(bg=current_bg_color, fg=current_fg_color, insertbackground=current_fg_color)
    edit_pwm_end_label.config(bg=current_bg_color, fg=current_fg_color)
    pwm_end_entry.config(bg=current_bg_color, fg=current_fg_color, insertbackground=current_fg_color)
    edit_timestep_label.config(bg=current_bg_color, fg=current_fg_color)
    timestep_entry.config(bg=current_bg_color, fg=current_fg_color, insertbackground=current_fg_color)


    # Update port frame and its label
    port_frame.config(bg=current_bg_color)
    serial_title.config(bg=current_bg_color, fg=current_fg_color)
    # The SerialPorts ttk.Combobox will be restyled by the s.configure("TCombobox",...) above.


    # Update serial monitor frame and its widgets
    serial_frame.config(bg=current_bg_color)
    serial_monitor.config(bg=current_bg_color, fg=current_fg_color, insertbackground=current_fg_color) # insertbackground for cursor
    serial_sender.config(bg=current_bg_color, fg=current_fg_color, insertbackground=current_fg_color)

    # Update Data Config frame (Advanced Mode) and its widgets
    data_config_frame.config(bg=current_bg_color, highlightbackground=current_normal_color)
    graph_options_container.config(bg=current_bg_color) # Update container
    calibration_container.config(bg=current_bg_color) # Update container

    data_config_autolog_cb.config(**checkbutton_options)
    dark_mode_var_config.set(dark_mode_enabled) # Keep checkbox in sync with actual mode
    data_config_dark_mode_cb.config(**checkbutton_options)
    data_config_graph_frame.config(bg=current_bg_color, fg=current_fg_color)
    data_config_x_label.config(bg=current_bg_color, fg=current_fg_color)
    data_config_y_label.config(bg=current_bg_color, fg=current_fg_color)

    # Update Manual Control frame and its widgets
    manual_control_frame.config(bg=current_bg_color, highlightbackground=current_normal_color)
    manual_control_label.config(bg=current_bg_color, fg=current_fg_color)
    motor_speed_slider.config(bg=current_bg_color, fg=current_fg_color, troughcolor=current_fill_color, highlightbackground=current_bg_color) # Update slider colors

    # Update image label background
    if image_label:
        image_label.config(bg=current_bg_color)

    # Update canvases (buttons)
    for canvas_widget in [connect, start, edit_test_button, logger, log_data_button, sm_button,
                          calibrate_esc_button_adv, calibrate_loadcell_button_adv, # These are now in Advanced Mode frame
                          zero_loadcell_button, calibrate_loadcell_action_button, back_to_adv_calibration_button,
                          manual_test_button, stop_manual_button]: # Manual control buttons
        canvas_widget.config(bg=current_bg_color)
        # Update polygons in canvases
        for item_id in canvas_widget.find_all():
            if canvas_widget.type(item_id) == "polygon":
                canvas_widget.itemconfig(item_id, fill=current_fill_color, outline=current_normal_color)
            elif canvas_widget.type(item_id) == "text":
                canvas_widget.itemconfig(item_id, fill=current_fg_color) # Ensure text color is updated


    # Update loadcell calibration frame and its child widgets' colors
    # These widgets are children of calibration_container, so they need to be updated.
    loadcell_picker_label.config(bg=current_bg_color, fg=current_fg_color)
    # The Combobox's style should handle its background/foreground, but if needed:
    # Removed direct fieldbackground config here as it causes the error
    loadcell_picker.config(background=current_bg_color, foreground=current_fg_color) # Removed fieldbackground
    known_mass_label.config(bg=current_bg_color, fg=current_fg_color)
    known_mass_entry.config(bg=current_bg_color, fg=current_fg_color, insertbackground=current_fg_color)


    # Update Matplotlib plot
    Thrust_Figure.patch.set_facecolor(current_bg_color)
    axis.set_facecolor(current_bg_color_plot) # Plot internal background
    axis.tick_params(axis='x', colors=current_fg_color)
    axis.tick_params(axis='y', colors=current_fg_color)
    if axis.title:
        axis.title.set_color(current_fg_color)
    if axis.xaxis.label:
        axis.xaxis.label.set_color(current_fg_color)
    if axis.yaxis.label:
        axis.yaxis.label.set_color(current_fg_color)
    fig1.draw_idle()


# Tkinter functions
#------------------------------------------------
def update_test_settings_display():
    # Update labels for display mode
    Test_Name_Label.config(text=f'Test Name: {test_name}')
    pwm_step_label.config(text=f'PWM Step: {settings[0]}')
    pwm_start_label.config(text=f'PWM Start: {settings[1]}')
    pwm_end_label.config(text=f'PWM End: {settings[2]}')
    timestep_label.config(text=f'Timestep: {settings[3]}s')

def change_color(feature, new_color):
    # Feature-specific button outline change
    if feature == connect:
        feature.itemconfig(connectB, outline=new_color)
    elif feature == start:
        feature.itemconfig(startB, outline=new_color)
    elif feature == sm_button:
        feature.itemconfig(sm_button_rect, outline=new_color)
    elif feature == logger: # This is the Data Config button now (Advanced Mode)
        feature.itemconfig(loggerB, outline=new_color)
    elif feature == edit_test_button: # Renamed from 'test'
        feature.itemconfig(edit_test_button_rect, outline=new_color)
    elif feature == log_data_button:
        feature.itemconfig(log_data_button_rect, outline=new_color)
    # Data Config Panel internal buttons (now part of the Advanced Mode frame)
    elif feature == calibrate_esc_button_adv:
        calibrate_esc_button_adv.itemconfig(calibrate_esc_button_rect_adv, outline=new_color)
    elif feature == calibrate_loadcell_button_adv:
        calibrate_loadcell_button_adv.itemconfig(calibrate_loadcell_button_rect_adv, outline=new_color)
    elif feature == zero_loadcell_button: # Zero loadcell button
        zero_loadcell_button.itemconfig(zero_loadcell_button_rect, outline=new_color)
    elif feature == calibrate_loadcell_action_button: # Calibrate loadcell action button
        calibrate_loadcell_action_button.itemconfig(calibrate_loadcell_action_button_rect, outline=new_color)
    elif feature == back_to_adv_calibration_button:
        back_to_adv_calibration_button.itemconfig(back_to_adv_calibration_button_rect, outline=new_color)
    # Manual Control Panel buttons
    elif feature == manual_test_button:
        manual_test_button.itemconfig(manual_test_button_rect, outline=new_color)
    elif feature == stop_manual_button:
        stop_manual_button.itemconfig(stop_manual_control_button_rect, outline=new_color)


def on_mouse_down(event):
    global lastx, lasty
    lastx = event.widget.winfo_pointerx()
    lasty = event.widget.winfo_pointery()

def move_cursor_randomly():
    global connected
    if not connected:
        direction = [-1, 1]
        a = random.randint(50, 200) * random.choice(direction)
        b = random.randint(50, 200) * random.choice(direction)
        pyautogui.move(a, b, duration=0.02)

def on_mouse_move(event):
    global lastx, lasty
    deltax = event.widget.winfo_pointerx() - lastx
    deltay = event.widget.winfo_pointery() - lasty
    root.geometry("+%d+%d" % (root.winfo_x() + deltax, root.winfo_y() + deltay))
    lastx = event.widget.winfo_pointerx()
    lasty = event.widget.winfo_pointery()


# Saving Data
#------------------------------------------------
def logger_clicked():
    Output_Data = ""
    try:
        if not data_map['Time']:
            print("No data to save.")
            return

        for i in range(len(data_map['Time'])):
            Output_Data += (
                f"{data_map['Time'][i]},"
                f"{data_map['PWM'][i]},"
                f"{data_map['Current'][i]},"
                f"{data_map['RPM'][i]},"
                f"{data_map['Thrust'][i]},"
                f"{data_map['Torque'][i]}\n"
            )
        save_readings(Output_Data)
    except Exception as e:
        print(f"Couldn't save data: {e}")

def save_readings(data):
    global test_name, currentDIR
    if test_name == "":
        import datetime
        now = datetime.datetime.now()
        test_name = now.strftime("%y-%m-%d-%H-%M-%S")

    folder_name = os.path.join(currentDIR, 'logged_runs')
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"Created folder: {folder_name}")
    filename = os.path.join(folder_name, f"Thrust-Test-{test_name}.csv")

    with open(filename, "w") as file:
        file.write("SSTL Thrust Test Platform\n")
        file.write("Time,PWM,Current,RPM,Thrust,Torque\n")
        file.write(f"{data}")
    print(f"File '{filename}' created and values written successfully.")

def log_data_clicked(): # Renamed from graph_manim
    logger_clicked() # Calls the logger_clicked function to save data
    # Optional: Visual feedback on the button
    log_data_button.itemconfig(log_data_toggle_text, text='Logging...')
    log_data_button.itemconfig(log_data_button_rect, outline=red)
    root.update_idletasks() # Force GUI update
    time.sleep(0.5) # Short delay to show "Logging..."
    log_data_button.itemconfig(log_data_toggle_text, text='Data Logged')
    log_data_button.itemconfig(log_data_button_rect, outline=green)
    root.after(1500, lambda: log_data_button.itemconfig(log_data_toggle_text, text='Log Data')) # Reset text after 1.5s

def load_images():
    global static_image, gif_frames, image_label

    # Load static image
    try:
        static_img = Image.open(os.path.join(currentDIR, "assets", "sstlab.png"))
        static_img = static_img.resize((300, 300), Image.LANCZOS)
        static_image = ImageTk.PhotoImage(static_img)
    except Exception as e:
        print(f"Error loading static image: {e}")
        static_image = None

    # Load GIF frames
    try:
        gif = Image.open(os.path.join(currentDIR, "assets", "loading.gif"))
        gif_frames = []
        for i in range(gif.n_frames):
            gif.seek(i)
            frame = gif.copy().resize((300, 300), Image.LANCZOS)
            gif_frames.append(ImageTk.PhotoImage(frame))
    except Exception as e:
        print(f"Error loading GIF: {e}")
        gif_frames = []

    if image_label is None:
        image_label = tk.Label(root, bg=current_bg_color)
        image_label.grid(row=1, column=4, rowspan=2, columnspan=3, padx=10, pady=10, sticky='nsew') # Adjusted column
        root.grid_rowconfigure(1, weight=5) # Made this row expandable with weight 5
        root.grid_rowconfigure(2, weight=5) # Made this row expandable with weight 5
        root.grid_columnconfigure(4, weight=1) # Column for image
        root.grid_columnconfigure(5, weight=1) # Column for image
        root.grid_columnconfigure(6, weight=1) # Column for image

    # Show static image initially
    if static_image:
        image_label.config(image=static_image)

def animate_gif():
    global gif_index, gif_animation, PWM
    if gif_frames:
        image_label.config(image=gif_frames[gif_index])
        gif_index = (gif_index + 1) % len(gif_frames)

        base_delay = 150 # ms, for slowest speed (0-25% PWM)
        delay = base_delay

        if PWM >= 75:
            delay = base_delay / 8 # Fastest (e.g., 150/8 = 18.75ms)
        elif PWM >= 50:
            delay = base_delay / 4 # Faster (e.g., 150/4 = 37.5ms)
        elif PWM >= 25:
            delay = base_delay / 2 # Fast (e.g., 150/2 = 75ms)
        # else: PWM < 25, delay remains base_delay (slowest)

        gif_animation = root.after(int(max(1, delay)), animate_gif) # Ensure delay is at least 1ms to prevent errors

#Debugging and keyboard shortcuts
#------------------------------------------------
def debug_shortcuts(event):
    # Define actions based on the key pressed
    '''
    if event.name == 'space':
        global kill
        if not kill:
            Send("e")
        kill = True
    '''
    if event.name == 'ctrl':
        t1=time.time()
        t2=t1
        while (t2 - t1)<0.2:
            t2=time.time()
            if event.name == 'b':
                connect_clicked()
    pass

def detect_key_press():
    # Hook the key press event to the debug_shortcuts function
    keyboard.on_press(debug_shortcuts)
detect_key_press()


# Initialize theme colors
current_bg_color = LIGHT_MODE_BG
current_fg_color = LIGHT_MODE_FG
current_fill_color = LIGHT_MODE_FILL_COLOR
current_normal_color = LIGHT_MODE_BORDER_COLOR
current_hover_color = LIGHT_MODE_HOVER_COLOR
current_press_color = LIGHT_MODE_PRESS_COLOR
current_bg_color_plot = LIGHT_MODE_BG

if dark_mode_enabled:
    # Set initial current_ colors to dark mode if it's enabled in config
    current_bg_color = DARK_MODE_BG
    current_fg_color = DARK_MODE_FG
    current_fill_color = DARK_MODE_FILL_COLOR
    current_normal_color = DARK_MODE_BORDER_COLOR
    current_hover_color = DARK_MODE_HOVER_COLOR
    current_press_color = DARK_MODE_PRESS_COLOR
    current_bg_color_plot = '#3a3a3a'


# GUI WINDOW
red = "#ff0000"
green = "#00ff00"
root = tk.Tk()
root.title("Thrust Bench")
root.state('zoomed') # Maximized window for Windows/Linux
# root.attributes('-fullscreen', True) # For true fullscreen cross-platform
root.resizable(True, True) # Allow resizing
root.config(bg=current_bg_color)  # background

# Apply ttk style for ttk widgets
s = ttk.Style()
s.configure("TCombobox", fieldbackground=current_bg_color, background=current_bg_color, foreground=current_fg_color)
s.map("TCombobox", fieldbackground=[('readonly', current_bg_color)])
s.map("TCombobox", selectbackground=[('readonly', current_bg_color)])
s.map("TCombobox", selectforeground=[('readonly', current_fg_color)])
s.configure("TButton", background=current_fill_color, foreground=current_fg_color)
s.map('TButton', background=[('active', current_hover_color), ('pressed', current_press_color)],
                 foreground=[('active', current_fg_color), ('pressed', current_fg_color)])


# Configure grid layout for the main window
# Row 0, 1, 2 for Graph and Image. Combined weight 5 for content above buttons.
root.grid_rowconfigure(0, weight=5)
root.grid_rowconfigure(1, weight=5)
root.grid_rowconfigure(2, weight=5)
root.grid_rowconfigure(3, weight=0)
root.grid_rowconfigure(4, weight=0)
root.grid_rowconfigure(5, weight=1) # Serial monitor can expand
root.grid_rowconfigure(6, weight=0) # Serial sender fixed height

# 7 columns for buttons and alignment (0-6)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)
root.grid_columnconfigure(3, weight=1)
root.grid_columnconfigure(4, weight=1)
root.grid_columnconfigure(5, weight=1)
root.grid_columnconfigure(6, weight=1)

# Setup the graph
Thrust_Figure = Figure(figsize=(6, 4), dpi=120) # Increased figsize and dpi slightly
Thrust_Figure.patch.set_facecolor(current_bg_color)
axis = Thrust_Figure.add_subplot(111)
axis.set_facecolor(current_bg_color_plot)
axis.tick_params(axis='x', colors=current_fg_color)
axis.tick_params(axis='y', colors=current_fg_color)
axis.grid(True)

fig1 = FigureCanvasTkAgg(Thrust_Figure, root)
fig1.get_tk_widget().grid(row=0, column=0, rowspan=3, columnspan=4, sticky='nsew', padx=10, pady=10)

# Test Settings Display
# Using tk.LabelFrame instead of ttk.LabelFrame
settings_display_frame = tk.LabelFrame(root, text="Current Test Settings", padx=10, pady=10,
                                       bg=current_bg_color, fg=current_fg_color,
                                       highlightbackground=current_normal_color, highlightthickness=2)
settings_display_frame.grid(row=0, column=4, columnspan=3, pady=110, padx=10, sticky='nwe')

# --- Display Labels for Settings ---
# These are initially visible
Test_Name_Label = tk.Label(settings_display_frame, font="Play 14 bold", fg=current_fg_color, bg=current_bg_color, highlightthickness=0, anchor='w')
Test_Name_Label.grid(row=0, column=0, columnspan=2, sticky='w', padx=5, pady=2) # Span 2 columns to make room for entries

pwm_step_label = tk.Label(settings_display_frame, font="Play 11", fg=current_fg_color, bg=current_bg_color, highlightthickness=0, anchor='w')
pwm_step_label.grid(row=1, column=0, columnspan=2, sticky='w', padx=5, pady=1)

pwm_start_label = tk.Label(settings_display_frame, font="Play 11", fg=current_fg_color, bg=current_bg_color, highlightthickness=0, anchor='w')
pwm_start_label.grid(row=2, column=0, columnspan=2, sticky='w', padx=5, pady=1)

pwm_end_label = tk.Label(settings_display_frame, font="Play 11", fg=current_fg_color, bg=current_bg_color, highlightthickness=0, anchor='w')
pwm_end_label.grid(row=3, column=0, columnspan=2, sticky='w', padx=5, pady=1)

timestep_label = tk.Label(settings_display_frame, font="Play 11", fg=current_fg_color, bg=current_bg_color, highlightthickness=0, anchor='w')
timestep_label.grid(row=4, column=0, columnspan=2, sticky='w', padx=5, pady=1)


# --- Entry Widgets (and their fixed labels) for Editing Settings ---
# These are created but NOT gridded initially.
test_name_var_display = tk.StringVar(value=test_name)
pwm_step_var_display = tk.StringVar(value=str(settings[0]))
pwm_start_var_display = tk.StringVar(value=str(settings[1]))
pwm_end_var_display = tk.StringVar(value=str(settings[2]))
timestep_var_display = tk.StringVar(value=str(settings[3]))

# Create static labels that will appear when entries are shown
edit_test_name_label = tk.Label(settings_display_frame, text="Test Name:", foreground=current_fg_color, background=current_bg_color)
edit_pwm_step_label = tk.Label(settings_display_frame, text="PWM Step:", foreground=current_fg_color, background=current_bg_color)
edit_pwm_start_label = tk.Label(settings_display_frame, text="PWM Start:", foreground=current_fg_color, background=current_bg_color)
edit_pwm_end_label = tk.Label(settings_display_frame, text="PWM End:", foreground=current_fg_color, background=current_bg_color)
edit_timestep_label = tk.Label(settings_display_frame, text="Timestep:", foreground=current_fg_color, background=current_bg_color)

# Create Entry widgets
test_name_entry = tk.Entry(settings_display_frame, textvariable=test_name_var_display, bg=current_bg_color, fg=current_fg_color, insertbackground=current_fg_color)
pwm_step_entry = tk.Entry(settings_display_frame, textvariable=pwm_step_var_display, bg=current_bg_color, fg=current_fg_color, insertbackground=current_fg_color)
pwm_start_entry = tk.Entry(settings_display_frame, textvariable=pwm_start_var_display, bg=current_bg_color, fg=current_fg_color, insertbackground=current_fg_color)
pwm_end_entry = tk.Entry(settings_display_frame, textvariable=pwm_end_var_display, bg=current_bg_color, fg=current_fg_color, insertbackground=current_fg_color)
timestep_entry = tk.Entry(settings_display_frame, textvariable=timestep_var_display, bg=current_bg_color, fg=current_fg_color, insertbackground=current_fg_color)

# Initialize display with current settings (redundant as labels are pre-configured with values, but good practice)
update_test_settings_display()


# Define common polygon points for buttons
p1 = (10*0.75, 10*0.75)
p2 = (10*0.75, 35*0.75)
p3 = (15*0.75, 45*0.75)
p4 = (15*0.75, 70*0.75)
p5 = (310*0.75, 70*0.75)
p6 = (310*0.75, 25*0.75)
p7 = (295*0.75, 10*0.75)
button_width = 320*0.75
button_height = 75*0.75

# Shorter/Wider button for data config options AND manual control buttons
data_button_width = 200 * 0.75 # Shorter width for inner buttons
data_button_height = 50 * 0.75 # Shorter height
data_p1 = (10*0.5, 10*0.5)
data_p2 = (10*0.5, 35*0.5)
data_p3 = (15*0.5, 45*0.5)
data_p4 = (15*0.5, 70*0.5)
data_p5 = (290*0.5, 70*0.5) # Adjusted for shorter width
data_p6 = (290*0.5, 25*0.5)
data_p7 = (275*0.5, 10*0.5)


# --- Buttons in a single row (row 4) ---
# Order from left to right: Serial Monitor, Log Data, Advanced Mode, Edit Test, Start Test, Connect (with Serial Picker above it)

# 1. Serial Monitor button (Column 0)
sm_button = Canvas(root,width=button_width,height=button_height, bg=current_bg_color,borderwidth=0,highlightthickness=0)
sm_button_rect = sm_button.create_polygon(
p1,p2,p3,p4,p5,p6,p7,
outline=current_normal_color, width=2,
fill=current_fill_color
)
sm_button.create_text((button_width/2,button_height/2), text="Serial Monitor", font="Play 12 bold",fill=current_fg_color)
sm_button.grid(row=4, column=0, pady=5, padx=5)
sm_button.bind("<Enter>", lambda event: change_color(sm_button,current_hover_color))
sm_button.bind("<Leave>", lambda event: change_color(sm_button,current_normal_color))
sm_button.bind("<Button-1>", lambda event: change_color(sm_button,current_press_color))
sm_button.bind("<ButtonRelease-1>", lambda event: SerialMonitor())

# 2. Log Data button (Column 1)
log_data_button = Canvas(root, width=button_width, height=button_height, bg=current_bg_color, borderwidth=0, highlightthickness=0)
log_data_button_rect = log_data_button.create_polygon(
    p1, p2, p3, p4, p5, p6, p7,
    outline=current_normal_color, width=2,
    fill=current_fill_color
)
log_data_toggle_text = log_data_button.create_text((button_width/2, button_height/2), text="Log Data", font="Play 12 bold", fill=current_fg_color)
log_data_button.grid(row=4, column=1, pady=5, padx=5)
log_data_button.bind("<Enter>", lambda event: change_color(log_data_button, current_hover_color))
log_data_button.bind("<Leave>", lambda event: change_color(log_data_button, current_normal_color))
log_data_button.bind("<Button-1>", lambda event: change_color(log_data_button, current_press_color))
log_data_button.bind("<ButtonRelease-1>", lambda event: threading.Thread(target=log_data_clicked).start())

# 3. Advanced Mode (Data Config) button (Column 2)
logger = Canvas(root, width=button_width, height=button_height, bg=current_bg_color, borderwidth=0, highlightthickness=0)
loggerB = logger.create_polygon(
    p1, p2, p3, p4, p5, p6, p7,
    outline=current_normal_color, width=2,
    fill=current_fill_color
)
logger.create_text((button_width/2, button_height/2), text="Advanced Mode", font="Play 12 bold", fill=current_fg_color) # Renamed to Advanced Mode
logger.grid(row=4, column=2, pady=3, padx=5)
logger.bind("<Enter>", lambda event: change_color(logger, current_hover_color))
logger.bind("<Leave>", lambda event: change_color(logger, current_normal_color))
logger.bind("<Button-1>", lambda event: change_color(logger, current_press_color))
logger.bind("<ButtonRelease-1>", lambda event: toggle_advanced_mode_panel()) # Call new toggle function

# 4. Edit Test button (Column 3)
edit_test_button = Canvas(root, width=button_width, height=button_height, bg=current_bg_color, borderwidth=0, highlightthickness=0)
edit_test_button_rect = edit_test_button.create_polygon(
    p1, p2, p3, p4, p5, p6, p7,
    outline=current_normal_color, width=3,
    fill=current_fill_color
)
edit_test_button_text = edit_test_button.create_text((button_width/2, button_height/2), text="Edit Test", font="Play 12 bold", fill=current_fg_color) # Renamed to Edit Test
edit_test_button.grid(row=4, column=3, pady=5, padx=5) # Changed column from 4 to 3
edit_test_button.bind("<Enter>", lambda event: change_color(edit_test_button, current_hover_color))
edit_test_button.bind("<Leave>", lambda event: change_color(edit_test_button, current_normal_color))
edit_test_button.bind("<Button-1>", lambda event: change_color(edit_test_button, current_press_color))
edit_test_button.bind("<ButtonRelease-1>", lambda event: toggle_edit_mode())

# 5. Start Test button (Column 4)
start = Canvas(root, width=button_width, height=button_height, bg=current_bg_color, borderwidth=0, highlightthickness=0)
startB = start.create_polygon(
    p1, p2, p3, p4, p5, p6, p7,
    outline=current_normal_color, width=3,
    fill=current_fill_color
)
start_toggle_text = start.create_text((button_width/2, button_height/2), text="Start Test", font="Play 12 bold", fill=current_fg_color)
start.grid(row=4, column=4, pady=5, padx=5) # Changed column from 5 to 4
start.bind("<Enter>", lambda event: change_color(start, current_hover_color))
start.bind("<Leave>", lambda event: change_color(start, current_normal_color))
start.bind("<Button-1>", lambda event: change_color(start, current_press_color))
start.bind("<ButtonRelease-1>", lambda event: start_clicked())

# 6. Connect button (Column 5)
connect = Canvas(root, width=button_width, height=button_height, bg=current_bg_color, borderwidth=0, highlightthickness=0)
connectB = connect.create_polygon(
    p1, p2, p3, p4, p5, p6, p7,
    outline=current_normal_color, width=3,
    fill=current_fill_color
)
connect_toggle_text = connect.create_text((button_width/2, button_height/2), text="Connect", font="Play 12 bold", fill=current_fg_color)
connect.grid(row=4, column=5, pady=5, padx=5) # Changed column from 6 to 5
connect.bind("<Enter>", lambda event: change_color(connect, current_hover_color))
connect.bind("<Leave>", lambda event: change_color(connect, current_normal_color))
connect.bind("<Button-1>", lambda event: change_color(connect, current_press_color))
connect.bind("<ButtonRelease-1>", lambda event: connect_clicked())

# Serial Port Picker - Directly above Connect button (Column 5, Row 3)
port_frame = tk.Frame(root, bg=current_bg_color)
port_frame.grid(row=3, column=5, pady=10, padx=(0, 5)) # Reduced padx on right
port_frame.bind("<Enter>", refreshSerialPorts)
serial_title = tk.Label(port_frame, font=('Play', 14), fg=current_fg_color, bg=current_bg_color, text="Serial Port :")
serial_title.pack(side="left")
n = tk.StringVar()
SerialPorts = ttk.Combobox(port_frame, width=10, textvariable=n, style='TCombobox') # Apply TCombobox style
SerialPorts['values'] = (sp)
SerialPorts.pack(pady=15, padx=20, side=("right"))
SerialPorts.current()


# Data Config Frame (Advanced Mode)
data_config_frame = tk.Frame(root, bg=current_bg_color, borderwidth=2, relief="groove",
                             highlightbackground=current_normal_color, highlightthickness=2)
data_config_frame.grid_columnconfigure(0, weight=1) # Graph Options container
data_config_frame.grid_columnconfigure(1, weight=1) # Calibration Options container
data_config_frame.grid_forget() # Initially hidden

# Sub-frames within Advanced Mode for organization (horizontal arrangement)
graph_options_container = tk.Frame(data_config_frame, bg=current_bg_color)
graph_options_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

calibration_container = tk.Frame(data_config_frame, bg=current_bg_color)
calibration_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
# Make calibration_container a grid manager for its contents
calibration_container.grid_columnconfigure(0, weight=1)
calibration_container.grid_columnconfigure(1, weight=1)


# Content for Graphing Options Container (Moved from data_config_frame)
# Auto logging checkbox
autolog_var = tk.BooleanVar(value=autolog)
data_config_autolog_cb = tk.Checkbutton(
    graph_options_container, # Parented to graph_options_container
    text="Enable csv Logging",
    variable=autolog_var,
    command=lambda: set_autolog_in_main_window(autolog_var.get()),
    bg=current_bg_color, fg=current_fg_color, selectcolor=current_fill_color
)
data_config_autolog_cb.pack(pady=10)

# Dark mode checkbox
dark_mode_var_config = tk.BooleanVar(value=dark_mode_enabled) # Separate var for this window's checkbox
data_config_dark_mode_cb = tk.Checkbutton(
    graph_options_container, # Parented to graph_options_container
    text="Enable Dark Mode",
    variable=dark_mode_var_config,
    command=lambda: toggle_dark_mode(dark_mode_var_config.get()),
    bg=current_bg_color, fg=current_fg_color, selectcolor=current_fill_color
)
data_config_dark_mode_cb.pack(pady=5)

# Graphing options frame within data_config_frame
data_config_graph_frame = tk.LabelFrame(graph_options_container, text="Graphing Options", bg=current_bg_color, fg=current_fg_color) # Parented to graph_options_container
data_config_graph_frame.pack(pady=10, padx=5, fill="x", expand=True) # Reduced padx

# X variable selection
data_config_x_label = tk.Label(data_config_graph_frame, text="X-Axis:", bg=current_bg_color, fg=current_fg_color)
data_config_x_label.grid(row=0, column=0, padx=5, pady=5)
data_config_x_var = tk.StringVar(value=graph_x)
data_config_x_combo = ttk.Combobox(
    data_config_graph_frame,
    textvariable=data_config_x_var,
    values=['Time', 'PWM', 'Current', 'RPM', 'Thrust', 'Torque'],
    state="readonly",
    style='TCombobox'
)
data_config_x_combo.grid(row=0, column=1, padx=5, pady=5)

# Y variable selection
data_config_y_label = tk.Label(data_config_graph_frame, text="Y-Axis:", bg=current_bg_color, fg=current_fg_color)
data_config_y_label.grid(row=1, column=0, padx=5, pady=5)
data_config_y_var = tk.StringVar(value=graph_y)
data_config_y_combo = ttk.Combobox(
    data_config_graph_frame,
    textvariable=data_config_y_var,
    values=['Time', 'PWM', 'Current', 'RPM', 'Thrust', 'Torque'],
    state="readonly",
    style='TCombobox'
)
data_config_y_combo.grid(row=1, column=1, padx=5, pady=5)

# Update Graph button (Canvas version)
data_config_graph_btn_canvas = Canvas(data_config_graph_frame, width=data_button_width, height=data_button_height, bg=current_bg_color, borderwidth=0, highlightthickness=0)
data_config_graph_btn_rect = data_config_graph_btn_canvas.create_polygon(
    data_p1, data_p2, data_p3, data_p4, data_p5, data_p6, data_p7,
    outline=current_normal_color, width=2, fill=current_fill_color
)
data_config_graph_btn_text = data_config_graph_btn_canvas.create_text((data_button_width/2, data_button_height/2), text="Update Graph", font="Play 9 bold", fill=current_fg_color)
data_config_graph_btn_canvas.grid(row=2, column=0, columnspan=2, pady=5, padx=5)
data_config_graph_btn_canvas.bind("<Enter>", lambda event: change_color(data_config_graph_btn_canvas, current_hover_color))
data_config_graph_btn_canvas.bind("<Leave>", lambda event: change_color(data_config_graph_btn_canvas, current_normal_color))
data_config_graph_btn_canvas.bind("<Button-1>", lambda event: change_color(data_config_graph_btn_canvas, current_press_color))
data_config_graph_btn_canvas.bind("<ButtonRelease-1>", lambda event: update_axes_in_main_window(data_config_x_var.get(), data_config_y_var.get()))


# Set as Default button for data config (Canvas version)
data_config_default_btn_canvas = Canvas(data_config_graph_frame, width=data_button_width, height=data_button_height, bg=current_bg_color, borderwidth=0, highlightthickness=0)
data_config_default_btn_rect = data_config_default_btn_canvas.create_polygon(
    data_p1, data_p2, data_p3, data_p4, data_p5, data_p6, data_p7,
    outline=current_normal_color, width=2, fill=current_fill_color
)
data_config_default_btn_text = data_config_default_btn_canvas.create_text((data_button_width/2, data_button_height/2), text="Set as Default", font="Play 9 bold", fill=current_fg_color)
data_config_default_btn_canvas.grid(row=3, column=0, columnspan=2, pady=10, padx=5)
data_config_default_btn_canvas.bind("<Enter>", lambda event: change_color(data_config_default_btn_canvas, current_hover_color))
data_config_default_btn_canvas.bind("<Leave>", lambda event: change_color(data_config_default_btn_canvas, current_normal_color))
data_config_default_btn_canvas.bind("<Button-1>", lambda event: change_color(data_config_default_btn_canvas, current_press_color))
data_config_default_btn_canvas.bind("<ButtonRelease-1>", lambda event: save_data_config())


# Calibration Options within Advanced Mode (new section)
# Main label for calibration section
calibration_main_label = tk.Label(calibration_container, text="Calibration Options", font="Play 12 bold", bg=current_bg_color, fg=current_fg_color)
# Packing of these will be handled by show_default_calibration_options

# Calibrate ESC button (within Advanced Mode)
calibrate_esc_button_adv = Canvas(calibration_container, width=data_button_width, height=data_button_height, bg=current_bg_color, borderwidth=0, highlightthickness=0)
calibrate_esc_button_rect_adv = calibrate_esc_button_adv.create_polygon(
    data_p1, data_p2, data_p3, data_p4, data_p5, data_p6, data_p7,
    outline=current_normal_color, width=2, fill=current_fill_color
)
calibrate_esc_button_text_adv = calibrate_esc_button_adv.create_text((data_button_width/2, data_button_height/2), text="Calibrate ESC", font="Play 9 bold", fill=current_fg_color)
calibrate_esc_button_adv.bind("<Enter>", lambda event: change_color(calibrate_esc_button_adv, current_hover_color))
calibrate_esc_button_adv.bind("<Leave>", lambda event: change_color(calibrate_esc_button_adv, current_normal_color))
calibrate_esc_button_adv.bind("<Button-1>", lambda event: change_color(calibrate_esc_button_adv, current_press_color))
calibrate_esc_button_adv.bind("<ButtonRelease-1>", lambda event: threading.Thread(target=calibrate_esc_func).start())

# Calibrate Loadcells button (within Advanced Mode)
calibrate_loadcell_button_adv = Canvas(calibration_container, width=data_button_width, height=data_button_height, bg=current_bg_color, borderwidth=0, highlightthickness=0)
calibrate_loadcell_button_rect_adv = calibrate_loadcell_button_adv.create_polygon(
    data_p1, data_p2, data_p3, data_p4, data_p5, data_p6, data_p7,
    outline=current_normal_color, width=2, fill=current_fill_color
)
calibrate_loadcell_button_text_adv = calibrate_loadcell_button_adv.create_text((data_button_width/2, data_button_height/2), text="Calibrate Loadcells", font="Play 9 bold", fill=current_fg_color)
calibrate_loadcell_button_adv.bind("<Enter>", lambda event: change_color(calibrate_loadcell_button_adv, current_hover_color))
calibrate_loadcell_button_adv.bind("<Leave>", lambda event: change_color(calibrate_loadcell_button_adv, current_normal_color))
calibrate_loadcell_button_adv.bind("<Button-1>", lambda event: change_color(calibrate_loadcell_button_adv, current_press_color))
calibrate_loadcell_button_adv.bind("<ButtonRelease-1>", lambda event: show_loadcell_calibration_menu_adv())

# Loadcell Calibration Sub-menu elements (initially hidden, parented to calibration_container)
loadcell_var = tk.StringVar(value="1") # Global definition for loadcell_var (moved here from inside function)

# Define all loadcell calibration widgets, parented to calibration_container
# These will be gridded/ungridded by show_loadcell_calibration_menu_adv and back_to_adv_calibration_menu
loadcell_picker_label = tk.Label(calibration_container, text="Select Loadcell:", bg=current_bg_color, fg=current_fg_color, font="Play 10")
loadcell_picker = ttk.Combobox(calibration_container, textvariable=loadcell_var, values=["1", "2", "3"], state="readonly", font="Play 10", width=8, style='TCombobox')

zero_loadcell_button = Canvas(calibration_container, width=data_button_width, height=data_button_height, bg=current_bg_color, borderwidth=0, highlightthickness=0)
zero_loadcell_button_rect = zero_loadcell_button.create_polygon(
    data_p1, data_p2, data_p3, data_p4, data_p5, data_p6, data_p7,
    outline=current_normal_color, width=2, fill=current_fill_color
)
zero_loadcell_button.create_text((data_button_width/2, data_button_height/2), text="Zero Loadcell", font="Play 9 bold", fill=current_fg_color)
zero_loadcell_button.bind("<Enter>", lambda event: change_color(zero_loadcell_button, current_hover_color))
zero_loadcell_button.bind("<Leave>", lambda event: change_color(zero_loadcell_button, current_normal_color))
zero_loadcell_button.bind("<Button-1>", lambda event: change_color(zero_loadcell_button, current_press_color))
zero_loadcell_button.bind("<ButtonRelease-1>", lambda event: threading.Thread(target=zero_loadcell_func).start())

known_mass_label = tk.Label(calibration_container, text="Known Mass:", bg=current_bg_color, fg=current_fg_color, font="Play 10")
known_mass_entry = tk.Entry(calibration_container, font="Play 10", bg=current_bg_color, fg=current_fg_color, insertbackground=current_fg_color)

calibrate_loadcell_action_button = Canvas(calibration_container, width=data_button_width, height=data_button_height, bg=current_bg_color, borderwidth=0, highlightthickness=0)
calibrate_loadcell_action_button_rect = calibrate_loadcell_action_button.create_polygon(
    data_p1, data_p2, data_p3, data_p4, data_p5, data_p6, data_p7,
    outline=current_normal_color, width=2, fill=current_fill_color
)
calibrate_loadcell_action_button.create_text((data_button_width/2, data_button_height/2), text="Calibrate", font="Play 9 bold", fill=current_fg_color)
calibrate_loadcell_action_button.bind("<Enter>", lambda event: change_color(calibrate_loadcell_action_button, current_hover_color))
calibrate_loadcell_action_button.bind("<Leave>", lambda event: change_color(calibrate_loadcell_action_button, current_normal_color))
calibrate_loadcell_action_button.bind("<Button-1>", lambda event: change_color(calibrate_loadcell_action_button, current_press_color))
calibrate_loadcell_action_button.bind("<ButtonRelease-1>", lambda event: threading.Thread(target=calibrate_loadcell_func).start())

back_to_adv_calibration_button = Canvas(calibration_container, width=data_button_width, height=data_button_height, bg=current_bg_color, borderwidth=0, highlightthickness=0)
back_to_adv_calibration_button_rect = back_to_adv_calibration_button.create_polygon(
    data_p1, data_p2, data_p3, data_p4, data_p5, data_p6, data_p7,
    outline=current_normal_color, width=2, fill=current_fill_color
)
back_to_adv_calibration_button.create_text((data_button_width/2, data_button_height/2), text="Back", font="Play 9 bold", fill=current_fg_color)
back_to_adv_calibration_button.bind("<Enter>", lambda event: change_color(back_to_adv_calibration_button, current_hover_color))
back_to_adv_calibration_button.bind("<Leave>", lambda event: change_color(back_to_adv_calibration_button, current_normal_color))
back_to_adv_calibration_button.bind("<Button-1>", lambda event: change_color(back_to_adv_calibration_button, current_press_color))
back_to_adv_calibration_button.bind("<ButtonRelease-1>", lambda event: back_to_adv_calibration_menu())


# Manual Speed Control Frame (next to Data Config frame)
manual_control_frame = tk.Frame(root, bg=current_bg_color, borderwidth=2, relief="groove",
                                 highlightbackground=current_normal_color, highlightthickness=2)
manual_control_frame.grid_columnconfigure(0, weight=1) # Allow slider to expand
manual_control_frame.grid_forget() # Initially hidden

manual_control_label = tk.Label(manual_control_frame, text="Manual Motor Control", font="Play 12 bold", bg=current_bg_color, fg=current_fg_color)
manual_control_label.pack(pady=10)

motor_speed_slider = tk.Scale(manual_control_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                              label="Speed (PWM)", length=200, bg=current_bg_color, fg=current_fg_color,
                              troughcolor=current_fill_color, highlightbackground=current_bg_color,
                              command=send_manual_speed_on_slider_move) # Command to send speed on slider move
motor_speed_slider.pack(pady=5, padx=10)

manual_test_button = Canvas(manual_control_frame, width=data_button_width, height=data_button_height, bg=current_bg_color, borderwidth=0, highlightthickness=0)
manual_test_button_rect = manual_test_button.create_polygon(
    data_p1, data_p2, data_p3, data_p4, data_p5, data_p6, data_p7,
    outline=current_normal_color, width=2, fill=current_fill_color
)
manual_test_button_text = manual_test_button.create_text((data_button_width/2, data_button_height/2), text="Manual Test", font="Play 9 bold", fill=current_fg_color) # Renamed to Manual Test
manual_test_button.pack(pady=5)
manual_test_button.bind("<Enter>", lambda event: change_color(manual_test_button, current_hover_color))
manual_test_button.bind("<Leave>", lambda event: change_color(manual_test_button, current_normal_color))
manual_test_button.bind("<Button-1>", lambda event: change_color(manual_test_button, current_press_color))
manual_test_button.bind("<ButtonRelease-1>", lambda event: send_manual_test_start()) # This initiates the manual test session


stop_manual_button = Canvas(manual_control_frame, width=data_button_width, height=data_button_height, bg=current_bg_color, borderwidth=0, highlightthickness=0)
stop_manual_button_rect = stop_manual_button.create_polygon(
    data_p1, data_p2, data_p3, data_p4, data_p5, data_p6, data_p7,
    outline=current_normal_color, width=2, fill=current_fill_color
)
stop_manual_button_text = stop_manual_button.create_text((data_button_width/2, data_button_height/2), text="Stop & Log", font="Play 9 bold", fill=current_fg_color)
stop_manual_button.pack(pady=5)
stop_manual_button.bind("<Enter>", lambda event: change_color(stop_manual_button, current_hover_color))
stop_manual_button.bind("<Leave>", lambda event: change_color(stop_manual_button, current_normal_color))
stop_manual_button.bind("<Button-1>", lambda event: change_color(stop_manual_button, current_press_color))
stop_manual_button.bind("<ButtonRelease-1>", lambda event: stop_manual_control_and_log())


# Serial Monitor frame
serial_frame = tk.Frame(root, bg=current_bg_color)
serial_monitor = scrolledtext.ScrolledText(serial_frame, height=5, # Increased height for better visibility
                            font = ("Arial", 12), bg=current_bg_color, fg=current_fg_color, insertbackground=current_fg_color)
serial_monitor.pack(padx=4, pady=4, fill='both', expand=True) # Allow vertical expansion

serial_sender = tk.Entry(root, bg=current_bg_color, fg=current_fg_color, insertbackground=current_fg_color)
serial_sender.bind('<Return>',Send_text)

# Initial placement of serial monitor (expanded by default)
if expanded:
    serial_frame.grid(row=5, column=0, columnspan=7, sticky='nsew', padx=5, pady=5)
    serial_monitor.pack(padx=4, pady=4, fill='both', expand=True)
    serial_sender.grid(row=6, column=0, columnspan=7, sticky='ew', padx=5, pady=5)


load_images()
apply_theme()
root.mainloop()
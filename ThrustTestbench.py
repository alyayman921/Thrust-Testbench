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

#Display Debug Messages
matplotlib.use("TkAgg")
sp = serial_ports()
print(sp)
currentDIR = os.getcwd()
connected = False
expanded=False
kill = False
autolog = True
serial_thread = None
serial_thread_running = False
calibrate_state = False  # Did you calibrate the esc
static_image = None
gif_frames = []
gif_index = 0
gif_animation = None
image_label = None
test_name = ""
data = ""
graph_x = 'Time'  # Default X-axis
graph_y = 'Thrust'  # Default Y-axis
data_map = { # all data for a run
    'Time': [],
    'PWM': [],
    'Current': [],
    'RPM': [],
    'Thrust': [],
    'Torque': []
}

# Configuration file handling
TEST_CONFIG_FILE = "config_test.ini"
DATA_CONFIG_FILE = "config_data.ini"
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
            'Timestep': '2',
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
            'autolog': 'True'
        }
        with open(DATA_CONFIG_FILE, 'w') as configfile:
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
    }
    with open(TEST_CONFIG_FILE, 'w') as configfile:
        config.write(configfile)
def save_data_config():
    global graph_x,graph_y
    config = configparser.ConfigParser()
    config['GRAPH'] = {
        'x_axis': graph_x,
        'y_axis': graph_y
    }
    config['GENERAL'] = {
        'autolog': str(autolog),
    }
    with open(DATA_CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

# Load configuration at startup
config_test = load_test_config()
config_data = load_data_config()
graph_x = config_data['GRAPH'].get('x_axis', 'Time')
graph_y = config_data['GRAPH'].get('y_axis', 'Thrust')
autolog = config_data['GENERAL'].getboolean('autolog', True)
settings = [
    float(config_test['TEST'].get('pwm_step', '5')),
    float(config_test['TEST'].get('pwm_start', '0')),
    float(config_test['TEST'].get('pwm_end', '100')),
    float(config_test['TEST'].get('Timestep', '2'))
]


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
    global Serial, data, serial_thread_running, data_map
    while serial_thread_running:
        try:
            readings = Serial.read()
            if readings != "" and readings != '\n' and readings!=None:
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
                                data_map['Thrust'].append(float(values[4]))
                                data_map['Torque'].append(float(values[5]))
                                # Update graph in real-Time
                                root.after(0, update_graph)
                            except ValueError:
                                print("Data Mismatch or incomplete data received")
                        else:
                            SerialMonitorInsert(f"Incomplete data packet: {part}")
                    # Keep the last (incomplete) part
                    data = parts[-1]
                else :
                    SerialMonitorInsert(data)
        except Exception as e:
            print(f"Error reading from serial: {e}")
            serial_thread_running = False # Stop thread on error
            break


# Button Functions
#------------------------------------------------
def connect_clicked():
    global connected, serial_thread_running, Serial
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
            Serial = Serial_Communications(COM, 9600)
            connected = True
            print('started')
            connect.itemconfig(connect_toggle_text, text='Connected')
            serial_read_start()
            fix_autostart()
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
                    root.after_cancel(gif_animation)
                animate_gif()
        # If button says "Stop Test"
        else:
            kill = True  # Set kill flag to stop the loop
            Send("e")
            start.itemconfig(start_toggle_text, text='Start Test')
            start.itemconfig(startB, outline=green)

def define_test_clicked():
    global settings,test_name
    # Create a new window
    settings_window = tk.Toplevel(root)
    settings_window.title("PWM Settings")
    settings_window.transient(root) # Make it appear on top of the main window
    settings_window.grab_set() # Make it modal

    # Default values
    default_values = {
        "Test_Name": test_name, # Use current test_name
        'pwm_step': str(settings[0]),
        'pwm_start': str(settings[1]),
        'pwm_end': str(settings[2]),
        'Timestep': str(settings[3]),
    }

    # Variables to store the entries
    test_name_var = tk.StringVar(value=default_values["Test_Name"])
    pwm_step_var = tk.StringVar(value=default_values["pwm_step"])
    pwm_start_var = tk.StringVar(value=default_values["pwm_start"])
    pwm_end_var = tk.StringVar(value=default_values["pwm_end"])
    Timestep_var = tk.StringVar(value=default_values["Timestep"])

    # Create and layout widgets
    label_frame = ttk.Frame(settings_window, padding="10")
    label_frame.pack(fill=tk.BOTH, expand=True)

    # Run Name
    ttk.Label(label_frame, text="Test Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    test_name_entry = ttk.Entry(label_frame, textvariable=test_name_var)
    test_name_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)

    # PWM Step
    ttk.Label(label_frame, text="PWM Step:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
    pwm_step_entry = ttk.Entry(label_frame, textvariable=pwm_step_var)
    pwm_step_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)

    # PWM Start
    ttk.Label(label_frame, text="PWM Start:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
    pwm_start_entry = ttk.Entry(label_frame, textvariable=pwm_start_var)
    pwm_start_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)

    # PWM End
    ttk.Label(label_frame, text="PWM End:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
    pwm_end_entry = ttk.Entry(label_frame, textvariable=pwm_end_var)
    pwm_end_entry.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)

    # Timestep
    ttk.Label(label_frame, text="Timestep:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
    Timestep_entry = ttk.Entry(label_frame, textvariable=Timestep_var)
    Timestep_entry.grid(row=4, column=1, sticky=tk.EW, padx=5, pady=5)

    # Save button functionality
    def save_and_close():
        global settings, test_name
        # Store the values in variables
        test_name = test_name_var.get()
        try:
            pwm_step = float(pwm_step_var.get())
            pwm_start = float(pwm_start_var.get())
            pwm_end = float(pwm_end_var.get())
            Timestep = float(Timestep_var.get())
            settings = [pwm_step, pwm_start, pwm_end, Timestep]
            print("Saved values:")
            print(f"Run Name: {test_name}")
            Test_Name_Change(test_name)
            update_test_settings_display() # Update display
            print(settings)
            settings_window.destroy()
        except ValueError:
            print("Error: Please enter valid numbers for PWM settings.")
            # tk.messagebox.showerror("Invalid Input", "Please enter valid numbers for PWM settings.")


    # Save button
    save_button = ttk.Button(label_frame, text="Save", command=save_and_close)
    save_button.grid(row=5, column=0, columnspan=2, pady=10, padx=30)

    # Set as Default button
    set_default_button = ttk.Button(label_frame, text="Set as Default", command=save_test_config)
    set_default_button.grid(row=6, column=0, columnspan=2, pady=10)

    # Configure grid weights
    label_frame.columnconfigure(1, weight=1)
    settings_window.wait_window(settings_window)

def data_config_clicked():
    global autolog, graph_x, graph_y
    # Create configuration window
    config_window = tk.Toplevel(root)
    config_window.title("Data Configuration")
    config_window.transient(root) # Make it appear on top of the main window
    config_window.grab_set() # Make it modal

    # Auto logging checkbox
    autolog_var = tk.BooleanVar(value=autolog)
    autolog_cb = tk.Checkbutton(
        config_window,
        text="Enable csv Logging",
        variable=autolog_var,
        command=lambda: set_autolog(autolog_var.get())
    )
    autolog_cb.pack(pady=10)

    # Graphing options frame
    graph_frame = tk.LabelFrame(config_window, text="Graphing Options")
    graph_frame.pack(pady=10, padx=20, fill="x")

    # X variable selection
    tk.Label(graph_frame, text="X-Axis:").grid(row=0, column=0, padx=5, pady=5)
    x_var = tk.StringVar(value=graph_x)
    x_combo = ttk.Combobox(
        graph_frame,
        textvariable=x_var,
        values=['Time', 'PWM', 'Current', 'RPM', 'Thrust', 'Torque'],
        state="readonly"
    )
    x_combo.grid(row=0, column=1, padx=5, pady=5)

    # Y variable selection
    tk.Label(graph_frame, text="Y-Axis:").grid(row=1, column=0, padx=5, pady=5)
    y_var = tk.StringVar(value=graph_y)
    y_combo = ttk.Combobox(
        graph_frame,
        textvariable=y_var,
        values=['Time', 'PWM', 'Current', 'RPM', 'Thrust', 'Torque'],
        state="readonly"
    )
    y_combo.grid(row=1, column=1, padx=5, pady=5)

    default_btn = tk.Button(
        graph_frame,
        text="Set as Default",
        command=save_data_config)
    # Set as default button
    default_btn.grid(row=3, column=0, columnspan=2, pady=10)

    def set_default():
        global graph_x, graph_y
        graph_x = x_var.get()
        graph_y = y_var.get()
        update_graph()  # Update graph immediately
        config_window.destroy()
    # Graph button
    graph_btn = tk.Button(
        graph_frame,
        text="Update Graph",
        command=lambda: update_axes(x_var.get(), y_var.get())
    )
    graph_btn.grid(row=2, column=0, columnspan=2, pady=5)
    # Close button
    close_btn = tk.Button(
        config_window,
        text="Close",
        command=config_window.destroy)
    close_btn.pack(pady=10)
    config_window.wait_window(config_window)

# New calibration functions and UI management
def show_calibration_options():
    # Hide the main Calibrate button
    Calibrate.grid_forget()

    # Show ESC and Loadcell calibrate buttons in the same grid area
    calibrate_esc_button.grid(row=3, column=1, pady=5, padx=5, sticky='ew')
    calibrate_loadcell_button.grid(row=4, column=1, pady=5, padx=5, sticky='ew')

    # Store references to hide them later
    Calibrate.current_sub_buttons = [calibrate_esc_button, calibrate_loadcell_button]

def calibrate_esc_func():
    Calibrate.itemconfig(CalibrateB, outline=red) # Use main button's color for feedback
    Send('c')
    time.sleep(4)
    Calibrate.itemconfig(CalibrateB, outline=green)
    print("ESC Calibration Done!")
    Calibrate.itemconfig(CalibrateB, outline=normal_color) # Reset color
    back_to_main_calibrate_menu() # Retract buttons after calibration

def show_loadcell_calibration_menu():
    # Hide initial calibration sub-buttons
    for btn in Calibrate.current_sub_buttons:
        btn.grid_forget()

    # Show loadcell calibration elements in the same grid area as the Calibrate button
    loadcell_calibrate_frame.grid(row=3, column=1, rowspan=2, pady=5, padx=5, sticky='nsew')
    loadcell_picker_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')
    loadcell_picker.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
    zero_loadcell_button.grid(row=1, column=0, columnspan=2, pady=5, padx=5, sticky='ew')
    known_mass_label.grid(row=2, column=0, padx=5, pady=5, sticky='w')
    known_mass_entry.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
    calibrate_loadcell_action_button.grid(row=3, column=0, columnspan=2, pady=5, padx=5, sticky='ew')
    back_to_main_calibrate_button.grid(row=4, column=0, columnspan=2, pady=5, padx=5, sticky='ew')

def zero_loadcell_func():
    selected_loadcell = loadcell_var.get()
    if not selected_loadcell:
        print("Error: Please select a loadcell to zero.")
        return
    Send(f"zl{selected_loadcell}")
    print(f"Zero command sent for Loadcell {selected_loadcell}")

def calibrate_loadcell_func():
    selected_loadcell = loadcell_var.get()
    known_mass_str = known_mass_entry.get()

    if not selected_loadcell:
        print("Error: Please select a loadcell.")
        return
    if not known_mass_str:
        print("Error: Please enter a known mass.")
        return

    try:
        known_mass = float(known_mass_str)
        command = f"cl{selected_loadcell}{known_mass}"
        Send(command)
        print(f"Calibration command sent: {command}")
    except ValueError:
        print("Error: Known mass must be a number.")

def back_to_main_calibrate_menu():
    # Hide loadcell calibration elements
    loadcell_calibrate_frame.grid_forget()

    # Hide ESC and Loadcell calibrate buttons if they are currently shown
    if hasattr(Calibrate, 'current_sub_buttons'):
        for btn in Calibrate.current_sub_buttons:
            btn.grid_forget()

    # Show main Calibrate button
    Calibrate.grid(row=4, column=1, pady=5, padx=5, sticky='ew')


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
        root.grid_rowconfigure(5, weight=0) # Serial frame will be fixed height
        root.grid_rowconfigure(6, weight=0) # Serial sender will be fixed height

        serial_frame.grid(row=5, column=0, columnspan=7, sticky='nsew', padx=5, pady=5)
        serial_monitor.pack(padx=4, pady=4, fill='x', expand=False) # Do not expand vertically
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
    global kill, settings, data, autolog
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
    if gif_animation:
        root.after_cancel(gif_animation)
    if static_image and image_label:
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
    x_data = data_map[graph_x]
    y_data = data_map[graph_y]

    # Only plot if we have data
    if x_data and y_data:
        axis.plot(x_data, y_data, 'b-')
        axis.set_title(f"{graph_y} vs {graph_x}")
        axis.set_xlabel(graph_x)
        axis.set_ylabel(graph_y)

    # Set grid and background
    axis.grid(True)
    axis.set_facecolor("#dddddd")
    axis.tick_params(axis='x', colors='#001122')
    axis.tick_params(axis='y', colors='#001122')

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


# Tkinter functions
#------------------------------------------------
def Test_Name_Change(test_name):
    Test_Name_Label.config(text=f'Test Name:\n {test_name}')

def update_test_settings_display():
    Test_Name_Label.config(text=f'Test Name:\n {test_name}')
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
    elif feature == logger:
        feature.itemconfig(loggerB, outline=new_color)
    elif feature == test:
        feature.itemconfig(testB, outline=new_color)
    elif feature == Calibrate: # Main calibrate button
        feature.itemconfig(CalibrateB, outline=new_color)
    elif feature == log_data_button:
        feature.itemconfig(log_data_button_rect, outline=new_color)
    elif feature == calibrate_esc_button: # New ESC calibrate button
        feature.itemconfig(calibrate_esc_button_rect, outline=new_color)
    elif feature == calibrate_loadcell_button: # New Loadcell calibrate button
        feature.itemconfig(calibrate_loadcell_button_rect, outline=new_color)
    elif feature == zero_loadcell_button: # Zero loadcell button
        feature.itemconfig(zero_loadcell_button_rect, outline=new_color)
    elif feature == calibrate_loadcell_action_button: # Calibrate loadcell action button
        feature.itemconfig(calibrate_loadcell_action_button_rect, outline=new_color)
    elif feature == back_to_main_calibrate_button:
        feature.itemconfig(back_to_main_calibrate_button_rect, outline=new_color)


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

    folder_name=os.path.join(currentDIR, 'logged_runs')
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"Created folder: {folder_name}")
    else:
        print(f"Folder already exists: {folder_name}")
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
        image_label = tk.Label(root, bg='#dddddd')
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
    global gif_index, gif_animation
    if gif_frames:
        image_label.config(image=gif_frames[gif_index])
        gif_index = (gif_index + 1) % len(gif_frames)
        gif_animation = root.after(100, animate_gif)  # Adjust speed as needed


#Debugging and keyboard shortcuts
#------------------------------------------------
def debug_shortcuts(event):
    # Define actions based on the key pressed
    if event.name == 'space':
        Send("e")
        kill = True

def detect_key_press():
    # Hook the key press event to the debug_shortcuts function
    keyboard.on_press(debug_shortcuts)
detect_key_press()

# GUI WINDOW

normal_color = "#5b3065"  # border
hover_color = "#ba5da3"
press_color = "#fffaaa"
fill_color = "#001122"
red = "#ff0000"
green = "#00ff00"
root = tk.Tk()
root.title("Thrust Bench")
root.state('zoomed') # Maximized window for Windows/Linux
# root.attributes('-fullscreen', True) # For true fullscreen cross-platform
root.resizable(True, True) # Allow resizing
root.config(bg='#dddddd')  # background

# Configure grid layout for the main window
# Row 0, 1, 2 for Graph and Image. Combined weight 5 for content above buttons.
root.grid_rowconfigure(0, weight=5)
root.grid_rowconfigure(1, weight=5)
root.grid_rowconfigure(2, weight=5)
root.grid_rowconfigure(3, weight=0) # Serial port picker row (fixed height)
root.grid_rowconfigure(4, weight=0) # Button row (fixed height)
root.grid_rowconfigure(5, weight=0) # Serial monitor frame (fixed height for 3 lines)
root.grid_rowconfigure(6, weight=0) # Serial sender (fixed height)

# 7 columns for buttons and alignment (0-6)
root.grid_columnconfigure(0, weight=1) # Graph / Button 7 (Serial Monitor)
root.grid_columnconfigure(1, weight=1) # Graph / Button 6 (Calibrate)
root.grid_columnconfigure(2, weight=1) # Graph / Button 5 (Data Config)
root.grid_columnconfigure(3, weight=1) # Graph / Button 4 (Define Test)
root.grid_columnconfigure(4, weight=1) # Image / Button 1 (Connect)
root.grid_columnconfigure(5, weight=1) # Image / Button 2 (Start Test)
root.grid_columnconfigure(6, weight=1) # Image / Button 3 (Log Data)

# Setup the graph
Thrust_Figure = Figure(figsize=(6, 4), dpi=120) # Increased figsize and dpi slightly
Thrust_Figure.patch.set_facecolor("#dddddd")
axis = Thrust_Figure.add_subplot(111)
axis.set_facecolor("#dddddd")
axis.tick_params(axis='x', colors='#001122')
axis.tick_params(axis='y', colors='#001122')
axis.grid(True)

fig1 = FigureCanvasTkAgg(Thrust_Figure, root)
fig1.get_tk_widget().grid(row=0, column=0, rowspan=3, columnspan=4, sticky='nsew', padx=10, pady=10) # Adjusted columnspan to 4

# Test Settings Display
# Using a LabelFrame for better organization and a title
settings_display_frame = ttk.LabelFrame(root, text="Current Test Settings", padding="10")
settings_display_frame.grid(row=0, column=4, columnspan=3, pady=110, padx=10, sticky='nwe')

Test_Name_Label = tk.Label(settings_display_frame, text='Test Name:\n', font="Play 14 bold", fg="#001122", bg="#dddddd", highlightthickness=0, anchor='w')
Test_Name_Label.pack(fill='x', padx=5, pady=2)

pwm_step_label = tk.Label(settings_display_frame, text='PWM Step:', font="Play 11", fg="#001122", bg="#dddddd", highlightthickness=0, anchor='w')
pwm_step_label.pack(fill='x', padx=5, pady=1)

pwm_start_label = tk.Label(settings_display_frame, text='PWM Start:', font="Play 11", fg="#001122", bg="#dddddd", highlightthickness=0, anchor='w')
pwm_start_label.pack(fill='x', padx=5, pady=1)

pwm_end_label = tk.Label(settings_display_frame, text='PWM End:', font="Play 11", fg="#001122", bg="#dddddd", highlightthickness=0, anchor='w')
pwm_end_label.pack(fill='x', padx=5, pady=1)

timestep_label = tk.Label(settings_display_frame, text='Timestep:', font="Play 11", fg="#001122", bg="#dddddd", highlightthickness=0, anchor='w')
timestep_label.pack(fill='x', padx=5, pady=1)

# Initialize display with current settings
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


# --- Buttons in a single row (row 4) ---
# Ordered from right to left as requested (1. Connect, 2. Start Test, 3. Define Test, 4. Data Config, 5. Log Data, 6. Calibrate, 7. Serial Monitor)

# 1. Connect button (Column 4)
connect = Canvas(root, width=button_width, height=button_height, bg="#dddddd", borderwidth=0, highlightthickness=0)
connectB = connect.create_polygon(
    p1, p2, p3, p4, p5, p6, p7,
    outline=normal_color, width=3,
    fill=fill_color
)
connect_toggle_text = connect.create_text((button_width/2, button_height/2), text="Connect", font="Play 12 bold", fill="white")
connect.grid(row=4, column=6, pady=5, padx=5, sticky='ew')
connect.bind("<Enter>", lambda event: change_color(connect, hover_color))
connect.bind("<Leave>", lambda event: change_color(connect, normal_color))
connect.bind("<Button-1>", lambda event: change_color(connect, press_color))
connect.bind("<ButtonRelease-1>", lambda event: connect_clicked())

# Serial Port Picker - Directly above Connect button
port_frame = tk.Frame(root, bg='#dddddd')
port_frame.grid(row=3, column=6, pady=10, sticky='s') # Placed directly above connect button
port_frame.bind("<Enter>", refreshSerialPorts)
serial_title = tk.Label(port_frame, font=('Play', 14), fg='#001122', bg="#dddddd", text="Serial Port :")
serial_title.pack(side="left")
n = tk.StringVar()
SerialPorts = ttk.Combobox(port_frame, width=10, textvariable=n)
SerialPorts['values'] = (sp)
SerialPorts.pack(pady=15, padx=20, side=("right"))
SerialPorts.current()


# 2. Start Test button (Column 5)
start = Canvas(root, width=button_width, height=button_height, bg="#dddddd", borderwidth=0, highlightthickness=0)
startB = start.create_polygon(
    p1, p2, p3, p4, p5, p6, p7,
    outline=normal_color, width=3,
    fill=fill_color
)
start_toggle_text = start.create_text((button_width/2, button_height/2), text="Start Test", font="Play 12 bold", fill="white")
start.grid(row=4, column=5, pady=5, padx=5, sticky='ew')
start.bind("<Enter>", lambda event: change_color(start, hover_color))
start.bind("<Leave>", lambda event: change_color(start, normal_color))
start.bind("<Button-1>", lambda event: change_color(start, press_color))
start.bind("<ButtonRelease-1>", lambda event: start_clicked())

# 3. Define Test button (Column 3)
test = Canvas(root, width=button_width, height=button_height, bg="#dddddd", borderwidth=0, highlightthickness=0)
testB = test.create_polygon(
    p1, p2, p3, p4, p5, p6, p7,
    outline=normal_color, width=3,
    fill=fill_color
)
test.create_text((button_width/2, button_height/2), text="Define Test", font="Play 12 bold", fill="white")
test.grid(row=4, column=4, pady=5, padx=5, sticky='ew')
test.bind("<Enter>", lambda event: change_color(test, hover_color))
test.bind("<Leave>", lambda event: change_color(test, normal_color))
test.bind("<Button-1>", lambda event: change_color(test, press_color))
test.bind("<ButtonRelease-1>", lambda event: define_test_clicked())

# 4. Data Configuration button (Column 2)
logger = Canvas(root, width=button_width, height=button_height, bg="#dddddd", borderwidth=0, highlightthickness=0)
loggerB = logger.create_polygon(
    p1, p2, p3, p4, p5, p6, p7,
    outline=normal_color, width=2,
    fill=fill_color
)
logger.create_text((button_width/2, button_height/2), text="Data Config", font="Play 12 bold", fill="white")
logger.grid(row=4, column=3, pady=3, padx=5, sticky='ew')
logger.bind("<Enter>", lambda event: change_color(logger, hover_color))
logger.bind("<Leave>", lambda event: change_color(logger, normal_color))
logger.bind("<Button-1>", lambda event: change_color(logger, press_color))
logger.bind("<ButtonRelease-1>", lambda event: data_config_clicked())

# 5. Log Data button (Column 6 - rightmost)
log_data_button = Canvas(root, width=button_width, height=button_height, bg="#dddddd", borderwidth=0, highlightthickness=0)
log_data_button_rect = log_data_button.create_polygon(
    p1, p2, p3, p4, p5, p6, p7,
    outline=normal_color, width=2,
    fill=fill_color
)
log_data_toggle_text = log_data_button.create_text((button_width/2, button_height/2), text="Log Data", font="Play 12 bold", fill="white")
log_data_button.grid(row=4, column=1, pady=5, padx=5, sticky='ew')
log_data_button.bind("<Enter>", lambda event: change_color(log_data_button, hover_color))
log_data_button.bind("<Leave>", lambda event: change_color(log_data_button, normal_color))
log_data_button.bind("<Button-1>", lambda event: change_color(log_data_button, press_color))
log_data_button.bind("<ButtonRelease-1>", lambda event: threading.Thread(target=log_data_clicked).start())


# 6. Calibrate button (Column 1) - Now acts as 'Calibration Options'
Calibrate = Canvas(root, width=button_width, height=button_height, bg="#dddddd", borderwidth=0, highlightthickness=0)
CalibrateB = Calibrate.create_polygon(
    p1, p2, p3, p4, p5, p6, p7,
    outline=normal_color, width=2,
    fill=fill_color
)
Calibrate_toggle_text = Calibrate.create_text((button_width/2, button_height/2), text="Calibration Options", font="Play 12 bold", fill="white")
Calibrate.grid(row=4, column=2, pady=5, padx=5, sticky='ew')
Calibrate.bind("<Enter>", lambda event: change_color(Calibrate, hover_color))
Calibrate.bind("<Leave>", lambda event: change_color(Calibrate, normal_color))
Calibrate.bind("<Button-1>", lambda event: change_color(Calibrate, press_color))
Calibrate.bind("<ButtonRelease-1>", lambda event: show_calibration_options()) # Call new function

# New calibration buttons (initially hidden)
# Calibrate ESC button
calibrate_esc_button = Canvas(root, width=button_width, height=button_height, bg="#dddddd", borderwidth=0, highlightthickness=0)
calibrate_esc_button_rect = calibrate_esc_button.create_polygon(
    p1, p2, p3, p4, p5, p6, p7,
    outline=normal_color, width=2,
    fill=fill_color
)
calibrate_esc_button.create_text((button_width/2, button_height/2), text="Calibrate ESC", font="Play 10 bold", fill="white")
calibrate_esc_button.bind("<Enter>", lambda event: change_color(calibrate_esc_button, hover_color))
calibrate_esc_button.bind("<Leave>", lambda event: change_color(calibrate_esc_button, normal_color))
calibrate_esc_button.bind("<Button-1>", lambda event: change_color(calibrate_esc_button, press_color))
calibrate_esc_button.bind("<ButtonRelease-1>", lambda event: threading.Thread(target=calibrate_esc_func).start())

# Calibrate Loadcells button
calibrate_loadcell_button = Canvas(root, width=button_width, height=button_height, bg="#dddddd", borderwidth=0, highlightthickness=0)
calibrate_loadcell_button_rect = calibrate_loadcell_button.create_polygon(
    p1, p2, p3, p4, p5, p6, p7,
    outline=normal_color, width=2,
    fill=fill_color
)
calibrate_loadcell_button.create_text((button_width/2, button_height/2), text="Calibrate Loadcells", font="Play 10 bold", fill="white")
calibrate_loadcell_button.bind("<Enter>", lambda event: change_color(calibrate_loadcell_button, hover_color))
calibrate_loadcell_button.bind("<Leave>", lambda event: change_color(calibrate_loadcell_button, normal_color))
calibrate_loadcell_button.bind("<Button-1>", lambda event: change_color(calibrate_loadcell_button, press_color))
calibrate_loadcell_button.bind("<ButtonRelease-1>", lambda event: show_loadcell_calibration_menu())


# Loadcell Calibration Sub-menu elements (initially hidden)
loadcell_calibrate_frame = tk.Frame(root, bg="#dddddd", borderwidth=2, relief="groove")
loadcell_calibrate_frame.grid_columnconfigure(1, weight=1) # Allow loadcell picker and entry to expand

loadcell_var = tk.StringVar(value="1") # Default loadcell
loadcell_picker_label = tk.Label(loadcell_calibrate_frame, text="Select Loadcell:", bg="#dddddd", font="Play 10")
loadcell_picker = ttk.Combobox(loadcell_calibrate_frame, textvariable=loadcell_var, values=["1", "2", "3"], state="readonly", font="Play 10", width=8)

zero_loadcell_button = Canvas(loadcell_calibrate_frame, width=button_width, height=button_height*0.7, bg="#dddddd", borderwidth=0, highlightthickness=0)
zero_loadcell_button_rect = zero_loadcell_button.create_polygon(
    p1, p2, p3, p4, p5, p6, p7,
    outline=normal_color, width=2,
    fill=fill_color
)
zero_loadcell_button.create_text((button_width/2, button_height*0.7/2), text="Zero Loadcell", font="Play 9 bold", fill="white")
zero_loadcell_button.bind("<Enter>", lambda event: change_color(zero_loadcell_button, hover_color))
zero_loadcell_button.bind("<Leave>", lambda event: change_color(zero_loadcell_button, normal_color))
zero_loadcell_button.bind("<Button-1>", lambda event: change_color(zero_loadcell_button, press_color))
zero_loadcell_button.bind("<ButtonRelease-1>", lambda event: threading.Thread(target=zero_loadcell_func).start())

known_mass_label = tk.Label(loadcell_calibrate_frame, text="Known Mass:", bg="#dddddd", font="Play 10")
known_mass_entry = tk.Entry(loadcell_calibrate_frame, font="Play 10")

calibrate_loadcell_action_button = Canvas(loadcell_calibrate_frame, width=button_width, height=button_height*0.7, bg="#dddddd", borderwidth=0, highlightthickness=0)
calibrate_loadcell_action_button_rect = calibrate_loadcell_action_button.create_polygon(
    p1, p2, p3, p4, p5, p6, p7,
    outline=normal_color, width=2,
    fill=fill_color
)
calibrate_loadcell_action_button.create_text((button_width/2, button_height*0.7/2), text="Calibrate", font="Play 9 bold", fill="white")
calibrate_loadcell_action_button.bind("<Enter>", lambda event: change_color(calibrate_loadcell_action_button, hover_color))
calibrate_loadcell_action_button.bind("<Leave>", lambda event: change_color(calibrate_loadcell_action_button, normal_color))
calibrate_loadcell_action_button.bind("<Button-1>", lambda event: change_color(calibrate_loadcell_action_button, press_color))
calibrate_loadcell_action_button.bind("<ButtonRelease-1>", lambda event: threading.Thread(target=calibrate_loadcell_func).start())

back_to_main_calibrate_button = Canvas(loadcell_calibrate_frame, width=button_width, height=button_height*0.7, bg="#dddddd", borderwidth=0, highlightthickness=0)
back_to_main_calibrate_button_rect = back_to_main_calibrate_button.create_polygon(
    p1, p2, p3, p4, p5, p6, p7,
    outline=normal_color, width=2,
    fill=fill_color
)
back_to_main_calibrate_button.create_text((button_width/2, button_height*0.7/2), text="Back", font="Play 9 bold", fill="white")
back_to_main_calibrate_button.bind("<Enter>", lambda event: change_color(back_to_main_calibrate_button, hover_color))
back_to_main_calibrate_button.bind("<Leave>", lambda event: change_color(back_to_main_calibrate_button, normal_color))
back_to_main_calibrate_button.bind("<Button-1>", lambda event: change_color(back_to_main_calibrate_button, press_color))
back_to_main_calibrate_button.bind("<ButtonRelease-1>", lambda event: back_to_main_calibrate_menu())


# 7. Serial Monitor button (Column 0 - leftmost)
sm_button = Canvas(root,width=button_width,height=button_height, bg="#dddddd",borderwidth=0,highlightthickness=0)
sm_button_rect = sm_button.create_polygon(
p1,p2,p3,p4,p5,p6,p7,
outline=normal_color, width=2,
fill=fill_color
)
sm_button.create_text((button_width/2,button_height/2), text="Serial Monitor", font="Play 12 bold",fill="white")
sm_button.grid(row=4, column=0, pady=5, padx=5, sticky='ew')
sm_button.bind("<Enter>", lambda event: change_color(sm_button,hover_color))
sm_button.bind("<Leave>", lambda event: change_color(sm_button,normal_color))
sm_button.bind("<Button-1>", lambda event: change_color(sm_button,press_color))
sm_button.bind("<ButtonRelease-1>", lambda event: SerialMonitor())


serial_frame=Frame(root, bg='#eeeeee')
serial_monitor = scrolledtext.ScrolledText(serial_frame, height=3, # Max 3 lines height
                            font = ("Arial", 12))
serial_monitor.pack(padx=4, pady=4, fill='x', expand=False) # Do not expand vertically

serial_sender=tk.Entry(root)
serial_sender.bind('<Return>',Send_text)

load_images()
root.mainloop()
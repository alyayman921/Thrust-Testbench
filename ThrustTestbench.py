import os
import math
import time
import random
import keyboard
import threading
import pyautogui
import numpy as np
import configparser
import tkinter as tk
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
from tkinter import scrolledtext
from tkinter import simpledialog
import matplotlib
matplotlib.use("TkAgg")  # Set the backend before importing Figure
from matplotlib.figure import Figure
from serial_sniffer import serial_ports
from serial_communicator import Serial_Communications
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

sp = serial_ports()
print(sp)
currentDIR = os.getcwd()
connected = False 
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
speed = 0
Thrust_value = 0
settings = [1, 0, 10, 0.2]
test_name = ""
data = ""
graph_x = 'time'  # Default X-axis
graph_y = 'thrust'  # Default Y-axis
data_map = { # all data for a run
    'time': [],
    'pwm': [],
    'current': [],
    'rpm': [],
    'thrust': [],
    'torque': []
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
            'timestep': '2',
        }
        with open(TEST_CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        return config_test
def load_data_config():
    config = configparser.ConfigParser()
    if os.path.exists(DATA_CONFIG_FILE):
        config.read(DATA_CONFIG_FILE)
        return config
    else:
        # Create default config
        config['GRAPH'] = {
            'x_axis': 'time',
            'y_axis': 'thrust'
        }
        config['GENERAL'] = {
            'autolog': 'True'
        }
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        return config_data
def save_test_config():
    global settings
    config = configparser.ConfigParser()
    config['TEST'] = {
        'pwm_step': str(settings[0]),
        'pwm_start': str(settings[1]),
        'pwm_end': str(settings[2]),
        'timestep': str(settings[3]),
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
graph_x = config_data['GRAPH'].get('x_axis', 'time')
graph_y = config_data['GRAPH'].get('y_axis', 'thrust')
autolog = config_data['GENERAL'].getboolean('autolog', True)
settings = [
    float(config_test['TEST'].get('pwm_step', '5')),
    float(config_test['TEST'].get('pwm_start', '0')),
    float(config_test['TEST'].get('pwm_end', '100')),
    float(config_test['TEST'].get('timestep', '2'))
]


#Serial Communication
def Send(a):  # Send to Serial Port func
    global Serial
    Serial.send(f"{a}")

def Send_text(event=None):  # Send to Serial Port from user input
    Serial.send(serial_sender.get())  # serial_sender is the textbox
    serial_sender.delete(0, tk.END)

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
        readings = Serial.read()
        if readings != "" and readings != '\n':
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
                            data_map['time'].append(float(values[0]))
                            data_map['pwm'].append(float(values[1]))
                            data_map['current'].append(float(values[2]))
                            data_map['rpm'].append(float(values[3]))
                            data_map['thrust'].append(float(values[4]))
                            data_map['torque'].append(float(values[5]))
                            
                            # Update graph in real-time
                            root.after(0, update_graph)
                        except ValueError:
                            print("Could not convert data to float")
                # Keep the last (incomplete) part
                data = parts[-1]

# Button Functions
def connect_clicked():
    global connected, serial_thread_running, Serial
    refreshSerialPorts()
    if connected:
        print('stopped')
        Send('e')
        connect.itemconfig(toggle_text, text='COM Stopped')
        connected = False
        Serial.close()
        serial_thread_running = False  # Signal thread to stop
        if serial_thread and serial_thread.is_alive():
            serial_thread.join(timeout=1.0)  # Wait for thread to finish
    else:
        connected = True
        try:
            print('started')
            connect.itemconfig(toggle_text, text='COM Started')
            COM = SerialPorts.get()
            Serial = Serial_Communications(COM, 9600)
            fix_autostart()
        except Exception as e:
            print('Error While Opening Serial Port')
            connected = False
           
def start_clicked():
    global kill, connected, gif_animation
    if connected:
        if start.itemconfig(toggle_text)['text'][4] == 'Start Test':  
            kill = False  # Reset kill flag
            testThread = threading.Thread(target=test_loop)
            testThread.start()
            start.itemconfig(toggle_text, text='Stop Test')
            start.itemconfig(startB, outline=red)
            serial_read_start()
            if gif_frames:
                if gif_animation:
                    root.after_cancel(gif_animation)
                animate_gif()
        # If button says "Stop Test"
        else: 
            kill = True  # Set kill flag to stop the loop
            Send("e")
            start.itemconfig(toggle_text, text='Start Test')
            start.itemconfig(startB, outline=green)

def define_test_clicked():
    global settings
    # Create a new window
    settings_window = tk.Toplevel(root)
    settings_window.title("PWM Settings")
    
    # Default values
    default_values = {
        "Test_Name": "",
        'pwm_step': str(settings[0]),
        'pwm_start': str(settings[1]),
        'pwm_end': str(settings[2]),
        'timestep': str(settings[3]),
    }
    
    # Variables to store the entries
    test_name_var = tk.StringVar(value=default_values["Test_Name"])
    pwm_step_var = tk.StringVar(value=default_values["pwm_step"])
    pwm_start_var = tk.StringVar(value=default_values["pwm_start"])
    pwm_end_var = tk.StringVar(value=default_values["pwm_end"])
    timestep_var = tk.StringVar(value=default_values["timestep"])

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
    timestep_entry = ttk.Entry(label_frame, textvariable=timestep_var)
    timestep_entry.grid(row=4, column=1, sticky=tk.EW, padx=5, pady=5)
    
    # Save button functionality
    def save_and_close():
        global settings, test_name
        # Store the values in variables
        test_name = test_name_var.get()
        pwm_step = float(pwm_step_var.get())
        pwm_start = float(pwm_start_var.get())
        pwm_end = float(pwm_end_var.get())
        timestep = float(timestep_var.get())
        settings = [pwm_step, pwm_start, pwm_end, timestep]
        # Print them (you can use them as needed)
        print("Saved values:")
        print(f"Run Name: {test_name}")
        print(settings)
        
        # Close the settings window
        #settings_window.destroy()
    
    # Save button
    save_button = ttk.Button(label_frame, text="Save", command=save_and_close)
    save_button.grid(row=5, column=0, columnspan=2, pady=10, padx=30)

    # Set as Default button
    save_button = ttk.Button(label_frame, text="Set as Default", command=save_test_config)
    save_button.grid(row=6, column=0, columnspan=2, pady=10)
    
    # Configure grid weights
    label_frame.columnconfigure(1, weight=1)

def data_config_clicked():
    global autolog, graph_x, graph_y
    # Create configuration window
    config_window = tk.Toplevel(root)
    config_window.title("Data Configuration")
    config_window.geometry("400x300")
    
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
        values=['time', 'pwm', 'current', 'rpm', 'thrust', 'torque'],
        state="readonly"
    )
    x_combo.grid(row=0, column=1, padx=5, pady=5)
    
    # Y variable selection
    tk.Label(graph_frame, text="Y-Axis:").grid(row=1, column=0, padx=5, pady=5)
    y_var = tk.StringVar(value=graph_y)
    y_combo = ttk.Combobox(
        graph_frame, 
        textvariable=y_var,
        values=['time', 'pwm', 'current', 'rpm', 'thrust', 'torque'],
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

def calibrate_clicked():
    Calibrate.itemconfig(toggle_text, text="Calibrate")
    Calibrate.itemconfig(calibrateB, outline=red)
    Send('c')
    time.sleep(4)
    Calibrate.itemconfig(toggle_text, text="Calibrated")
    Calibrate.itemconfig(calibrateB, outline=green)

# Runtime Functions
def fix_autostart():
    Send("i")
    Send("0")
    Send("e")

def test_loop():
    global kill, settings, t0, data, autolog
    # Reset data storage at start of test
    for key in data_map:
        data_map[key] = []
    
    t0 = time.time()  # Reset time reference when test starts
    Send('i')  # INIT TEST START
    start.itemconfig(toggle_text, text='Testing')
    pwm_step = settings[0]
    pwm_start = settings[1]
    pwm_end = settings[2]
    timestep = settings[3]
    pwm = pwm_start
    while pwm <= pwm_end and not kill:
        print(pwm)
        set_speed(pwm)
        Send(pwm)  # PWM signal Once
        time.sleep(timestep) 
        pwm += pwm_step     
    Send('e')  # End Test
    time.sleep(0.2)
    if autolog:
        logger_clicked()
    if gif_animation:
        root.after_cancel(gif_animation)
    if static_image and image_label:
        image_label.config(image=static_image)
    if kill:
        print("Test stopped")
        kill = True
        start.itemconfig(toggle_text, text='Start Test')
    else:
        print("Test completed, automatically logged")
        kill = True
        start.itemconfig(toggle_text, text='Start Test')

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
        #axis.set_xlabel(graph_x)
        #axis.set_ylabel(graph_y)
        axis.set_title(f"{graph_y} vs {graph_x}")
    
    # Set grid and background
    axis.grid(True)
    axis.set_facecolor("#dddddd")
    axis.tick_params(axis='x', colors='#001122')
    axis.tick_params(axis='y', colors='#001122')
    
    # Redraw canvas
    fig1.draw_idle()

def set_speed(value):
    global speed
    speed = value
    #Label3.config(text=f"PWM Cycle = {speed}%")

def set_autolog(value):
    global autolog
    autolog = value

def update_axes(x, y):
    global graph_x, graph_y
    graph_x = x
    graph_y = y
    update_graph()

# Tkinter functions
def Thrust_Title_Change(t):
    global Thrust_value
    Thrust_value = t
    Label2.config(text=f'Thrust = {t}')

def change_color(feature, new_color):
    # Feature-specific button outline change
    if feature == connect:
        feature.itemconfig(connectB, outline=new_color)
    elif feature == start:
        feature.itemconfig(startB, outline=new_color)
    elif feature == manimG:
        feature.itemconfig(manimB, outline=new_color)
    elif feature == logger:
        feature.itemconfig(loggerB, outline=new_color)
    elif feature == test:
        feature.itemconfig(testB, outline=new_color)
    elif feature == Calibrate:
        feature.itemconfig(calibrateB, outline=new_color)

def on_mouse_down(event):
    global lastx, lasty
    lastx = event.widget.winfo_pointerx()
    lasty = event.widget.winfo_pointery()

def move_cursor():
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
def logger_clicked():
    global data, data_map
    Output_Data = ""
    # Use data from our structured storage
    for i in range(len(data_map['time'])):
        Output_Data += (
            f"{data_map['time'][i]},"
            f"{data_map['pwm'][i]},"
            f"{data_map['current'][i]},"
            f"{data_map['rpm'][i]},"
            f"{data_map['thrust'][i]},"
            f"{data_map['torque'][i]}\n"
        )
    save_readings(Output_Data)

def save_readings(data):
    global test_name, kill,currentDIR
    if test_name == "":
        import datetime
        now = datetime.datetime.now()
        test_name = now.strftime("%y-%m-%d-%H-%M-%S")

    filename = f"{currentDIR}\\runs\\Thrust-Test-{test_name}.csv"            
    with open(filename, "w") as file:
        file.write("SSTL Thrust Test Platform\n")
        file.write("time,pwm,current,rpm,thrust,torque\n")
        file.write(f"{data}")
    print(f"File '{filename}' created and values written successfully.")

def graph_manim():
    ## Change button color
    manimG.itemconfig(toggle_text, text='Graphing')
    manimG.itemconfig(manimB, outline=green)
    # do something here
    arm.itemconfig(toggle_text, text='Exported')
    arm.itemconfig(armB, outline=red)

def load_images():
    global static_image, gif_frames, image_label
    
    # Load static image
    try:
        static_img = Image.open(currentDIR+"\\assets\\sstlab.png")
        static_img = static_img.resize((200, 200), Image.LANCZOS)
        static_image = ImageTk.PhotoImage(static_img)
    except Exception as e:
        print(f"Error loading static image: {e}")
        static_image = None
    
    # Load GIF frames
    try:
        gif = Image.open(currentDIR+"\\assets\\loading.gif")
        gif_frames = []
        for i in range(gif.n_frames):
            gif.seek(i)
            frame = gif.copy().resize((200, 200), Image.LANCZOS)
            gif_frames.append(ImageTk.PhotoImage(frame))
    except Exception as e:
        print(f"Error loading GIF: {e}")
        gif_frames = []
    
    # Create image label if it doesn't exist
    if image_label is None:
        image_label = tk.Label(root, bg='#dddddd')
        image_label.place(x=1010, y=200)  # Position in empty space
    
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
def debug_shortcuts(event):
    global t0, armed, kill
    readings = ""
    i = 0
    # Define actions based on the key pressed
    if event.name == 'space':
        Send("e")
        kill = True

def detect_key_press():
    # Hook the key press event to the debug_shortcuts function
    keyboard.on_press(debug_shortcuts)

#detect_key_press()
# GUI WINDOW
normal_color = "#5b3065"  # border
hover_color = "#ba5da3"
press_color = "#fffaaa"
fill_color = "#001122"
red = "#ff0000"
green = "#00ff00"
root = tk.Tk()
root.title("Thrust Bench")
root.geometry('1280x720+200+10')
root.resizable(False, False)
root.config(bg='#dddddd')  # background

# Serial port picker
port_frame = tk.Frame(root, bg='#dddddd')
port_frame.pack()
port_frame.place(y=505, x=1045)
port_frame.bind("<Enter>", refreshSerialPorts)
serial_title = tk.Label(port_frame, font=('Play', 14), fg='#001122', bg="#dddddd", text="Serial Port :")
serial_title.pack(side="left")
n = tk.StringVar()
SerialPorts = ttk.Combobox(port_frame, width=7, textvariable=n)
SerialPorts['values'] = (sp)
SerialPorts.pack(pady=15, padx=20, side=("right"))
SerialPorts.current()

# Setup the graph
Thrust_Figure = Figure(figsize=(5, 3), dpi=200)
Thrust_Figure.patch.set_facecolor("#dddddd")
axis = Thrust_Figure.add_subplot(111)
#axis.set_ylabel("Force")
#axis.set_xlabel("Time")
axis.set_facecolor("#dddddd")
axis.tick_params(axis='x', colors='#001122')
axis.tick_params(axis='y', colors='#001122')
axis.grid(True)

fig1 = FigureCanvasTkAgg(Thrust_Figure, root)
fig1.get_tk_widget().pack()
fig1.get_tk_widget().place(x=50, y=0)

# Test Label
Label1 = tk.Label(root, text='Test Name:', font="play 16 bold", fg="#001122", bg="#dddddd", highlightthickness=0)
Label1.pack()
Label1.place(x=970, y=70)

# Connect button
connect = Canvas(root, width=320*0.75, height=75*0.75, bg="#dddddd", borderwidth=0, highlightthickness=0)
p1 = (10*0.75, 10*0.75)
p2 = (10*0.75, 35*0.75)
p3 = (15*0.75, 45*0.75)
p4 = (15*0.75, 70*0.75)
p5 = (310*0.75, 70*0.75)
p6 = (310*0.75, 25*0.75)
p7 = (295*0.75, 10*0.75)
connectB = connect.create_polygon(
    p1, p2, p3, p4, p5, p6, p7,
    outline=normal_color, width=3,
    fill=fill_color
)

toggle_text = connect.create_text((160*0.75, 40*0.75), text="Connect", font="Play 12 bold", fill="white")
connect.place(x=1025, y=550)
connect.bind("<Enter>", lambda event: change_color(connect, hover_color))
connect.bind("<Leave>", lambda event: change_color(connect, normal_color))
connect.bind("<Button-1>", lambda event: change_color(connect, press_color))
connect.bind("<ButtonRelease-1>", lambda event: connect_clicked())

# Start Test button
start = Canvas(root, width=320*0.75, height=75*0.75, bg="#dddddd", borderwidth=0, highlightthickness=0)
p1 = (10*0.75, 10*0.75)
p2 = (10*0.75, 35*0.75)
p3 = (15*0.75, 45*0.75)
p4 = (15*0.75, 70*0.75)
p5 = (310*0.75, 70*0.75)
p6 = (310*0.75, 25*0.75)
p7 = (295*0.75, 10*0.75)
startB = start.create_polygon(
    p1, p2, p3, p4, p5, p6, p7,
    outline=normal_color, width=3,
    fill=fill_color
)

toggle_text = start.create_text((160*0.75, 40*0.75), text="Start Test", font="Play 12 bold", fill="white")
start.place(x=1025, y=620)
if connected:
    start.bind("<Enter>", lambda event: change_color(start, hover_color))
else:
    start.bind("<Enter>", lambda event: move_cursor())
start.bind("<Leave>", lambda event: change_color(start, normal_color))
start.bind("<Button-1>", lambda event: change_color(start, press_color))
start.bind("<ButtonRelease-1>", lambda event: start_clicked())

# Animate Graph button
manimG = Canvas(root, width=320*0.75, height=75*0.75, bg="#dddddd", borderwidth=0, highlightthickness=0)
p1 = (10*0.75, 10*0.75)
p2 = (10*0.75, 35*0.75)
p3 = (15*0.75, 45*0.75)
p4 = (15*0.75, 70*0.75)
p5 = (310*0.75, 70*0.75)
p6 = (310*0.75, 25*0.75)
p7 = (295*0.75, 10*0.75)
manimB = manimG.create_polygon(
    p1, p2, p3, p4, p5, p6, p7,
    outline=normal_color, width=3,
    fill=fill_color
)
toggle_text = manimG.create_text((160*0.75, 40*0.75), text="Animate Graph", font="Play 12 bold", fill="white")
manimG.place(x=280, y=620)
manimG.bind("<Button-1>", lambda event: change_color(manimG, press_color))
manimG.bind("<ButtonRelease-1>", lambda event: graph_manim())
manimG.bind("<Enter>", lambda event: change_color(manimG, hover_color))
manimG.bind("<Leave>", lambda event: change_color(manimG, normal_color))

# Data Configuration button (replaces Logger)
logger = Canvas(root, width=320*0.75, height=75*0.75, bg="#dddddd", borderwidth=0, highlightthickness=0)
loggerB = logger.create_polygon(
    p1, p2, p3, p4, p5, p6, p7,
    outline=normal_color, width=2,
    fill=fill_color
)
logger.create_text((160*0.75, 40*0.75), text="Data Config", font="Play 12 bold", fill="white")
logger.place(x=530, y=620)
logger.bind("<Enter>", lambda event: change_color(logger, hover_color))
logger.bind("<Leave>", lambda event: change_color(logger, normal_color))
logger.bind("<Button-1>", lambda event: change_color(logger, press_color))
logger.bind("<ButtonRelease-1>", lambda event: data_config_clicked())

# Define Test button
test = Canvas(root, width=320*0.75, height=75*0.75, bg="#dddddd", borderwidth=0, highlightthickness=0)
p1 = (10*0.75, 10*0.75)
p2 = (10*0.75, 35*0.75)
p3 = (15*0.75, 45*0.75)
p4 = (15*0.75, 70*0.75)
p5 = (310*0.75, 70*0.75)
p6 = (310*0.75, 25*0.75)
p7 = (295*0.75, 10*0.75)
testB = test.create_polygon(
    p1, p2, p3, p4, p5, p6, p7,
    outline=normal_color, width=3,
    fill=fill_color
)
toggle_text = test.create_text((160*0.75, 40*0.75), text="Define Test", font="Play 12 bold", fill="white")
test.place(x=775, y=620)

test.bind("<Enter>", lambda event: change_color(test, hover_color))
test.bind("<Leave>", lambda event: change_color(test, normal_color))
test.bind("<Button-1>", lambda event: change_color(test, press_color))
test.bind("<ButtonRelease-1>", lambda event: define_test_clicked())

# Calibrate button
Calibrate = Canvas(root, width=320*0.75, height=75*0.75, bg="#dddddd", borderwidth=0, highlightthickness=0)
calibrateB = Calibrate.create_polygon(
    p1, p2, p3, p4, p5, p6, p7,
    outline=normal_color, width=2,
    fill=fill_color
)
Calibrate.create_text((160*0.75, 40*0.75), text="Calibrate", font="Play 12 bold", fill="white")
Calibrate.place(x=30, y=620)
Calibrate.bind("<Button-1>", lambda event: change_color(Calibrate, press_color))
Calibrate.bind("<ButtonRelease-1>", lambda event: calibrate_clicked())

# Serial monitor
serial_frame = Frame(width=1280, height=180)
serial_frame.place(y=720)
serial_monitor = scrolledtext.ScrolledText(
    serial_frame, 
    width=114,  
    height=7,  
    font=("Arial", 15)
) 
serial_monitor.pack(padx=4)
serial_sender = tk.Entry(root, width=1280)
serial_sender.pack(side='bottom')
serial_sender.bind('<Return>', Send_text)

load_images()
root.mainloop()
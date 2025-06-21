import os
import math
import time
import random
import keyboard
import threading
import pyautogui
import numpy as np
import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import simpledialog
from serial_sniffer import serial_ports
from serial_communicator import Serial_Communications

sp=serial_ports()
print(sp)
connected=False 
currentDIR=os.getcwd()
armed=False
kill = False  
autolog=False
calibrate_state=False # Did you calibrate the esc
speed=0
Thrust_value=0
settings=[1,0,10,0.2]
test_name=""
data=""

def Send(a): # Send to Serial Port func
    global Serial
    Serial.send(f"{a}")

def Send_text(event=None): # Send to Serial Port from user input
    global b,Serial,armed
    if armed:
        Serial.send(serial_sender.get()) # serial_sender is the textbox
        serial_sender.delete(0, tk.END)

def refreshSerialPorts(event=None): # checks if a serial port is connected or disconnected while connected
    global sp
    sp=serial_ports()
    SerialPorts['values'] = (sp) 

def connect_clicked():
    global connected,c,Serial,t0
    refreshSerialPorts()
    if connected==True:
        print('stopped')
        connect.itemconfig(toggle_text,text='COM Stopped')
        connected=False
        Serial.close()
    else :
        connected = True
        t0=time.time()
        try:
            print('started')
            connect.itemconfig(toggle_text,text='COM Started')
            COM=SerialPorts.get()
            Serial=Serial_Communications(COM,9600)
            fix_autostart()
            #serial_clicked()
            pass
        except Exception as e:
            print('Error While Opening Serial Port')

def fix_autostart():
    arm_clicked()
    Send("i")
    Send("0")
    Send("e")
    arm_clicked()

def start_clicked():
    global armed,kill
    global speed
    if armed:
        if start.itemconfig(toggle_text)['text'][4] == 'Start Test':  # If button says "Start Test"
            kill = False  # Reset kill flag
            testThread = threading.Thread(target=test_loop)
            testThread.start()
            start.itemconfig(toggle_text, text='Stop Test')
            start.itemconfig(startB, outline=red)
        else:  # If button says "Stop Test"
            kill = True  # Set kill flag to stop the loop
            start.itemconfig(toggle_text, text='Start Test')
            start.itemconfig(startB, outline=green)
            Send(0)  # Send 0 to stop the motor
            Send("e")
    else:
        Send("0") 
        Send("e") # Disarm the motor
        start.itemconfig(toggle_text, text='Start Test')
        start.itemconfig(startB, outline=green)

def test_loop():
    global kill, settings, t0, data,autolog
    t0 = time.time()  # Reset time reference when test starts
    Send('i') #INIT TEST START
    pwm_step = settings[0]
    pwm_start = settings[1]
    pwm_end = settings[2]
    timestep = settings[3]
    
    pwm = pwm_start
    while pwm <= pwm_end and not kill:
        start_time = time.time()
        set_speed(pwm)
        # Continuously send PWM and receive data for the entire timestep duration
        while (time.time() - start_time) < timestep and not kill:
            Send(pwm)  # Continuously send PWM signal
            time.sleep(0.05)  # Small delay to avoid overwhelming serial       
        pwm += pwm_step

    #Read Inputs
    serial_clicked()
    time.sleep(0.2)
    if autolog:
        logger_clicked()
    if kill:
        print("Test stopped")
        kill=True
    else:
        print("Test completed, automatically logged")

def serial_clicked():
    #serialThread=threading.Thread(target=SerialRefresh).start()
    serialThread=threading.Thread(target=SerialMonitorRefresh).start()

def SerialRefresh():
    global Serial,data
    while True:
        readings = Serial.read()
        data+=readings+'\n'

def SerialMonitorRefresh():
    global Serial,data
    buffer = []
    last_flush_time = time.time()
    
    while True:
        readings = Serial.read()
        data+=readings

def logger_clicked():
    global data
    Data=""
    data.strip()
    lines=data.split('$')
    for line in lines:
        Data+=line[:-3]
        Data+='\n'
    save_readings(Data)
    data=""

def save_readings(data):
    global test_name
    if test_name=="":
        import datetime
        now = datetime.datetime.now()
        test_name = now.strftime("%y-%m-%d-%H-%M-%S")

    filename = f"Thrust-Test-{test_name}.csv"            
    with open(filename, "w") as file:
        file.write("SSTL Thrust Test Platform\n")
        file.write("Time,PWM,Thrust\n")
        file.write(f"{data}\n")
    print(f"File '{filename}' created and values written successfully.")

def arm_clicked():
    global armed,calibrate_state
    if not(armed):
        armed=True

        ##Change button color
        arm.itemconfig(toggle_text,text='Armed')
        arm.itemconfig(armB,outline=green)
        print("Armed")
    else:
        armed=False
        Send("0") # set speed = 0
        Send('e') # Disarm the motor
        arm.itemconfig(toggle_text,text='Not Armed')
        arm.itemconfig(armB,outline=red)
        print("Not armed")

def calibrate_clicked():
    Calibrate.itemconfig(toggle_text, text="Calibrate")
    Calibrate.itemconfig(calibrateB,outline=red)
    Send('c')
    time.sleep(4)
    Calibrate.itemconfig(toggle_text, text="Calibrated")
    Calibrate.itemconfig(calibrateB,outline=green)

def test_clicked():
    global settings
    # Create a new window
    settings_window = tk.Toplevel(root)
    settings_window.title("PWM Settings")
    
    # Default values
    default_values = {
        "Test_Name":"",
        "pwm_step": "5",
        "pwm_start": "0",
        "pwm_end": "100",
        "timestep": "2"
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
        test_name=test_name_var.get()
        pwm_step = float(pwm_step_var.get())
        pwm_start = float(pwm_start_var.get())
        pwm_end = float(pwm_end_var.get())
        timestep = float(timestep_var.get())
        settings = [pwm_step,pwm_start,pwm_end,timestep]
        
        # Print them (you can use them as needed)
        print("Saved values:")
        print(f"Run Name: {test_name}")
        print(f"PWM Step: {pwm_step}")
        print(f"PWM Start: {pwm_start}")
        print(f"PWM End: {pwm_end}")
        print(f"Timestep: {timestep}")
        
        # Close the settings window
        settings_window.destroy()
    
    # Save button
    save_button = ttk.Button(label_frame, text="Save", command=save_and_close)
    save_button.grid(row=5, column=0, columnspan=2, pady=10)
    
    # Configure grid weights
    label_frame.columnconfigure(1, weight=1)

def set_speed(value):
        global speed
        speed = value
        #Label3.config(text=f"PWM Cycle = {speed}%")

def open_speed_window():
    speed_window = tk.Toplevel()
    speed_window.title("Select Speed")
    # Create buttons for 25%, 50%, 75%, and 100%
    buttons = [("0%", 0),("25%", 25), ("50%", 50), ("75%", 75), ("100%", 100)]

    for (text, value) in buttons:
        button = tk.Button(speed_window, text=text, command=lambda v=value: set_value(v,speed_window))
        button.pack(pady=5)
    # Entry for custom speed input
    custom_entry = tk.Entry(speed_window)
    custom_entry.pack(pady=5)
    def set_value(v,window):
        set_speed(v)
        close_window(window)
    def close_window(window):
        speed_window.destroy()  # Close the window

    def add_custom_speed():
        try:
            custom_value = float(custom_entry.get())
            if custom_value < 0:
                custom_value= -custom_value
            if custom_value> 100:
                custom_value=100
            set_speed(custom_value)
            close_window(speed_window)
        except ValueError:
            print("Please enter a valid number")

    # Button to add custom speed
    add_button = tk.Button(speed_window, text="Send Custom Speed", command=add_custom_speed)
    add_button.pack(pady=5)

def Thrust_Title_Change(t):
    noting=0
    #Label2.config(text=f'Thrust= {t}')

def change_color(feature,new_color):
    #feature.itemconfig(f"{feature}B", outline=new_color)
    feature.itemconfig(connectB, outline=new_color)

def on_mouse_down(event):
  global lastx, lasty
  lastx = event.widget.winfo_pointerx()
  lasty = event.widget.winfo_pointery()

def move_cursor():
    if not armed:
        direction=[-1,1]
        a=random.randint(50,200)*random.choice(direction)
        b=random.randint(50,200)*random.choice(direction)
        pyautogui.move(a,b,duration=0.02)

def on_mouse_move(event):
  global lastx, lasty
  deltax = event.widget.winfo_pointerx() - lastx
  deltay = event.widget.winfo_pointery() - lasty
  root.geometry("+%d+%d" % (root.winfo_x() + deltax, root.winfo_y() + deltay))
  lastx = event.widget.winfo_pointerx()
  lasty = event.widget.winfo_pointery()

def debug_shortcuts(event):
    global  t0,armed,kill
    readings=""
    i=0
    # Define actions based on the key pressed
    if event.name == 'space':
        Send("0")
        armed=False
        kill=True
'''
def detect_key_press():
    # Hook the key press event to the debug_shortcuts function
    keyboard.on_press(debug_shortcuts)

detect_key_press()
'''
# GUI WINDOW
normal_color = "#5b3065" #border
hover_color = "#ba5da3"
press_color = "#fffaaa"
fill_color="#001122"
red="#ff0000"
green="#00ff00"
root=tk.Tk()
root.title("Thrust Bench")
root.geometry('1280x720+200+10')
root.resizable(False, False)
root.config(bg='#dddddd') # background



# Serial port picker
port_frame=tk.Frame(root,bg='#dddddd')
port_frame.pack()
port_frame.place(y=505,x=1045)
port_frame.bind("<Enter>",refreshSerialPorts)
serial_title=tk.Label(port_frame,font=('Play',14),fg='#001122',bg="#dddddd",text="Serial Port :")
serial_title.pack(side="left")
n = tk.StringVar() 
SerialPorts = ttk.Combobox(port_frame, width = 7, textvariable = n) 
SerialPorts['values'] = (sp) 
SerialPorts.pack(pady=15,padx=20,side=("right"))
SerialPorts.current() 



#Connect button
connect = Canvas(root,width=320*0.75,height=75*0.75, bg="#dddddd",borderwidth=0,highlightthickness=0)
p1 = (10*0.75, 10*0.75)
p2=(10*0.75,35*0.75)
p3=(15*0.75,45*0.75)
p4=(15*0.75,70*0.75)
p5=(310*0.75,70*0.75)
p6=(310*0.75,25*0.75)
p7=(295*0.75,10*0.75)
connectB = connect.create_polygon(
p1,p2,p3,p4,p5,p6,p7,
outline=normal_color, width=3,
fill=fill_color
)

toggle_text=connect.create_text((160*0.75,40*0.75), text="Connect", font="Play 12 bold",fill="white")
connect.place(x=1025,y=550)
connect.bind("<Enter>", lambda event: change_color(connect,hover_color))
connect.bind("<Leave>", lambda event: change_color(connect,normal_color))
connect.bind("<Button-1>", lambda event: change_color(connect,press_color))
connect.bind("<ButtonRelease-1>", lambda event: connect_clicked())



#Start Test button
start = Canvas(root,width=320*0.75,height=75*0.75, bg="#dddddd",borderwidth=0,highlightthickness=0)
p1 = (10*0.75, 10*0.75)
p2=(10*0.75,35*0.75)
p3=(15*0.75,45*0.75)
p4=(15*0.75,70*0.75)
p5=(310*0.75,70*0.75)
p6=(310*0.75,25*0.75)
p7=(295*0.75,10*0.75)
startB = start.create_polygon(
p1,p2,p3,p4,p5,p6,p7,
outline=normal_color, width=3,
fill=fill_color
)

toggle_text=start.create_text((160*0.75,40*0.75), text="Start Test", font="Play 12 bold",fill="white")
start.place(x=1025,y=620)
start.bind("<Enter>", lambda event: change_color(start,hover_color))
start.bind("<Leave>", lambda event: change_color(start,normal_color))
start.bind("<Button-1>", lambda event: change_color(start,press_color))
start.bind("<ButtonRelease-1>", lambda event: start_clicked())


#arm button
arm = Canvas(root,width=320*0.75,height=75*0.75, bg="#dddddd",borderwidth=0,highlightthickness=0)
p1 = (10*0.75, 10*0.75)
p2=(10*0.75,35*0.75)
p3=(15*0.75,45*0.75)
p4=(15*0.75,70*0.75)
p5=(310*0.75,70*0.75)
p6=(310*0.75,25*0.75)
p7=(295*0.75,10*0.75)
armB = arm.create_polygon(
p1,p2,p3,p4,p5,p6,p7,
outline=normal_color, width=3,
fill=fill_color
)
toggle_text=arm.create_text((160*0.75,40*0.75), text="Arm", font="Play 12 bold",fill="white")
arm.place(x=775,y=620)
arm.bind("<Button-1>", lambda event: change_color(arm,press_color))
arm.bind("<ButtonRelease-1>", lambda event: arm_clicked())
arm.bind("<Enter>", lambda event: change_color(arm,hover_color))
arm.bind("<Leave>", lambda event: change_color(arm,normal_color))


# Logger
logger = Canvas(root,width=320*0.75,height=75*0.75, bg="#dddddd",borderwidth=0,highlightthickness=0) #button
loggerB = logger.create_polygon(
    p1,p2,p3,p4,p5,p6,p7,
outline=normal_color, width=2,
fill=fill_color
)
logger.create_text((160*0.75,40*0.75), text="Log Data", font="Play 12 bold",fill="white")
logger.place(x=530,y=620)
logger.bind("<Enter>", lambda event: change_color(logger,hover_color))
logger.bind("<Leave>", lambda event: change_color(logger,normal_color))
logger.bind("<Button-1>", lambda event: change_color(logger,press_color))
logger.bind("<ButtonRelease-1>", lambda event: logger_clicked())

#define test button
test = Canvas(root,width=320*0.75,height=75*0.75, bg="#dddddd",borderwidth=0,highlightthickness=0)
p1 = (10*0.75, 10*0.75)
p2=(10*0.75,35*0.75)
p3=(15*0.75,45*0.75)
p4=(15*0.75,70*0.75)
p5=(310*0.75,70*0.75)
p6=(310*0.75,25*0.75)
p7=(295*0.75,10*0.75)
testB = test.create_polygon(
p1,p2,p3,p4,p5,p6,p7,
outline=normal_color, width=3,
fill=fill_color
)
toggle_text=test.create_text((160*0.75,40*0.75), text="Define Test", font="Play 12 bold",fill="white")
test.place(x=280,y=620)

test.bind("<Enter>", lambda event: change_color(test,hover_color))
test.bind("<Leave>", lambda event: change_color(test,normal_color))
test.bind("<Button-1>", lambda event: change_color(test,press_color))
test.bind("<ButtonRelease-1>", lambda event: test_clicked())

# Serial monitor
Calibrate = Canvas(root,width=320*0.75,height=75*0.75, bg="#dddddd",borderwidth=0,highlightthickness=0) #button
calibrateB = Calibrate.create_polygon(
p1,p2,p3,p4,p5,p6,p7,
outline=normal_color, width=2,
fill=fill_color
)
Calibrate.create_text((160*0.75,40*0.75), text="Calibrate", font="Play 12 bold",fill="white")
Calibrate.place(x=30,y=620)
#Calibrate.bind("<Enter>", lambda event: change_color(Calibrate,hover_color))
#Calibrate.bind("<Leave>", lambda event: change_color(Calibrate,normal_color))
Calibrate.bind("<Button-1>", lambda event: change_color(Calibrate,press_color))
Calibrate.bind("<ButtonRelease-1>", lambda event: calibrate_clicked())

serial_frame=Frame(width=1280,height=180)
serial_frame.place(y=720)
serial_monitor = scrolledtext.ScrolledText(serial_frame, 
                            width = 114,  
                            height = 7,  
                            font = ("Arial", 
                                    15)) 
serial_monitor.pack(padx=4)
serial_sender=tk.Entry(root,width=1280)
serial_sender.pack(side='bottom')
serial_sender.bind('<Return>',Send_text)

root.mainloop()
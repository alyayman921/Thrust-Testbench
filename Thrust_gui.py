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
from matplotlib.figure import Figure
from serial_sniffer import serial_ports
from serial_communicator import Serial_Communications
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg




sp=serial_ports()
print(sp)
running=False
expanded=False
currentDIR=os.getcwd()
armed=False
speed=0
Thrust_value=0


def connect_clicked():
    global running,c,Serial,t0
    refreshSerialPorts()
    if running==True:
        print('stopped')
        connect.itemconfig(toggle_text,text='COM Stopped')
        running=False
        Serial.close()
    else :
        running = True
        print('started')
        connect.itemconfig(toggle_text,text='COM Started')
        t0=time.time()
        try:
            COM=SerialPorts.get()
            Serial=Serial_Communications(COM,9600)
            SerialMonitor()
            pass
        except Exception as e:
            print('Error While Opening Serial Port')

def start_clicked():
    global armed
    global speed
    if armed:
        Send(f"{speed}") #Sent Values
        start.itemconfig(toggle_text,text='Push Motor Speed')
        start.itemconfig(startB,outline=green)
    else:
        start.itemconfig(toggle_text,text='Test Stopped')
        start.itemconfig(startB,outline=red)

def SerialMonitor():
    global expanded
    if expanded:
        expanded=False
        root.geometry("1280x720")
        root.after(0, root.update)
    else:
        expanded=True
        root.geometry("1280x905")
        root.after(0, root.update)
        serialThread=threading.Thread(target=SerialMonitorRefresh).start()
def SerialMonitorRefresh():
    global Serial
    #global t0
    while expanded:
        readings=Serial.read()
        if readings!="":
            Thrust_Title_Change(readings)
            #if readings!="0":
                
            update_graph(readings)
            serial_monitor.insert(tk.END, readings+'\n')
            serial_monitor.see(tk.END)
            

        pass
def Send(a): # Send to Serial Port func
    global Serial
    Serial.send(a)

def Send_text(event=None): # Send to Serial Port from user input
    global b,Serial,armed
    if armed:
        Serial.send(serial_sender.get()) #
        serial_sender.delete(0, tk.END)

def refreshSerialPorts(event=None): # checks if a serial port is connected or disconnected while running
    global sp
    sp=serial_ports()
    SerialPorts['values'] = (sp) 

def on_mouse_down(event):
  global lastx, lasty
  lastx = event.widget.winfo_pointerx()
  lasty = event.widget.winfo_pointery()

def on_mouse_move(event):
  global lastx, lasty
  deltax = event.widget.winfo_pointerx() - lastx
  deltay = event.widget.winfo_pointery() - lasty
  root.geometry("+%d+%d" % (root.winfo_x() + deltax, root.winfo_y() + deltay))
  lastx = event.widget.winfo_pointerx()
  lasty = event.widget.winfo_pointery()

def change_color(feature,new_color):
    #feature.itemconfig(f"{feature}B", outline=new_color)
    feature.itemconfig(connectB, outline=new_color)

def arm_clicked():
    global armed
    if not(armed):
        armed=True
        ##Change button color
        arm.itemconfig(toggle_text,text='Armed')
        arm.itemconfig(armB,outline=green)
        print("armed")
    else:
        armed=False
        Send("0") # Disarm the motor
        arm.itemconfig(toggle_text,text='Not Armed')
        arm.itemconfig(armB,outline=red)
        print("not armed")

def set_speed(value):
        global speed
        speed = value
        print(f"Selected Speed: {speed}")
        Label3.config(text=f"PWM Cycle = {speed}%")

def open_speed_window():
    speed_window = tk.Toplevel()
    speed_window.title("Select Speed")
    # Create buttons for 25%, 50%, 75%, and 100%
    buttons = [("0%", 0),("25%", 25), ("50%", 50), ("75%", 75), ("100%", 100)]
    for (text, value) in buttons:
        button = tk.Button(speed_window, text=text, command=lambda v=value: set_speed(v))
        button.pack(pady=5)
    # Entry for custom speed input
    custom_entry = tk.Entry(speed_window)
    custom_entry.pack(pady=5)
    def close_window():
        speed_window.destroy()  # Close the window

    def add_custom_speed():
        try:
            custom_value = float(custom_entry.get())
            if custom_value < 0:
                custom_value= -custom_value
            if custom_value> 100:
                custom_value=100
            set_speed(custom_value)
        except ValueError:
            print("Please enter a valid number")

    # Button to add custom speed
    add_button = tk.Button(speed_window, text="Add Custom Speed", command=add_custom_speed)
    add_button.pack(pady=5)

def Thrust_Title_Change(t):
    Label2.config(text=f'Thrust= {t} N')
def move_cursor():
    if not armed:
        direction=[-1,1]
        a=random.randint(50,200)*random.choice(direction)
        b=random.randint(50,200)*random.choice(direction)
        pyautogui.move(a,b,duration=0.105)
def update_graph(thrust):
    global t0,x,y,y2
    try:
        y.append(float(thrust))
        #y2.append(float(thrust)*20)
        x.append(time.time() - t0)
    except ValueError:
        print(f"Skipping non-numeric value: {thrust}")

    
    # Plot the new data
    axis.plot(x, y, linestyle="-", color="b", label="Thrust")
    #axis2.plot(x, y2, linestyle="-", color="b", label="Torque")
    
    # Dynamically adjust the y-axis limits
    if y:  # Ensure there are valid y values to set limits
        axis.set_ylim(min(y) - 1, max(y) + 1)  # Adjust the limits as needed
        #axis2.set_ylim(min(y2) - 1, max(y2) + 1)  # Adjust the limits as needed
    
    # Redraw the canvas
    fig1.draw()
    #fig2.draw()

# Create the filename
def save_readings(data):
    import datetime
    now = datetime.datetime.now()
    timestamp = now.strftime("%y-%m-%d-%H-%M")
    print(timestamp)
    filename = f"Thrust-{timestamp}.txt"            
    with open(filename, "w") as file:
        file.write("SSTL Thrust Test Platform\n")
        file.write(f"{data}\n")
    print(f"File '{filename}' created and values written successfully.")

def debug_shortcuts(event):
    global  t0
    global x,y,y2
    readings=""
    i=0
    # Define actions based on the key pressed
    if event.name == 'space':
        Send("0")
        armed=False
        # make the button show "ARM"
    if event.name=='g':
        update_graph(np.sin(random.randint(0,2*180)))
    if event.name=="s":
        t0=time.time()
    if event.name=="l":
        while i<len(x):
            readings+=f"Time ={x[i]}, Thrust={y[i]}, Torque={y2[i]}\n"
            i+=1
        print(readings)
        save_readings(readings)

def detect_key_press():
    # Hook the key press event to the debug_shortcuts function
    keyboard.on_press(debug_shortcuts)
#threading.Thread(target=detect_key_press).start()
detect_key_press()

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

#root.iconbitmap(f"{currentDIR}/controller_assets/icon.ico")

#Figures
Thrust_Figure = Figure(figsize=(5, 2.8), dpi=200)
Thrust_Figure.patch.set_facecolor("#dddddd")
axis = Thrust_Figure.add_subplot(111)
axis.set_title("Thrust figure")
#axis.set_xlabel("Time")
axis.set_ylabel("Force")
axis.set_facecolor("#dddddd")
axis.tick_params(axis='x', colors='#001122')  # Change x-axis ticks color
axis.tick_params(axis='y', colors='#001122')  # Change y-axis ticks color
axis.set_title("Thrust", color='#001122')  # Change title color
#axis.legend()
x = []
y = []
fig1 = FigureCanvasTkAgg(Thrust_Figure, root)
fig1.get_tk_widget().pack()
fig1.get_tk_widget().place(x=50,y=50)

#Torque Figure
#Tourqe_Figure = Figure(figsize=(3, 2), dpi=200)
#Tourqe_Figure.patch.set_facecolor("#dddddd")
#axis2 = Tourqe_Figure.add_subplot(111)
#axis2.set_title("Torque figure")
#axis2.set_xlabel("Time")
#axis2.set_ylabel("Torque")
#axis2.set_facecolor("#dddddd")
#axis2.tick_params(axis='x', colors='#001122')  # Change x-axis ticks color
#axis2.tick_params(axis='y', colors='#001122')  # Change y-axis ticks color
#axis2.set_title("Torque ", color='#001122')  # Change title color
#axis.legend()
#y2 = []
#fig2 = FigureCanvasTkAgg(Tourqe_Figure, root)
#fig2.get_tk_widget().pack()
#fig2.get_tk_widget().place(x=650,y=150)




#Title
#Label1=tk.Label(root,text='Thrust Test Platform',font="play 24 bold",fg="#001122", bg="#dddddd",highlightthickness=0)
#Label1.pack()
#Label1.place(x=40,y=40)

#Thrust
RPM_Value="0"
Label2=tk.Label(root,text=f'RPM = {RPM_Value}',font="play 16 bold",fg="#001122", bg="#dddddd",highlightthickness=0)
Label2.pack()
Label2.place(x=900,y=100)

#Motor Speed
Label3=tk.Label(root,text=f'PWM Cycle = 0%',font="play 16 bold",fg="#001122", bg="#dddddd",highlightthickness=0)
Label3.pack()
Label3.place(x=100,y=100)


# Serial port picker
port_frame=tk.Frame(root,bg='#dddddd')
port_frame.pack()
port_frame.place(y=575,x=1045)
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
connect.place(x=1025,y=620)
connect.bind("<Enter>", lambda event: change_color(connect,hover_color))
connect.bind("<Leave>", lambda event: change_color(connect,normal_color))
connect.bind("<Button-1>", lambda event: change_color(connect,press_color))
connect.bind("<ButtonRelease-1>", lambda event: connect_clicked())

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






# Speed Controller
speed_controller = Canvas(root,width=320*0.75,height=75*0.75, bg="#dddddd",borderwidth=0,highlightthickness=0) #button
speedB = speed_controller.create_polygon(
p1,p2,p3,p4,p5,p6,p7,
outline=normal_color, width=2,
fill=fill_color
)
speed_controller.create_text((160*0.75,40*0.75), text="Speed Controller", font="Play 12 bold",fill="white")
speed_controller.place(x=530,y=620)
speed_controller.bind("<Enter>", lambda event: change_color(speed_controller,hover_color))
speed_controller.bind("<Leave>", lambda event: change_color(speed_controller,normal_color))
speed_controller.bind("<Button-1>", lambda event: change_color(speed_controller,press_color))
speed_controller.bind("<ButtonRelease-1>", lambda event: open_speed_window())


#start button
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
toggle_text=start.create_text((160*0.75,40*0.75), text="Push Motor Speed", font="Play 12 bold",fill="white")
start.place(x=280,y=620)

start.bind("<Enter>", lambda event: change_color(start,hover_color))
start.bind("<Enter>", lambda event: move_cursor())
start.bind("<Leave>", lambda event: change_color(start,normal_color))
start.bind("<Button-1>", lambda event: change_color(start,press_color))
start.bind("<ButtonRelease-1>", lambda event: start_clicked())

# Serial monitor
sm_button = Canvas(root,width=320*0.75,height=75*0.75, bg="#dddddd",borderwidth=0,highlightthickness=0) #button
smB = sm_button.create_polygon(
p1,p2,p3,p4,p5,p6,p7,
outline=normal_color, width=2,
fill=fill_color
)
sm_button.create_text((160*0.75,40*0.75), text="Serial Monitor", font="Play 12 bold",fill="white")
sm_button.place(x=30,y=620)
sm_button.bind("<Enter>", lambda event: change_color(sm_button,hover_color))
sm_button.bind("<Leave>", lambda event: change_color(sm_button,normal_color))
sm_button.bind("<Button-1>", lambda event: change_color(sm_button,press_color))
sm_button.bind("<ButtonRelease-1>", lambda event: SerialMonitor())

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
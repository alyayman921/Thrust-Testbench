import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
import random
import math
# Create a basic Tkinter window
root = tk.Tk()
root.title("Graph in Tkinter")
root.geometry("600x400")

# Create a Figure object and add a plot to it
figure = Figure(figsize=(3, 2), dpi=200)
ax = figure.add_subplot(111)
ax.set_title("Sample Graph")
ax.set_xlabel("X Axis")
ax.set_ylabel("Y Axis")
ax.legend()
ax.set_facecolor("#ffffff")
# Example data to plot
x = []
y = []
pi=3.14159
# Plot the data
def update():
	i=0
	while True:
		x.append(i)
		rpm=random.randint(0,100)
		y.append(math.sin(x[i]*pi/30)*100)
		ax.plot(x, y, linestyle="-", color="b", label="y = x^2")
		i+=1
		time.sleep(0.001)
		canvas.draw()

canvas = FigureCanvasTkAgg(figure, root)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
threading.Thread(target=update).start()
# Integrate the Figure with Tkinter using FigureCanvasTkAgg

# Run the Tkinter event loop
root.mainloop()

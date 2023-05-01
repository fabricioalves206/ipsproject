#! /usr/bin/python3

import serial
import threading
import time
from tkinter import *
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk)


# cleaning buffer
def clearBuffer():
    ser.read_all()
    ser.flushOutput()
    ser.flushInput()
    ser.flush()


def onPushSend():
    try:
        # read the command line and get which value and function
        line = strToSend.get()
        command = line.split("=", 1)
        value = command[1]
        func = command[0]
        match func:
            case 'gain':
                msg = "$" + "G" + value + "#"
            case 'pi':
                msg = "$" + "P" + value + "#"
            case _:
                print("command doesnt exist")
                return

        # send the command
        for i in range (0,3):
            ser.write(msg.encode())
            print("msg sent !")

        # format command line
        sendButton.text = ""
        labelCommandSent.config(fg="blue")
        time.sleep(0.005)
        labelCommandSent.config(fg=ui.cget('bg'))

    except Exception:
        print("Command not sent")


def receive():
    if data[0] == b'P':
        strReceivedPower.set(data[1])
    if data[0] == b'C':
        strReceivedCurrent.set(data[1])
    if data[0] == b'G':
        strReceivedGain.set(data[1])
    ui.after(1, receive)


def update_plot():
    global plot_data, buffer_size
    try:
        data_float = float(data[1])
    except Exception:
        data_float = 0.0
    plot_data.append(data_float)

# removing old data from the graphic
    if len(plot_data) > buffer_size:
      plot_data.pop(0)
    ax.plot(plot_data, markevery=50)
    figure_canvas.draw()
    ui.after(100, update_plot)

# other way to plot data
'''
    x.append(time.time())
    y.append(int(data_float))
    ax.clear()
    ax.plot(x, y)
    ax.set_xlabel('Tempo (s)')
    ax.set_ylabel('Dados')
    ax.set_title('Gráfico em Tempo Real')
'''


def serialevent():
    global data, type_data, ser
    mesure = []
    clearBuffer()
    while True:
        while not stop_reading.is_set():
            while ser.inWaiting() == 0:
                data = ("NDA", 'NDA')
            data_byte = ser.read(1)
            if data_byte == b'$':
                type_data = ser.read(1)
                while data_byte != b'#':
                    data_byte = ser.read(1)
                    data_str = data_byte.decode('utf-8').rstrip('\r\n')
                    if data_str.isdigit():
                        mesure.append(data_str)
                data = (type_data, ''.join(mesure))
                mesure.clear()
                time.sleep(0.005)
        ui.title("IHM - Stopped")

# initializing communication
port = '/dev/ttyACM0'
baudrate = 115200

try:
    ser = serial.Serial(port, baudrate, bytesize=8, parity='N', stopbits=1, timeout=None, rtscts=False,
                        dsrdtr=False)
    print("serial port " + ser.name + " opened")
except Exception:
    print("error open serial port: " + port)
    exit()

# making sure there is no data
while ser.inWaiting() > 0:
   pass

# variable to stop reading when we want to send command
stop_reading = threading.Event()

# les donnes vont être ecrites ici pendant le temps que la thread est activate
data = ()
type_data = ""
plot_data = []
buffer_size = 1000
x = []
y = []

t = threading.Thread(target=serialevent)
t.start()

# creating IHM
ui = Tk()

ui.title("IHM")
ui.geometry("1000x400")

main_frame = Frame(ui)

labelToSendMes = Label(main_frame, text="Command to Send", font=("Arial", 10), fg="black")
labelCommandSent = Label(main_frame, text="Command sent !", font=("Arial", 10), fg="blue")
strToSend = StringVar()
toSendEntry = Entry(main_frame, textvariable=strToSend)

sendButton = Button(main_frame, text="SEND", font=("Arial", 10, "bold"), bg="seagreen3", fg="black", bd=3,
                    relief=RAISED, command=onPushSend)

labelReceivedMesPower = Label(main_frame, text="Last Data Received power", font=("Arial", 10), fg="black")
labelReceivedMesCurrent = Label(main_frame, text="Last Data Received current", font=("Arial", 10), fg="black")
labelReceivedMesGain =  Label(main_frame, text="Gain", font=("Arial", 10), fg="black")
strReceivedPower = StringVar()
strReceivedCurrent = StringVar()
strReceivedGain = StringVar()
receivedEntryPower = Entry(main_frame, textvariable=strReceivedPower)
receivedEntryCurrent = Entry(main_frame, textvariable=strReceivedCurrent)
receivedEntryGain = Entry(main_frame, textvariable=strReceivedGain)
labelCommandSent.config(fg=ui.cget('bg'))
main_frame.pack(side="left", fill="y", padx="5px")
labelToSendMes.pack()
toSendEntry.pack()
labelCommandSent.bind()
sendButton.pack()
labelReceivedMesPower.pack()
receivedEntryPower.pack()
labelReceivedMesCurrent.pack()
receivedEntryCurrent.pack()
labelReceivedMesGain.pack()
receivedEntryGain.pack()


# prepare data
data_buffer_power = []
data_buffer_current = []
for i in range(0, 100):
    if data[0] == b'P':
        data_buffer_power.append(data[1])
    if data[0] == b'C':
        data_buffer_current.append(data[1])

power_t = range(0, len(data_buffer_power))

# receive new data
ui.after(1, receive())

# create a figure
figure = Figure(figsize=(6, 4), dpi=100)

# create FigureCanvasTkAgg object
figure_canvas = FigureCanvasTkAgg(figure, ui)
# figure_canvas.Place(Left)

# create the toolbar
NavigationToolbar2Tk(figure_canvas, ui)

# create axes
ax = figure.add_subplot(1, 1, 1)

# create the barchart
#axes.plot(power_t, data_buffer_power)
#axes.set_title('data received')
#axes.set_ylabel('height')

figure_canvas.get_tk_widget().pack(side="left", fill=BOTH, expand=1)

# update plot
ui.after(100, update_plot)
ui.mainloop()


print("Thread stopped.")
ser.close()


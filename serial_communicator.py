import sys
import serial
from time import sleep
class Serial_Communications:

    def __init__(self,COM,BAUD):
        self.COM=COM ## Com port in This Serial Object Instance which you call is the 1st argument which is COM
        self.BAUD=BAUD ## Baud Rate in This Serial Object Instance which you call is the 2st argument which is BAUD
        self.serial=serial.Serial(COM,BAUD,timeout=0.01) # Initialize This Serial Instance with inputs
        sleep(0.3)

    def send(self,data):
        try:
            self.serial.write(data.encode('utf-8'))
            self.serial.write('\n'.encode('utf-8'))
            pass
        except Exception as e:
            print("Error Writing To Serial")
        

    def read(self):
        try:
            data=self.serial.readline().decode('utf-8')
            return data
            pass
        except Exception as e:
            print("Error Reading From Serial")

    def close(self):
        try:
            data=self.serial.close()
            pass
        except Exception as e:
            print("Error Closing From Serial")

if __name__=='__main__':
    import time
    a=Serial_Communications("COM5",9600)
    while True:
        a.send("3")
        time.sleep(1)
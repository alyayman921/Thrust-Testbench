#include <time.h>
#include <string.h>
#include "esc.h"
#include "sensors.h"

Motor Motor1(9);
loadCell ThrustCell1(2,3);
currentSensor CS1(A0);
infraredSensor IR1(5);

bool Armed=0; 
char received; String command;
int test_n=1; float PWM,T,Torque,Current,RPM,t0,t1,t2;
void SendtoDataAquisition(float freq);

void setup() {
  Serial.begin(9600);
  Motor1.connect();
  Motor1.speed(0);
  //ThrustCell1.connect();
  CS1.connect();
  IR1.connect();
  pinMode(LED_BUILTIN,OUTPUT);
  pinMode(A0,INPUT); 
}

void loop() {
  // put your main code here, to run repeatedly:
  if (Serial.available() > 0){
    received=Serial.read();
    if(received!='\n'){ // if the message is not empty
    command+=received;
    }else{ 
    //WHEN A NEW LINE BEGINS CHECK FOR SPECIAL Strings
      // Motor Strings
      //--------------------------------
      // Calibrate Motor
      if(command=="c"){
        Serial.println("ESC Calibration Start");
        digitalWrite(LED_BUILTIN,0); 
        Motor1.calibrate();
        digitalWrite(LED_BUILTIN,1);
        Serial.println("ESC Calibration done");
      }else if(command=="i"){
        // initiate test, Can write to motors
        Serial.print("Test# ");Serial.print(test_n);Serial.print(" Started\n");
        digitalWrite(LED_BUILTIN,0);
        Armed=1;
        t0=millis();
      }else if(command=="e"){
        // end test, Can't write to motors
        digitalWrite(LED_BUILTIN,1); // Off
        Motor1.speed(0);
        PWM=0;
        Serial.print("Test# ");Serial.print(test_n);Serial.print(" Ended\n");
        test_n++;
        Armed=0;// end test

      // Loadcell calibration strings
      //--------------------------------
      }else if(command=="z"){
        ThrustCell1.loadCell_Zero();
      }else{
        // if not a special string,it must be motor speed->send pwm value to motor and get readings
        PWM=command.toFloat();
          if(PWM<=100.0&&Armed)
          {
            Motor1.speed(PWM);// Send Speed to Motor 
          }
      }
          // Reset buffer
          command=""; 
    }
  }
  t2=millis();
  SendtoDataAquisition(20); // 20 Hz
} 

void SendtoDataAquisition(float freq){ // Send to data Aquisition
  if(Armed && (t2-t1)/1000 >= (1.0/freq) ){// when the test starts, send the data at a rate of idk hz

            // we need to get the readings within 1/freq seconds so we send updated version for the required frequency
            // we can't use delays, code can never sleep (Dangerous while having to stop a motor)
            
            //Readings from sensors
            //Current=CS1.currentReading(); // fix this delay please
            RPM=IR1.rpmReading();
            //T=ThrustCell1.thrustReading(); // infinite loop while disconnected
            //Torque=??
            
            //time,pwm,current,rpm,thrust,torque$
            //Time at this reading
            Serial.print((millis()-t0)/1000);Serial.print(',');
            Serial.print(PWM);Serial.print(',');
            // Current Ampere reading
            Serial.print(Current); Serial.print(',');
            // RPM reading
            Serial.print(RPM); Serial.print(',');
            // Thrust reading
            Serial.print(T);Serial.print(',');
            // Torque reading
            Serial.print(Torque);
            Serial.print("$"); // NO NEW LINE
            t1=t2;
  }
}
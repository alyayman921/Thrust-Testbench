#include "esc.h"
#include <time.h>
#include <string.h>
Motor Motor1(9);
bool Armed=0; // 
char received; 
String command;
float PWM,T,t0,t1,t2;
float pushSpeed_TEST(float PWM);

void setup() {
  // put your setup code here, to run once:
Motor1.connect();
Motor1.speed(0);
Serial.begin(9600);
  pinMode(LED_BUILTIN,OUTPUT);
  pinMode(A0,INPUT); 
}

//  الموتور بيبدأ لوحده دايما ليه

void loop() {
  // put your main code here, to run repeatedly:
  if (Serial.available() > 0){
    received=Serial.read();
    if(received!='\n'){ // if the message is not empty
    command+=received;
    }else{ 
    //WHEN A NEW LINE BEGINS CHECK FOR SPECIAL CHARACTERS
      if(command=="c"){
        // Calibrate Motor
        digitalWrite(LED_BUILTIN,0); 
        Motor1.calibrate();
        digitalWrite(LED_BUILTIN,1);
      }else if(command=="i"){
        // initiate test, Can write to motors
        digitalWrite(LED_BUILTIN,0);
        Armed=1;
        t0=millis();
      }else if(command=="e"){
        // end test, Can't write to motors
        digitalWrite(LED_BUILTIN,1); // Off
        Motor1.speed(0);
        Armed=0;// end test
      // if not a special character, send pwm value to motor
      }else{
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
  if(Armed && t2-t1>=50.0){// when the test starts, send the data at a rate of 20 hz
            //Readings from sensors
            T=pushSpeed_TEST(PWM); // Test only
            //time,pwm,current,rpm,thrust,torque$
            Serial.print((millis()-t0)/1000);
            Serial.print(',');
            Serial.print(PWM);
            Serial.print(',');
            Serial.print("Current");
            Serial.print(',');
            Serial.print("RPM");
            Serial.print(',');
            Serial.print(T);
            Serial.print(',');
            Serial.print("Torque");
            Serial.print("$"); // NO NEW LINE?
            t1=t2;
  }
  } 

float pushSpeed_TEST(float PWM){
  //actually push the speed
  return PWM*10;
}

#include "Motor.h"
Servo esc1;

bool state; // test state boolean
char received;
String command;
float PWM,T,t0;

float pushSpeed_TEST(float PWM);

void setup() {
  // put your setup code here, to run once:
Serial.begin(9600);
pinMode(LED_BUILTIN,OUTPUT);
pinMode(A0,INPUT); 
}

void loop() {
  // put your main code here, to run repeatedly:
  if (Serial.available() > 0){
    received=Serial.read();
    if(received!='\n'){ // if the message is not empty
      if(received=='c'){  
      // Calibrate Motor
        digitalWrite(LED_BUILTIN,0); // ON
        Motor(esc1,9);  
        digitalWrite(LED_BUILTIN,1); // Off
      }
      if(received=='i'){ 
        // initiate test
        state=1;
        t0=millis();
        digitalWrite(LED_BUILTIN,0); // ON
      }
      if(received=='e'){ 
        digitalWrite(LED_BUILTIN,1); // Off
        state=0;// end test
      }
    }else{ // if input isnt an initializing character
      command+=received;
    }
  }
      if(command!=""){ // when a newline begins
        PWM=command.toFloat();
          if(PWM<=100)
          {
            // Send Speed to Motor 
            Motor pushSpeed_esc(esc1,PWM);

            //Read Thrust output
            //T=analogRead(A0); // is this it?
            T=pushSpeed_TEST(PWM); // Test only

            //Output Data $time,PWM,Thrust|\n
            Serial.print("$");
            Serial.print((millis()-t0)/1000);
            Serial.print(',');
            Serial.print(PWM);
            Serial.print(',');
            Serial.print(T);
            Serial.println('|');

            // Reset Buffer
            command="";
          }
      }
    
  } 

float pushSpeed_TEST(float PWM){
  //actually push the speed
  return PWM*10;
}

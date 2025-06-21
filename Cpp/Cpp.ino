#include "esc.h"
Motor Motor1(9);

bool state=0; // test state boolean
char received; 
String command;
float PWM,T,t0;
float pushSpeed_TEST(float PWM);


void setup() {
  // put your setup code here, to run once:
  Motor1.connect();
  Serial.begin(9600);
  pinMode(LED_BUILTIN,OUTPUT);
  pinMode(A0,INPUT); 
}

//  الموتور بيبدأ لوحده دايما

void loop() {
  // put your main code here, to run repeatedly:
  if (Serial.available() > 0){
    received=Serial.read();
    if(received!='\n'){ // if the message is not empty
    command+=received;
    }else{ 
    //WHEN A NEW LINE BEGINS CHECK FOR SPECIAL CHARACTERS
      if(command=="c")
      {// Calibrate Motor
        digitalWrite(LED_BUILTIN,1); // ON
        Motor1.calibrate();
        digitalWrite(LED_BUILTIN,0); // Off
      }else if(command=="i"){
        // initiate test, Can write to motors
        digitalWrite(LED_BUILTIN,0); // ON
        state=1;
        t0=millis();
      }else if(command=="e"){
        // end test, Can't write to motors
        digitalWrite(LED_BUILTIN,1); // Off
        Motor1.speed(0);
        state=0;// end test

      // if not a special character, send pwm value to motor
      }else{
        PWM=command.toFloat();
          if(PWM<=100.0&&state)
          {
            Motor1.speed(PWM);// Send Speed to Motor 
          }
      }
          // Reset buffer
          command=""; 
    }
    
  }
  if(state){// when the test starts, send the data at a rate of idk per hertz
            
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
            delay(50);
  }
  } 

float pushSpeed_TEST(float PWM){
  //actually push the speed
  return PWM*10;
}

#include <string.h>
#include <time.h>
bool state; // test state boolean
char received;
String command;
float PWM,T,t0;
float pushSpeed(float PWM);
void setup() {
  // put your setup code here, to run once:
Serial.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:
  if (Serial.available() > 0){
    received=Serial.read();
    if(received!='\n'&&state){ // if the message is not empty
      command+=received; 
    }else{
      if (command!=""){ // when a newline begins
      PWM=command.toFloat();
      if (PWM){
      T=pushSpeed(PWM); // Thrust = loadcell reading!! 2 lines here 
      Serial.print((millis()-t0)/1000);Serial.print(',');Serial.print(PWM);Serial.print(',');Serial.println(T);
      }
      }
      command=""; 
    }
    if(received=='i'){ 
      state=1;// initiate test
      t0=millis();
    }
    if(received=='e'){ 
      state=0;// end test
    }
  }
}

float pushSpeed(float PWM){
  //actually push the speed
  return PWM*50;
}

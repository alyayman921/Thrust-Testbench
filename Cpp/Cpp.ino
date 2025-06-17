#include <cmath>
#include <time.h>
#include <string.h>
char received;
String command;
void processInput(String command);
void pushSpeed(int PWM);
void pushSpeed(int PWM[3],float Timestep);

void setup() {
  // put your setup code here, to run once:
Serial.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:
  if (Serial.available() > 0){
    received=Serial.read();
    if(received=='S'){
      Serial.println("KILL YOURSELF");
    }
    if(received!='\n'){
      command+=received;
      //Serial.println(command);
    }else{
      processInput(command);
      command="";
    }
  }
}

void processInput(String command){
// Command input == Test_Mode1|PWM_Percentage
// Command input == Test_Mode2|PWM_Percentage_step|Start_PWM|End_PWM|Timestep
  int Test_Mode=command[0];
  int PWM_Percentage;
  int PWM[3];//PWM_Percentage_step,Start_PWM,End_PWM;
  String temp;
  float Timestep;

  command.remove(0,2);
  //Serial.println(command);
    if(Test_Mode==1){// Constant speed test
    // Call to Push Motor Speed
    PWM_Percentage=command.toInt();
    pushSpeed(PWM_Percentage);
    } else{
      for(int j=1;j<5;j++){
        for (int i=0 ; i<command.length() ; i++){
            if (command[i]!='|'){
              temp=+command[i];
            }else{
              if (j==4){
                Timestep=temp.toFloat();
              }else{
                PWM[j-1]=temp.toInt();
              }
              temp="";
              // Call overloaded function to push speed
              pushSpeed(PWM,Timestep);
            }
          }
          }
    }
}

void pushSpeed(int PWM){
  //actually push the speed
}

void pushSpeed(int PWM[3],float Timestep){
  //PWM3=PWM_Percentage_step|Start_PWM|End_PWM, Timestep
  //actually push the speed
}
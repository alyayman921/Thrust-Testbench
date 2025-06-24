#include <Servo.h>

class Motor{
  public:
    Servo myMotor;
    int pin;
    Motor(int pin){
    this-> pin=pin;
    }

    void connect(){
      myMotor.attach(pin);  
    }

    void speed(int pwm){
      int microSecs = 1000+pwm*10;
      myMotor.writeMicroseconds(microSecs);
      }

    void calibrate(){
        myMotor.writeMicroseconds(2000);  
        delay(2000);                 
        myMotor.writeMicroseconds(1000); 
        delay(2000);                
    }
  };
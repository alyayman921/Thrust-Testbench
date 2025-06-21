#include <Servo.h>

class Motor{
  public:
    Servo myMotor;
    int pin;
    int pwm;
    int microSecs;
    Motor(int pin) {
      this->pin=pin;
  }
      void connect(){
      myMotor.attach(pin);  // Attach the ESC to pin 9 (can use any PWM pin)
      } 
    void speed(int pwm) {
      this->pwm=pwm;
      microSecs = 1000+pwm*10;
      myMotor.writeMicroseconds(microSecs);
      }
      
    void calibrate(){
        //Serial.println("Calibration Start");
        //Serial.println("Sending Low pulse");
        myMotor.writeMicroseconds(2000);  
        delay(2000);                 
        //Serial.println("Sending High pulse");
        myMotor.writeMicroseconds(1000); 
        delay(2000);                
        //Serial.println("Calibration done");
    }
  };
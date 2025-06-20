#include <Servo.h>
#include <time.h>
#include <string.h>
class Motor{
  public:
    Servo esc;
    int pin;
    int pwm;
    String init_state;
    Motor(Servo esc,int pin) {
      this->pin=pin;
      this->esc=esc;
      this->init_state=init_state;

      esc.attach(pin);  // Attach the ESC to pin 9 (can use any PWM pin)
      // Initialization sequence
      esc.writeMicroseconds(1000);  // Send minimum throttle (1ms pulse)
      delay(2000);                 // Wait for ESC to recognize the signal (some ESCs need up to 5s)
      esc.writeMicroseconds(2000);  // Send minimum throttle (1ms pulse)
      delay(2000);                 // Wait for ESC to recognize the signal (some ESCs need up to 5s)
      init_state="Tried To Initialize";
  }
  void pushSpeed_esc(Servo esc,int pwm) {
    this->esc=esc;
    this->pwm=pwm;
    int speed = 1000+pwm*10;
    esc.writeMicroseconds(speed);
    }
  };
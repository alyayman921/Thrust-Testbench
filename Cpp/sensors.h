#include "HX711.h"

class loadCell {
public:
  HX711 scale;
  int DOUT;
  int CLK; 
  float weight;
  // Constructor
  loadCell(int DOUT, int CLK) {
    this->DOUT = DOUT;
    this->CLK = CLK;
  }
  void connect() {
    scale.begin(DOUT, CLK);
    }
  float thrustReading() {
    weight = scale.get_units(10); // Does this produce a delay?
    return weight;
  }
  void loadCell_Zero() {
    scale.set_scale(); // Raw data scale
    scale.tare(); // Reset the reading to 0
  }
};
class infraredSensor {
public:
  int pin;
  int rpm;
signed long prevmicros = 0;
  unsigned long duration;
  boolean currentstate;
  boolean prevstate = 0;
  // constructor
  infraredSensor(int pin) { this->pin = pin; }

  void connect() { pinMode(pin, INPUT); };
  float rpmReading() {
    currentstate = digitalRead(pin);
    if (prevstate != currentstate) {
      if (currentstate == LOW) // if the state changed
      {
        duration = (micros() - prevmicros);
        rpm = ((60000000 / duration) /
               2); // rpm = (freq)*1000000*60; Check This please, i didnt test
                   // or change anything and don't know how it works
        prevmicros = micros();
      }
    }
    prevstate = currentstate;
    return rpm;
  }
};

class currentSensor {
public:
  int cs_pin;
  float no_load_voltage;
  float sensitivity;
  float Samples;
  // constructor
  currentSensor(int cs_pin) { this->cs_pin = cs_pin; }
  void connect() { pinMode(cs_pin, INPUT); }

  float currentReading() {
    for (int x = 0; x < 150; x++) {
      float reading = analogRead(cs_pin);
      Samples += reading;
      delay(3);
    }
    float AvgVolt = Samples / 150.0;
    float voltage = AvgVolt * 5.0 / 1023.0;
    float current = (voltage - no_load_voltage) / sensitivity;
    return current;
  }
};

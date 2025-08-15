#include "HX711.h"

class loadCell {
public:
  HX711 scale;
  int DOUT;
  int CLK; 
  float weight;
  float calibration_factor = 430.69; 

  // Constructor
  loadCell(int DOUT, int CLK) {
    this->DOUT = DOUT;
    this->CLK = CLK;
  }
  void connect() {
    scale.begin(DOUT, CLK);
    }
  float thrustReading() {
    weight = scale.get_units(1); // Does this produce a delay?
    return weight;
  }
  void loadCell_Zero() {
    scale.set_scale(1); // Raw data scale
    scale.tare(); // Reset the reading to 0
  }
  // NO DELAY CODE, NOT TESTED
  /*
  unsigned long currentMillis = millis();
  unsigned long currentMicros = micros();

  // Step 1: Check if new data is available from HX711
  // DOUT goes LOW when data is ready
  if (digitalRead(DOUT_PIN) == LOW && !data_ready) {
    // Data is ready, start reading bits
    data_ready = true;
    raw_reading = 0;
    bit_counter = 0;
    last_sck_toggle_time = currentMicros; // Reset time for first SCK toggle
    digitalWrite(SCK_PIN, HIGH); // Raise SCK for first bit
    return; // Finish this loop iteration, next iteration will process the first bit
  }
  // Step 2: If data is ready, bit-bang to read 24 bits
  if (data_ready) {
    if (bit_counter < 24) { // Read 24 bits
      if (currentMicros - last_sck_toggle_time >= SCK_TOGGLE_INTERVAL_US) {
        if (digitalRead(SCK_PIN) == LOW) {
          // SCK was low, now make it HIGH to clock out the next bit
          digitalWrite(SCK_PIN, HIGH);
          last_sck_toggle_time = currentMicros;
        } else {
          // SCK was high, now read the bit and make it LOW
          raw_reading <<= 1; // Shift existing reading left by 1
          if (digitalRead(DOUT_PIN) == HIGH) {
            raw_reading |= 1; // Set the last bit if DOUT is HIGH
          }
          digitalWrite(SCK_PIN, LOW);
          last_sck_toggle_time = currentMicros;
          bit_counter++;
        }
      }
    } else {
      // Finished reading 24 bits, perform additional clock pulses for channel/gain selection (e.g., 1 pulse for A/128)
      if (currentMicros - last_sck_toggle_time >= SCK_TOGGLE_INTERVAL_US) {
        if (digitalRead(SCK_PIN) == LOW) {
          digitalWrite(SCK_PIN, HIGH);
          last_sck_toggle_time = currentMicros;
        } else {
          digitalWrite(SCK_PIN, LOW);
          // Reading is complete for this cycle
          data_ready = false; // Reset flag for next reading
          bit_counter = 0; // Reset bit counter
          // Process and send data
          Serial.print("Raw: ");
          Serial.println(raw_reading); // Or use Serial.write for binary data if needed
        }
      }
    }
  }
  */
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

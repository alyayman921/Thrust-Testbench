# Thrust Testbench Software

This repository contains the software for a Thrust Testbench, designed to control and monitor thrust tests of propulsion systems. The software provides a graphical user interface (GUI) for defining test parameters, initiating tests, monitoring real-time data, and logging results.




## Features

*   **Serial Communication:** Establishes and manages serial communication with the testbench hardware.
*   **Real-time Data Monitoring:** Displays live data during tests, including PWM, Current, RPM, Thrust, and Torque.
*   **Configurable Test Parameters:** Allows users to define PWM step, start, and end values, as well as timestep for tests.
*   **Data Logging:** Automatically logs test data to CSV files for post-analysis.
*   **Graphical Visualization:** Plots real-time data on a graph within the GUI.
*   **Serial Port Sniffer:** Automatically detects available serial ports.
*   **Calibration:** Provides a calibration function for the ESC.
*   **User-friendly GUI:** Built with Tkinter for an intuitive user experience.
## Installation

[Download Latest Release](https://github.com/alyayman921/Thrust-Testbench/releases)
### Or
To set up the Thrust Testbench software, follow these steps:

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/alyayman921/Thrust-Testbench
    cd ThrustTestbench
    ```

2.  **Install dependencies:**

    Run Dependencies batch file or you can install them manually using pip:

    ```bash
    pip install pyserial matplotlib numpy keyboard pyautogui Pillow tk
    ```

    *Note: `tk` is usually included with Python installations, but if you encounter issues, you might need to install it separately depending on your operating system.*


3.  **Run the application:**

    Execute the main Python script:

    ```bash
    python ThrustTestbench.py
    ```

# Usage
1.  **Connect to Serial Port:**

    *   The software will automatically list available serial ports in the 'Serial Port' dropdown menu.
    *   Select the appropriate COM port for your testbench.
    *   Click the 'Connect' button to establish a serial connection. The button text will change to 'COM Started' upon successful connection.

2.  **Define Test Parameters:**

    *   Click the 'Define Test' button.
    *   A new window will appear where you can set:
        *   **Test Name:** A name for your test run (e.g., 'Motor_A_Test_1').
        *   **PWM Step:** The increment for PWM values during the test.
        *   **PWM Start:** The initial PWM value.
        *   **PWM End:** The final PWM value.
        *   **Timestep:** The duration (in seconds) for which each PWM value is held.
    *   Click 'Save' to apply the settings. You can also click 'Set as Default' to save these settings to `config_test.ini` for future use.

3.  **Calibrate (if necessary):**

    *   If your ESC or the Loadcell require calibration, click the 'Calibrate' button and follow instructions shown.

4.  **Start and Stop Test:**

    *   Once connected and test parameters are defined, click the 'Start Test' button to begin the test sequence.
    *   The GUI will display real-time data on the graph.
    *   To stop an ongoing test, click the 'Stop Test' button, or press space.

5.  **Data Configuration:**

    *   Click the 'Data Config' button to configure data logging and graphing options.
    *   You can enable/disable CSV logging and select the X and Y axes for the real-time graph.
    *   Click 'Update Graph' to apply changes to the graph or 'Set as Default' to save these settings to `config_data.ini`.

6.  **Serial Monitor:**

    *   Click the 'Serial Monitor' button to expand/collapse a console window that displays raw serial communication data. You can also send commands directly via the input field at the bottom of this monitor.
    * Sending 'c' Character to Serial port starts calibration of the esc.
    * Sending 'i' makes you arm the motor and start a test.
    * Sending any number after a test starts from 0 to 100 is equivalent to sending PWM signal to motor from 1000 to 2000.
    * Sending 'e' is stop and disarm the motor, and ends the test, Note that for a manual test the Program will not store data to csv file
## Project Structure

*   `ThrustTestbench.py`: The main application file, containing the Tkinter GUI, test logic, data handling, and integration with serial communication.
*   `serial_communicator.py`: A Python class for handling serial port communication (sending and reading data).
*   `serial_sniffer.py`: A utility script to detect and list available serial ports on the system.
*   `config_data.ini`: Configuration file for data logging and graphing settings (e.g., default X/Y axis for plots, autologging).
*   `config_test.ini`: Configuration file for defining test parameters (e.g., PWM step, start, end, timestep).

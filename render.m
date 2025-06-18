
% Read data from CSV file
data = readmatrix("data.csv", 'NumHeaderLines', 2);

% Extract columns (assuming format: Time,PWM,Thrust)
time = data(:,1);
pwm = data(:,2);
thrust = data(:,3);

% Create figure with two subplots
figure('Name', 'Thrust Bench Analysis', 'NumberTitle', 'off', 'Position', [100 100 1200 600]);

% First subplot: Thrust vs Time
subplot(2,1,1);
plot(time, thrust, 'b-', 'LineWidth', 1.5);
title('Thrust vs Time');
xlabel('Time (s)');
ylabel('Thrust (N)');
grid on;

% Set y-axis to start from 0
y_limits = ylim;
ylim([0 y_limits(2)*1.1]);

% Second subplot: PWM vs Time
subplot(2,1,2);
plot(time, pwm, 'r-', 'LineWidth', 1.5);
title('PWM Signal vs Time');
xlabel('Time (s)');
ylabel('PWM (%)');
grid on;

% Set y-axis limits for PWM (0-100%)
ylim([0 100]);


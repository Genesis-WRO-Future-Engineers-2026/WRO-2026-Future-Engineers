/*
 * PWM Pulse Generator (for Raspberry Pi integration)
 *
 * Overview:
 * Receives pulse width via serial communication from Raspberry Pi,
 * and generates PWM pulses for servo and ESC.
 *
 * Communication Protocol:
 * - Servo control: "S<pulse_width_us>\n"  e.g., "S1500\n" -> 1500 microseconds
 * - ESC control:   "E<pulse_width_us>\n"  e.g., "E1500\n" -> 1500 microseconds
 *
 * Operation:
 * - Continues outputting the same pulse width until new value arrives from Raspberry Pi
 * - Enters safe stop state if communication timeout occurs
 *
 * Connections:
 * - Servo signal: Arduino pin 9
 * - ESC signal:   Arduino pin 10
 * - Serial comm:  Arduino Nano TX/RX <-> Raspberry Pi GPIO14/15
 */

#include <Servo.h>

// ============================================================================
// Pin Definitions
// ============================================================================
const int SERVO_PIN = 9;   // Pin for servo motor
const int ESC_PIN = 10;    // Pin for ESC (Electronic Speed Controller)

// ============================================================================
// Pulse Width Range Settings
// ============================================================================
// Servo typical range: 500-2400 microseconds
const int SERVO_MIN_PULSE = 500;
const int SERVO_MAX_PULSE = 2400;

// ESC typical range: 1000-2000 microseconds
const int ESC_MIN_PULSE = 1000;
const int ESC_MAX_PULSE = 2000;

// ============================================================================
// Initial/Stop Values
// ============================================================================
const int SERVO_NEUTRAL_PULSE = 1500;  // Servo neutral position (center)
const int ESC_STOP_PULSE = 1500;       // ESC stop pulse

// ============================================================================
// Communication Timeout Settings
// ============================================================================
const unsigned long COMM_TIMEOUT_MS = 1000;  // Timeout after 1 second of no communication

// ============================================================================
// Global Variables
// ============================================================================
Servo servo;  // Servo control object
Servo esc;    // ESC control object

// Current pulse widths (microseconds)
int current_servo_pulse = SERVO_NEUTRAL_PULSE;
int current_esc_pulse = ESC_STOP_PULSE;

// Last communication timestamp
unsigned long last_comm_time = 0;

// Timeout state flag
bool is_timeout = false;

// ============================================================================
// Setup Function
// ============================================================================
void setup() {
  // Initialize serial communication at 115200 bps
  Serial.begin(115200);

  // Attach servo and ESC to pins
  servo.attach(SERVO_PIN, SERVO_MIN_PULSE, SERVO_MAX_PULSE);
  esc.attach(ESC_PIN, ESC_MIN_PULSE, ESC_MAX_PULSE);

  // Set initial state: neutral steering, stopped motor
  servo.writeMicroseconds(current_servo_pulse);
  esc.writeMicroseconds(current_esc_pulse);

  // Print initialization complete message
  Serial.println("Arduino Pulse Generator Ready");
  Serial.println("Waiting for commands from Raspberry Pi...");

  // Start communication timer
  last_comm_time = millis();
}

// ============================================================================
// Main Loop
// ============================================================================
void loop() {
  // Check if data is received via serial
  if (Serial.available() > 0) {
    // Read string until newline
    String command = Serial.readStringUntil('\n');
    command.trim();

    // Process command
    if (command.length() > 0) {
      processCommand(command);
      // Reset communication timer
      last_comm_time = millis();
      // Clear timeout state
      if (is_timeout) {
        is_timeout = false;
        Serial.println("Communication restored");
      }
    }
  }

  // Check for communication timeout
  if (!is_timeout && (millis() - last_comm_time > COMM_TIMEOUT_MS)) {
    // Timeout occurred -> enter safe stop state
    is_timeout = true;
    current_servo_pulse = SERVO_NEUTRAL_PULSE;
    current_esc_pulse = ESC_STOP_PULSE;
    servo.writeMicroseconds(current_servo_pulse);
    esc.writeMicroseconds(current_esc_pulse);
    Serial.println("Communication timeout - Emergency stop");
  }

  // Maintain current pulse width (Servo library automatically continues output)
  // Note: No action needed, Servo library automatically outputs pulses at 50Hz
}

// ============================================================================
// Command Processing Function
// ============================================================================
void processCommand(String command) {
  if (command.length() < 2) {
    Serial.println("Error: Invalid command format");
    return;
  }

  // Determine command type ('S'=Servo, 'E'=ESC)
  char command_type = command.charAt(0);

  // Get numeric value from second character onward
  int pulse_width = command.substring(1).toInt();

  // Process servo command
  if (command_type == 'S' || command_type == 's') {
    // Constrain pulse width to valid range
    pulse_width = constrain(pulse_width, SERVO_MIN_PULSE, SERVO_MAX_PULSE);

    // Update pulse width
    current_servo_pulse = pulse_width;
    servo.writeMicroseconds(current_servo_pulse);

    // Debug output
    Serial.print("Servo: ");
    Serial.print(current_servo_pulse);
    Serial.println(" us");
  }
  // Process ESC command
  else if (command_type == 'E' || command_type == 'e') {
    // Constrain pulse width to valid range
    pulse_width = constrain(pulse_width, ESC_MIN_PULSE, ESC_MAX_PULSE);

    // Update pulse width
    current_esc_pulse = pulse_width;
    esc.writeMicroseconds(current_esc_pulse);

    // Debug output
    Serial.print("ESC: ");
    Serial.print(current_esc_pulse);
    Serial.println(" us");
  }
  // Unknown command
  else {
    Serial.print("Error: Unknown command type '");
    Serial.print(command_type);
    Serial.println("'");
  }
}

# Autonomous Minicar Wall-Following Algorithm Implementation Plan

## Project Overview

### Target Performance
- **Objective**: Achieve lap times under 9 seconds for competitive racing
- **Control Loop Frequency**: 100Hz (10ms cycle time)
- **Competition Format**: 6 minutes total time with multiple retry attempts
- **Strategy**: Optimize for best-of-3 lap times rather than consistency

### Hardware Configuration
- **Microcontroller**: Arduino Nano R4 (single-board implementation)
- **Sensors**: 5x VL53L0X Time-of-Flight distance sensors
- **Actuators**: Servo motor (steering) + ESC (speed control) via PWM
- **Vehicle**: Tamiya TT-02 chassis, 4WD configuration

## Algorithm Architecture

### Core Strategy: Left Wall Following with Geometric Calculation

The algorithm implements a reliable wall-following approach using continuous left wall detection, avoiding unreliable right wall measurements due to sharp angles and shortcuts in the course layout.

## Mathematical Foundation

### 1. Sensor Configuration

#### Sensor Placement Geometry
```
Sensor Array Configuration (angles relative to vehicle forward direction):
- Sensor 1: -70° (left rear)
- Sensor 2: -20° (left front)  
- Sensor 3:   0° (front center)
- Sensor 4: +20° (right front)
- Sensor 5: +70° (right rear)
```

#### Polar to Cartesian Conversion
For each sensor `i` with angle `θᵢ` and measured distance `dᵢ`:

```
x_i = d_i × cos(θᵢ)
y_i = d_i × sin(θᵢ)
```

Where:
- `x_i`: lateral distance from vehicle centerline
- `y_i`: longitudinal distance from vehicle front

### 2. Wall Detection Algorithm

#### Two-Point Line Calculation
For wall detection using sensor pairs, calculate wall line equation `ax + by + c = 0`:

**Left Wall (Sensors 1 & 2):**
```
Point A: (x₁, y₁) = (d₁ × cos(-70°), d₁ × sin(-70°))
Point B: (x₂, y₂) = (d₂ × cos(-20°), d₂ × sin(-20°))

Line coefficients:
a_left = y₂ - y₁
b_left = x₁ - x₂  
c_left = x₂ × y₁ - x₁ × y₂
```

**Right Wall (Sensors 4 & 5):**
```
Point C: (x₄, y₄) = (d₄ × cos(+20°), d₄ × sin(+20°))
Point D: (x₅, y₅) = (d₅ × cos(+70°), d₅ × sin(+70°))

Line coefficients:
a_right = y₅ - y₄
b_right = x₄ - x₅
c_right = x₅ × y₄ - x₄ × y₅
```

### 3. Intersection Point Calculation

#### Y-Axis Intersection Method
Calculate where each wall line intersects the y-axis (vehicle forward direction):

```
For line ax + by + c = 0, intersection with x = 0:
y_intersection = -c / b

Left wall intersection:  y_left = -c_left / b_left
Right wall intersection: y_right = -c_right / b_right
```

#### Geometric Interpretation
- `y_left > y_right`: Vehicle positioned closer to right wall
- `y_left < y_right`: Vehicle positioned closer to left wall  
- `y_left ≈ y_right`: Vehicle centered between walls

### 4. Steering Control Algorithm

#### Proportional Control Based on Intersection Difference
```
intersection_diff = y_left - y_right
steering_angle = intersection_diff × GAIN_FACTOR

Where:
GAIN_FACTOR = 0.1 (tunable parameter)
MAX_STEERING_ANGLE = 30° (mechanical limit)
```

#### Control Logic State Machine

**State 1: Both Walls Detected**
```
if (left_wall_valid && right_wall_valid):
    steering_angle = clamp(intersection_diff × GAIN_FACTOR, -MAX_ANGLE, +MAX_ANGLE)
```

**State 2: Left Wall Only**
```
if (left_wall_valid && !right_wall_valid):
    steering_angle = -MAX_ANGLE × OPEN_SIDE_RATIO  // Turn left (away from wall)
    
Where OPEN_SIDE_RATIO = 0.5 (conservative turn rate)
```

**State 3: Right Wall Only**
```
if (!left_wall_valid && right_wall_valid):
    steering_angle = +MAX_ANGLE × OPEN_SIDE_RATIO  // Turn right (away from wall)
```

**State 4: No Walls Detected**
```
if (!left_wall_valid && !right_wall_valid):
    steering_angle = 0  // Continue straight
```

### 5. Sensor Reliability and Range Limitations

#### VL53L0X Characteristics
- **Effective Range**: 80cm maximum, 60cm reliable
- **Update Rate**: Limited to ~20Hz with current configuration
- **Range Limitation Strategy**: Use maximum range detection as "open space" indicator

#### Wall Validity Criteria
```
Wall is considered valid if:
1. Both sensor distances < RELIABLE_RANGE (700mm)
2. Distance difference between sensors < MAX_DIFF (200mm)  
3. Calculated line angle within reasonable bounds (±45° from perpendicular)
```

## Implementation Architecture

### 1. Main Control Loop (10ms cycle)

```cpp
void control_loop() {
    // Phase 1: Sensor Data Acquisition (2ms)
    SensorData readings = read_all_sensors();
    
    // Phase 2: Wall Detection (2ms)
    WallDetection walls = detect_walls(readings);
    
    // Phase 3: Steering Calculation (1ms)  
    float steering_angle = calculate_steering(walls);
    
    // Phase 4: Actuator Control (1ms)
    set_steering_angle(steering_angle);
    set_speed(current_speed_profile);
    
    // Phase 5: Telemetry/Debug (4ms)
    output_debug_data(readings, walls, steering_angle);
}
```

### 2. Sensor Management

#### I2C Address Management
```cpp
const uint8_t SENSOR_ADDRESSES[5] = {0x30, 0x2B, 0x2D, 0x2E, 0x2F};
const float SENSOR_ANGLES[5] = {-70.0, -20.0, 0.0, 20.0, 70.0};
const uint8_t SHUTDOWN_PINS[5] = {2, 3, 4, 5, 6};
```

#### Sequential Initialization Protocol
```cpp
void initialize_sensors() {
    // Shutdown all sensors
    for (int i = 0; i < 5; i++) {
        digitalWrite(SHUTDOWN_PINS[i], LOW);
    }
    delay(50);
    
    // Initialize each sensor with unique I2C address
    for (int i = 0; i < 5; i++) {
        digitalWrite(SHUTDOWN_PINS[i], HIGH);
        delay(50);
        
        VL53L0X sensor;
        sensor.init();
        sensor.setAddress(SENSOR_ADDRESSES[i]);
        sensor.startContinuous();
        sensors[i] = sensor;
    }
}
```

### 3. PWM Control Implementation

#### High-Precision Servo Control
```cpp
const int SERVO_PIN = 9;
const int ESC_PIN = 10;

// Servo: 500-2400μs range for ±90° steering
// ESC: 1000-2000μs range for reverse-forward speed

void set_steering_angle(float angle_degrees) {
    int pulse_us = map(angle_degrees, -90, 90, 500, 2400);
    servo.writeMicroseconds(pulse_us);
}

void set_speed(float speed_ms) {
    int pulse_us = speed_ms * 1000;  // Convert ms to μs
    esc.writeMicroseconds(pulse_us);
}
```

## Performance Optimization Strategies

### 1. Speed Profiles

#### Adaptive Speed Based on Course Geometry
```cpp
typedef struct {
    float base_speed;      // Base forward speed (1.5-1.7ms pulse)
    float turn_speed;      // Reduced speed for tight turns
    float straight_speed;  // Maximum speed for straights
} SpeedProfile;

SpeedProfile calculate_speed_profile(WallDetection walls) {
    if (walls.both_walls_detected) {
        float corridor_width = walls.right_intersection - walls.left_intersection;
        
        if (corridor_width > 800) {  // Wide section (home straight)
            return {1.65, 1.55, 1.75};  // Aggressive profile
        } else if (corridor_width > 500) {  // Medium section
            return {1.55, 1.50, 1.65};  // Balanced profile  
        } else {  // Narrow section
            return {1.50, 1.45, 1.55};  // Conservative profile
        }
    }
    return {1.52, 1.48, 1.58};  // Default safe profile
}
```

### 2. Predictive Control

#### Look-Ahead Distance Calculation
```cpp
const float REACTION_TIME = 0.1;  // 100ms system response time
const float SAFETY_MARGIN = 1.2;  // 20% safety factor

float calculate_lookahead_distance(float current_speed) {
    // Convert speed pulse to actual velocity (empirical calibration needed)
    float velocity_mps = (current_speed - 1.5) * CALIBRATION_FACTOR;
    
    return velocity_mps * REACTION_TIME * SAFETY_MARGIN;
}
```

### 3. Sensor Range Optimization

#### Dynamic Range Selection
```cpp
void optimize_sensor_timing(float expected_wall_distance) {
    if (expected_wall_distance < 300) {  // Close to wall
        vl53l0x.setMeasurementTimingBudget(20000);  // High accuracy mode
    } else if (expected_wall_distance < 600) {  // Medium distance
        vl53l0x.setMeasurementTimingBudget(33000);  // Balanced mode
    } else {  // Far from wall
        vl53l0x.setMeasurementTimingBudget(50000);  // Long range mode
    }
}
```

## Error Handling and Safety

### 1. Sensor Fault Detection

#### Invalid Reading Detection
```cpp
bool is_sensor_reading_valid(uint16_t distance) {
    return (distance > 50 &&           // Minimum detection range
            distance < 8000 &&         // Maximum valid range
            distance != 65535);        // Error code check
}
```

#### Graceful Degradation
```cpp
void handle_sensor_failure(int failed_sensor_id) {
    switch (failed_sensor_id) {
        case 1:  // Left rear sensor failed
            // Use only left front sensor for wall detection
            use_single_point_wall_detection = true;
            break;
            
        case 2:  // Left front sensor failed  
            // Fall back to distance-based control
            use_fallback_control = true;
            break;
            
        // Additional failure modes...
    }
}
```

### 2. Safety Limits

#### Emergency Stop Conditions
```cpp
void safety_check(SensorData readings) {
    // Front obstacle detection
    if (readings.front_distance < EMERGENCY_STOP_DISTANCE) {
        emergency_stop();
        return;
    }
    
    // Sensor consistency check
    if (sensor_readings_inconsistent(readings)) {
        reduce_speed_to_safe_level();
    }
    
    // Control loop timing check
    if (loop_execution_time > MAX_LOOP_TIME) {
        trigger_failsafe_mode();
    }
}
```

## Calibration and Tuning Parameters

### Key Tunable Parameters
```cpp
// Geometric calculation parameters
const float GAIN_FACTOR = 0.1;           // Steering response gain
const float MAX_STEERING_ANGLE = 30.0;   // Maximum steering angle (degrees)
const float OPEN_SIDE_RATIO = 0.5;       // Turn ratio for open sides

// Sensor reliability parameters  
const int RELIABLE_RANGE = 700;          // Reliable sensor range (mm)
const int MAX_SENSOR_DIFF = 200;         // Maximum difference between sensor pair
const int MIN_WALL_DISTANCE = 100;       // Minimum safe wall distance

// Speed control parameters
const float BASE_SPEED_PULSE = 1.52;     // Base forward speed pulse width (ms)
const float TURN_SPEED_REDUCTION = 0.05; // Speed reduction in turns
const float STRAIGHT_SPEED_BOOST = 0.1;  // Speed increase on straights

// Timing parameters
const int CONTROL_LOOP_INTERVAL = 10;    // Main loop interval (ms)
const int SENSOR_UPDATE_INTERVAL = 5;    // Sensor reading interval (ms)
const int PWM_UPDATE_INTERVAL = 1;       // PWM output update interval (ms)
```

### Performance Monitoring
```cpp
typedef struct {
    float average_lap_time;
    float wall_following_accuracy;
    int sensor_fault_count;
    float control_loop_jitter;
    float maximum_achievable_speed;
} PerformanceMetrics;

void log_performance_data(PerformanceMetrics metrics) {
    // Serial output for analysis and optimization
    Serial.print("LAP_TIME:");
    Serial.print(metrics.average_lap_time);
    Serial.print(",ACCURACY:");
    Serial.print(metrics.wall_following_accuracy);
    // Additional metrics...
}
```

## Expected Performance Outcomes

### Target Specifications
- **Lap Time**: Sub-9 second lap times
- **Control Accuracy**: ±50mm wall following precision
- **System Reliability**: 99%+ successful lap completion rate
- **Response Time**: <20ms from sensor input to actuator output

### Competitive Advantages
1. **Deterministic Control**: Mathematical precision over heuristic approaches
2. **Robust Sensor Strategy**: Left-wall following avoids unreliable right-wall detection
3. **Optimal Hardware Utilization**: Single-board simplicity with maximum performance
4. **Adaptive Speed Control**: Course-aware speed optimization for time minimization

This algorithm provides a solid mathematical foundation for achieving competitive autonomous minicar performance while maintaining system reliability and implementation feasibility within the Arduino Nano R4 platform constraints.

## Future Improvements and Optimization Plan

Based on current system analysis and competitive requirements, the following enhancements have been identified for achieving sub-9-second lap times and 100Hz control loop performance.

### 1. Dynamic Wall Distance Optimization

#### Current Issue
Fixed target wall distance (constant-based approach) limits optimization potential across varying course geometries.

#### Proposed Solution: Adaptive Distance Control
```cpp
typedef struct {
    float left_distance;
    float right_distance;
    float corridor_width;
    float curvature_estimate;
} CourseGeometry;

float calculate_optimal_wall_distance(CourseGeometry course) {
    // Dynamic calculation based on corridor width and curve estimation
    float base_distance = course.corridor_width * 0.4;  // 40% offset from center
    
    // Adjust for curvature (tighter curves = closer to inside wall)
    float curvature_factor = 1.0 - (abs(course.curvature_estimate) * 0.2);
    
    return clamp(base_distance * curvature_factor, 150.0, 400.0);  // 15-40cm range
}

// Real-time optimization using both sensor measurements
WallDistanceTarget optimize_wall_following(SensorData sensors) {
    CourseGeometry course = analyze_course_geometry(sensors);
    float target_left = calculate_optimal_wall_distance(course);
    float target_right = course.corridor_width - target_left;
    
    return {target_left, target_right, course.corridor_width};
}
```

### 2. Maximum Speed Profile Correction

#### Current Issue  
Documentation incorrectly specified maximum speed pulse as 1.7ms; actual maximum is 1.4ms.

#### Corrected Speed Implementation
```cpp
// Corrected ESC pulse width specifications
const float ESC_STOP_PULSE = 1.5;      // Stop/neutral position
const float ESC_MIN_PULSE = 1.0;       // Maximum reverse  
const float ESC_MAX_PULSE = 1.4;       // MAXIMUM FORWARD (corrected)

typedef struct {
    float straight_speed;    // Maximum speed for straights
    float curve_speed;       // Reduced speed for curves
    float approach_speed;    // Speed when approaching obstacles
    float emergency_speed;   // Minimum safe speed
} SpeedProfile;

SpeedProfile aggressive_profile = {
    .straight_speed = 1.4,   // Maximum forward speed
    .curve_speed = 1.32,     // 80% of maximum for curves
    .approach_speed = 1.25,  // 62.5% for tight sections
    .emergency_speed = 1.15  // 37.5% for emergency situations
};
```

### 3. Intelligent Acceleration Management

#### Aggressive Speed Optimization Strategy
```cpp
typedef enum {
    ACCEL_ZONE_STRAIGHT,     // Long straight sections
    ACCEL_ZONE_EXIT,         // Curve exit acceleration
    ACCEL_ZONE_APPROACH,     // Curve approach deceleration  
    ACCEL_ZONE_EMERGENCY     // Safety-limited zones
} AccelZone;

float calculate_dynamic_speed(SensorData sensors, AccelZone zone, float current_speed) {
    switch(zone) {
        case ACCEL_ZONE_STRAIGHT:
            // Aggressive acceleration to maximum speed
            if (sensors.front_distance > 800) {  // Clear path ahead
                return min(current_speed + 0.05, ESC_MAX_PULSE);  // Rapid accel
            }
            break;
            
        case ACCEL_ZONE_EXIT:
            // Post-curve acceleration based on wall opening
            float wall_opening_factor = calculate_wall_opening_rate(sensors);
            if (wall_opening_factor > 0.5) {  // Walls are opening (curve exit)
                return min(current_speed + 0.03, ESC_MAX_PULSE);
            }
            break;
            
        case ACCEL_ZONE_APPROACH:
            // Predictive deceleration based on curve tightness
            float curve_severity = estimate_curve_severity(sensors);
            float target_curve_speed = ESC_MAX_PULSE * (1.0 - curve_severity * 0.4);
            return target_curve_speed;
            
        case ACCEL_ZONE_EMERGENCY:
            // Emergency deceleration
            return max(current_speed - 0.1, aggressive_profile.emergency_speed);
    }
    
    return current_speed;  // No change
}

// Curve severity estimation using sensor geometry
float estimate_curve_severity(SensorData sensors) {
    float left_gradient = abs(sensors.left_20 - sensors.left_70) / 500.0;   // mm difference
    float right_gradient = abs(sensors.right_20 - sensors.right_70) / 500.0;
    
    float max_gradient = max(left_gradient, right_gradient);
    return clamp(max_gradient, 0.0, 1.0);  // Normalize to 0-1 severity scale
}
```

### 4. High-Frequency Sensor Optimization

#### VL53L0X Performance Enhancement for 100Hz Operation
```cpp
// Optimized timing budget configuration
const uint32_t HIGH_SPEED_BUDGET = 20000;    // 20ms for high-speed operation
const uint32_t BALANCED_BUDGET = 33000;      // 33ms for balanced operation
const uint32_t ACCURACY_BUDGET = 50000;      // 50ms for high-accuracy operation

void optimize_sensor_timing_budget(VL53L0X_Dev_t *sensor, float expected_distance) {
    uint32_t timing_budget;
    
    if (expected_distance < 300) {         // Close range - need accuracy
        timing_budget = ACCURACY_BUDGET;
    } else if (expected_distance < 600) {  // Medium range - balanced
        timing_budget = BALANCED_BUDGET;
    } else {                               // Long range - speed priority
        timing_budget = HIGH_SPEED_BUDGET;
    }
    
    VL53L0X_SetMeasurementTimingBudgetMicroSeconds(sensor, timing_budget);
}

// Asynchronous sensor reading for 100Hz operation
typedef struct {
    bool measurement_ready[5];
    uint16_t last_distance[5];
    uint32_t last_update_time[5];
} AsyncSensorManager;

bool update_sensors_async(AsyncSensorManager *mgr, VL53L0X_Dev_t sensors[5]) {
    bool all_updated = true;
    uint32_t current_time = millis();
    
    for (int i = 0; i < 5; i++) {
        uint8_t ready = 0;
        VL53L0X_GetMeasurementDataReady(&sensors[i], &ready);
        
        if (ready) {
            VL53L0X_RangingMeasurementData_t measurement;
            VL53L0X_GetRangingMeasurementData(&sensors[i], &measurement);
            
            mgr->last_distance[i] = measurement.RangeMilliMeter;
            mgr->last_update_time[i] = current_time;
            mgr->measurement_ready[i] = true;
            
            // Restart measurement immediately
            VL53L0X_ClearInterruptMask(&sensors[i], VL53L0X_REG_SYSTEM_INTERRUPT_CLEAR);
        } else {
            // Check for timeout (older than 50ms)
            if (current_time - mgr->last_update_time[i] > 50) {
                mgr->measurement_ready[i] = false;
                all_updated = false;
            }
        }
    }
    
    return all_updated;
}
```

### 5. Additional Critical Improvements

#### A. Predictive Control Enhancement
```cpp
// Look-ahead distance calculation for predictive steering
float calculate_predictive_steering(SensorData current, SensorData previous, float vehicle_speed) {
    // Estimate wall trajectory using sensor velocity
    float left_wall_velocity = (current.left_20 - previous.left_20) / 0.01;  // mm/s
    float right_wall_velocity = (current.right_20 - previous.right_20) / 0.01;
    
    // Predict wall position 100ms ahead
    float predicted_left = current.left_20 + (left_wall_velocity * 0.1);
    float predicted_right = current.right_20 + (right_wall_velocity * 0.1);
    
    // Calculate predictive steering correction
    WallDetection predicted_walls = {predicted_left, predicted_right, true, true};
    return calculate_steering(predicted_walls) * 1.2;  // Amplify for prediction
}
```

#### B. Sensor Fusion and Reliability
```cpp
// Weighted sensor fusion for improved reliability
float calculate_reliable_distance(float dist_20, float dist_70, float confidence_20, float confidence_70) {
    // Distance confidence based on measurement consistency
    float total_confidence = confidence_20 + confidence_70;
    if (total_confidence < 0.1) return -1;  // Invalid measurement
    
    float weighted_distance = (dist_20 * confidence_20 + dist_70 * confidence_70) / total_confidence;
    return weighted_distance;
}

// Confidence calculation based on measurement stability
float calculate_sensor_confidence(float current, float previous, float measurement_time) {
    float change_rate = abs(current - previous) / measurement_time;
    float base_confidence = (current > 50 && current < 1500) ? 1.0 : 0.0;  // Range check
    
    // Reduce confidence for rapidly changing measurements (potential noise)
    float stability_factor = exp(-change_rate / 1000.0);  // Exponential decay for instability
    
    return base_confidence * stability_factor;
}
```

#### C. Power Management Optimization
```cpp
// Dynamic power management for extended operation
void optimize_power_consumption(float battery_voltage, float target_lap_time) {
    if (battery_voltage < 7.0) {  // Low battery condition
        // Reduce sensor update frequency to conserve power
        for (int i = 0; i < 5; i++) {
            VL53L0X_SetMeasurementTimingBudgetMicroSeconds(&sensors[i], BALANCED_BUDGET);
        }
        
        // Limit maximum speed to extend operation time
        aggressive_profile.straight_speed = min(1.35, ESC_MAX_PULSE);
    } else if (target_lap_time < 8.0) {  // Aggressive mode for fast times
        // Maximize performance regardless of power consumption
        for (int i = 0; i < 5; i++) {
            VL53L0X_SetMeasurementTimingBudgetMicroSeconds(&sensors[i], HIGH_SPEED_BUDGET);
        }
        
        aggressive_profile.straight_speed = ESC_MAX_PULSE;
    }
}
```

#### D. Memory and Processing Optimization
```cpp
// Efficient data structures for 100Hz operation
typedef struct __attribute__((packed)) {
    uint16_t distances[5];      // 10 bytes
    uint8_t confidence[5];      // 5 bytes  
    uint32_t timestamp;         // 4 bytes
} CompactSensorData;           // Total: 19 bytes vs 40+ bytes for floats

// Ring buffer for sensor history (memory-efficient)
#define HISTORY_SIZE 10
CompactSensorData sensor_history[HISTORY_SIZE];
uint8_t history_index = 0;

void store_sensor_data(CompactSensorData data) {
    sensor_history[history_index] = data;
    history_index = (history_index + 1) % HISTORY_SIZE;
}

// Fast integer-based steering calculation
int16_t calculate_fast_steering(CompactSensorData data) {
    // Use integer arithmetic for speed (avoiding float operations)
    int32_t left_intersection = (int32_t)data.distances[0] * cos_table_20;   // Precomputed lookup
    int32_t right_intersection = (int32_t)data.distances[4] * cos_table_70;
    
    int32_t intersection_diff = left_intersection - right_intersection;
    return (int16_t)clamp(intersection_diff >> 8, -300, 300);  // Fixed-point division
}
```

### 6. Testing and Validation Framework

#### Performance Benchmarking
```cpp
typedef struct {
    uint32_t loop_count;
    uint32_t total_execution_time;
    uint32_t max_execution_time;
    uint32_t sensor_read_failures;
    float average_lap_time;
} PerformanceMetrics;

void log_performance_metrics(PerformanceMetrics metrics) {
    Serial.print("PERF,");
    Serial.print(metrics.loop_count);
    Serial.print(",");
    Serial.print(metrics.total_execution_time / metrics.loop_count);  // Average loop time
    Serial.print(",");
    Serial.print(metrics.max_execution_time);
    Serial.print(",");
    Serial.print(metrics.sensor_read_failures);
    Serial.print(",");
    Serial.println(metrics.average_lap_time);
}
```

### 7. Missing Critical Elements

#### A. Emergency Safety Systems
- **Collision Avoidance**: Front sensor emergency stop at <100mm
- **Stuck Detection**: Motor current monitoring for wheel slip detection
- **Communication Watchdog**: Arduino reset capability for system recovery

#### B. Course Learning Capabilities
- **Lap Time Optimization**: Store successful racing lines for course-specific optimization
- **Parameter Adaptation**: Dynamic tuning based on course characteristics

#### C. Competitive Strategy Features
- **Multi-Mode Racing**: Conservative/Balanced/Aggressive profiles for different attempt strategies
- **Time-Based Decisions**: Speed adjustment based on remaining competition time

These improvements collectively target the sub-9-second lap time goal while maintaining system reliability and achieving the 100Hz control loop objective. The emphasis on dynamic optimization, corrected speed parameters, and high-frequency sensor operation addresses the core performance limitations identified in the current system.

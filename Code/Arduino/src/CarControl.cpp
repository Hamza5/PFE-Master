/*
Arduino program allowing to control the body of the car and get the readings
from the distance sensors and the digital temperature and humidity sensor.

Hamza Abbad
*/
#include "CarControl.h"

dht DHTSensor;
Servo sonar;
double * distances;
int speed;
int rotationAngle;
char command;

void setup() {
  // Distance sensors
  pinMode(DISTANCE_SENSOR_1_TRIG, OUTPUT);
  pinMode(DISTANCE_SENSOR_1_ECHO, INPUT);
  pinMode(DISTANCE_SENSOR_2_TRIG, OUTPUT);
  pinMode(DISTANCE_SENSOR_2_ECHO, INPUT);
  pinMode(DISTANCE_SENSOR_3_TRIG, OUTPUT);
  pinMode(DISTANCE_SENSOR_3_ECHO, INPUT);
  pinMode(DISTANCE_SENSOR_R_TRIG, OUTPUT);
  pinMode(DISTANCE_SENSOR_R_ECHO, INPUT);
  // DC Motors
  pinMode(RIGHT_MOTOR_PIN1, OUTPUT);
  pinMode(RIGHT_MOTOR_PIN2, OUTPUT);
  pinMode(LEFT_MOTOR_PIN1, OUTPUT);
  pinMode(LEFT_MOTOR_PIN2, OUTPUT);
  pinMode(RIGHT_MOTOR_SPEED_PIN, OUTPUT);
  pinMode(LEFT_MOTOR_SPEED_PIN, OUTPUT);
  // DHT22
  DHTSensor.read22(DHT_DATA);
  // Servo motor
  sonar.attach(SERVO_PIN);
  // Serial connection
  Serial.begin(BAUD_RATE);
  Serial.setTimeout(SERIAL_TIMEOUT);

  rotationAngle = MIN_ANGLE;
  // sonar.write(rotationAngle);

  speed = 127;
  Serial.print("P");
  Serial.println(speed);
}

void loop() {
  if (Serial.available()) {
    command = Serial.read();
    switch (command) {
      case GET_DISTANCES:
        distances = getDistances();
        Serial.print("|");
        for (size_t i = 0; i < DISTANCES_COUNT; i++) {
          Serial.print(distances[i]);
          Serial.print("|");
        }
        Serial.println();
        free(distances);
        break;
      case MOVE_FORWARD:
        moveForward(speed);
        break;
      case MOVE_BACKWARD:
        moveBackward(speed);
        break;
      case TURN_RIGHT:
        turnRight(speed);
        break;
      case TURN_LEFT:
        turnLeft(speed);
        break;
      case STOP:
        stop();
        break;
      case TEMP:
        DHTSensor.read22(DHT_DATA);
        Serial.print("T");
        Serial.println(DHTSensor.temperature);
        break;
      case SET_SPEED:
        speed = Serial.parseInt();
        Serial.print("P");
        Serial.println(speed);
        break;
    }
  }
}

void forwardRight(byte speed) {
  digitalWrite(RIGHT_MOTOR_PIN1, HIGH);
  digitalWrite(RIGHT_MOTOR_PIN2, LOW);
  analogWrite(RIGHT_MOTOR_SPEED_PIN, speed);
}

void backwardRight(byte speed) {
  digitalWrite(RIGHT_MOTOR_PIN1, LOW);
  digitalWrite(RIGHT_MOTOR_PIN2, HIGH);
  analogWrite(RIGHT_MOTOR_SPEED_PIN, speed);
}

void forwardLeft(byte speed) {
  digitalWrite(LEFT_MOTOR_PIN1, HIGH);
  digitalWrite(LEFT_MOTOR_PIN2, LOW);
  analogWrite(LEFT_MOTOR_SPEED_PIN, speed);
}

void backwardLeft(byte speed) {
  digitalWrite(LEFT_MOTOR_PIN1, LOW);
  digitalWrite(LEFT_MOTOR_PIN2, HIGH);
  analogWrite(LEFT_MOTOR_SPEED_PIN, speed);
}

void stop() {
  analogWrite(LEFT_MOTOR_SPEED_PIN, 0);
  analogWrite(RIGHT_MOTOR_SPEED_PIN, 0);
  digitalWrite(RIGHT_MOTOR_PIN1, LOW);
  digitalWrite(RIGHT_MOTOR_PIN2, LOW);
  digitalWrite(LEFT_MOTOR_PIN1, LOW);
  digitalWrite(LEFT_MOTOR_PIN2, LOW);
}

void moveForward(byte speed) {
  forwardLeft(speed);
  forwardRight(speed);
}

void moveBackward(byte speed) {
  backwardLeft(speed);
  backwardRight(speed);
}

void turnRight(byte speed) {
  backwardRight(speed);
  forwardLeft(speed);
}

void turnLeft(byte speed) {
  backwardLeft(speed);
  forwardRight(speed);
}

double * getDistances() {
  double * distances = (double *) malloc(DISTANCES_COUNT * sizeof(double));
  int i;
  if (rotationAngle == MIN_ANGLE) {
    while (rotationAngle <= MAX_ANGLE) {
        sonar.write(rotationAngle);
        delay(TURN_WAIT_TIME);
        i = (rotationAngle-MIN_ANGLE)/STEP_ANGLE;
        distances[i] = getDistance(ROTATING);
        rotationAngle += STEP_ANGLE;
    }
    rotationAngle = MAX_ANGLE;
  } else {
    while (rotationAngle >= MIN_ANGLE) {
        sonar.write(rotationAngle);
        delay(TURN_WAIT_TIME);
        i = (rotationAngle-MIN_ANGLE)/STEP_ANGLE;
        distances[i] = getDistance(ROTATING);
        rotationAngle -= STEP_ANGLE;
    }
    rotationAngle = MIN_ANGLE;
  }
  return distances;
}

double getDistance(DISTANCE_SENSOR sensor) {
  unsigned long duration;
  int trig;
  int echo;
  switch (sensor) {
    case RIGHT:
      trig = DISTANCE_SENSOR_1_TRIG;
      echo = DISTANCE_SENSOR_1_ECHO;
      break;
    case CENTER:
      trig = DISTANCE_SENSOR_2_TRIG;
      echo = DISTANCE_SENSOR_2_ECHO;
      break;
    case LEFT:
      trig = DISTANCE_SENSOR_3_TRIG;
      echo = DISTANCE_SENSOR_3_ECHO;
      break;
    case ROTATING:
      trig = DISTANCE_SENSOR_R_TRIG;
      echo = DISTANCE_SENSOR_R_ECHO;
      break;
  }
  digitalWrite(trig, HIGH);// Generate
  delayMicroseconds(10);   // the
  digitalWrite(trig, LOW); // pulse
  duration = pulseIn(echo, HIGH, MAX_WAIT_TIME);
  return (duration/1e6) * getSoundSpeed(DHTSensor.temperature) / 2;
}

double getSoundSpeed(double temperature) {
  return SOUND_SPEED_FACTOR * temperature + SOUND_SPEED_CONSTANT;
}

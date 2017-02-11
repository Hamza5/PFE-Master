/*
Arduino program allowing to control the body of the car and get the readings
from the distance sensors and the digital temperature and humidity sensor.

Hamza Abbad
*/
// #define DEBUG
#include "CarControl.h"

dht DHTSensor;
double * distances;
bool stopped = true;
DISTANCE_SENSOR direction;
int speed = 127;
unsigned long started;

void setup() {
  // Distance sensors
  pinMode(DISTANCE_SENSOR_1_TRIG, OUTPUT);
  pinMode(DISTANCE_SENSOR_1_ECHO, INPUT);
  pinMode(DISTANCE_SENSOR_2_TRIG, OUTPUT);
  pinMode(DISTANCE_SENSOR_2_ECHO, INPUT);
  pinMode(DISTANCE_SENSOR_3_TRIG, OUTPUT);
  pinMode(DISTANCE_SENSOR_3_ECHO, INPUT);
  // DC Motors
  pinMode(RIGHT_MOTOR_PIN1, OUTPUT);
  pinMode(RIGHT_MOTOR_PIN2, OUTPUT);
  pinMode(LEFT_MOTOR_PIN1, OUTPUT);
  pinMode(LEFT_MOTOR_PIN2, OUTPUT);
  pinMode(RIGHT_MOTOR_SPEED_PIN, OUTPUT);
  pinMode(LEFT_MOTOR_SPEED_PIN, OUTPUT);
  // DHT22
  // pinMode(DHT_DATA, INPUT);
  DHTSensor.read22(DHT_DATA);
  // Serial connection
  Serial.begin(BAUD_RATE);
  Serial.setTimeout(SERIAL_TIMEOUT);
  // Random number generation. This pin is not connected
  randomSeed(analogRead(0));
  started = millis();
}

void loop() {
  if (Serial.available()) {
    char command = Serial.read();
    int action_delay = MOVE_ACTION_TIME;
    switch (command) {
      case GET_DISTANCES:
        distances = getDistances();
        Serial.print("|");
        for (size_t i = 0; i < 3; i++) {
          Serial.print(distances[i]);
          Serial.print("|");
        }
        Serial.println();
        break;
      case MOVE_FORWARD:
        moveForward(speed);
        if (Serial.available()) {
          action_delay = Serial.parseInt();
        }
        delay(action_delay);
        stop();
        break;
      case MOVE_BACKWARD:
        moveBackward(speed);
        if (Serial.available()) {
          action_delay = Serial.parseInt();
        }
        delay(action_delay);
        stop();
        break;
      case TURN_RIGHT:
        turnRight(speed);
        if (Serial.available()) {
          action_delay = Serial.parseInt();
        }
        delay(action_delay);
        stop();
        break;
      case TURN_LEFT:
        turnLeft(speed);
        if (Serial.available()) {
          action_delay = Serial.parseInt();
        }
        delay(action_delay);
        stop();
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
        Serial.println("P"+speed);
        break;
      case NAVIGATE:
        stopped = false;
        break;
    }
  } else if (!stopped) {
    navigate(speed);
    delay(MOVE_ACTION_TIME);
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
  stopped = true;
}

void moveForward(byte speed) {
  stopped = false;
  forwardLeft(speed);
  forwardRight(speed);
}

void moveBackward(byte speed) {
  stopped = false;
  backwardLeft(speed);
  backwardRight(speed);
}

void turnRight(byte speed) {
  stopped = false;
  backwardRight(speed);
  forwardLeft(speed);
}

void turnLeft(byte speed) {
  stopped = false;
  backwardLeft(speed);
  forwardRight(speed);
}

double * getDistances() {
  double * distances = (double *) malloc(3 * sizeof(double));
  distances[0] = getDistance(LEFT);
  distances[1] = getDistance(CENTER);
  distances[2] = getDistance(RIGHT);
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

double averageDistance() {
  double * distances = getDistances();
  int corrects = 0;
  double sum = 0;
  for (size_t i = 0; i < 3; i++) {
    if (distances[i] > 0) {
      corrects++;
      sum += distances[i];
    }
  }
  if (corrects > 0) return sum / corrects;
  else return 0;
}

unsigned int argmin(double * array, unsigned int length) {
  unsigned int minIndex = 0;
  for (size_t i = 1; i < length; i++)
    if (array[i] < array[minIndex]) minIndex = i;
  return minIndex;
}

void navigate(byte speed) {
  double * distances = getDistances();
  if (distances[CENTER] < MIN_OBSTACLE_DISTANCE) moveBackward(speed);
  else
  if (distances[LEFT] > 0 && distances[LEFT] < MAX_OBSTACLE_DISTANCE && argmin(distances, 3) == LEFT) direction = RIGHT;
  else if (distances[RIGHT] > 0 && distances[RIGHT] < MAX_OBSTACLE_DISTANCE && argmin(distances, 3) == RIGHT) direction = LEFT;
  else direction = CENTER;
  #ifdef DEBUG
  Serial.print(direction == CENTER ? "^" : (direction == RIGHT ? ">" : "<"));
  #else
  if (direction == CENTER) moveForward(speed);
  else if (direction == RIGHT) turnRight(speed);
  else turnLeft(speed);
  #endif
}

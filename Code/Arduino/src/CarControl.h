/*
Header file for CarControl.cpp

Hamza Abbad
*/

#ifndef CARCONTROL_H
#define CARCONTROL_H

#include <Arduino.h>
#include <dht.h>

#define BAUD_RATE 9600

// HR-S04 distance sensors
#define DISTANCE_SENSOR_1_TRIG 22
#define DISTANCE_SENSOR_1_ECHO 23
#define DISTANCE_SENSOR_2_TRIG 24
#define DISTANCE_SENSOR_2_ECHO 25
#define DISTANCE_SENSOR_3_TRIG 26
#define DISTANCE_SENSOR_3_ECHO 27

enum DISTANCE_SENSOR { LEFT = 0, CENTER = 1, RIGHT = 2 };

// DHT22 sensors
#define DHT_DATA 51

// DC Motors
#define RIGHT_MOTOR_PIN1 11
#define RIGHT_MOTOR_PIN2 10
#define LEFT_MOTOR_PIN1 9
#define LEFT_MOTOR_PIN2 8
#define RIGHT_MOTOR_SPEED_PIN 12
#define LEFT_MOTOR_SPEED_PIN 13

double getSoundSpeed(double);
double getDistance(DISTANCE_SENSOR sensor);
double * getDistances();
void forwardRight(byte);
void backwardRight(byte);
void forwardLeft(byte);
void backwardLeft(byte);
void stop();
void moveForward(byte);
void moveBackward(byte);
void turnRight(byte);
void turnLeft(byte);

// Commands
#define GET_DISTANCES 'D'
#define MOVE_FORWARD 'F'
#define MOVE_BACKWARD 'B'
#define TURN_LEFT 'L'
#define TURN_RIGHT 'R'
#define STOP 'S'
#define TEMP 'T'
#define SET_SPEED 'P'

// Other
#define MAX_WAIT_TIME 30000 // Maximum waiting time for the echo (3O ms)
#define SOUND_SPEED_CONSTANT 331.4
#define SOUND_SPEED_FACTOR 0.6
#define SERIAL_TIMEOUT 100 // milliseconds

#endif

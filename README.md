# -IMU-Position-Tracking-and-Interactive-Animation
This project aims at creating a HCI maze solving game with 3D objects in python.
It has a firmware part and a software part.

In firmware part, it uses a 9DOF GY-86 IMU unit(“joystick”) to track the trajectory(translational movement and rotational movement of an object). The GY-86 sensor detects the translational acceleration, angular acceleration and the strength of magnetic field of the unit in x, y and z axises. First, the arduino code uses a self-designed Kalman Filter to correct the 9 readings. Then it sends those data through serial communication protocol to python. 

In the software part, Python first gets the readings and uses DCM matrix calculation to transform the 9 raw readings into the global position of the unit. With this data it changes position of the 3d object on Tkinter according to linear transformation, making the 3d object move as it is in real world.

Then you can control your joystick to play the simple maze game. You can first pick up an 3d object you want to play with. Then you try to control it to make it pass the maze. 

The libraries I used are listed here:

Arduino:
"Wire.h"
"I2Cdev.h"
"MPU6050.h"
"Timer.h"
"HMC5883L.h"
Python:
Pyserial
Tkinter

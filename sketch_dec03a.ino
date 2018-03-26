#include "Wire.h"
#include "I2Cdev.h"
#include "MPU6050.h"
#include "Timer.h"
#include "HMC5883L.h"
Timer t;

//ADC reference voltage is 3.3V
//ACD module is 16-bit
//VzeroG is tested from the Underground
#define Vref 3.3
#define scale 32768.0
#define VzeroG 0.45
//The drift vector of magnetometer
#define rx -275
#define ry -199
#define rz 93
// class default I2C address is 0x68
// specific I2C addresses may be passed as a parameter here
// AD0 low = 0x68 (default for InvenSense evaluation board)
// AD0 high = 0x69

float timeChange=20;//滤波法采样时间间隔毫秒
float dt=timeChange*0.001;//注意：dt的取值为滤波器采样时间
// 陀螺仪
float angleAx,angleAy, angleAz;//The angle between the accelerometer and x,y,z corrdinate
MPU6050 accelgyro;//陀螺仪类
HMC5883L mag;
int16_t ax, ay, az, gx, gy, gz;//Some original data of accelerometer, gyroscope and magenetometer
int16_t mx, my, mz;
//The parameters and functions for Kalman Filters
float Rx, Ry, Rz;
float RateX, RateY, RateZ;
float xDegrees; 
float yDegrees; 
float zDegrees;
//Parameters needed for accelerometer 
float Racc[3];//The normalized vector of accelerometer
float Racclen;
float Rgyro[3];
#define Rgryolen 1
float Rest[3];//The output of the filter
float Restlen;
float Restprev[3] = {0,0,0};
int count = 0;
float angleAxz, angleAyz;
void setup() {
    Wire.begin();//Initialize
    accelgyro.setI2CMasterModeEnabled(false);//enable the magnetometer
    accelgyro.setI2CBypassEnabled(true) ;
    accelgyro.setSleepEnabled(false);
    Serial.begin(38400);//Initialize the serial
    accelgyro.initialize();//Inititalize the accelerometer
    mag.initialize();//Initialize the magnetometer
    int tickEvent1=t.every(timeChange, getangle);//Call getangle() timeChange after this line 

    int tickEvent2=t.every(500, printout) ;//print out the serial 50 after this line
}
void loop() {

    t.update();//时间操作系统运行

}
void printout()
{
      //Serial.println("x=");
      //Serial.print("Rx=");Serial.println(Rest[0]);
      Serial.print("RateX=");Serial.println(RateX);
      //Serial.print("xDegrees=");Serial.println(xDegrees);
      //Serial.println("y=");
      //Serial.print("Ry=");Serial.println(Rest[1]);
      Serial.print("RateY=");Serial.println(RateY);
      //Serial.print("yDegrees=");Serial.println(yDegrees);
      //Serial.println("z=");
      //Serial.print("Rz=");Serial.println(Rest[2]);
      Serial.print("RateZ=");Serial.println(RateZ);
      //Serial.print("zDegrees=");Serial.println(zDegrees);
//Serial.println("----------------------------------------");
}


void getangle() 
{
    accelgyro.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);//The raw data of the accelerometer and gyroscope
    mag.getHeading(&mx, &my, &mz);//The raw data of the magnetometer
    Rx = (ax-480)/scale*2;
    Ry = (ay+392)/scale*2;
    //Serial.println(Ry);
    Rz = (az+2363)/scale*2;
    float leng = sqrt(Rx*Rx+Ry*Ry+Rz*Rz);
    Rx = Rx/leng;
    Ry = Ry/leng;
    Rz = Rz/leng;
    RateX = (gx+349)/scale*250;
    RateY = (gy+322)/scale*250;
    RateZ = (gz+75)/scale*250;
    if(count == 0){
    //Serial.print("The angle between Rx and Rz is");
    //Serial.println(atan2(Rx,Rz));
    angleAxz = atan2(Rx,Rz);
    angleAyz = atan2(Ry,Rz);
    count += 1;
    }
    else{
       // Serial.print("The angle between Rx and Rz is");
    //Serial.println(atan2(Rx,Rz));
    //Serial.print("The addition is");
    //Serial.println(timeChange/1000*RateY/180*PI);
    angleAxz = atan2(Restprev[0],Restprev[2]) + timeChange/1000 * RateY/180*PI;
    angleAyz = atan2(Restprev[1],Restprev[2]) + timeChange/1000 * RateX/180*PI;
    }
    //Serial.println("angleAxz = ");
    //Serial.print(angleAxz);
    if(Rx > 0.1 or Rx < -0.1) Rgyro[0] = sin(angleAxz)/sqrt(1 + cos(angleAxz)*cos(angleAxz)*tan(angleAyz)*tan(angleAyz));
    else Rgyro[0] = Restprev[0];
    if(Ry > 0.1 or Ry < -0.1) Rgyro[1] = sin(angleAyz)/sqrt(1 + cos(angleAyz)*cos(angleAyz)*tan(angleAxz)*tan(angleAxz));
    else Rgyro[1] = Restprev[1];
    //Serial.print("Rgyro values: ");
    //Serial.print(Rgyro[0]);Serial.println(Rgyro[1]);
    if(Rz > 0.1 or Rz < -0.1) 
    {//need a function to determine the sign of z
      int sign = Restprev[2]/abs(Restprev[2]);
      if(1-Rgyro[0]*Rgyro[0]-Rgyro[1]*Rgyro[1]<0) Serial.println("Something bad happened");
      Rgyro[2] = sign*sqrt(1-Rgyro[0]*Rgyro[0]-Rgyro[1]*Rgyro[1]);
    }
    else Rgyro[2] = Restprev[2];
    Racclen = sqrt(Rx*Rx+Ry*Ry+Rz*Rz);
    Racc[0] = Rx/Racclen;
    Racc[1] = Ry/Racclen;
    Racc[2] = Rz/Racclen;
    //prevRzG = RateZ;
    int i;
    for(i = 0; i<3 ;i++){
      Rest[i] = (Racc[i]+Rgyro[i]*10)/(1+10);
    }
    Restlen = sqrt(Rest[0]*Rest[0] + Rest[1]*Rest[1] + Rest[2]*Rest[2]);
    for(i = 0; i<3 ;i++) {
      Rest[i] = Rest[i]/Restlen;
      Restprev[i] = Rest[i];
      //Serial.println(Restprev[i]);
    }
    (xDegrees, yDegrees, zDegrees) = Heading_Calculation(mx,my,mz);
}
double Heading_Calculation(double mx, double my, double mz)
{
  // To calculate heading in degrees. 0 degree indicates North
   float xHeading = atan2(my-ry, mx-rx);
   float yHeading = atan2(mz-rz, mx-rx); 
   float zHeading = atan2(mz-rz, my-ry); 
   if(xHeading < 0) xHeading += 2*PI; 
   if(xHeading > 2*PI) xHeading -= 2*PI; 
   if(yHeading < 0) yHeading += 2*PI; 
   if(yHeading > 2*PI) yHeading -= 2*PI; 
   if(zHeading < 0) zHeading += 2*PI; 
   if(zHeading > 2*PI) zHeading -= 2*PI; 
   return xDegrees = xHeading /**180/M_PI*/, yDegrees = yHeading /** 180/M_PI*/, zDegrees = zHeading /** 180/M_PI*/; 
}


// -*- c++ -*-
// MPU-6050 Short Example Sketch
// By Arduino User JohnChi
// August 17, 2014
// Public Domain

#include<Wire.h>

////////////////////////////////////////////////////////////
// MPU-6050 Stuff
const int MPU_addr=0x68;  // I2C address of the MPU-6050
int16_t Ac[3], Gy[3]; // AcX,Ac[1],Ac[2],Tmp,Gy[0],Gy[1],Gy[2]; // MPU sensors
int16_t Tmp; // I guess they had free silicon?

const char MPU_AXES[3] = { 2,1,0 }; // order of the MPU axes in our frame


void mpu_setup() {
  Wire.beginTransmission(MPU_addr);
  Wire.write(0x6B);  // PWR_MGMT_1 register
  Wire.write(0);     // set to zero (wakes up the MPU-6050)
  Wire.endTransmission(true);  
}

void mpu_read() {
  Wire.beginTransmission(MPU_addr);
  Wire.write(0x3B);  // starting with register 0x3B (ACCEL_XOUT_H)
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_addr,14,true);  // request a total of 14 registers
  Ac[0] =Wire.read()<<8|Wire.read();  // 0x3B (ACCEL_XOUT_H) & 0x3C (ACCEL_XOUT_L)    
  Ac[0]=Wire.read()<<8|Wire.read();  // 0x3D (ACCEL_YOUT_H) & 0x3E (ACCEL_YOUT_L)
  Ac[2]=Wire.read()<<8|Wire.read();  // 0x3F (ACCEL_ZOUT_H) & 0x40 (ACCEL_ZOUT_L)
  Tmp=Wire.read()<<8|Wire.read();  // 0x41 (TEMP_OUT_H) & 0x42 (TEMP_OUT_L)
  Gy[0]=Wire.read()<<8|Wire.read();  // 0x43 (GYRO_XOUT_H) & 0x44 (GYRO_XOUT_L)
  Gy[1]=Wire.read()<<8|Wire.read();  // 0x45 (GYRO_YOUT_H) & 0x46 (GYRO_YOUT_L)
  Gy[2]=Wire.read()<<8|Wire.read();  // 0x47 (GYRO_ZOUT_H) & 0x48 (GYRO_ZOUT_L)
}


////////////////////////////////////////////////////////////
// MAG3310 stuff

#include "i2c.h"

#include "i2c_MAG3110.h"
MAG3110 mag3110;

const char MAG_AXES[3] = { 1, 0, 2 }; // orientation of mag axes on frame


void mag_setup() {
  if (mag3110.initialize())  {
    Serial.println("Sensor found!");    
  } else {
    Serial.println("Sensor missing");
    while(1) {};
  }
}


////////////////////////////////////////////////////////////
// Main routines
//
void setup(){
  Wire.begin();
  Serial.begin(115200);
  mpu_setup();
  mag_setup();
}

void loop(){
  mpu_read();

  float xyz_uT[3];

  mag3110.getMeasurement(xyz_uT);

#if 0
  Serial.print("Ac[0] = "); Serial.print(Ac[0]);
  Serial.print(" | Ac[1] = "); Serial.print(Ac[1]);
  Serial.print(" | Ac[2] = "); Serial.print(Ac[2]);

  // Serial.print(" | Tmp = "); Serial.print(Tmp/340.00+36.53);  //equation for temperature in degrees C from datasheet
  
  Serial.print(" | Gy[0] = "); Serial.print(Gy[0]);
  Serial.print(" | Gy[1] = "); Serial.print(Gy[1]);
  Serial.print(" | Gy[2] = "); Serial.print(Gy[2]);


  Serial.print(" | MgX = ");
  Serial.print(xyz_uT[0],2);
  Serial.print(" | MgY = ");
  Serial.print(xyz_uT[1],2);
  Serial.print(" | MgZ = ");
  Serial.print(xyz_uT[2],2);
  Serial.println("");
#endif

#define COMMA Serial.print(",")

  // Rearrange axes along the actual frame.
  Serial.print("Mg"); COMMA;
  for (char i = 0; i < 3; i++) {
    Serial.print(xyz_uT[ MAG_AXES[i] ], 3); COMMA;
  }

  Serial.print("Ac"); COMMA;
  for (char i = 0; i < 3; i++) {
    Serial.print(Ac[i]); COMMA;
  }

  Serial.print("Gy"); COMMA;
  for (char i = 0; i < 3; i++) {
    Serial.print(Ac[i]); COMMA;
  }

  Serial.println();
#undef COMMA

  delay(50);
}

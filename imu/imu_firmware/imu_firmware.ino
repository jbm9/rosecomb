// -*- c++ -*-
// MPU-6050 Short Example Sketch
// By Arduino User JohnChi
// August 17, 2014
// Public Domain

#include <Wire.h>

// For MAG3110 calibration, run this with
// #define ENABLE_MAG_CAL_OUTPUT 1

////////////////////////////////////////////////////////////
// MPU-6050 Stuff
const int MPU_addr=0x68;  // I2C address of the MPU-6050
int16_t Ac[3], Gy[3]; // AcX,Ac[1],Ac[2],Tmp,Gy[0],Gy[1],Gy[2]; // MPU sensors
int16_t Tmp; // I guess they had free silicon?

const char MPU_AXES[3] = { 1,2,0 }; // order of the MPU axes in our frame


void mpu_setup() {
  Wire.beginTransmission(MPU_addr);
  Wire.write(0x6B);  // PWR_MGMT_1 register
  Wire.write(0x00);  // Disable SLEEP, wake up
  Wire.endTransmission(true);

  delay(1);

  Wire.beginTransmission(MPU_addr);
  Wire.write(0x6B);  // PWR_MGMT_1 register
  Wire.write(0x01);  // Enable PLL on x-axis gyro
  Wire.endTransmission(true);

  Wire.beginTransmission(MPU_addr);
  Wire.write(0x6C);  // PWR_MGMT_2 register
  Wire.write(0x01);  // Disable z-axis gyro...
  Wire.endTransmission(true);


  Wire.beginTransmission(MPU_addr);
  Wire.write(0x19);  // SMPRT_DIV, p11
  Wire.write(9);  // Don't need 1kHz sample rate: divide by 1+9=10
  Wire.endTransmission(true);

  Wire.beginTransmission(MPU_addr);
  Wire.write(0x1A);  // CONFIG, p13
  Wire.write(0x03);  // Disable FSYNC, set a 44Hz BW DLPF
  Wire.endTransmission(true);



  Wire.beginTransmission(MPU_addr);
  Wire.write(0x6B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_addr, 2, true);
  Serial.println(Wire.read(), HEX);
  Serial.println(Wire.read(), HEX);

  Serial.println("0x19:");
  Wire.beginTransmission(MPU_addr);
  Wire.write(0x19);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_addr, 4, true);
  Serial.println(Wire.read(), HEX);
  Serial.println(Wire.read(), HEX);
  Serial.println(Wire.read(), HEX);
  Serial.println(Wire.read(), HEX);

}

void mpu_read() {

  Wire.beginTransmission(MPU_addr);
  Wire.write(0x43);  // pull Gyro data.
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_addr,6,true);  // request a total of 14 registers

  Gy[0]=Wire.read()<<8|Wire.read();  // 0x43 (GYRO_XOUT_H) & 0x44 (GYRO_XOUT_L)
  Gy[1]=Wire.read()<<8|Wire.read();  // 0x45 (GYRO_YOUT_H) & 0x46 (GYRO_YOUT_L)
  Gy[2]=Wire.read()<<8|Wire.read();  // 0x47 (GYRO_ZOUT_H) & 0x48 (GYRO_ZOUT_L)

  Wire.beginTransmission(MPU_addr);
  Wire.write(0x3B);  // starting with register 0x3B (ACCEL_XOUT_H)
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_addr,6,true);  // request a total of 14 registers
  Ac[0]=Wire.read()<<8|Wire.read();  // 0x3B (ACCEL_XOUT_H) & 0x3C (ACCEL_XOUT_L)
  Ac[1]=Wire.read()<<8|Wire.read();  // 0x3D (ACCEL_YOUT_H) & 0x3E (ACCEL_YOUT_L)
  Ac[2]=Wire.read()<<8|Wire.read();  // 0x3F (ACCEL_ZOUT_H) & 0x40 (ACCEL_ZOUT_L)

  // Tmp  =Wire.read()<<8|Wire.read();  // 0x41 (TEMP_OUT_H) & 0x42 (TEMP_OUT_L)

}


////////////////////////////////////////////////////////////
// MAG3310 stuff

#include "i2c.h"

#include "i2c_MAG3110.h"
MAG3110 mag3110;

const char MAG_AXES[3] = {  0, 1, 2 }; // orientation of mag axes on frame

float mag_offsets[3] = { 0.0, 0.0, 0.0 };

void mag_cal() {
  digitalWrite(13, 1);

  delay(100);

  const int N = 2000;

  for (int i = 0; i < N; i++) {
    float xyz_uT[3];
    mag3110.getMeasurement(xyz_uT);
    for (char j = 0; j < 3; j++) {
      mag_offsets[j] += xyz_uT[j];
    }
    delayMicroseconds(50);
  }

  Serial.print("Calibration: ");
  for (char j = 0; j < 3; j++) {
    mag_offsets[j] /= N;
    Serial.print(mag_offsets[j], 2);
    Serial.print(" ");
  }
  Serial.println();
  digitalWrite(13, 0);
}


void mag_setup() {
  pinMode(13, OUTPUT);
  if (mag3110.initialize(20))  {
    Serial.println("Sensor found!");
    mag3110.setRawMode(0);
    mag3110.setSensorAutoReset(1);

    mag_cal();

  } else {
    Serial.println("Sensor missing");
    while(1) {};
  }
}


////////////////////////////////////////////////////////////
// Main routines//
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

#define COMMA Serial.print(",")

#if ENABLE_MAG_CAL_OUTPUT
  // We need raw readings to use with the python calibration script
  int16_t xyz[3];
  mag3110.getMeasurement(xyz);

  Serial.print("MR"); COMMA;
  for (char i = 0; i < 3; i++) {
    Serial.print(xyz[i], DEC); COMMA;
  }
  Serial.println();
#endif

  // Rearrange axes along the actual frame.
  Serial.print("Mg"); COMMA;
  for (char i = 0; i < 3; i++) {
    float a = xyz_uT[ MAG_AXES[i] ] - mag_offsets[ MAG_AXES[i] ];
    Serial.print(a, 3); COMMA;
  }

  Serial.print("Ac"); COMMA;
  for (char i = 0; i < 3; i++) {
    Serial.print(Ac[ MPU_AXES[i] ]); COMMA;
  }

  Serial.print("Gy"); COMMA;
  for (char i = 0; i < 3; i++) {
    Serial.print(Gy[ MPU_AXES[i] ]); COMMA;
  }

  Serial.println();
#undef COMMA

  delay(50);
}

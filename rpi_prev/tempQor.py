#! /usr/bin/env python
# I2C driver to get temperature data on T37 RF Boards
import smbus
import time
import sys
import math
import RPi.GPIO as GPIO


    
bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

Reg_SEL = 0x00 # Temperature Register
Qorvo1_temp_address = 0x4C #Qorvo Side 1 Temp Sensor Address on RF Board
Qorvo2_temp_address = 0x49 #Macom Side 2 Temp SensorAddress on RF Board

def tempSen(Qorvo_temp_degC):
    bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)
    #Qorvo_temp_address = 0x4E #Qorvo Temp Sensor Address on Chainstick
    #MACOM_temp_address = 0x4B #Macom PA Temp SensorAddress on Chainstick
    Reg_SEL = 0x00 # Temperature Register
    Qorvo1_temp_address = 0x4C #   was 0x48   Qorvo Side 1 Temp Sensor Address on RF Board
    Qorvo2_temp_address = 0x49 #Macom Side 2 Temp SensorAddress on RF Board

    Qorvo_Temp = bus.read_i2c_block_data(Qorvo1_temp_address,Reg_SEL)
    Qorvo_Temp_MSB = Qorvo_Temp[0] << 8
    Qorvo_Temp_LSB = Qorvo_Temp[1]
    Qorvo_Temp_Final = Qorvo_Temp_MSB | Qorvo_Temp_LSB
    Q1_11bit = Qorvo_Temp_Final >> 5 #change to 11bit
    #print ("Qorvo_11bit:",bin(Q1_11bit))

    #check bit status Qorvo 1
    Q1pos_neg_check = Q1_11bit & 0b10000000000
    Q1_check_bit = Q1pos_neg_check >> 10

    if (Q1_check_bit == 0):
        Qorvo_temp_degC = Q1_11bit * 0.125
        print ("Qorvo1 Temp degC: ", Qorvo_temp_degC) 
        return Qorvo_temp_degC
    else:
        Qorvo_temp_degC = Q1_11bit ^ 0b11111111111
        Qorvo_temp_degC = Qorvo_temp_degC + 1
        Qorvo_temp_degC = Qorvo_temp_degC * -0.125
        print ("Qorvo1 Temp degC: -", Qorvo_temp_degC) 
        return Qorvo_temp_degC
        
   #print("Return")
        print ("Qorvo1 Temp degC: ", Qorvo_temp_degC)   
         print ("Qorvo1 Temp degC: -", Qorvo_temp_degC) 
        return Qorvo_temp_deg
    

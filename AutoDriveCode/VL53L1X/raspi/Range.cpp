#include <iostream>
#include "VL53L1X.h"
#include <unistd.h>
#include <ctime>

using namespace std;

VL53L1X Distance_Sensor;


int main()
{
	
	
   bool status;  
   status = Distance_Sensor.begin();
  // cout << status << endl;
  int counter = 0;
  int rate = 0;
  double time = 0;
  clock_t begin = clock();

while(counter < 500){

   
   Distance_Sensor.startMeasurement(); //Write configuration bytes to initiate measurement

  //Poll for completion of measurement. Takes 40-50ms.
  while(Distance_Sensor.newDataReady() == false){
    usleep(5);
 }   


  int distance = Distance_Sensor.getDistance(); //Get the result of the measurement from the sensor
  cout << "Distance(mm) :"<< distance << endl;
  counter++;

}

  clock_t end = clock();
  time = begin - end;
  rate = 50/time;
  cout << time;
 return 0;
}


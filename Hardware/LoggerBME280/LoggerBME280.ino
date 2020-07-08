#include <Wire.h>
#include <Adafruit_BME280.h>

Adafruit_BME280 bme; // I2C

unsigned long delayTime;

void setup() {
    Serial.begin(9600);
    if (! bme.begin(0x76, &Wire)) {
        Serial.println("$");
        while (1);
    }
    delayTime = 100;
}

void loop() {
    printValues();
    delay(delayTime);
}

void printValues() {
    Serial.print("$");
    Serial.print(bme.readTemperature());
    Serial.print(",");

    Serial.print(bme.readHumidity());
    Serial.print(",");
    
    Serial.print(bme.readPressure());
    Serial.print("#");
    Serial.println();
}

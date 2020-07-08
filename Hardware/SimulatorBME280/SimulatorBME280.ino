unsigned long delayTime;

void setup() {
    Serial.begin(9600);
    delayTime = 100;
}

void loop() {
    printValues();
    delay(delayTime);
}

void printValues() {
    Serial.print("$");
    Serial.print(random(15, 25));
    Serial.print(",");

    Serial.print(random(30, 40));
    Serial.print(",");
    
    Serial.print(random(90000, 100000));
    Serial.print("#");
    Serial.println();
}

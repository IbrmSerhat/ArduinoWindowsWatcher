#include <Arduino.h>
#include "A4988.h"

// Motor pin tanımlamaları
int Step = 3;   // Step pini
int Dire = 2;   // Direction pini
int Sleep = 4;  // Sleep modu kontrolü
int MS1 = 7;    // Microstepping kontrol pin 1
int MS2 = 6;    // Microstepping kontrol pin 2
int MS3 = 5;    // Microstepping kontrol pin 3

// Motor özellikleri
const int spr = 200;      // Tam turda adım sayısı (steps per revolution)
int RPM = 40;            // Dakikadaki dönüş sayısı
int Microsteps = 4;      // Microstepping ayarı (1, 2, 4, 8, or 16)

// Motor sürücü nesnesi
A4988 stepper(spr, Dire, Step, MS1, MS2, MS3);

void setup() {
  // Pin ayarları
  pinMode(Step, OUTPUT);
  pinMode(Dire, OUTPUT);
  pinMode(Sleep, OUTPUT);
  
  // Başlangıç durumu
  digitalWrite(Step, LOW);
  digitalWrite(Dire, LOW);
  digitalWrite(Sleep, LOW);  // Sleep modunu aktif et
  
  // Motor ayarları
  stepper.begin(RPM, Microsteps);
  
  // Seri haberleşme başlat
  Serial.begin(9600);
}

void loop() {
  if (Serial.available() > 0) {
    // Veri geldiğinde Sleep'ten çık
    digitalWrite(Sleep, HIGH);
    
    // Seri porttan gelen veriyi oku
    String data = Serial.readStringUntil('\n');
    
    // Veriyi parçala (format: "adım_sayısı,yön")
    int comma = data.indexOf(',');
    int steps = data.substring(0, comma).toInt();
    int direction = data.substring(comma + 1).toInt();
    
    // Yön ve adım sayısına göre motoru döndür
    if (direction == 1) {
      stepper.rotate(steps * (360.0 / spr));  // Derece cinsinden döndürme
    } else {
      stepper.rotate(-steps * (360.0 / spr));
    }
    
    // İşlem tamamlandı bilgisini gönder
    Serial.println("OK");
    
    // İşlem bittikten sonra Sleep moduna geç
    digitalWrite(Sleep, LOW);
  }
  // Loop boştayken Sleep modunda kalır
}
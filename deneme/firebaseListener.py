import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import time
from datetime import datetime
import os
import serial
import serial.tools.list_ports

class FirebaseListener:
    def __init__(self):
        # Firebase yapılandırması
        cred = credentials.Certificate('deskupper-4a86b-firebase-adminsdk-wvl1f-54277bff6b.json')
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://deskupper-4a86b-default-rtdb.firebaseio.com'
        })
        
        # Veritabanı referansını güncelle
        self.db_ref = db.reference('desk_status/current')
        
        # Arduino bağlantısını başlat
        self.serial_port = self.connect_arduino()
        
        # Son değeri sakla
        self.last_value = 0
        
        # Dinleyiciyi başlat
        self.start_listener()
    
    def connect_arduino(self):
        try:
            # Mevcut portları listele
            ports = list(serial.tools.list_ports.comports())
            print("Mevcut portlar:")
            for p in ports:
                print(f"- {p.device}: {p.description}")
            
            # Arduino'yu bul
            arduino_port = None
            for port in ports:
                if "Arduino" in port.description or "CH340" in port.description or "USB Serial" in port.description:
                    arduino_port = port.device
                    break
            
            if arduino_port:
                serial_port = serial.Serial(arduino_port, 9600, timeout=1)
                print(f"Arduino bağlandı: {arduino_port}")
                return serial_port
            else:
                print("Arduino bulunamadı!")
                return None
            
        except Exception as e:
            print(f"Bağlantı hatası: {str(e)}")
            return None

    def control_motor(self, value):
        if not self.serial_port:
            print("Arduino bağlı değil!")
            return
        
        try:
            print(f"\nMotor Kontrol Detayları:")
            print("-" * 30)
            print(f"Yeni değer: {value}")
            print(f"Önceki değer: {self.last_value}")
            
            # Değişim miktarını hesapla
            change = value - self.last_value
            print(f"Değişim miktarı: {change}")
            
            if change != 0:  # Değişim varsa
                # Her 1 birimlik değişim için 1 tam tur (200 adım)
                steps = abs(change) * 200  # 1 tam tur = 200 adım
                direction = "1" if change > 0 else "0"
                
                command = f"{steps},{direction}\n"
                print(f"Arduino'ya gönderilen komut: {command.strip()}")
                print(f"Motor {abs(change)} tam tur {'saat yönünde' if change > 0 else 'saat yönü tersinde'} dönecek")
                
                # Seri port durumunu kontrol et
                print(f"Seri port açık mı: {self.serial_port.is_open}")
                print(f"Seri port ayarları: {self.serial_port.baudrate} baud")
                
                # Komutu gönder
                bytes_written = self.serial_port.write(command.encode())
                print(f"Gönderilen byte sayısı: {bytes_written}")
                
                time.sleep(0.1)
                
                if self.serial_port.in_waiting:
                    response = self.serial_port.readline().decode().strip()
                    print(f"Arduino'dan gelen yanıt: {response}")
                    if response == "OK":
                        print("Motor hareketi tamamlandı!")
                else:
                    print("Motor komutu gönderildi")
                
                # Hareket tamamlandıktan sonra son değeri güncelle
                self.last_value = value
            else:
                print("Değişim yok, motor hareket etmeyecek")
            
        except Exception as e:
            print(f"Motor kontrol hatası: {str(e)}")
            print(f"Hata detayı: {type(e).__name__}")

    def on_data_change(self, event):
        """Firebase'den veri değişikliklerini dinle"""
        try:
            if event.data:  # Yeni veri varsa
                print("\nGelen Firebase Verisi:")
                print(event.data)
                
                # Sadece hedef yüksekliği al
                target_height = event.data.get('targetHeight', 0)
                
                print(f"\nYeni Hedef Yükseklik Algılandı!")
                print("-" * 30)
                print(f"Hedef Yükseklik: {target_height} (type: {type(target_height)})")
                print("-" * 30)
                
                # Doğrudan motoru kontrol et
                self.control_motor(target_height)
                
        except Exception as e:
            print(f"Hata oluştu: {str(e)}")
            print(f"Hata detayı: {type(e).__name__}")
    
    def start_listener(self):
        """Dinleyiciyi başlat"""
        print("Firebase dinleyici başlatıldı...")
        print("Masa yüksekliği değişikliklerini bekleniyor...")
        print("-" * 30)
        
        # Verileri dinle
        self.db_ref.listen(self.on_data_change)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nProgram sonlandırılıyor...")
            if self.serial_port:
                self.serial_port.close()

if __name__ == "__main__":
    listener = FirebaseListener() 
import tkinter as tk
from tkinter import messagebox
import serial
import serial.tools.list_ports

class StepperControlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Step Motor Kontrolü")
        
        # Arduino bağlantısı
        self.serial_port = None
        self.connect_arduino()
        
        # GUI elemanları
        self.create_widgets()
    
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
                # Arduino UNO için tipik tanımlayıcıları kontrol et
                if "Arduino" in port.description or "CH340" in port.description or "USB Serial" in port.description:
                    arduino_port = port.device
                    break
            
            if arduino_port:
                self.serial_port = serial.Serial(arduino_port, 9600, timeout=1)
                print(f"Arduino bağlandı: {arduino_port}")
            else:
                print("Arduino bulunamadı!")
                messagebox.showerror("Hata", "Arduino bulunamadı! Lütfen bağlantıyı kontrol edin.")
            
        except Exception as e:
            print(f"Bağlantı hatası: {str(e)}")
            messagebox.showerror("Hata", f"Bağlantı hatası: {str(e)}")
    
    def create_widgets(self):
        # Adım sayısı girişi
        tk.Label(self.root, text="Adım Sayısı:").pack(pady=5)
        self.steps_entry = tk.Entry(self.root)
        self.steps_entry.pack(pady=5)
        
        # Yön seçimi
        self.direction_var = tk.StringVar(value="1")
        tk.Radiobutton(self.root, text="Saat Yönü", variable=self.direction_var, value="1").pack()
        tk.Radiobutton(self.root, text="Saat Yönü Tersi", variable=self.direction_var, value="0").pack()
        
        # Çalıştır butonu
        tk.Button(self.root, text="Çalıştır", command=self.run_motor).pack(pady=10)
    
    def run_motor(self):
        if not self.serial_port:
            messagebox.showerror("Hata", "Arduino bağlı değil!")
            return
        
        try:
            steps = int(self.steps_entry.get())
            direction = self.direction_var.get()
            
            # Arduino'ya komutu gönder
            command = f"{steps},{direction}\n"
            self.serial_port.write(command.encode())
            
            # Arduino'dan yanıt bekle
            response = self.serial_port.readline().decode().strip()
            if response == "OK":
                messagebox.showinfo("Başarılı", "Motor hareketi tamamlandı!")
            
        except ValueError:
            messagebox.showerror("Hata", "Geçerli bir adım sayısı giriniz!")
        except Exception as e:
            messagebox.showerror("Hata", f"İşlem hatası: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = StepperControlGUI(root)
    root.mainloop() 
import sys
import win32gui
import time
import csv
from datetime import datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QCoreApplication, QTimer
import os

class SystemTrayApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.last_active_window = ""
        self.window_times = {}
        self.last_switch_time = time.time()
        self.last_firebase_update = time.time()  # Firebase güncelleme zamanı
        
        # Firebase yapılandırması
        self.setup_firebase()
        
        # Sistem tepsisi simgesi oluştur
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(QIcon("LinkTreeler(1).png"))
        
        # Menü oluştur
        self.tray_menu = QMenu()
        
        # Menü öğeleri ekle
        self.action_hello = QAction("LogMesaj")
        self.action_hello.triggered.connect(self.show_running_programs)
        self.tray_menu.addAction(self.action_hello)
        
        self.action_exit = QAction("Çıkış")
        self.action_exit.triggered.connect(self.exit_app)
        self.tray_menu.addAction(self.action_exit)
        
        # Menüyü sistem tepsisi simgesine bağla
        self.tray_icon.setContextMenu(self.tray_menu)
        
        # Sistem tepsisi simgesini göster
        self.tray_icon.show()
        
        # Simgeye çift tıklama olayını bağla
        self.tray_icon.activated.connect(self.tray_icon_activated)

        # İki timer kullanacağız
        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self.update_display)
        self.display_timer.start(1000)  # Ekranı her saniye güncelle
        
        self.firebase_timer = QTimer()
        self.firebase_timer.timeout.connect(self.update_firebase)
        self.firebase_timer.start(50000)  # Firebase'i her 30 saniyede bir güncelle
    
    def setup_firebase(self):
        # Firebase kimlik bilgilerini yükle
        cred = credentials.Certificate('deskupper-4a86b-firebase-adminsdk-wvl1f-54277bff6b.json')
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://deskupper-4a86b-default-rtdb.firebaseio.com'
        })
        
        # Veritabanı referansını al
        self.db_ref = db.reference('window_times')

    def update_firebase(self):
        try:
            current_time = time.time()
            
            # Aktif pencereyi güncelle
            if self.last_active_window:
                elapsed = current_time - self.last_switch_time
                temp_times = self.window_times.copy()
                if self.last_active_window in temp_times:
                    temp_times[self.last_active_window] += elapsed
                else:
                    temp_times[self.last_active_window] = elapsed
            else:
                temp_times = self.window_times.copy()
            
            # Veriyi hazırla
            data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'windows': {}
            }
            
            for window, duration in temp_times.items():
                data['windows'][self.sanitize_key(window)] = {
                    'name': window,
                    'duration': int(duration),
                    'minutes': int(duration // 60),
                    'seconds': int(duration % 60)
                }
            
            # Firebase'e gönder
            self.db_ref.child(datetime.now().strftime('%Y-%m-%d')).set(data)
            print()
            print("\nVeriler Firebase'e gönderildi!")
            
        except Exception as e:
            print(f"\nFirebase güncelleme hatası: {str(e)}")

    def sanitize_key(self, key):
        # Firebase key'leri için geçersiz karakterleri temizle
        return key.replace('.', '_').replace('$', '_').replace('#', '_').replace('[', '_').replace(']', '_').replace('/', '_')

    def get_active_window_title(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            return win32gui.GetWindowText(hwnd)
        except:
            return ""

    def check_active_window(self):
        current_window = self.get_active_window_title()
        current_time = time.time()
        
        if current_window != self.last_active_window and current_window.strip() != "":
            # Önceki pencerenin süresini güncelle
            if self.last_active_window:
                elapsed_time = current_time - self.last_switch_time
                if self.last_active_window in self.window_times:
                    self.window_times[self.last_active_window] += elapsed_time
                else:
                    self.window_times[self.last_active_window] = elapsed_time
            
            # Yeni pencere sözlükte yoksa ekle
            if current_window not in self.window_times:
                self.window_times[current_window] = 0.0
            
            self.last_active_window = current_window
            self.last_switch_time = current_time

    def update_log_entry(self, window_name):
        # Pencere için mevcut log kaydını bul
        existing_entry = None
        for entry in self.log_data:
            if entry['window'] == window_name:
                existing_entry = entry
                break
        
        # Mevcut kayıt varsa güncelle, yoksa yeni kayıt oluştur
        if existing_entry:
            existing_entry['duration'] = int(self.window_times[window_name])
            existing_entry['timestamp'] = datetime.now().strftime('%H:%M:%S')
        else:
            self.log_data.append({
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'window': window_name,
                'duration': int(self.window_times[window_name])
            })

    def print_window_times(self):
        print("\nPencere Süreleri (CSV formatında):")
        print("Saat,Uygulama,Saniye")
        
        # Mevcut aktif pencerenin süresini geçici olarak hesapla
        temp_times = self.window_times.copy()
        if self.last_active_window:
            current_duration = temp_times.get(self.last_active_window, 0)
            current_duration += time.time() - self.last_switch_time
            temp_times[self.last_active_window] = current_duration
            
            # Aktif pencere için log kaydını güncelle
            for entry in self.log_data:
                if entry['window'] == self.last_active_window:
                    entry['duration'] = int(current_duration)
                    entry['timestamp'] = datetime.now().strftime('%H:%M:%S')

        # Log verilerini yazdır (her uygulama için tek satır)
        for entry in self.log_data:
            print(f"{entry['timestamp']},{entry['window']},{entry['duration']}")

    def get_visible_windows(self):
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                if window_text and not window_text.isspace():
                    windows.append(window_text)
            return True

        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        return windows
    
    def show_running_programs(self):
        visible_windows = self.get_visible_windows()
        filtered_windows = [w for w in visible_windows if len(w) > 0 and w != "Program Manager"]
        message = "Açık Programlar:\n" + "\n".join(filtered_windows)
        
        self.tray_icon.showMessage(
            "Açık Pencereler",
            message,
            QSystemTrayIcon.Information,
            5000
        )
    
    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_running_programs()
    
    def exit_app(self):
        # Son durumu kaydet
        if self.last_active_window:
            elapsed_time = time.time() - self.last_switch_time
            self.window_times[self.last_active_window] += elapsed_time
            self.update_log_entry(self.last_active_window)
        
        print("\nProgram Kapatılıyor - Tüm Kayıtlar:")
        self.print_window_times()
        QCoreApplication.quit()
    
    def run(self):
        sys.exit(self.app.exec_())

    def update_display(self):
        # Aktif pencereyi kontrol et
        self.check_active_window()
        # Süreleri yazdır
        self.print_real_time_stats()

    def print_real_time_stats(self):
        current_time = time.time()
        
        # Terminal ekranını temizle (Windows için)
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("\nPencere Süreleri (Gerçek Zamanlı):")
        print("Uygulama                                     Süre")
        print("-" * 60)
        
        # Geçici süreleri hesapla
        temp_times = self.window_times.copy()
        if self.last_active_window:
            elapsed = current_time - self.last_switch_time
            if self.last_active_window in temp_times:
                temp_times[self.last_active_window] += elapsed
            else:
                temp_times[self.last_active_window] = elapsed

        # Süreleri sırala (en uzun süre en üstte)
        sorted_times = sorted(temp_times.items(), key=lambda x: x[1], reverse=True)
        
        for window, duration in sorted_times:
            duration = int(duration)
            minutes = duration // 60
            seconds = duration % 60
            
            # Aktif pencereyi belirt
            is_active = " *" if window == self.last_active_window else ""
            
            # Pencere adını kısalt eğer çok uzunsa
            window_name = window[:40] + "..." if len(window) > 40 else window
            window_name = window_name.ljust(40)
            
            if minutes > 0:
                time_str = f"{minutes}d {seconds:02d}s"
            else:
                time_str = f"{seconds}s"
            
            print(f"{window_name} {time_str:>8}{is_active}")

if __name__ == "__main__":
    app = SystemTrayApp()
    app.run() 
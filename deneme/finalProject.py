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
import serial
import serial.tools.list_ports
from system_tray_app import SystemTrayApp
from firebaseListener import FirebaseListener
import threading
import win32process
import psutil  # Bu kütüphaneyi import etmeniz gerekiyor

class ModifiedSystemTrayApp(SystemTrayApp):
    def __init__(self, firebase_app=None, qapp=None):
        # QApplication'ı dışarıdan al
        self.app = qapp
        
        # Firebase başlatmayı engelle
        self.skip_firebase = True
        
        # Diğer değişkenleri başlat
        self.last_active_window = ""
        self.window_times = {}
        self.last_switch_time = time.time()
        self.last_firebase_update = time.time()
        
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
        
        # Firebase referansını güncelle
        if firebase_app:
            self.db_ref = db.reference('window_times', app=firebase_app)
        
        # Timer'ları başlat
        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self.update_display)
        self.display_timer.start(1000)
        
        self.firebase_timer = QTimer()
        self.firebase_timer.timeout.connect(self.update_firebase)
        self.firebase_timer.start(3000)

    def setup_firebase(self):
        # Firebase kurulumunu atla
        if hasattr(self, 'skip_firebase'):
            return
        super().setup_firebase()

    def sanitize_key(self, key):
        # Firebase key'leri için geçersiz karakterleri temizle
        return key.replace('.', '_').replace('$', '_').replace('#', '_').replace('[', '_').replace(']', '_').replace('/', '_')

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
                safe_key = self.sanitize_key(window)
                data['windows'][safe_key] = {
                    'name': window,
                    'duration': int(duration),
                    'minutes': int(duration // 60),
                    'seconds': int(duration % 60)
                }
            
            # Firebase'e gönder
            if self.db_ref:  # db_ref varsa gönder
                self.db_ref.child(datetime.now().strftime('%Y-%m-%d')).set(data)
                print("\nVeriler Firebase'e gönderildi!")
                print(f"Aktif pencere: {self.last_active_window}")
                print(f"Toplam pencere sayısı: {len(temp_times)}")
            
        except Exception as e:
            print(f"\nFirebase güncelleme hatası: {str(e)}")
            print(f"Hata detayı: {type(e).__name__}")

    def get_app_name_from_window(self, hwnd):
        """Pencere handle'ından uygulama adını al"""
        try:
            # Pencereye ait process ID'yi al
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            # Process ID'den process nesnesini al
            process = psutil.Process(pid)
            
            # Uygulamanın tam yolunu al ve sadece exe adını döndür
            return process.exe().split('\\')[-1].lower().replace('.exe', '')
        except Exception as e:
            print(f"Uygulama adı alınamadı: {str(e)}")
            return win32gui.GetWindowText(hwnd)  # Fallback olarak pencere başlığını döndür

    def update_display(self):
        """Aktif pencereyi takip et"""
        try:
            # Aktif pencere handle'ını al
            hwnd = win32gui.GetForegroundWindow()
            
            # Uygulama adını al
            current_app = self.get_app_name_from_window(hwnd)
            
            # Eğer uygulama adı değiştiyse
            if current_app != self.last_active_window:
                current_time = time.time()
                
                # Önceki uygulamanın süresini güncelle
                if self.last_active_window:
                    elapsed = current_time - self.last_switch_time
                    if self.last_active_window in self.window_times:
                        self.window_times[self.last_active_window] += elapsed
                    else:
                        self.window_times[self.last_active_window] = elapsed
                
                # Yeni uygulamayı kaydet
                self.last_active_window = current_app
                self.last_switch_time = current_time
                
        except Exception as e:
            print(f"Pencere güncellenirken hata: {str(e)}")

    def exit_app(self):
        """Uygulamayı güvenli bir şekilde kapat"""
        try:
            # Son aktif pencerenin süresini güncelle
            if self.last_active_window:
                current_time = time.time()
                elapsed_time = current_time - self.last_switch_time
                
                # Güvenli bir şekilde window_times sözlüğünü güncelle
                if self.last_active_window not in self.window_times:
                    self.window_times[self.last_active_window] = 0
                self.window_times[self.last_active_window] += elapsed_time

            # Son verileri Firebase'e gönder
            if hasattr(self, 'db_ref'):
                self.update_firebase()

            # Timer'ları durdur
            self.display_timer.stop()
            self.firebase_timer.stop()

            # Uygulamayı kapat
            self.tray_icon.hide()
            QCoreApplication.quit()
            
        except Exception as e:
            print(f"Uygulama kapatılırken hata oluştu: {str(e)}")
            # Hata olsa bile uygulamayı kapatmaya çalış
            self.tray_icon.hide()
            QCoreApplication.quit()

class ModifiedFirebaseListener(FirebaseListener):
    def __init__(self, firebase_app=None):
        # Firebase başlatmayı engelle
        self.skip_firebase = True
        
        # Parent sınıfın __init__ metodunu çağır
        super().__init__()
        
        # Firebase referansını güncelle
        if firebase_app:
            self.db_ref = db.reference('desk_status/current', app=firebase_app)

    def setup_firebase(self):
        # Firebase kurulumunu atla
        if hasattr(self, 'skip_firebase'):
            return
        super().setup_firebase()

class FinalProject:
    def __init__(self):
        # Firebase yapılandırması (tek bir kere yapılmalı)
        cred = credentials.Certificate('deskupper-4a86b-firebase-adminsdk-wvl1f-54277bff6b.json')
        try:
            self.firebase_app = firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://deskupper-4a86b-default-rtdb.firebaseio.com'
            }, name='single_instance')
        except ValueError:
            self.firebase_app = firebase_admin.get_app(name='single_instance')

        # System Tray uygulamasını başlat
        self.system_tray = None
        self.firebase_listener = None
        
        # Thread'leri başlat
        self.start_applications()

    def start_firebase_listener(self):
        """Firebase Listener'ı ayrı bir thread'de başlat"""
        try:
            self.firebase_listener = ModifiedFirebaseListener(firebase_app=self.firebase_app)
        except Exception as e:
            print(f"Firebase Listener başlatma hatası: {str(e)}")

    def start_applications(self):
        """Her iki uygulamayı da başlat"""
        try:
            # QApplication'ı başlat
            self.app = QApplication(sys.argv)
            
            # Firebase Listener'ı ayrı bir thread'de başlat
            firebase_thread = threading.Thread(target=self.start_firebase_listener)
            firebase_thread.daemon = True
            firebase_thread.start()

            # System Tray uygulamasını ana thread'de başlat
            self.system_tray = ModifiedSystemTrayApp(
                firebase_app=self.firebase_app,
                qapp=self.app
            )
            
            # Çıkış fonksiyonunu override et
            original_exit = self.system_tray.exit_app
            def new_exit():
                print("Uygulamalar kapatılıyor...")
                original_exit()
                if self.firebase_listener and self.firebase_listener.serial_port:
                    self.firebase_listener.serial_port.close()
                QCoreApplication.quit()
            
            self.system_tray.exit_app = new_exit
            
            # Uygulamayı çalıştır
            sys.exit(self.app.exec_())
            
        except Exception as e:
            print(f"Uygulama başlatma hatası: {str(e)}")

if __name__ == "__main__":
    try:
        app = FinalProject()
    except Exception as e:
        print(f"Ana program hatası: {str(e)}") 
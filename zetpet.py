import os
import sys
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QSystemTrayIcon, QMenu, QAction, QVBoxLayout, QGridLayout, QPushButton, QScrollArea, QGraphicsOpacityEffect
from PyQt5.QtGui import QIcon, QPixmap, QPalette, QColor
from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation, QTimer
from PIL import Image


# Fungsi untuk membersihkan metadata ICC dari gambar PNG
def clean_png_metadata(image_path):
    img = Image.open(image_path)
    if img.format == 'PNG':
        img.save(image_path, format='PNG', pnginfo=None)  # Menghapus metadata


class CharacterWidget(QWidget):
    def __init__(self, image_path, character_name, parent=None):
        super().__init__(parent)
        self.character_name = character_name
        self.setFixedSize(300, 400)  # Ukuran widget karakter

        # Mengatur style dan border agar seragam dan modern
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-radius: 18px;
                border: 2px solid #dddddd;
            }
            QWidget:hover {
                border: 2px solid #6c63ff;
            }
        """)

        # Membersihkan metadata gambar jika perlu
        clean_png_metadata(image_path)

        # Membaca dan menyesuaikan ukuran gambar
        pix = QPixmap(image_path)
        if pix.isNull():
            print(f"Error: Tidak dapat memuat gambar {image_path}")
            return
        
        # Skala gambar agar konsisten di grid
        pix = pix.scaled(250, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label = QLabel()
        self.image_label.setPixmap(pix)
        self.image_label.setAlignment(Qt.AlignCenter)

        # Tombol untuk memilih karakter
        self.button = QPushButton(f"Pilih {character_name}")
        self.button.setFixedWidth(200)  # Sesuaikan ukuran tombol
        self.button.setStyleSheet("""
            QPushButton {
                background-color: #6c63ff;
                color: white;
                padding: 10px 20px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background-color: #574fd6;
                border: 2px solid #6c63ff;
            }
        """)
        self.button.setCursor(Qt.PointingHandCursor)

        # Efek dan animasi
        self.effect = QGraphicsOpacityEffect(self.button)
        self.button.setGraphicsEffect(self.effect)
        self.effect.setOpacity(0.0)

        self.anim = QPropertyAnimation(self.effect, b"opacity")
        self.anim.setDuration(300)
        self.button.setVisible(True)

        self.leave_timer = QTimer()
        self.leave_timer.setSingleShot(True)
        self.leave_timer.timeout.connect(self.fadeOut)

        # Layout utama
        layout = QVBoxLayout(self)
        layout.addWidget(self.image_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.button, alignment=Qt.AlignCenter)
        layout.setContentsMargins(10, 10, 10, 10)

    def enterEvent(self, event):
        # Memulai animasi hover
        if self.anim.state() != QPropertyAnimation.Running:
            self.leave_timer.stop()  # Menghentikan timer leave agar tidak ada delay
            self.anim.stop()
            self.anim.setStartValue(self.effect.opacity())
            self.anim.setEndValue(1.0)
            self.anim.start()

    def leaveEvent(self, event):
        self.leave_timer.start(300)

    def fadeOut(self):
        self.anim.stop()
        self.anim.setStartValue(self.effect.opacity())
        self.anim.setEndValue(0.0)
        self.anim.start()


class AnimeMascot(QWidget):
    def __init__(self):
        super().__init__()
        QApplication.setQuitOnLastWindowClosed(False)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.label = QLabel(self)

        # Menentukan path folder karakter secara relatif
        self.waifu_folder = self.resource_path('assets/waifu')
        self.character_files = [f for f in os.listdir(self.waifu_folder) if f.lower().endswith('.png')]

        if self.character_files:
            self.loadCharacter(self.character_files[0])

        self.setupTrayIcon()
        self.dragging = False
        self.offset = QPoint()
        self.show()

        self.character_window = None  # Flag untuk mencegah multiple window

    def resource_path(self, relative_path):
        """Mendapatkan path resource yang dapat digunakan baik saat aplikasi dijalankan sebagai skrip maupun exe"""
        try:
            # Saat dijalankan sebagai exe
            base_path = sys._MEIPASS
        except Exception:
            # Saat dijalankan sebagai skrip
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)

    def setupTrayIcon(self):
        tray = QSystemTrayIcon(QIcon(self.resource_path("assets/Zetnime.ico")), self)
        tray.setToolTip("Zetnime • Klik kanan untuk menu")

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #f7f7f7;
                color: #333;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
                font-family: 'Segoe UI', sans-serif;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #6c63ff;
                color: white;
            }
        """)

        pilih_karakter_action = QAction("Pilih Karakter", self)
        pilih_karakter_action.triggered.connect(self.showCharacterSelection)

        keluar_action = QAction("Keluar", self)
        keluar_action.triggered.connect(QApplication.instance().quit)

        menu.addAction(pilih_karakter_action)
        menu.addSeparator()
        menu.addAction(keluar_action)

        tray.setContextMenu(menu)
        tray.show()
        self.tray_icon = tray

    def showCharacterSelection(self):
        if self.character_window is not None and self.character_window.isVisible():
            return  # Jangan buka jendela karakter lagi jika sudah ada

        self.character_window = QWidget(flags=Qt.Window)
        self.character_window.setWindowTitle("Pilih Karakter")
        self.character_window.setStyleSheet("background-color: #f5f5f5;")
        self.character_window.resize(1280, 820)

        scroll = QScrollArea(self.character_window)
        scroll.setWidgetResizable(True)
        scroll.setGeometry(0, 0, 1280, 820)
        scroll.setStyleSheet("border: none;")

        container = QWidget()
        grid = QGridLayout(container)
        grid.setContentsMargins(40, 40, 40, 40)
        grid.setSpacing(30)

        cols = 3  # Grid 3 kolom
        for idx, fn in enumerate(self.character_files):
            path = os.path.join(self.waifu_folder, fn)
            name = fn[:-4]
            widget = CharacterWidget(path, name)
            widget.button.clicked.connect(lambda _, f=fn: self.onCharacterChosen(f))
            r, c = divmod(idx, cols)
            grid.addWidget(widget, r, c, alignment=Qt.AlignCenter)

        scroll.setWidget(container)
        self.character_window.show()
        self.character_window.raise_()
        self.character_window.activateWindow()

    def onCharacterChosen(self, filename):
        self.loadCharacter(filename)
        self.character_window.close()
        self.character_window = None

    def loadCharacter(self, filename):
        path = os.path.join(self.waifu_folder, filename)
        pix = QPixmap(path).scaled(666, 375, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        if pix.isNull(): return

        self.label.setPixmap(pix)
        self.label.setFixedSize(pix.size())
        self.resize(pix.size())

        geo = QApplication.primaryScreen().geometry()
        x = geo.width()  - self.width()  - 20
        y = geo.height() - self.height() - 20
        self.move(x, y)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = e.pos()

    def mouseMoveEvent(self, e):
        if self.dragging:
            self.move(self.pos() + e.pos() - self.offset)

    def mouseReleaseEvent(self, e):
        self.dragging = False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    pastel = QPalette()
    pastel.setColor(QPalette.Window, QColor("#f7f7f7"))
    pastel.setColor(QPalette.Base, QColor("#ffffff"))
    pastel.setColor(QPalette.Text, Qt.black)
    app.setPalette(pastel)

    mascot = AnimeMascot()
    sys.exit(app.exec_())

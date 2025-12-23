import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

interfaces_path = os.path.join(current_dir, 'interfaces')
if interfaces_path not in sys.path:
    sys.path.append(interfaces_path)

from interfaces import library
from interfaces import data_add_page
from interfaces import data_search_page
from interfaces import data_delete_page
from interfaces import data_json_operations_page

# Extract modülleri interfaces klasörü içinde
from interfaces import extract_from_docx
from interfaces import extract_from_pdf
from interfaces import extract_from_turkishVideo
from interfaces import extract_from_englishVideo



def get_desktop_dir() -> str:
    userprofile = os.environ.get("USERPROFILE") or os.path.expanduser("~")

    candidates = [
        os.path.join(userprofile, "OneDrive", "Desktop"),
        os.path.join(userprofile, "Desktop"),
        os.path.join(userprofile, "OneDrive", "Masaüstü"),
        os.path.join(userprofile, "Masaüstü"),
    ]

    homedrive = os.environ.get("HOMEDRIVE")
    homepath = os.environ.get("HOMEPATH")
    if homedrive and homepath:
        home = homedrive + homepath
        candidates.extend([
            os.path.join(home, "Desktop"),
            os.path.join(home, "OneDrive", "Desktop"),
        ])

    for p in candidates:
        if p and os.path.isdir(p):
            return p

    fallback = os.path.join(userprofile, "Desktop")
    try:
        os.makedirs(fallback, exist_ok=True)
        return fallback
    except Exception:
        return current_dir


def get_desktop_txt_path(input_path: str) -> str:
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    desktop = get_desktop_dir()
    try:
        os.makedirs(desktop, exist_ok=True)
    except Exception:
        pass
    return os.path.join(desktop, f"{base_name}.txt")


class MainWindow(library.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kullanıcı Arayüzü")
        self.resize(1100, 700)

        # Sayfalar
        self.add_page = data_add_page.AddPage()
        self.search_page = data_search_page.SearchPage()
        self.delete_page = data_delete_page.DeletePage()
        self.json_page = data_json_operations_page.JsonUploadPage()

        # Stack
        self.stack = library.QStackedWidget()
        self.stack.addWidget(self.add_page)
        self.stack.addWidget(self.search_page)
        self.stack.addWidget(self.delete_page)
        self.stack.addWidget(self.json_page)

        # Ana layout
        main_layout = library.QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(10)
        self.setLayout(main_layout)

        # ÜST BUTONLAR
        top_buttons = library.QHBoxLayout()
        top_buttons.setSpacing(10)

        top_buttons.addWidget(
            library.QPushButton("Veri Ekle", clicked=lambda: self.stack.setCurrentWidget(self.add_page))
        )
        top_buttons.addWidget(
            library.QPushButton("Veri Ara", clicked=lambda: self.stack.setCurrentWidget(self.search_page))
        )
        top_buttons.addWidget(
            library.QPushButton("Veri Sil", clicked=lambda: self.stack.setCurrentWidget(self.delete_page))
        )
        top_buttons.addWidget(
            library.QPushButton("JSON İşlemleri", clicked=lambda: self.stack.setCurrentWidget(self.json_page))
        )

        main_layout.addLayout(top_buttons)
        main_layout.addWidget(self.stack, stretch=1)

        # ALT BUTONLAR
        divider = library.QFrame()
        divider.setFrameShape(library.QFrame.HLine)
        divider.setFrameShadow(library.QFrame.Sunken)
        main_layout.addWidget(divider)

        bottom_buttons = library.QHBoxLayout()
        bottom_buttons.setSpacing(10)

        bottom_buttons.addWidget(library.QPushButton("DOCX Seç", clicked=self.open_docx_dialog))
        bottom_buttons.addWidget(library.QPushButton("PDF Seç", clicked=self.open_pdf_dialog))
        bottom_buttons.addWidget(library.QPushButton("TR Video Seç", clicked=self.open_tr_video_dialog))
        bottom_buttons.addWidget(library.QPushButton("EN Video Seç", clicked=self.open_en_video_dialog))

        main_layout.addLayout(bottom_buttons)

    # ---------------------------------------------------------------------
    # MODÜLER AKIŞ: sadece dosya seç + output path belirle + modül fonksiyonu çağır
    # ---------------------------------------------------------------------
    def open_docx_dialog(self):
        path, _ = library.QFileDialog.getOpenFileName(
            self, "DOCX Dosyası Seç", "", "Word Dosyaları (*.docx)"
        )
        if not path:
            return

        out_txt = get_desktop_txt_path(path)

        try:
            # Beklenen: interfaces/extract_from_docx.py içinde extract_docx_to_txt(input_path, output_txt_path)
            extract_from_docx.extract_docx_to_txt(path, out_txt)
            library.QMessageBox.information(self, "Başarılı", f"TXT masaüstüne kaydedildi:\n{out_txt}")
        except Exception as e:
            library.QMessageBox.critical(self, "Hata", f"DOCX işlemi başarısız:\n{e}")

    def open_pdf_dialog(self):
        path, _ = library.QFileDialog.getOpenFileName(
            self, "PDF Dosyası Seç", "", "PDF Dosyaları (*.pdf)"
        )
        if not path:
            return

        out_txt = get_desktop_txt_path(path)

        try:
            # Beklenen: interfaces/extract_from_pdf.py içinde extract_pdf_to_txt(input_path, output_txt_path)
            extract_from_pdf.extract_pdf_to_txt(path, out_txt)
            library.QMessageBox.information(self, "Başarılı", f"TXT masaüstüne kaydedildi:\n{out_txt}")
        except Exception as e:
            library.QMessageBox.critical(self, "Hata", f"PDF işlemi başarısız:\n{e}")

    def open_tr_video_dialog(self):
        path, _ = library.QFileDialog.getOpenFileName(
            self,
            "Türkçe Video Dosyası Seç",
            "",
            "Video Dosyaları (*.mp4 *.mkv *.mov *.avi *.webm);;Tüm Dosyalar (*.*)"
        )
        if not path:
            return

        out_txt = get_desktop_txt_path(path)

        try:
            # Beklenen: interfaces/extract_from_turkishVideo.py içinde extract_tr_video_to_txt(input_path, output_txt_path)
            extract_from_turkishVideo.extract_tr_video_to_txt(path, out_txt)
            library.QMessageBox.information(self, "Başarılı", f"TXT masaüstüne kaydedildi:\n{out_txt}")
        except Exception as e:
            library.QMessageBox.critical(self, "Hata", f"TR video işlemi başarısız:\n{e}")

    def open_en_video_dialog(self):
        path, _ = library.QFileDialog.getOpenFileName(
            self,
            "İngilizce Video Dosyası Seç",
            "",
            "Video Dosyaları (*.mp4 *.mkv *.mov *.avi *.webm);;Tüm Dosyalar (*.*)"
        )
        if not path:
            return

        out_txt = get_desktop_txt_path(path)

        try:
            # Beklenen: interfaces/extract_from_englishVideo.py içinde extract_en_video_to_txt(input_path, output_txt_path)
            extract_from_englishVideo.extract_en_video_to_txt(path, out_txt)
            library.QMessageBox.information(self, "Başarılı", f"TXT masaüstüne kaydedildi:\n{out_txt}")
        except Exception as e:
            library.QMessageBox.critical(self, "Hata", f"EN video işlemi başarısız:\n{e}")


if __name__ == "__main__":
    app = library.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

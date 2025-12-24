import library
from pyswip import Prolog
import os

class TranslationPage(library.QWidget):
    def __init__(self):
        super().__init__()
        
        # --- Düzen ---
        layout = library.QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Başlık
        title = library.QLabel("🤖 Yapay Zeka Destekli Çeviri")
        title.setAlignment(library.Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2196F3; margin-bottom: 20px;")
        layout.addWidget(title)

        # 1. Giriş Alanı (Türkçe)
        input_label = library.QLabel("Türkçe Cümle:")
        input_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(input_label)

        self.input_text = library.QTextEdit()
        self.input_text.setPlaceholderText("Örn: Ben okula gidiyorum (veya sadece 'gidiyorum')")
        self.input_text.setMaximumHeight(80)
        self.input_text.setStyleSheet("font-size: 14px; padding: 10px; border: 2px solid #ccc; border-radius: 8px;")
        layout.addWidget(self.input_text)

        # Çevir Butonu
        self.translate_btn = library.QPushButton("Çevir ➜")
        self.translate_btn.setCursor(library.Qt.PointingHandCursor)
        self.translate_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3; color: white; font-size: 16px; font-weight: bold; padding: 12px; border-radius: 8px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self.translate_btn.clicked.connect(self.run_translation)
        layout.addWidget(self.translate_btn)

        # 2. Çıktı Alanı (İngilizce)
        output_label = library.QLabel("İngilizce Çeviri:")
        output_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(output_label)

        self.output_text = library.QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("font-size: 16px; color: #333; padding: 10px; border: 2px solid #2196F3; border-radius: 8px; background-color: #f9f9f9;")
        layout.addWidget(self.output_text)

        # Detay Alanı
        self.details_label = library.QLabel("Sistem Durumu: Hazır")
        self.details_label.setStyleSheet("color: #666; font-size: 12px; margin-top: 5px;")
        layout.addWidget(self.details_label)

        layout.addStretch()
        self.setLayout(layout)

        # Prolog Motorunu Başlat
        self.prolog = Prolog()
        try:
            # Prolog dosyasının yolunu bul (morphology.pl üzerinden gidelim)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Bir üst klasöre çıkıp morphology.pl'yi buluyoruz
            prolog_path = os.path.join(os.path.dirname(current_dir), "morphology.pl")
            
            # Windows için ters slash düzeltmesi
            prolog_path = prolog_path.replace("\\", "/")
            
            if os.path.exists(prolog_path):
                self.prolog.consult(prolog_path)
                print(f"Prolog yüklendi: {prolog_path}")
            else:
                self.output_text.setText(f"Hata: Prolog dosyası bulunamadı:\n{prolog_path}")
                
        except Exception as e:
            print(f"Prolog hatası: {e}")
            self.output_text.setText("Hata: Prolog motoru başlatılamadı.\nLütfen SWI-Prolog ve pyswip kütüphanesini kontrol edin.")

    def run_translation(self):
        text = self.input_text.toPlainText().strip().lower()
        if not text:
            return

        self.output_text.setText("Analiz ediliyor...")
        library.QApplication.processEvents()

        try:
            # Prolog Sorgusu: translate_sentence("text", English)
            # Tırnak işaretlerini kaçış karakteriyle düzeltelim
            safe_text = text.replace('"', '\\"')
            query = f"translate_sentence(\"{safe_text}\", EnglishSentence)"
            
            results = list(self.prolog.query(query))
            
            if results:
                # Byte string gelirse decode et
                translation = results[0]['EnglishSentence']
                if isinstance(translation, bytes):
                    translation = translation.decode('utf-8')
                
                self.output_text.setText(str(translation))
                self.details_label.setText("✅ Başarıyla çevrildi.")
            else:
                self.output_text.setText("Çeviri bulunamadı veya kelime kökü veritabanında yok.")
                self.details_label.setText("⚠️ Morfolojik analiz başarısız.")

        except Exception as e:
            self.output_text.setText(f"Sorgu Hatası: {str(e)}")
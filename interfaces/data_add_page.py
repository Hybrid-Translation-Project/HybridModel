import library

class AddPage(library.QWidget):
    def __init__(self):
        super().__init__()
        
        # --- Ana Dikey Düzen ---
        main_layout = library.QVBoxLayout()
        main_layout.setContentsMargins(50, 50, 50, 50) # Kenarlardan boşluk bırak
        main_layout.setSpacing(20)

        # Başlık
        title = library.QLabel("Yeni Veri Ekleme")
        title.setAlignment(library.Qt.AlignCenter)
        # Biraz CSS ile başlığı büyütelim
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50; margin-bottom: 20px;")
        main_layout.addWidget(title)

        # --- Form Kutusu (Ortalamak için) ---
        # Formun çok genişlemesini engellemek için bir kutu içine alıyoruz
        form_container = library.QWidget()
        form_layout = library.QFormLayout()
        form_layout.setLabelAlignment(library.Qt.AlignRight | library.Qt.AlignVCenter) # Etiketleri sağa yasla
        
        # Girdi Alanları
        self.tr_input = library.QLineEdit()
        self.tr_input.setPlaceholderText("Örn: Elma")
        self.tr_input.setStyleSheet("padding: 8px; font-size: 14px;") # Biraz daha şık kutular

        self.en_input = library.QLineEdit()
        self.en_input.setPlaceholderText("Örn: Apple")
        self.en_input.setStyleSheet("padding: 8px; font-size: 14px;")

        self.type_combo = library.QComboBox()
        self.type_combo.addItems(["noun", "verb", "adjective", "adverb"])
        self.type_combo.setStyleSheet("padding: 5px; font-size: 14px;")

        # Form satırlarını ekle (Sol taraf etiket, sağ taraf kutu)
        form_layout.addRow(library.QLabel("Türkçe Kelime:"), self.tr_input)
        form_layout.addRow(library.QLabel("İngilizce Kelime:"), self.en_input)
        form_layout.addRow(library.QLabel("Kelime Türü:"), self.type_combo)

        form_container.setLayout(form_layout)
        
        # Form genişliğini sınırla (Örn: Maksimum 500 piksel)
        form_container.setMaximumWidth(600)

        # --- Yatay Hizalama (Formu yatayda ortala) ---
        center_layout = library.QHBoxLayout()
        center_layout.addStretch()       # Sol boşluk
        center_layout.addWidget(form_container) # Form
        center_layout.addStretch()       # Sağ boşluk
        
        main_layout.addLayout(center_layout)

        # --- Kaydet Butonu ---
        self.save_button = library.QPushButton("Veriyi Kaydet")
        self.save_button.setCursor(library.Qt.PointingHandCursor)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3; 
                color: white; 
                padding: 10px 20px; 
                font-size: 16px; 
                border-radius: 5px;
                font-weight: bold;
                main_layout.addSpacing(300)
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.save_button.setFixedWidth(200) 
        self.save_button.clicked.connect(self.save_data)

        # Butonu ortalama
        button_center_layout = library.QHBoxLayout()
        button_center_layout.addStretch()
        button_center_layout.addWidget(self.save_button)
        button_center_layout.addStretch()

        main_layout.addLayout(button_center_layout)

        # Bu kod, tüm elemanları yukarı iter ve boşluğu en altta bırakır.
        main_layout.addStretch() 

        self.setLayout(main_layout)

    def save_data(self):
        tr = self.tr_input.text().strip()
        en = self.en_input.text().strip()
        kelime_turu = self.type_combo.currentText()

        if not tr or not en:
            library.QMessageBox.warning(self, "Hata", "TR ve EN alanları boş olamaz!")
            return

        # Aynı TR ve EN var mı kontrol
        col = library.mongo_api.get_mongo_collection()
        existing = col.find_one({"tr": tr, "en": en," type": kelime_turu})
        if existing:
            library.QMessageBox.warning(self, "Hata", "Bu veri zaten mevcut!")
            return

        # Veri ekle
        library.mongo_api.add_word(tr, en, kelime_turu) # NOT: add_word fonksiyonunu kelime türünü de alacak şekilde güncellemelisin ileride.
        library.QMessageBox.information(self, "Başarılı", f"{tr} → {en} ({kelime_turu}) eklendi!")
        self.tr_input.clear()
        self.en_input.clear()
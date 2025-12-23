import library

class JsonUploadPage(library.QWidget):
    def __init__(self):
        super().__init__()
        
        # --- Ana Düzen ---
        main_layout = library.QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(15)

        # Başlık
        title = library.QLabel("JSON ile Toplu Veri Yükleme")
        title.setAlignment(library.Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #FF9800; margin-bottom: 10px;")
        main_layout.addWidget(title)

        # Bilgilendirme Metni (GÜNCELLENDİ: Type alanı eklendi)
        info_text = (
            "Lütfen aşağıdaki formatta bir JSON dosyası seçiniz:\n\n"
            '[\n'
            '  {"tr": "elma", "en": "apple", "type": "isim"},\n'
            '  {"tr": "koşmak", "en": "run", "type": "fiil"}\n'
            ']\n\n'
            '* "type" alanı zorunludur (isim, fiil, sıfat vb.)'
        )
        info_lbl = library.QLabel(info_text)
        info_lbl.setStyleSheet("color: #bbb; font-style: italic; font-family: Consolas; margin-bottom: 10px; border: 1px dashed #555; padding: 10px;")
        info_lbl.setAlignment(library.Qt.AlignCenter)
        main_layout.addWidget(info_lbl)

        # --- Dosya Seçme Alanı ---
        file_layout = library.QHBoxLayout()
        
        self.file_path_input = library.QLineEdit()
        self.file_path_input.setPlaceholderText("Dosya seçilmedi...")
        self.file_path_input.setReadOnly(True) 
        self.file_path_input.setStyleSheet("padding: 8px; color: #fff;")
        
        self.select_button = library.QPushButton("Dosya Seç")
        self.select_button.setCursor(library.Qt.PointingHandCursor)
        self.select_button.setStyleSheet("background-color: #555; color: white; padding: 8px 15px;")
        self.select_button.clicked.connect(self.select_file)

        file_layout.addWidget(self.file_path_input)
        file_layout.addWidget(self.select_button)
        
        main_layout.addLayout(file_layout)

        # --- Yükle Butonu ---
        self.upload_button = library.QPushButton("Verileri Veritabanına İşle")
        self.upload_button.setCursor(library.Qt.PointingHandCursor)
        self.upload_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800; 
                color: white; 
                padding: 12px; 
                font-size: 16px; 
                font-weight: bold; 
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """)
        self.upload_button.clicked.connect(self.process_json)
        self.upload_button.setEnabled(False) 
        main_layout.addWidget(self.upload_button)

        # --- Log Ekranı ---
        main_layout.addWidget(library.QLabel("İşlem Logları:"))
        self.log_area = library.QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background-color: #222; color: #0f0; font-family: Consolas; font-size: 12px;")
        main_layout.addWidget(self.log_area)

        self.setLayout(main_layout)
        self.selected_file = None

    def select_file(self):
        file_name, _ = library.QFileDialog.getOpenFileName(
            self, "JSON Dosyası Seç", "", "JSON Files (*.json)"
        )
        if file_name:
            self.selected_file = file_name
            self.file_path_input.setText(file_name)
            self.upload_button.setEnabled(True)
            self.log_message(f"Dosya seçildi: {file_name}")

    def log_message(self, msg):
        self.log_area.append(f">> {msg}")
        library.QApplication.processEvents()

    def process_json(self):
        if not self.selected_file:
            return

        self.log_area.clear()
        self.log_message("Dosya okunuyor ve analiz ediliyor...")
        
        try:
            with open(self.selected_file, 'r', encoding='utf-8') as f:
                data = library.json.load(f)
            
            if not isinstance(data, list):
                library.QMessageBox.warning(self, "Hata", "JSON formatı hatalı! En dışta bir liste [] olmalı.")
                return

            col = library.mongo_api.get_mongo_collection()
            
            success_count = 0
            skip_count = 0
            error_count = 0

            for item in data:
                tr = item.get("tr")
                en = item.get("en")
                kelime_turu = item.get("type") # type alanını oku
                
                # 1. KONTROL: Eksik veri var mı?
                if not tr or not en or not kelime_turu:
                    self.log_message(f"EKSİK VERİ: {item} -> 'tr', 'en' ve 'type' alanları zorunludur.")
                    error_count += 1
                    continue

                # 2. KONTROL: Mükerrer kayıt (Zaten var mı?)
                # Sadece TR ve EN eşleşmesi yeterli, aynı kelimeyi tekrar eklemeyelim.
                existing = col.find_one({"tr": tr, "en": en})
                if existing:
                    self.log_message(f"ATLANDI (Mevcut): {tr} - {en}")
                    skip_count += 1
                    continue

                # 3. İŞLEM: Veritabanına Ekleme
                try:
                    # DİKKAT: mongo_api.add_word fonksiyonunu 3 parametreli olacak şekilde güncellemelisin!
                    # library.mongo_api.add_word(tr, en, kelime_turu)
                    
                    # Şimdilik mevcut yapını bozmamak için varsayalım ki add_word güncellendi
                    # veya doğrudan insert_one yapalım ki garanti olsun:
                    col.insert_one({"tr": tr, "en": en, "type": kelime_turu})
                    
                    self.log_message(f"EKLENDİ: {tr} - {en} ({kelime_turu})")
                    success_count += 1
                except Exception as e:
                    self.log_message(f"DB HATASI: {e}")
                    error_count += 1

            # Özet Rapor
            library.QMessageBox.information(
                self, 
                "İşlem Tamamlandı", 
                f"Toplam Veri: {len(data)}\n"
                f"✅ Başarılı: {success_count}\n"
                f"⏭️ Zaten Var: {skip_count}\n"
                f"❌ Hatalı/Eksik: {error_count}"
            )
            self.log_message(f"--- SONUÇ: {success_count} eklendi, {skip_count} atlandı, {error_count} hata. ---")
            
            self.selected_file = None
            self.file_path_input.clear()
            self.upload_button.setEnabled(False)

        except Exception as e:
            library.QMessageBox.critical(self, "Dosya Hatası", f"Dosya okunamadı:\n{str(e)}")
import library

class DeletePage(library.QWidget):
    def __init__(self):
        super().__init__()
        
        # --- Ana Düzen ---
        main_layout = library.QVBoxLayout()
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(20)

        # Başlık (Kırmızı tonlu - Uyarıcı)
        title = library.QLabel("ID ile Veri Silme")
        title.setAlignment(library.Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #D32F2F; margin-bottom: 20px;")
        main_layout.addWidget(title)

        # --- Orta Alan (Kutu ve Buton) ---
        center_widget = library.QWidget()
        center_widget.setMaximumWidth(600) # Genişliği sınırla
        
        center_layout = library.QVBoxLayout(center_widget)
        center_layout.setSpacing(15)

        # ID Giriş Alanı
        self.id_input = library.QLineEdit()
        self.id_input.setPlaceholderText("Silinecek verinin ID'sini buraya yapıştırın...")
        self.id_input.setStyleSheet("padding: 10px; font-size: 14px; border: 2px solid #555; border-radius: 5px;")
        
        # Silme Butonu (Kırmızı)
        self.delete_button = library.QPushButton("Veriyi Kalıcı Olarak Sil")
        self.delete_button.setCursor(library.Qt.PointingHandCursor)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F; 
                color: white; 
                padding: 12px 20px; 
                font-size: 16px; 
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #B71C1C;
            }
        """)
        self.delete_button.clicked.connect(self.delete_data)

        # Elemanları orta kutuya ekle
        center_layout.addWidget(library.QLabel("ID Bilgisi:"))
        center_layout.addWidget(self.id_input)
        center_layout.addSpacing(10)
        center_layout.addWidget(self.delete_button)

        # --- Yatay Hizalama (Kutuyu Ortala) ---
        h_layout = library.QHBoxLayout()
        h_layout.addStretch()
        h_layout.addWidget(center_widget)
        h_layout.addStretch()

        main_layout.addLayout(h_layout)
        
        # En alta boşluk atarak her şeyi yukarı it
        main_layout.addStretch()

        self.setLayout(main_layout)

    def delete_data(self):
        doc_id = self.id_input.text().strip()
        
        # 1. Kontrol: Boş mu?
        if not doc_id:
            library.QMessageBox.warning(self, "Hata", "Lütfen bir ID giriniz!")
            return

        # 2. Kontrol: Emin misin? (Güvenlik Önlemi)
        confirm = library.QMessageBox.question(
            self, 
            "Silme Onayı", 
            f"Bu ID'ye sahip veriyi silmek istediğinize emin misiniz?\nID: {doc_id}\n\nBu işlem geri alınamaz!",
            library.QMessageBox.Yes | library.QMessageBox.No,
            library.QMessageBox.No # Varsayılan olarak 'Hayır' seçili olsun
        )

        if confirm == library.QMessageBox.Yes:
            try:
                success = library.mongo_api.delete_word_by_id(doc_id)
                if success:
                    library.QMessageBox.information(self, "Başarılı", "Veri başarıyla silindi!")
                    self.id_input.clear()
                else:
                    library.QMessageBox.warning(self, "Hata", "Bu ID veritabanında bulunamadı.")
            except Exception as e:
                library.QMessageBox.critical(self, "Hata", str(e))
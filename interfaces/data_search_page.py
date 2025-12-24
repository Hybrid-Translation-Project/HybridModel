import library

class SearchPage(library.QWidget):
    def __init__(self):
        super().__init__()
        layout = library.QVBoxLayout()

        # Arama Alanı
        self.search_input = library.QLineEdit()
        self.search_input.setPlaceholderText("Aramak için kelime yazın...")
        self.search_input.setStyleSheet("padding: 8px; font-size: 14px;")
        self.search_input.textChanged.connect(self.on_search_text_changed)

        self.search_button = library.QPushButton("Ara")
        self.search_button.clicked.connect(self.search_data)

        # Liste
        self.list_widget = library.QListWidget()
        self.list_widget.setStyleSheet("font-size: 14px;")
        
        # --- SAĞ TIK MENÜSÜ AYARLARI ---
        # Listenin sağ tık menüsüne (Context Menu) izin veriyoruz
        self.list_widget.setContextMenuPolicy(library.Qt.CustomContextMenu)
        # Sağ tıklandığında 'show_context_menu' fonksiyonunu çalıştır
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)

        self.load_last_50()

        # Düzen
        layout.addWidget(library.QLabel("Arama:"))
        layout.addWidget(self.search_input)
        layout.addWidget(self.search_button)
        layout.addWidget(library.QLabel("Sonuçlar (Sağ tık ile işlem yapabilirsiniz):"))
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

    def load_last_50(self):
        self.list_widget.clear()
        try:
            col = library.mongo_api.get_mongo_collection()
            last_50 = col.find().sort("_id", -1).limit(50)
            for doc in last_50:
                # Görünümü ID dahil olacak şekilde ayarladık
                display_text = f"{doc.get('_id')} | {doc.get('tr')} → {doc.get('en')}"
                self.list_widget.addItem(display_text)
        except Exception as e:
            print(f"Hata: {e}")

    def on_search_text_changed(self, text):
        if not text.strip():
            self.load_last_50()

    def search_data(self):
        term = self.search_input.text().strip()
        if not term:
            self.load_last_50()
            return
            
        self.list_widget.clear()
        col = library.mongo_api.get_mongo_collection()
        results = col.find({
            "$or": [{"tr": {"$regex": term, "$options": "i"}},
                    {"en": {"$regex": term, "$options": "i"}}]
        })
        
        found = False
        for doc in results:
            found = True
            display_text = f"{doc.get('_id')} | {doc.get('tr')} → {doc.get('en')}"
            self.list_widget.addItem(display_text)
            
        if not found:
            self.list_widget.addItem("Sonuç bulunamadı...")

    def show_context_menu(self, pos):
        """Sağ tıklandığında açılan menü"""
        # Tıklanan öğeyi al
        item = self.list_widget.itemAt(pos)
        if not item:
            return  # Boşluğa tıklandıysa menü açma

        # Menüyü oluştur
        menu = library.QMenu(self)
        
        # Seçenekler
        copy_id_action = library.QAction("ID Kopyala", self)
        delete_action = library.QAction("❌ Bu Veriyi Sil", self)

        # İşlevleri bağla
        copy_id_action.triggered.connect(lambda: self.copy_id(item))
        delete_action.triggered.connect(lambda: self.delete_item(item))

        # Seçenekleri menüye ekle
        menu.addAction(copy_id_action)
        menu.addSeparator() # Araya çizgi atar
        menu.addAction(delete_action)

        # Menüyü farenin olduğu yerde göster
        menu.exec(library.QCursor.pos())

    def parse_id_from_item(self, item):
        """Listedeki metinden ID'yi ayıklar ( 'ID | TR -> EN' formatı)"""
        text = item.text()
        if "|" in text:
            return text.split("|")[0].strip()
        return None

    def copy_id(self, item):
        doc_id = self.parse_id_from_item(item)
        if doc_id:
            library.QApplication.clipboard().setText(doc_id)
            print(f"ID Kopyalandı: {doc_id}")

    def delete_item(self, item):
        doc_id = self.parse_id_from_item(item)
        if not doc_id:
            return

        # Kullanıcıya sor
        reply = library.QMessageBox.question(
            self, "Silme Onayı", 
            f"Bu veriyi silmek istediğinize emin misiniz?\nID: {doc_id}",
            library.QMessageBox.Yes | library.QMessageBox.No, 
            library.QMessageBox.No
        )

        if reply == library.QMessageBox.Yes:
            try:
                # Mongo API üzerinden sil
                success = library.mongo_api.delete_word_by_id(doc_id)
                if success:
                    library.QMessageBox.information(self, "Başarılı", "Veri silindi.")
                    # Listeyi yenile (İster sadece o satırı silebilirsin, ister veritabanından yenilersin)
                    # Veritabanından yenilemek en garantisidir.
                    self.search_data() 
                else:
                    library.QMessageBox.warning(self, "Hata", "Silinemedi. ID bulunamamış olabilir.")
            except Exception as e:
                library.QMessageBox.critical(self, "Hata", str(e))  
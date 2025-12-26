# 🌐 PrologPlus - Türkçe-İngilizce Hibrit Çeviri Sistemi

**Hybrid Probabilistic Translator v2.0**

Türkçe cümleleri İngilizce'ye çeviren, Prolog tabanlı hibrit bir makine çevirisi sistemidir. Olasılıksal puanlama, morfolojik analiz ve MongoDB entegrasyonu ile çalışır.

---

## 👥 Ekip

- **Serhat**
- **Görkem**
- **Samet**
- **Sadık**
---

## 📋 İçindekiler

- [Proje Durumu](#-proje-durumu)
- [Tamamlanan Özellikler](#-tamamlanan-özellikler)
- [Eksikler ve Düzeltilmesi Gerekenler](#-eksikler-ve-düzeltilmesi-gerekenler)
- [Kurulum](#-kurulum)
- [Kullanım](#-kullanım)
- [Dosya Yapısı](#-dosya-yapısı)
- [Mimari](#-mimari)

---

## 📊 Proje Durumu

| Bileşen | Durum | Açıklama |
|---------|-------|----------|
| Prolog Çeviri Motoru | ✅ Tamamlandı | SOV→SVO dönüşümü, puanlama sistemi |
| Morfoloji Modülü | ✅ Tamamlandı | 6 zaman, şahıs ekleri, olumsuzluk |
| MongoDB Entegrasyonu | ✅ Tamamlandı | 11 koleksiyon, dinamik veri |
| Python API | ✅ Tamamlandı | Prolog facts oluşturma |
| Kullanıcı Arayüzü | 🔄 Kısmen | Temel arayüz mevcut |
| AI Fallback | ⏳ Planlandı | Bilinmeyen kelimeler için |

---

## ✅ Tamamlanan Özellikler

### 1. Hibrit Olasılıksal Çeviri Motoru (`que_translator.pl`)

- **Gelişmiş Puanlama Sistemi:**
  - Frekans tabanlı skorlama (%25)
  - Eşdizimlilik (Collocation) analizi (%25)
  - Anlam uyumu (Semantic compatibility) (%20)
  - POS (kelime türü) uyumu (%15)
  - İngilizce n-gram doğallık (%15)

- **SOV → SVO Dönüşümü:**
  - Türkçe: `Ben okula gidiyorum` (Özne-Nesne-Fiil)
  - İngilizce: `I am going to school` (Özne-Fiil-Nesne)

### 2. Morfoloji Modülü (`morphology.pl`)

- **Desteklenen Zamanlar:**
  | Türkçe Zaman | İngilizce Karşılık | Örnek |
  |--------------|-------------------|-------|
  | Şimdiki Zaman (-yor) | Present Continuous | geliyorum → I am coming |
  | Geçmiş Zaman (-di) | Past Simple | geldim → I came |
  | Gelecek Zaman (-ecek) | Future | geleceğim → I will come |
  | Geniş Zaman (-er) | Present Simple | gelirim → I come |
  | Gereklilik (-meli) | Should | gelmeliyim → I should come |
  | Yeterlilik (-ebil) | Can | gelebilirim → I can come |

- **Olumsuzluk Desteği:**
  - `gelmiyorum` → `I am not coming`
  - `gitmedim` → `I did not go`
  - `gelmeyeceğim` → `I will not come`

- **Şahıs Ekleri:**
  - 1. tekil (ben), 2. tekil (sen), 3. tekil (o)
  - 1. çoğul (biz), 2. çoğul (siz), 3. çoğul (onlar)

### 3. MongoDB Veritabanı Entegrasyonu

- **11 Koleksiyon:**
  
  | Koleksiyon | Kayıt Sayısı | Açıklama |
  |------------|--------------|----------|
  | words | ~50+ | Kelime çevirileri |
  | collocations | ~20+ | Eşdizimlilik kuralları |
  | semantic_rules | ~15+ | Anlam uyumu kuralları |
  | ngrams | ~30+ | İngilizce n-gram frekansları |
  | grammar_rules | ~10+ | Gramer kuralları |
  | verb_roots | 51 | Türkçe-İngilizce fiil kökleri |
  | irregular_verbs | 37 | İngilizce düzensiz fiiller |
  | tense_suffixes | 21 | Türkçe zaman ekleri |
  | person_suffixes | 30 | Türkçe şahıs ekleri |
  | turkish_irregular_roots | 13 | Düzensiz kök değişimleri |
  | auxiliary_verbs | 31 | İngilizce yardımcı fiiller |

- **Dinamik Prolog Facts:**
  - `morphology_data.pl` dosyası MongoDB'den otomatik oluşturulur
  - `python morphology_api.py --generate` komutu ile güncellenir

### 4. Python API Katmanı

- **`morphology_api.py`:** MongoDB'den Prolog facts oluşturma
- **`mongo_api.py`:** Genel MongoDB işlemleri
- **`setup_mongodb.py`:** Veritabanı kurulumu ve seed data

---

## ❌ Eksikler ve Düzeltilmesi Gerekenler

### 🔴 Kritik Hatalar

1. **`istiyorum` çalışmıyor**
   - Sorun: `iste` kökü `ist` + `iyor` olarak yanlış parse ediliyor
   - Çözüm: Ünlü ile biten köklerin `-iyor` eki ile birleşmesi düzeltilmeli
   - Dosya: `morphology.pl` → `find_tense_and_root/4`
   - Çözüldü ✅

2. **`bakiyorum` → `lookking` (çift k hatası)**
   - Sorun: Present participle oluşturulurken CVC kuralı yanlış uygulanıyor
   - Çözüm: Tek heceli fiiller için düzeltme gerekli
   - Dosya: `morphology.pl` → `get_present_participle/2`

3. **Bazı fiiller için `turkish_irregular_root` eksik**
   - `istiy` → `iste` eklenmeli
   - `bakiy` → `bak` zaten çalışıyor gibi ama kontrol edilmeli

### 🟡 Orta Öncelikli

4. **Türkçe karakterler (ü, ö, ş, ğ, ı, ç)**
   - Şu an ASCII eşdeğerleri kullanılıyor
   - Gerçek Türkçe karakterlerle çalışacak şekilde genişletilebilir

5. **Nesne çevirisi eksik**
   - `Ali okula gidiyor` → Nesne (`okula`) düzgün çevrilmeli
   - Hal ekleri (-e, -de, -den) daha iyi handle edilmeli

6. **Polysemy (çok anlamlılık) desteği**
   - Mock data'da var ama tam entegre değil
   - Bağlama göre anlam seçimi iyileştirilmeli

### 🟢 Düşük Öncelikli / Gelecek Özellikler

7. **AI Fallback sistemi**
   - Bilinmeyen kelimeler için GPT/Claude API entegrasyonu
   - Planlandı ama henüz implement edilmedi

8. **Soru cümleleri**
   - `Nereye gidiyorsun?` → `Where are you going?`
   - Henüz desteklenmiyor

9. **Bileşik zamanlar**
   - `geliyordum` (geçmişte süreklilik)
   - `gelecektim` (gelecek in past)

10. **Edilgen çatı**
    - `yapıldı` → `was done`
    - Henüz desteklenmiyor

---

## 🚀 Kurulum

### Gereksinimler

- **SWI-Prolog** 8.0+ ([İndir](https://www.swi-prolog.org/download/stable))
- **Python** 3.10+ 
- **MongoDB** 6.0+ ([İndir](https://www.mongodb.com/try/download/community))
- **pip** paketleri: `pymongo`

### Adım 1: Repoyu Klonla

```bash
git clone <repo-url>
cd PrologPlus
```

### Adım 2: Python Ortamını Kur

```bash
# Virtual environment oluştur
python -m venv .venv

# Aktive et (Windows)
.venv\Scripts\activate

# Paketleri yükle
pip install pymongo
```

### Adım 3: MongoDB'yi Başlat

```bash
# MongoDB servisini başlat
mongod --dbpath /data/db

# Veya Windows servisi olarak
net start MongoDB
```

### Adım 4: Veritabanını Kur

```bash
# MongoDB'ye seed data yükle
python setup_mongodb.py
```

### Adım 5: Prolog Facts Oluştur

```bash
# MongoDB'den Prolog facts dosyası oluştur
python morphology_api.py --generate
```

### Adım 6: Test Et

```bash
# Prolog'u çalıştır
swipl

# Çeviriyi yükle ve test et
?- consult(que_translator).
?- cevir([ben, geliyorum]).
```

---

## 💻 Kullanım

### Prolog'dan Doğrudan Kullanım

```prolog
% Çeviri modülünü yükle
?- consult(que_translator).

% Tek kelime çevirisi
?- cevir([geliyorum]).
% Output: I am coming

% Cümle çevirisi
?- cevir([ben, okula, gidiyorum]).
% Output: I am going to school

% Morfoloji testi
?- morphology:translate_verb(geldim, X, Details).
% X = "I came"
% Details = [turkish_root:gel, english_root:come, tense:past_simple, ...]
```

### Python API Kullanımı

```python
from morphology_api import MorphologyDB

# MongoDB'ye bağlan
db = MorphologyDB()

# Tüm fiil köklerini al
roots = db.get_all_verb_roots()
for r in roots:
    print(f"{r.tr} → {r.en}")

# Prolog dosyası oluştur
db.export_to_prolog_file("morphology_data.pl")
```

### MongoDB'yi Güncelle ve Prolog'a Yansıt

```bash
# 1. MongoDB'de veri ekle/düzenle (MongoDB Compass veya shell ile)

# 2. Prolog facts dosyasını yeniden oluştur
python morphology_api.py --generate

# 3. Prolog'da veriyi yeniden yükle
?- reload_morphology_data.
```

---

## 📁 Dosya Yapısı

```
PrologPlus/
├── 📄 README.md                 # Bu dosya
├── 📄 que_translator.pl         # Ana çeviri motoru
├── 📄 morphology.pl             # Morfoloji modülü
├── 📄 morphology_data.pl        # MongoDB'den oluşturulan facts (otomatik)
├── 📄 mongo_con.pl              # Prolog-MongoDB bağlantısı + mock data
├── 📄 morphology_api.py         # Python morfoloji API
├── 📄 mongo_api.py              # Python MongoDB API
├── 📄 setup_mongodb.py          # Veritabanı kurulum scripti
├── 📄 user_interface.py         # Kullanıcı arayüzü
├── 📂 interfaces/               # Arayüz modülleri
│   ├── data_add_page.py
│   ├── data_delete_page.py
│   ├── data_search_page.py
│   └── ...
└── 📂 __pycache__/              # Python cache
```

---

## 🏗️ Mimari

```
┌─────────────────────────────────────────────────────────────────┐
│                      KULLANICI ARAYÜZÜ                          │
│                    (user_interface.py)                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PYTHON API KATMANI                           │
│         morphology_api.py  │  mongo_api.py                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────────┐
│    MongoDB      │ │  Prolog     │ │  morphology     │
│ (11 koleksiyon) │ │ Facts Gen.  │ │  _data.pl       │
└────────┬────────┘ └──────┬──────┘ └────────┬────────┘
         │                 │                  │
         │                 ▼                  │
         │    ┌────────────────────────┐      │
         │    │   morphology.pl        │◀─────┘
         │    │ (Morfolojik Analiz)    │
         │    └───────────┬────────────┘
         │                │
         ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    que_translator.pl                            │
│         (Hibrit Olasılıksal Çeviri Motoru)                      │
│                                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Frekans  │ │Collocation│ │ Semantic │ │  N-gram  │           │
│  │ Scoring  │ │ Analysis  │ │ Matching │ │ Scoring  │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                 │
│                    SOV → SVO Dönüşümü                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧪 Test Komutları

```bash
# Temel çeviri testi
swipl -g "consult(que_translator), cevir([geliyorum])" -t halt

# Cümle testi
swipl -g "consult(que_translator), cevir([ben, gidiyorum])" -t halt

# Morfoloji testi
swipl -g "consult(morphology), test_morphology" -t halt

# MongoDB bağlantı testi
python morphology_api.py
```

---

## 📝 Notlar

- Prolog dosyalarında Türkçe karakterler ASCII eşdeğerleri olarak yazılmıştır (ü→u, ö→o, ş→s, vb.)
- `morphology_data.pl` dosyası manuel düzenlenmemelidir - MongoDB'den oluşturulur
- Mock data `mongo_con.pl` içinde tanımlıdır, MongoDB bağlantısı yoksa kullanılır

---

## 📅 Son Güncelleme

**21 Aralık 2024**

---

## 📜 Lisans

Bu proje eğitim amaçlıdır.

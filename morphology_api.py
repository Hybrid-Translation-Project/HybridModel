import os
import sys

# MongoDB Kütüphanesi Kontrolü
try:
    from pymongo import MongoClient
except ImportError:
    print("HATA: 'pymongo' kütüphanesi yüklü değil.")
    sys.exit(1)

# =============================================================================
# AYARLAR
# =============================================================================
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "translator_db"
OUTPUT_FILE = "morphology_data.pl"

def generate_prolog_data():
    print(f"🔌 MongoDB'ye bağlanılıyor... ({DB_NAME})")
    
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        
        words_col = db["words"]          
        verbs_col = db["verb_roots"]     
        suffixes_col = db["tense_suffixes"]

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(":- encoding(utf8).\n")
            f.write(f"% OTOMATİK OLUŞTURULAN VERİ DOSYASI\n\n")

            # 1. İSİMLER
            print("📦 İsimler işleniyor...")
            count_n = 0
            for word in words_col.find():
                tr = word.get("turkish", "").strip().lower()
                en = word.get("english", "").strip().lower()
                w_type = word.get("type", "noun").strip().lower()
                
                if tr and en and (w_type == "noun" or w_type == ""):
                    if " " in en: f.write(f"noun({tr}, '{en}').\n")
                    else: f.write(f"noun({tr}, {en}).\n")
                    count_n += 1
            f.write(f"\n% {count_n} isim eklendi.\n\n")

            # 2. FİİLLER (Gramer Düzeltmeli)
            print("⚙️  Fiiller ve gramer kuralları işleniyor...")
            count_v = 0
            # Sesli harfleri tanıyalım (son harf ikilemesi için lazım olabilir)
            vowels = "aeiou"

            for verb in verbs_col.find():
                tr = verb.get("turkish", verb.get("turkish_root", "")).strip().lower()
                en = verb.get("english", verb.get("english_root", "")).strip().lower()
                v_type = verb.get("type", "regular").strip().lower()
                
                if tr and en:
                    f.write(f"verb_root({tr}, {en}, {v_type}).\n")
                    
                    if v_type == "irregular":
                        past = verb.get("past", f"{en}ed").strip().lower()
                        participle = verb.get("participle", f"{en}ed").strip().lower()
                        
                        # --- İNGİLİZCE GRAMER MANTIĞI (-ing Eki) ---
                        if en.endswith("e") and not en.endswith("ee"):
                            # Kural 1: Sonu 'e' ile bitiyorsa 'e' düşer (come -> coming)
                            present_part = f"{en[:-1]}ing"
                        elif en in ["run", "swim", "cut", "put", "get", "sit", "stop", "win", "plan"]:
                            # Kural 2: Bazı fiillerde son harf ikileşir (run -> running)
                            present_part = f"{en}{en[-1]}ing"
                        else:
                            # Kural 3: Normal ekle (go -> going)
                            present_part = f"{en}ing"
                        
                        f.write(f"irregular_verb({en}, {past}, {participle}, {present_part}).\n")
                    
                    count_v += 1
            f.write(f"\n% {count_v} fiil eklendi.\n\n")

            # 3. SABİT EKLER
            print("📝 Sabit veriler yazılıyor...")
            db_suffixes = list(suffixes_col.find())
            if len(db_suffixes) > 0:
                for s in db_suffixes:
                    sf = s.get("suffix", "")
                    tn = s.get("tense", "")
                    if sf and tn: f.write(f"tense_suffix(\"{sf}\", {tn}).\n")
            else:
                f.write('tense_suffix("iyor", present_continuous).\n')
                f.write('tense_suffix("di", past_simple).\n')
                f.write('tense_suffix("du", past_simple).\n')
                f.write('tense_suffix("ti", past_simple).\n')
                f.write('tense_suffix("tu", past_simple).\n')
                f.write('tense_suffix("ecek", future).\n')
                f.write('tense_suffix("acak", future).\n')
                f.write('tense_suffix("r", aorist).\n')
                f.write('tense_suffix("er", aorist).\n')
                f.write('tense_suffix("ar", aorist).\n')
                f.write('tense_suffix("meli", necessity).\n')
                f.write('tense_suffix("malı", necessity).\n')
            
            f.write('\n% --- Şahıs ve Yardımcı Fiiller ---\n')
            f.write('person_suffix("um", 1, singular, _).\n')
            f.write('person_suffix("sun", 2, singular, _).\n')
            f.write('person_suffix("uz", 1, plural, _).\n')
            f.write('person_suffix("sunuz", 2, plural, _).\n')
            f.write('person_suffix("lar", 3, plural, _).\n')
            f.write('person_suffix("m", 1, singular, past_simple).\n')
            f.write('person_suffix("n", 2, singular, past_simple).\n')
            f.write('person_suffix("k", 1, plural, past_simple).\n')
            
            f.write("auxiliary_verb(present_continuous, 1, singular, false, am).\n")
            f.write("auxiliary_verb(present_continuous, 3, singular, false, is).\n")
            f.write("auxiliary_verb(present_continuous, _, _, false, are).\n")
            f.write("auxiliary_verb(future, _, _, _, will).\n")
            f.write("auxiliary_verb(past_simple, _, _, true, 'did not').\n")
            
            f.write('\n% --- Türkçe Düzensiz Kökler ---\n')
            f.write('turkish_irregular_root("gid", git).\n')
            f.write('turkish_irregular_root("ed", et).\n')
            f.write('turkish_irregular_root("y", ye).\n')
            f.write('turkish_irregular_root("diy", de).\n')

        print(f"✅ GÜNCELLEME TAMAM! 'come -> coming' düzeltildi.")
        print(f"📊 {count_n} İsim, {count_v} Fiil işlendi.")

    except Exception as e:
        print(f"❌ HATA: {e}")

if __name__ == "__main__":
    generate_prolog_data()
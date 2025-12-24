"""
MongoDB Veritabanı Kurulum Scripti
==================================

Bu script, gelişmiş puanlama sisteminin verilerini MongoDB'ye yükler.

Koleksiyonlar:
1. words          - Kelimeler (polysemy + frekans + semantic class)
2. collocations   - Eşdizimlilik verileri
3. semantic_rules - Anlam uyumu kuralları
4. ngrams         - İngilizce n-gram frekansları
5. grammar_rules  - Dilbilgisi kuralları

AI Model:
- Hugging Face'den MarianMT modeli indirilir (g0rkm/final_marian_model)
- Türkçe-İngilizce çeviri için fine-tuned model

Kullanım:
    python setup_mongodb.py --init     # Tüm koleksiyonları oluştur ve doldur
    python setup_mongodb.py --clear    # Tüm verileri sil
    python setup_mongodb.py --export   # Mock data'yı JSON olarak export et
    python setup_mongodb.py --model    # AI modelini indir (Hugging Face'den)
    python setup_mongodb.py --all      # Hem veritabanı hem model kurulumu
"""

import sys
import json
import os
from typing import Dict, List, Any
from datetime import datetime

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    print("[HATA] pymongo yüklü değil. Yüklemek için: pip install pymongo")

# =============================================================================
# MONGODB BAĞLANTI AYARLARI
# =============================================================================

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "translator_db"

# Koleksiyon isimleri
COLLECTIONS = {
    "words": "words",
    "collocations": "collocations", 
    "semantic_rules": "semantic_rules",
    "ngrams": "ngrams",
    "grammar_rules": "grammar_rules",
    # Morfoloji koleksiyonları
    "verb_roots": "verb_roots",
    "irregular_verbs": "irregular_verbs",
    "tense_suffixes": "tense_suffixes",
    "person_suffixes": "person_suffixes",
    "turkish_irregular_roots": "turkish_irregular_roots",
    "auxiliary_verbs": "auxiliary_verbs",
    # Fonoloji kuralları
    "phonology_rules": "phonology_rules",
    # Türkçe morfoloji istisnaları
    "aorist_irregular_verbs": "aorist_irregular_verbs",
    "vowel_harmony_exceptions": "vowel_harmony_exceptions",
    "consonant_mutation_exceptions": "consonant_mutation_exceptions",
    "vowel_drop_words": "vowel_drop_words",
    # Yeni eklenen koleksiyonlar
    "case_suffixes": "case_suffixes",                     # İsim çekim ekleri
    "possessive_suffixes": "possessive_suffixes",         # İyelik ekleri
    "negation_suffixes": "negation_suffixes",             # Olumsuzluk ekleri
    "question_particles": "question_particles",           # Soru ekleri
    "postpositions": "postpositions",                     # Edatlar
    "conjunctions": "conjunctions",                       # Bağlaçlar
    "copula_suffixes": "copula_suffixes",                 # Ek-fiil ekleri
    "article_rules": "article_rules",                     # İngilizce article kuralları
    "buffer_consonant_exceptions": "buffer_consonant_exceptions",  # Kaynaştırma istisnaları
    "plural_suffixes": "plural_suffixes",                 # Çoğul ekleri
    "noun_roots": "noun_roots",                           # İsim kökleri
}


# =============================================================================
# VERİ ŞEMALARI
# =============================================================================

# 1. WORDS - Kelimeler
WORDS_DATA = [
    {
        "tr": "yüz",
        "tr_ascii": "yuz",
        "meanings": [
            {"en": "face", "pos": "noun", "frequency": 85, "semantic_class": "body_part", "domain": ["body", "general"]},
            {"en": "hundred", "pos": "noun", "frequency": 72, "semantic_class": "number", "domain": ["math", "quantity"]},
            {"en": "swim", "pos": "verb", "frequency": 35, "semantic_class": "motion", "domain": ["sport", "water"]}
        ]
    },
    {
        "tr": "ben",
        "tr_ascii": "ben",
        "meanings": [
            {"en": "I", "pos": "pronoun", "frequency": 98, "semantic_class": "animate", "domain": ["general"]}
        ]
    },
    {
        "tr": "sen",
        "tr_ascii": "sen",
        "meanings": [
            {"en": "you", "pos": "pronoun", "frequency": 95, "semantic_class": "animate", "domain": ["general"]}
        ]
    },
    {
        "tr": "o",
        "tr_ascii": "o",
        "meanings": [
            {"en": "he", "pos": "pronoun", "frequency": 90, "semantic_class": "animate", "domain": ["general"]},
            {"en": "she", "pos": "pronoun", "frequency": 90, "semantic_class": "animate", "domain": ["general"]},
            {"en": "it", "pos": "pronoun", "frequency": 85, "semantic_class": "inanimate", "domain": ["general"]}
        ]
    },
    {
        "tr": "sev",
        "tr_ascii": "sev",
        "meanings": [
            {"en": "love", "pos": "verb", "frequency": 78, "semantic_class": "emotion", "domain": ["emotion", "relationship"]},
            {"en": "like", "pos": "verb", "frequency": 82, "semantic_class": "emotion", "domain": ["emotion", "preference"]}
        ]
    },
    {
        "tr": "ye",
        "tr_ascii": "ye",
        "meanings": [
            {"en": "eat", "pos": "verb", "frequency": 75, "semantic_class": "consumption", "domain": ["food", "action"]}
        ]
    },
    {
        "tr": "iç",
        "tr_ascii": "ic",
        "meanings": [
            {"en": "drink", "pos": "verb", "frequency": 70, "semantic_class": "consumption", "domain": ["food", "action"]},
            {"en": "inside", "pos": "noun", "frequency": 45, "semantic_class": "location", "domain": ["space"]}
        ]
    },
    {
        "tr": "git",
        "tr_ascii": "git",
        "meanings": [
            {"en": "go", "pos": "verb", "frequency": 88, "semantic_class": "motion", "domain": ["motion", "action"]}
        ]
    },
    {
        "tr": "gel",
        "tr_ascii": "gel",
        "meanings": [
            {"en": "come", "pos": "verb", "frequency": 86, "semantic_class": "motion", "domain": ["motion", "action"]}
        ]
    },
    {
        "tr": "yıka",
        "tr_ascii": "yika",
        "meanings": [
            {"en": "wash", "pos": "verb", "frequency": 50, "semantic_class": "action", "domain": ["cleaning"]}
        ]
    },
    {
        "tr": "oku",
        "tr_ascii": "oku",
        "meanings": [
            {"en": "read", "pos": "verb", "frequency": 65, "semantic_class": "cognitive", "domain": ["education"]}
        ]
    },
    {
        "tr": "yaz",
        "tr_ascii": "yaz",
        "meanings": [
            {"en": "write", "pos": "verb", "frequency": 60, "semantic_class": "cognitive", "domain": ["education"]},
            {"en": "summer", "pos": "noun", "frequency": 55, "semantic_class": "time", "domain": ["season"]}
        ]
    },
    {
        "tr": "al",
        "tr_ascii": "al",
        "meanings": [
            {"en": "take", "pos": "verb", "frequency": 80, "semantic_class": "action", "domain": ["action"]},
            {"en": "buy", "pos": "verb", "frequency": 65, "semantic_class": "transaction", "domain": ["commerce"]},
            {"en": "red", "pos": "adjective", "frequency": 40, "semantic_class": "property", "domain": ["color"]}
        ]
    },
    {
        "tr": "ver",
        "tr_ascii": "ver",
        "meanings": [
            {"en": "give", "pos": "verb", "frequency": 78, "semantic_class": "action", "domain": ["action"]}
        ]
    },
    {
        "tr": "yap",
        "tr_ascii": "yap",
        "meanings": [
            {"en": "do", "pos": "verb", "frequency": 82, "semantic_class": "action", "domain": ["action"]},
            {"en": "make", "pos": "verb", "frequency": 75, "semantic_class": "action", "domain": ["creation"]}
        ]
    },
    {
        "tr": "oyna",
        "tr_ascii": "oyna",
        "meanings": [
            {"en": "play", "pos": "verb", "frequency": 70, "semantic_class": "action", "domain": ["entertainment"]}
        ]
    },
    {
        "tr": "elma",
        "tr_ascii": "elma",
        "meanings": [
            {"en": "apple", "pos": "noun", "frequency": 45, "semantic_class": "food", "domain": ["food", "fruit"]}
        ]
    },
    {
        "tr": "su",
        "tr_ascii": "su",
        "meanings": [
            {"en": "water", "pos": "noun", "frequency": 75, "semantic_class": "liquid", "domain": ["liquid", "nature"]}
        ]
    },
    {
        "tr": "kitap",
        "tr_ascii": "kitap",
        "meanings": [
            {"en": "book", "pos": "noun", "frequency": 70, "semantic_class": "object", "domain": ["education"]}
        ]
    },
    {
        "tr": "ev",
        "tr_ascii": "ev",
        "meanings": [
            {"en": "house", "pos": "noun", "frequency": 80, "semantic_class": "location", "domain": ["building"]},
            {"en": "home", "pos": "noun", "frequency": 78, "semantic_class": "location", "domain": ["family"]}
        ]
    },
    {
        "tr": "para",
        "tr_ascii": "para",
        "meanings": [
            {"en": "money", "pos": "noun", "frequency": 72, "semantic_class": "abstract", "domain": ["finance"]}
        ]
    },
    {
        "tr": "kedi",
        "tr_ascii": "kedi",
        "meanings": [
            {"en": "cat", "pos": "noun", "frequency": 55, "semantic_class": "animate", "domain": ["animal"]}
        ]
    },
    {
        "tr": "köpek",
        "tr_ascii": "kopek",
        "meanings": [
            {"en": "dog", "pos": "noun", "frequency": 52, "semantic_class": "animate", "domain": ["animal"]}
        ]
    },
    {
        "tr": "güzel",
        "tr_ascii": "guzel",
        "meanings": [
            {"en": "beautiful", "pos": "adjective", "frequency": 70, "semantic_class": "property", "domain": ["appearance"]},
            {"en": "nice", "pos": "adjective", "frequency": 68, "semantic_class": "property", "domain": ["quality"]}
        ]
    },
    {
        "tr": "büyük",
        "tr_ascii": "buyuk",
        "meanings": [
            {"en": "big", "pos": "adjective", "frequency": 75, "semantic_class": "property", "domain": ["size"]},
            {"en": "large", "pos": "adjective", "frequency": 70, "semantic_class": "property", "domain": ["size"]}
        ]
    },
    {
        "tr": "küçük",
        "tr_ascii": "kucuk",
        "meanings": [
            {"en": "small", "pos": "adjective", "frequency": 72, "semantic_class": "property", "domain": ["size"]}
        ]
    }
]

# 2. COLLOCATIONS - Eşdizimlilik
COLLOCATIONS_DATA = [
    {
        "word1": "yuz", "word2": "yika",
        "pattern": "NOUN + VERB",
        "meaning_hint": {"yuz": "face", "yika": "wash"},
        "frequency": 3200,
        "strength": 0.92,
        "example_tr": "yüzünü yıka",
        "example_en": "wash your face"
    },
    {
        "word1": "yuz", "word2": "metre",
        "pattern": "NUM + NOUN",
        "meaning_hint": {"yuz": "hundred"},
        "frequency": 2800,
        "strength": 0.88
    },
    {
        "word1": "yuz", "word2": "lira",
        "pattern": "NUM + NOUN",
        "meaning_hint": {"yuz": "hundred"},
        "frequency": 4500,
        "strength": 0.95
    },
    {
        "word1": "su", "word2": "ic",
        "pattern": "NOUN + VERB",
        "meaning_hint": {"su": "water", "ic": "drink"},
        "frequency": 5000,
        "strength": 0.94,
        "example_tr": "su iç",
        "example_en": "drink water"
    },
    {
        "word1": "elma", "word2": "ye",
        "pattern": "NOUN + VERB",
        "meaning_hint": {"elma": "apple", "ye": "eat"},
        "frequency": 2500,
        "strength": 0.90,
        "example_tr": "elma ye",
        "example_en": "eat an apple"
    },
    {
        "word1": "kitap", "word2": "oku",
        "pattern": "NOUN + VERB",
        "meaning_hint": {"kitap": "book", "oku": "read"},
        "frequency": 4200,
        "strength": 0.93,
        "example_tr": "kitap oku",
        "example_en": "read a book"
    },
    {
        "word1": "mektup", "word2": "yaz",
        "pattern": "NOUN + VERB",
        "meaning_hint": {"yaz": "write"},
        "frequency": 1800,
        "strength": 0.85
    },
    {
        "word1": "ev", "word2": "git",
        "pattern": "NOUN + VERB",
        "meaning_hint": {"ev": "home", "git": "go"},
        "frequency": 3800,
        "strength": 0.89,
        "example_tr": "eve git",
        "example_en": "go home"
    },
    {
        "word1": "para", "word2": "al",
        "pattern": "NOUN + VERB",
        "meaning_hint": {"para": "money", "al": "take"},
        "frequency": 2200,
        "strength": 0.82
    },
    {
        "word1": "para", "word2": "ver",
        "pattern": "NOUN + VERB",
        "meaning_hint": {"para": "money", "ver": "give"},
        "frequency": 2000,
        "strength": 0.80
    }
]

# 3. SEMANTIC RULES - Anlam Uyumu
SEMANTIC_RULES_DATA = [
    # Canlı özne uyumları
    {"subject_class": "animate", "verb_class": "emotion", "compatibility": 0.95, "description": "Canlılar duygu fiilleri kullanabilir"},
    {"subject_class": "animate", "verb_class": "motion", "compatibility": 0.90, "description": "Canlılar hareket edebilir"},
    {"subject_class": "animate", "verb_class": "consumption", "compatibility": 0.95, "description": "Canlılar yiyip içebilir"},
    {"subject_class": "animate", "verb_class": "cognitive", "compatibility": 0.85, "description": "Canlılar düşünebilir/okuyabilir"},
    {"subject_class": "animate", "verb_class": "action", "compatibility": 0.88, "description": "Canlılar aksiyon yapabilir"},
    
    # Cansız özne uyumları (düşük)
    {"subject_class": "inanimate", "verb_class": "emotion", "compatibility": 0.15, "description": "Cansızlar duygu hissedemez"},
    {"subject_class": "inanimate", "verb_class": "motion", "compatibility": 0.25, "description": "Cansızlar kendiliğinden hareket edemez"},
    {"subject_class": "inanimate", "verb_class": "consumption", "compatibility": 0.10, "description": "Cansızlar yiyemez"},
    
    # Nesne-fiil uyumları
    {"subject_class": "food", "verb_class": "consumption", "compatibility": 0.98, "description": "Yiyecekler tüketilir"},
    {"subject_class": "liquid", "verb_class": "consumption", "compatibility": 0.95, "description": "Sıvılar içilir"},
    {"subject_class": "object", "verb_class": "cognitive", "compatibility": 0.85, "description": "Nesneler okunabilir/yazılabilir"},
    {"subject_class": "body_part", "verb_class": "action", "compatibility": 0.75, "description": "Vücut parçalarına işlem yapılabilir"},
    {"subject_class": "location", "verb_class": "motion", "compatibility": 0.88, "description": "Konumlar hareket hedefidir"},
    
    # Sayı uyumsuzlukları
    {"subject_class": "number", "verb_class": "motion", "compatibility": 0.10, "description": "Sayılar hareket edemez"},
    {"subject_class": "number", "verb_class": "emotion", "compatibility": 0.05, "description": "Sayılar hissedemez"},
    {"subject_class": "number", "verb_class": "action", "compatibility": 0.15, "description": "Sayılar aksiyon yapamaz"}
]

# 4. NGRAMS - İngilizce N-gram
NGRAMS_DATA = [
    # Bigrams
    {"words": ["I", "love"], "frequency": 125000, "type": "bigram"},
    {"words": ["I", "like"], "frequency": 180000, "type": "bigram"},
    {"words": ["I", "eat"], "frequency": 45000, "type": "bigram"},
    {"words": ["I", "drink"], "frequency": 32000, "type": "bigram"},
    {"words": ["I", "go"], "frequency": 95000, "type": "bigram"},
    {"words": ["I", "come"], "frequency": 28000, "type": "bigram"},
    {"words": ["I", "read"], "frequency": 38000, "type": "bigram"},
    {"words": ["I", "write"], "frequency": 35000, "type": "bigram"},
    {"words": ["I", "wash"], "frequency": 12000, "type": "bigram"},
    {"words": ["you", "love"], "frequency": 85000, "type": "bigram"},
    {"words": ["you", "like"], "frequency": 120000, "type": "bigram"},
    {"words": ["wash", "face"], "frequency": 18000, "type": "bigram"},
    {"words": ["eat", "apple"], "frequency": 12000, "type": "bigram"},
    {"words": ["drink", "water"], "frequency": 25000, "type": "bigram"},
    {"words": ["read", "book"], "frequency": 35000, "type": "bigram"},
    {"words": ["go", "home"], "frequency": 55000, "type": "bigram"},
    {"words": ["go", "house"], "frequency": 8000, "type": "bigram"},
    {"words": ["love", "face"], "frequency": 8500, "type": "bigram"},
    
    # Trigrams
    {"words": ["I", "love", "you"], "frequency": 85000, "type": "trigram"},
    {"words": ["I", "like", "you"], "frequency": 45000, "type": "trigram"},
    {"words": ["I", "wash", "face"], "frequency": 5500, "type": "trigram"},
    {"words": ["I", "eat", "apple"], "frequency": 3200, "type": "trigram"},
    {"words": ["I", "drink", "water"], "frequency": 8500, "type": "trigram"},
    {"words": ["I", "read", "book"], "frequency": 12000, "type": "trigram"},
    {"words": ["I", "go", "home"], "frequency": 25000, "type": "trigram"}


]

# 5. GRAMMAR RULES - Dilbilgisi Kuralları
GRAMMAR_RULES_DATA = [
    {
        "id": "sov_to_svo",
        "pattern": "PRONOUN + NOUN + VERB",
        "tr_order": ["subject", "object", "predicate"],
        "en_order": ["subject", "predicate", "object"],
        "score_bonus": 20,
        "description": "Standart SOV -> SVO dönüşümü"
    },
    {
        "id": "sv_basic",
        "pattern": "PRONOUN + VERB",
        "tr_order": ["subject", "predicate"],
        "en_order": ["subject", "predicate"],
        "score_bonus": 15,
        "description": "Basit özne-yüklem cümlesi"
    },
    {
        "id": "sov_adj",
        "pattern": "PRONOUN + ADJECTIVE + NOUN + VERB",
        "tr_order": ["subject", "modifier", "object", "predicate"],
        "en_order": ["subject", "predicate", "modifier", "object"],
        "score_bonus": 25,
        "description": "Sıfatlı SOV cümlesi"
    }
]


# =============================================================================
# MORFOLOJİ VERİLERİ
# =============================================================================

# 6. VERB ROOTS - Fiil Kökleri (Türkçe → İngilizce)
VERB_ROOTS_DATA = [
    {"tr": "gel", "en": "come", "type": "irregular"},
    {"tr": "git", "en": "go", "type": "irregular"},
    {"tr": "gid", "en": "go", "type": "irregular", "note": "yumuşama: git→gid"},
    {"tr": "ye", "en": "eat", "type": "irregular"},
    {"tr": "yi", "en": "eat", "type": "irregular", "note": "ye→yi değişimi"},
    {"tr": "iç", "en": "drink", "type": "irregular"},
    {"tr": "yap", "en": "do", "type": "irregular"},
    {"tr": "al", "en": "take", "type": "irregular"},
    {"tr": "ver", "en": "give", "type": "irregular"},
    {"tr": "oku", "en": "read", "type": "irregular"},
    {"tr": "yaz", "en": "write", "type": "irregular"},
    {"tr": "sev", "en": "love", "type": "regular"},
    {"tr": "gör", "en": "see", "type": "irregular"},
    {"tr": "bil", "en": "know", "type": "irregular"},
    {"tr": "de", "en": "say", "type": "irregular"},
    {"tr": "söyle", "en": "tell", "type": "irregular"},
    {"tr": "düşün", "en": "think", "type": "irregular"},
    {"tr": "anla", "en": "understand", "type": "irregular"},
    {"tr": "bul", "en": "find", "type": "irregular"},
    {"tr": "bırak", "en": "leave", "type": "irregular"},
    {"tr": "hisset", "en": "feel", "type": "irregular"},
    {"tr": "koy", "en": "put", "type": "irregular"},
    {"tr": "otur", "en": "sit", "type": "irregular"},
    {"tr": "kalk", "en": "stand", "type": "irregular"},
    {"tr": "uyu", "en": "sleep", "type": "irregular"},
    {"tr": "uyan", "en": "wake", "type": "irregular"},
    {"tr": "koş", "en": "run", "type": "irregular"},
    {"tr": "yüz", "en": "swim", "type": "irregular"},
    {"tr": "sat", "en": "sell", "type": "irregular"},
    {"tr": "yıka", "en": "wash", "type": "regular"},
    {"tr": "oyna", "en": "play", "type": "regular"},
    {"tr": "çalış", "en": "work", "type": "regular"},
    {"tr": "konuş", "en": "speak", "type": "irregular"},
    {"tr": "dinle", "en": "listen", "type": "regular"},
    {"tr": "bekle", "en": "wait", "type": "regular"},
    {"tr": "başla", "en": "start", "type": "regular"},
    {"tr": "bitir", "en": "finish", "type": "regular"},
    {"tr": "aç", "en": "open", "type": "regular"},
    {"tr": "kapat", "en": "close", "type": "regular"},
    {"tr": "öğren", "en": "learn", "type": "regular"},
    {"tr": "öğret", "en": "teach", "type": "irregular"},
    {"tr": "hatırla", "en": "remember", "type": "regular"},
    {"tr": "unut", "en": "forget", "type": "irregular"},
    {"tr": "ol", "en": "be", "type": "irregular"},
    {"tr": "et", "en": "do", "type": "irregular", "note": "etmek yardımcı fiili"},
    {"tr": "iste", "en": "want", "type": "regular"},
    {"tr": "duy", "en": "hear", "type": "irregular"},
    {"tr": "tut", "en": "hold", "type": "irregular"},
    {"tr": "bak", "en": "look", "type": "regular"},
    {"tr": "dene", "en": "try", "type": "regular"},
    {"tr": "kullan", "en": "use", "type": "regular"},
]

# 7. IRREGULAR VERBS - İngilizce Düzensiz Fiiller
IRREGULAR_VERBS_DATA = [
    {"base": "be", "past": "was/were", "past_participle": "been", "present_participle": "being"},
    {"base": "come", "past": "came", "past_participle": "come", "present_participle": "coming"},
    {"base": "go", "past": "went", "past_participle": "gone", "present_participle": "going"},
    {"base": "eat", "past": "ate", "past_participle": "eaten", "present_participle": "eating"},
    {"base": "drink", "past": "drank", "past_participle": "drunk", "present_participle": "drinking"},
    {"base": "give", "past": "gave", "past_participle": "given", "present_participle": "giving"},
    {"base": "take", "past": "took", "past_participle": "taken", "present_participle": "taking"},
    {"base": "make", "past": "made", "past_participle": "made", "present_participle": "making"},
    {"base": "do", "past": "did", "past_participle": "done", "present_participle": "doing"},
    {"base": "see", "past": "saw", "past_participle": "seen", "present_participle": "seeing"},
    {"base": "have", "past": "had", "past_participle": "had", "present_participle": "having"},
    {"base": "get", "past": "got", "past_participle": "gotten", "present_participle": "getting"},
    {"base": "read", "past": "read", "past_participle": "read", "present_participle": "reading"},
    {"base": "write", "past": "wrote", "past_participle": "written", "present_participle": "writing"},
    {"base": "run", "past": "ran", "past_participle": "run", "present_participle": "running"},
    {"base": "swim", "past": "swam", "past_participle": "swum", "present_participle": "swimming"},
    {"base": "buy", "past": "bought", "past_participle": "bought", "present_participle": "buying"},
    {"base": "sell", "past": "sold", "past_participle": "sold", "present_participle": "selling"},
    {"base": "say", "past": "said", "past_participle": "said", "present_participle": "saying"},
    {"base": "tell", "past": "told", "past_participle": "told", "present_participle": "telling"},
    {"base": "think", "past": "thought", "past_participle": "thought", "present_participle": "thinking"},
    {"base": "know", "past": "knew", "past_participle": "known", "present_participle": "knowing"},
    {"base": "understand", "past": "understood", "past_participle": "understood", "present_participle": "understanding"},
    {"base": "find", "past": "found", "past_participle": "found", "present_participle": "finding"},
    {"base": "leave", "past": "left", "past_participle": "left", "present_participle": "leaving"},
    {"base": "feel", "past": "felt", "past_participle": "felt", "present_participle": "feeling"},
    {"base": "put", "past": "put", "past_participle": "put", "present_participle": "putting"},
    {"base": "sit", "past": "sat", "past_participle": "sat", "present_participle": "sitting"},
    {"base": "stand", "past": "stood", "past_participle": "stood", "present_participle": "standing"},
    {"base": "sleep", "past": "slept", "past_participle": "slept", "present_participle": "sleeping"},
    {"base": "wake", "past": "woke", "past_participle": "woken", "present_participle": "waking"},
    {"base": "forget", "past": "forgot", "past_participle": "forgotten", "present_participle": "forgetting"},
    {"base": "speak", "past": "spoke", "past_participle": "spoken", "present_participle": "speaking"},
    {"base": "teach", "past": "taught", "past_participle": "taught", "present_participle": "teaching"},
    {"base": "hear", "past": "heard", "past_participle": "heard", "present_participle": "hearing"},
    {"base": "hold", "past": "held", "past_participle": "held", "present_participle": "holding"},
    {"base": "want", "past": "wanted", "past_participle": "wanted", "present_participle": "wanting"},
]

# 8. TENSE SUFFIXES - Türkçe Zaman Ekleri
TENSE_SUFFIXES_DATA = [
    # Şimdiki Zamanın Hikayesi (-yordu)
    {"suffix": "iyordu", "tense": "past_continuous", "priority": 10, "description": "Şimdiki zamanın hikayesi (ince-düz)"},
    {"suffix": "ıyordu", "tense": "past_continuous", "priority": 10, "description": "Şimdiki zamanın hikayesi (kalın-düz)"},
    {"suffix": "uyordu", "tense": "past_continuous", "priority": 10, "description": "Şimdiki zamanın hikayesi (kalın-yuvarlak)"},
    {"suffix": "üyordu", "tense": "past_continuous", "priority": 10, "description": "Şimdiki zamanın hikayesi (ince-yuvarlak)"},
    {"suffix": "miyordu", "tense": "past_continuous", "priority": 10, "description": "Olumsuz (ince)"},
    {"suffix": "mıyordu", "tense": "past_continuous", "priority": 10, "description": "Olumsuz (kalın)"},
    {"suffix": "muyordu", "tense": "past_continuous", "priority": 10, "description": "Olumsuz (kalın-yuvarlak)"},
    {"suffix": "müyordu", "tense": "past_continuous", "priority": 10, "description": "Olumsuz (ince-yuvarlak)"},

    # Şimdiki Zaman (-yor)
    {"suffix": "iyor", "tense": "present_continuous", "priority": 1, "description": "Şimdiki zaman"},
    {"suffix": "ıyor", "tense": "present_continuous", "priority": 1, "description": "Şimdiki zaman"},
    {"suffix": "uyor", "tense": "present_continuous", "priority": 1, "description": "Şimdiki zaman"},
    {"suffix": "üyor", "tense": "present_continuous", "priority": 1, "description": "Şimdiki zaman"},
    {"suffix": "yor", "tense": "present_continuous", "priority": 2, "description": "Şimdiki zaman (kısa)"},
    
    # Geçmiş Zaman (-di/-dı/-dü/-du)
    {"suffix": "di", "tense": "past_simple", "priority": 1, "description": "Geçmiş zaman"},
    {"suffix": "dı", "tense": "past_simple", "priority": 1, "description": "Geçmiş zaman"},
    {"suffix": "du", "tense": "past_simple", "priority": 1, "description": "Geçmiş zaman"},
    {"suffix": "dü", "tense": "past_simple", "priority": 1, "description": "Geçmiş zaman"},
    {"suffix": "ti", "tense": "past_simple", "priority": 1, "description": "Geçmiş zaman (sert ünsüz)"},
    {"suffix": "tı", "tense": "past_simple", "priority": 1, "description": "Geçmiş zaman (sert ünsüz)"},
    {"suffix": "tu", "tense": "past_simple", "priority": 1, "description": "Geçmiş zaman (sert ünsüz)"},
    {"suffix": "tü", "tense": "past_simple", "priority": 1, "description": "Geçmiş zaman (sert ünsüz)"},
    
    # Gelecek Zaman (-ecek/-acak)
    {"suffix": "ecek", "tense": "future", "priority": 1, "description": "Gelecek zaman"},
    {"suffix": "acak", "tense": "future", "priority": 1, "description": "Gelecek zaman"},
    {"suffix": "eceg", "tense": "future", "priority": 1, "description": "Gelecek zaman (yumuşama)"},
    {"suffix": "acag", "tense": "future", "priority": 1, "description": "Gelecek zaman (yumuşama)"},
    
    # Geniş Zaman (-er/-ar/-ir/-ır/-ur/-ür/-r)
    {"suffix": "er", "tense": "aorist", "priority": 1, "description": "Geniş zaman"},
    {"suffix": "ar", "tense": "aorist", "priority": 1, "description": "Geniş zaman"},
    {"suffix": "ir", "tense": "aorist", "priority": 1, "description": "Geniş zaman"},
    {"suffix": "ır", "tense": "aorist", "priority": 1, "description": "Geniş zaman"},
    {"suffix": "ur", "tense": "aorist", "priority": 1, "description": "Geniş zaman"},
    {"suffix": "ür", "tense": "aorist", "priority": 1, "description": "Geniş zaman"},
    {"suffix": "r", "tense": "aorist", "priority": 2, "description": "Geniş zaman (tek heceli fiillerde)"},
    
    # Duyulan Geçmiş (-miş)
    {"suffix": "miş", "tense": "past_reported", "priority": 1, "description": "Duyulan geçmiş"},
    {"suffix": "muş", "tense": "past_reported", "priority": 1, "description": "Duyulan geçmiş"},
    {"suffix": "mış", "tense": "past_reported", "priority": 1, "description": "Duyulan geçmiş"},
    {"suffix": "müş", "tense": "past_reported", "priority": 1, "description": "Duyulan geçmiş"},
    
    # Gereklilik (-meli/-malı)
    {"suffix": "meli", "tense": "necessity", "priority": 1, "description": "Gereklilik"},
    {"suffix": "malı", "tense": "necessity", "priority": 1, "description": "Gereklilik"},
    
    # Yeterlilik (-ebil/-abil)
    {"suffix": "ebil", "tense": "ability", "priority": 1, "description": "Yeterlilik"},
    {"suffix": "abil", "tense": "ability", "priority": 1, "description": "Yeterlilik"},
]

# 9. PERSON SUFFIXES - Türkçe Şahıs Ekleri
PERSON_SUFFIXES_DATA = [

    # Şimdiki Zamanın Hikayesi için gerekli şahıs ekleri
    {"suffix": "m", "person": 1, "plurality": "singular", "tense": "past_continuous"},
    {"suffix": "n", "person": 2, "plurality": "singular", "tense": "past_continuous"},
    {"suffix": "", "person": 3, "plurality": "singular", "tense": "past_continuous"},
    {"suffix": "k", "person": 1, "plurality": "plural", "tense": "past_continuous"},
    {"suffix": "nuz", "person": 2, "plurality": "plural", "tense": "past_continuous"},
    {"suffix": "nüz", "person": 2, "plurality": "plural", "tense": "past_continuous"},
    {"suffix": "lar", "person": 3, "plurality": "plural", "tense": "past_continuous"},
    {"suffix": "ler", "person": 3, "plurality": "plural", "tense": "past_continuous"},



    # Şimdiki Zaman
    {"suffix": "um", "person": 1, "plurality": "singular", "tense": "present_continuous"},
    {"suffix": "sun", "person": 2, "plurality": "singular", "tense": "present_continuous"},
    {"suffix": "", "person": 3, "plurality": "singular", "tense": "present_continuous"},
    {"suffix": "uz", "person": 1, "plurality": "plural", "tense": "present_continuous"},
    {"suffix": "sunuz", "person": 2, "plurality": "plural", "tense": "present_continuous"},
    {"suffix": "lar", "person": 3, "plurality": "plural", "tense": "present_continuous"},
    {"suffix": "ler", "person": 3, "plurality": "plural", "tense": "present_continuous"},
    
    # Geçmiş Zaman
    {"suffix": "m", "person": 1, "plurality": "singular", "tense": "past_simple"},
    {"suffix": "n", "person": 2, "plurality": "singular", "tense": "past_simple"},
    {"suffix": "", "person": 3, "plurality": "singular", "tense": "past_simple"},
    {"suffix": "k", "person": 1, "plurality": "plural", "tense": "past_simple"},
    {"suffix": "niz", "person": 2, "plurality": "plural", "tense": "past_simple"},
    {"suffix": "lar", "person": 3, "plurality": "plural", "tense": "past_simple"},
    {"suffix": "ler", "person": 3, "plurality": "plural", "tense": "past_simple"},
    
    # Gelecek Zaman
    {"suffix": "im", "person": 1, "plurality": "singular", "tense": "future"},
    {"suffix": "sin", "person": 2, "plurality": "singular", "tense": "future"},
    {"suffix": "", "person": 3, "plurality": "singular", "tense": "future"},
    {"suffix": "iz", "person": 1, "plurality": "plural", "tense": "future"},
    {"suffix": "siniz", "person": 2, "plurality": "plural", "tense": "future"},
    {"suffix": "lar", "person": 3, "plurality": "plural", "tense": "future"},
    
    # Geniş Zaman (Ünlü uyumlu varyasyonlar)
    {"suffix": "im", "person": 1, "plurality": "singular", "tense": "aorist"},
    {"suffix": "ım", "person": 1, "plurality": "singular", "tense": "aorist"},
    {"suffix": "um", "person": 1, "plurality": "singular", "tense": "aorist"},
    {"suffix": "üm", "person": 1, "plurality": "singular", "tense": "aorist"},
    {"suffix": "sin", "person": 2, "plurality": "singular", "tense": "aorist"},
    {"suffix": "sın", "person": 2, "plurality": "singular", "tense": "aorist"},
    {"suffix": "sun", "person": 2, "plurality": "singular", "tense": "aorist"},
    {"suffix": "sün", "person": 2, "plurality": "singular", "tense": "aorist"},
    {"suffix": "", "person": 3, "plurality": "singular", "tense": "aorist"},
    {"suffix": "iz", "person": 1, "plurality": "plural", "tense": "aorist"},
    {"suffix": "ız", "person": 1, "plurality": "plural", "tense": "aorist"},
    {"suffix": "uz", "person": 1, "plurality": "plural", "tense": "aorist"},
    {"suffix": "üz", "person": 1, "plurality": "plural", "tense": "aorist"},
    {"suffix": "siniz", "person": 2, "plurality": "plural", "tense": "aorist"},
    {"suffix": "sınız", "person": 2, "plurality": "plural", "tense": "aorist"},
    {"suffix": "sunuz", "person": 2, "plurality": "plural", "tense": "aorist"},
    {"suffix": "sünüz", "person": 2, "plurality": "plural", "tense": "aorist"},
    {"suffix": "lar", "person": 3, "plurality": "plural", "tense": "aorist"},
    {"suffix": "ler", "person": 3, "plurality": "plural", "tense": "aorist"},
    
    # Gereklilik
    {"suffix": "yim", "person": 1, "plurality": "singular", "tense": "necessity"},
    {"suffix": "sin", "person": 2, "plurality": "singular", "tense": "necessity"},
    {"suffix": "", "person": 3, "plurality": "singular", "tense": "necessity"},
    {"suffix": "yiz", "person": 1, "plurality": "plural", "tense": "necessity"},
    {"suffix": "siniz", "person": 2, "plurality": "plural", "tense": "necessity"},
]

# 10. TURKISH IRREGULAR ROOTS - Türkçe Düzensiz Kök Değişimleri
# NOT: Bunlar kural-tabanlı açıklanabilir ama lookup için tutuluyor
TURKISH_IRREGULAR_ROOTS_DATA = [
    # Yemek fiili: ye → yi (şimdiki zamanda) - Kural: tek heceli ünlü ile biten fiiller
    {"alternate": "y", "canonical": "ye", "context": "present_continuous", "description": "ye→yi bağlayıcı ünlü düşmesi", "rule": "vowel_stem_contraction"},
    {"alternate": "yi", "canonical": "ye", "context": "general", "description": "ye→yi değişimi", "rule": "vowel_stem_contraction"},
    {"alternate": "yiy", "canonical": "ye", "context": "general", "description": "ye→yiy değişimi", "rule": "vowel_stem_buffer"},
    
    # Demek fiili: de → di - Kural: tek heceli ünlü ile biten fiiller
    {"alternate": "d", "canonical": "de", "context": "present_continuous", "description": "de→di bağlayıcı ünlü düşmesi", "rule": "vowel_stem_contraction"},
    {"alternate": "di", "canonical": "de", "context": "general", "description": "de→di değişimi", "rule": "vowel_stem_contraction"},
    {"alternate": "diy", "canonical": "de", "context": "general", "description": "de→diy değişimi", "rule": "vowel_stem_buffer"},
    
    # Gitmek: git → gid (yumuşama) - Kural: t→d before vowel
    {"alternate": "gid", "canonical": "git", "context": "before_vowel", "description": "t→d yumuşaması", "rule": "consonant_softening_t"},
    
    # Etmek: et → ed (yumuşama)
    {"alternate": "ed", "canonical": "et", "context": "before_vowel", "description": "t→d yumuşaması", "rule": "consonant_softening_t"},
    
    # Tatmak: tat → tad
    {"alternate": "tad", "canonical": "tat", "context": "before_vowel", "description": "t→d yumuşaması", "rule": "consonant_softening_t"},
    
    # Okumak: oku → okuy (ünlü kaynaşması) - Kural: ünlü+ünlü arası y kaynaştırma
    {"alternate": "okuy", "canonical": "oku", "context": "before_vowel", "description": "ünlü+yor kaynaşması", "rule": "buffer_y"},
    
    # Başlamak: başla → başlı (şimdiki zaman) - Kural: a→ı daralması -yor önünde
    {"alternate": "başlıy", "canonical": "başla", "context": "present_continuous", "description": "a→ı ünlü daralması", "rule": "vowel_narrowing_a"},
    
    # Anlamak: anla → anlı
    {"alternate": "anlıy", "canonical": "anla", "context": "present_continuous", "description": "a→ı ünlü daralması", "rule": "vowel_narrowing_a"},
    
    # Oynamak: oyna → oynu
    {"alternate": "oynuy", "canonical": "oyna", "context": "present_continuous", "description": "a→u ünlü daralması", "rule": "vowel_narrowing_a"},
]

# =============================================================================
# GENİŞ ZAMAN (AORİST) İSTİSNA FİİLLER - 13 Önemli Fiil
# =============================================================================
# Normalde tek heceli fiiller -ar/-er alır (yap-ar, çiz-er)
# AMA bu 13 fiil -ır/-ir/-ur/-ür alır

AORIST_IRREGULAR_VERBS_DATA = [
    # Bu 13 fiil tek heceli olmasına rağmen -ır/-ir/-ur/-ür alır
    {"root": "al", "aorist_suffix": "ır", "example": "alır", "en": "take", "note": "Tek heceli ama -ır alır"},
    {"root": "bil", "aorist_suffix": "ir", "example": "bilir", "en": "know", "note": "Tek heceli ama -ir alır"},
    {"root": "bul", "aorist_suffix": "ur", "example": "bulur", "en": "find", "note": "Tek heceli ama -ur alır"},
    {"root": "dur", "aorist_suffix": "ur", "example": "durur", "en": "stop/stand", "note": "Tek heceli ama -ur alır"},
    {"root": "gel", "aorist_suffix": "ir", "example": "gelir", "en": "come", "note": "Tek heceli ama -ir alır"},
    {"root": "gör", "aorist_suffix": "ür", "example": "görür", "en": "see", "note": "Tek heceli ama -ür alır"},
    {"root": "kal", "aorist_suffix": "ır", "example": "kalır", "en": "stay", "note": "Tek heceli ama -ır alır"},
    {"root": "ol", "aorist_suffix": "ur", "example": "olur", "en": "be/become", "note": "Tek heceli ama -ur alır"},
    {"root": "öl", "aorist_suffix": "ür", "example": "ölür", "en": "die", "note": "Tek heceli ama -ür alır"},
    {"root": "san", "aorist_suffix": "ır", "example": "sanır", "en": "think/assume", "note": "Tek heceli ama -ır alır"},
    {"root": "var", "aorist_suffix": "ır", "example": "varır", "en": "arrive", "note": "Tek heceli ama -ır alır"},
    {"root": "ver", "aorist_suffix": "ir", "example": "verir", "en": "give", "note": "Tek heceli ama -ir alır"},
    {"root": "vur", "aorist_suffix": "ur", "example": "vurur", "en": "hit", "note": "Tek heceli ama -ur alır"},
]

# =============================================================================
# ÜNLÜ UYUMU İSTİSNALARI (Alıntı Kelimeler / Loanwords)
# =============================================================================
# Arapça, Farsça, Fransızca kökenli kelimeler ünlü uyumunu bozar

VOWEL_HARMONY_EXCEPTIONS_DATA = [
    # Son hecesi kalın ünlü olmasına rağmen ince ek alan kelimeler
    {"word": "saat", "plural": "saatler", "wrong": "saatlar", "origin": "arabic", "exception_type": "plural"},
    {"word": "hayal", "plural": "hayaller", "wrong": "hayallar", "origin": "arabic", "exception_type": "plural"},
    {"word": "dikkat", "plural": "dikkatler", "wrong": "dikkatlar", "origin": "arabic", "exception_type": "plural"},
    {"word": "hareket", "plural": "hareketler", "wrong": "hareketlar", "origin": "arabic", "exception_type": "plural"},
    {"word": "rol", "plural": "roller", "wrong": "rollar", "origin": "french", "exception_type": "plural"},
    {"word": "gol", "plural": "goller", "wrong": "gollar", "origin": "english", "exception_type": "plural"},
    {"word": "alkol", "plural": "alkoller", "wrong": "alkollar", "origin": "arabic", "exception_type": "plural"},
    {"word": "kontrol", "plural": "kontroller", "wrong": "kontrollar", "origin": "french", "exception_type": "plural"},
    {"word": "petrol", "plural": "petroller", "wrong": "petrollar", "origin": "french", "exception_type": "plural"},
    {"word": "protokol", "plural": "protokoller", "wrong": "protokollar", "origin": "french", "exception_type": "plural"},
    {"word": "kalp", "possessive": "kalbi", "wrong": "kalbı", "origin": "arabic", "exception_type": "possessive"},
    {"word": "harf", "possessive": "harfi", "wrong": "harfı", "origin": "arabic", "exception_type": "possessive"},
]

# =============================================================================
# ÜNSÜZ YUMUŞAMASI İSTİSNALARI
# =============================================================================
# Normalde p,ç,t,k → b,c,d,ğ olur ama bazı kelimeler istisnadır

CONSONANT_MUTATION_EXCEPTIONS_DATA = [
    # Tek heceli kelimeler (yumuşama olmaz)
    {"word": "top", "with_suffix": "topu", "wrong": "tobu", "rule": "monosyllable", "description": "Tek heceli - yumuşama yok"},
    {"word": "et", "with_suffix": "eti", "wrong": "edi", "rule": "monosyllable", "description": "Tek heceli - yumuşama yok"},
    {"word": "at", "with_suffix": "atı", "wrong": "adı", "rule": "monosyllable", "description": "Tek heceli - yumuşama yok"},
    {"word": "ip", "with_suffix": "ipi", "wrong": "ibi", "rule": "monosyllable", "description": "Tek heceli - yumuşama yok"},
    {"word": "üç", "with_suffix": "üçü", "wrong": "ücü", "rule": "monosyllable", "description": "Tek heceli - yumuşama yok"},
    {"word": "saç", "with_suffix": "saçı", "wrong": "sacı", "rule": "monosyllable", "description": "Tek heceli - yumuşama yok"},
    {"word": "süt", "with_suffix": "sütü", "wrong": "südü", "rule": "monosyllable", "description": "Tek heceli - yumuşama yok"},
    {"word": "ok", "with_suffix": "oku", "wrong": "oğu", "rule": "monosyllable", "description": "Tek heceli - yumuşama yok"},
    
    # Yabancı kökenli kelimeler (yumuşama olmaz)
    {"word": "hukuk", "with_suffix": "hukuku", "wrong": "hukuğu", "rule": "loanword", "description": "Arapça - yumuşama yok"},
    {"word": "sanat", "with_suffix": "sanatı", "wrong": "sanadı", "rule": "loanword", "description": "Arapça - yumuşama yok"},
    {"word": "sepet", "with_suffix": "sepeti", "wrong": "sepedi", "rule": "loanword", "description": "Farsça - yumuşama yok"},
    {"word": "cumhuriyet", "with_suffix": "cumhuriyeti", "wrong": "cumhuriyedi", "rule": "loanword", "description": "Arapça - yumuşama yok"},
    {"word": "millet", "with_suffix": "milleti", "wrong": "milledi", "rule": "loanword", "description": "Arapça - yumuşama yok"},
    {"word": "devlet", "with_suffix": "devleti", "wrong": "devledi", "rule": "loanword", "description": "Arapça - yumuşama yok"},
    {"word": "merak", "with_suffix": "merakı", "wrong": "merağı", "rule": "loanword", "description": "Arapça - yumuşama yok"},
    {"word": "bisiklet", "with_suffix": "bisikleti", "wrong": "bisikledi", "rule": "loanword", "description": "Fransızca - yumuşama yok"},
    
    # Özel isimler
    {"word": "Ahmet", "with_suffix": "Ahmet'i", "wrong": "Ahmed'i", "rule": "proper_noun", "description": "Özel isim - yumuşama yok"},
    {"word": "Mehmet", "with_suffix": "Mehmet'i", "wrong": "Mehmed'i", "rule": "proper_noun", "description": "Özel isim - yumuşama yok"},
]

# =============================================================================
# ÜNLÜ DÜŞMESİ (Vowel Drop / Syncope)
# =============================================================================
# İkinci hecedeki dar ünlü, ünlü ile başlayan ek gelince düşer

VOWEL_DROP_DATA = [
    # İsimler - ünlü düşmesi olanlar
    {"base": "burun", "stem": "burn", "example_suffix": "u", "result": "burnu", "wrong": "burunu", "vowel_dropped": "u"},
    {"base": "ağız", "stem": "ağz", "example_suffix": "ı", "result": "ağzı", "wrong": "ağızı", "vowel_dropped": "ı"},
    {"base": "alın", "stem": "aln", "example_suffix": "ı", "result": "alnı", "wrong": "alını", "vowel_dropped": "ı"},
    {"base": "beyin", "stem": "beyn", "example_suffix": "i", "result": "beyni", "wrong": "beyini", "vowel_dropped": "i"},
    {"base": "boyun", "stem": "boyn", "example_suffix": "u", "result": "boynu", "wrong": "boyunu", "vowel_dropped": "u"},
    {"base": "karın", "stem": "karn", "example_suffix": "ı", "result": "karnı", "wrong": "karını", "vowel_dropped": "ı"},
    {"base": "göğüs", "stem": "göğs", "example_suffix": "ü", "result": "göğsü", "wrong": "göğüsü", "vowel_dropped": "ü"},
    {"base": "oğul", "stem": "oğl", "example_suffix": "u", "result": "oğlu", "wrong": "oğulu", "vowel_dropped": "u"},
    {"base": "şehir", "stem": "şehr", "example_suffix": "i", "result": "şehri", "wrong": "şehiri", "vowel_dropped": "i"},
    {"base": "nehir", "stem": "nehr", "example_suffix": "i", "result": "nehri", "wrong": "nehiri", "vowel_dropped": "i"},
    {"base": "ömür", "stem": "ömr", "example_suffix": "ü", "result": "ömrü", "wrong": "ömürü", "vowel_dropped": "ü"},
    {"base": "akıl", "stem": "akl", "example_suffix": "ı", "result": "aklı", "wrong": "akılı", "vowel_dropped": "ı"},
    {"base": "fikir", "stem": "fikr", "example_suffix": "i", "result": "fikri", "wrong": "fikiri", "vowel_dropped": "i"},
    {"base": "isim", "stem": "ism", "example_suffix": "i", "result": "ismi", "wrong": "isimi", "vowel_dropped": "i"},
    {"base": "kayın", "stem": "kayn", "example_suffix": "ı", "result": "kaynı", "wrong": "kayını", "vowel_dropped": "ı"},
    {"base": "zehir", "stem": "zehr", "example_suffix": "i", "result": "zehri", "wrong": "zehiri", "vowel_dropped": "i"},
    {"base": "çevir", "stem": "çevr", "example_suffix": "i", "result": "çevri", "wrong": "çeviri", "vowel_dropped": "i"},
    {"base": "devir", "stem": "devr", "example_suffix": "i", "result": "devri", "wrong": "deviri", "vowel_dropped": "i"},
    
    # Fiiller - ünlü düşmesi olanlar (bazı çekimlerde)
    {"base": "ayır", "stem": "ayr", "example_suffix": "ıl", "result": "ayrıl", "wrong": "ayırıl", "vowel_dropped": "ı", "type": "verb"},
    {"base": "çevir", "stem": "çevr", "example_suffix": "il", "result": "çevril", "wrong": "çeviril", "vowel_dropped": "i", "type": "verb"},
    {"base": "kavur", "stem": "kavr", "example_suffix": "ul", "result": "kavrul", "wrong": "kavurul", "vowel_dropped": "u", "type": "verb"},
    {"base": "savur", "stem": "savr", "example_suffix": "ul", "result": "savrul", "wrong": "savurul", "vowel_dropped": "u", "type": "verb"},
]

# 11. AUXILIARY VERBS - İngilizce Yardımcı Fiiller

# =============================================================================
# YENİ EKLERİN VERİ YAPILARI
# =============================================================================

# İSİM ÇEKİM EKLERİ (CASE SUFFIXES) - EN KRİTİK
# Yönelme, Bulunma, Ayrılma, Belirtme, Tamlayan
CASE_SUFFIXES_DATA = [
    # Yönelme Hali (Dative) - "to"
    {"case": "dative", "suffixes": ["e", "a", "ye", "ya"], "english_prep": "to",
     "harmony_type": "back_front", "description": "Eve git → Go to home",
     "examples": [{"tr": "eve", "en": "to the house", "base": "ev"}]},
    
    # Bulunma Hali (Locative) - "in/on/at"
    {"case": "locative", "suffixes": ["de", "da", "te", "ta"], "english_prep": "in/on/at",
     "harmony_type": "back_front_voiced", "description": "Evde → at home",
     "examples": [
         {"tr": "evde", "en": "at home", "base": "ev"},
         {"tr": "okulda", "en": "at school", "base": "okul"},
         {"tr": "parkta", "en": "in the park", "base": "park"}
     ]},
    
    # Ayrılma Hali (Ablative) - "from"
    {"case": "ablative", "suffixes": ["den", "dan", "ten", "tan"], "english_prep": "from",
     "harmony_type": "back_front_voiced", "description": "Evden → from home",
     "examples": [
         {"tr": "evden", "en": "from home", "base": "ev"},
         {"tr": "okuldan", "en": "from school", "base": "okul"}
     ]},
    
    # Belirtme Hali (Accusative) - "the" (definite object marker)
    {"case": "accusative", "suffixes": ["i", "ı", "u", "ü", "yi", "yı", "yu", "yü"],
     "english_prep": "the", "harmony_type": "fourfold",
     "description": "Kitabı oku → Read the book",
     "examples": [
         {"tr": "kitabı", "en": "the book (object)", "base": "kitap"},
         {"tr": "elmayı", "en": "the apple (object)", "base": "elma"}
     ]},
    
    # Tamlayan Hali (Genitive) - "of/'s"
    {"case": "genitive", "suffixes": ["in", "ın", "un", "ün", "nin", "nın", "nun", "nün"],
     "english_prep": "of", "harmony_type": "fourfold",
     "description": "Evin kapısı → The door of the house / The house's door",
     "examples": [
         {"tr": "evin", "en": "of the house", "base": "ev"},
         {"tr": "kapının", "en": "of the door", "base": "kapı"}
     ]},
    
    # Yalın Hal (Nominative) - subject marker, no suffix
    {"case": "nominative", "suffixes": [""], "english_prep": "",
     "harmony_type": "none", "description": "Ev güzel → The house is beautiful",
     "examples": [{"tr": "ev", "en": "house (subject)", "base": "ev"}]},
]

# İYELİK EKLERİ (POSSESSIVE SUFFIXES)
POSSESSIVE_SUFFIXES_DATA = [
    # 1. tekil şahıs - my
    {"person": 1, "plurality": "singular", "suffixes": ["im", "ım", "um", "üm", "m"],
     "english": "my", "harmony_type": "fourfold",
     "examples": [{"tr": "evim", "en": "my house", "base": "ev"}]},
    
    # 2. tekil şahıs - your
    {"person": 2, "plurality": "singular", "suffixes": ["in", "ın", "un", "ün", "n"],
     "english": "your", "harmony_type": "fourfold",
     "examples": [{"tr": "evin", "en": "your house", "base": "ev"}]},
    
    # 3. tekil şahıs - his/her/its (buffer: s/si)
    {"person": 3, "plurality": "singular", "suffixes": ["i", "ı", "u", "ü", "si", "sı", "su", "sü"],
     "english": "his/her/its", "harmony_type": "fourfold",
     "buffer_rule": "ünlü ile biten kelimelerde s kaynaştırma ünsüzü",
     "examples": [
         {"tr": "evi", "en": "his/her house", "base": "ev"},
         {"tr": "arabası", "en": "his/her car", "base": "araba"}
     ]},
    
    # 1. çoğul şahıs - our
    {"person": 1, "plurality": "plural", "suffixes": ["imiz", "ımız", "umuz", "ümüz", "miz", "mız", "muz", "müz"],
     "english": "our", "harmony_type": "fourfold",
     "examples": [{"tr": "evimiz", "en": "our house", "base": "ev"}]},
    
    # 2. çoğul şahıs - your (pl.)
    {"person": 2, "plurality": "plural", "suffixes": ["iniz", "ınız", "unuz", "ünüz", "niz", "nız", "nuz", "nüz"],
     "english": "your (pl.)", "harmony_type": "fourfold",
     "examples": [{"tr": "eviniz", "en": "your house", "base": "ev"}]},
    
    # 3. çoğul şahıs - their
    {"person": 3, "plurality": "plural", "suffixes": ["leri", "ları"],
     "english": "their", "harmony_type": "back_front",
     "examples": [{"tr": "evleri", "en": "their house", "base": "ev"}]},
]

# OLUMSUZLUK EKLERİ (NEGATION SUFFIXES)
NEGATION_SUFFIXES_DATA = [
    # Fiil olumsuzluğu - genel
    {"type": "verb_general", "suffixes": ["me", "ma"],
     "english_aux": "not", "harmony_type": "back_front",
     "description": "Gelme → Do not come / Not coming",
     "examples": [
         {"tr": "gelmedi", "en": "did not come", "base": "gel"},
         {"tr": "yapmıyor", "en": "is not doing", "base": "yap"}
     ]},
    
    # Geniş zaman olumsuzluğu
    {"type": "aorist_negative", "suffixes": ["mez", "maz"],
     "english_aux": "does not / do not", "harmony_type": "back_front",
     "description": "Yapmaz → He/She does not do",
     "examples": [
         {"tr": "yapmaz", "en": "does not do", "base": "yap"},
         {"tr": "gelmez", "en": "does not come", "base": "gel"}
     ]},
    
    # Gelecek zaman olumsuzluğu (özel durum)
    {"type": "future_negative", "suffixes": ["meyecek", "mayacak", "miyecek", "mıyacak", "muyacak", "müyecek"],
     "english_aux": "will not", "harmony_type": "fourfold",
     "description": "Gelmeyecek → Will not come",
     "examples": [{"tr": "gelmeyecek", "en": "will not come", "base": "gel"}]},
    
    # İsim/sıfat olumsuzluğu - değil
    {"type": "copula_negative", "word": "değil",
     "english_aux": "is not / am not / are not", 
     "conjugations": ["değilim", "değilsin", "değil", "değiliz", "değilsiniz", "değiller"],
     "description": "Evde değil → He is not at home",
     "examples": [
         {"tr": "güzel değil", "en": "is not beautiful"},
         {"tr": "öğrenci değilim", "en": "I am not a student"}
     ]},
    
    # Yokluk/Bulunmama - yok
    {"type": "existential_negative", "word": "yok",
     "english": "there is no / does not have",
     "opposite": "var",
     "description": "Param yok → I don't have money / There is no money",
     "examples": [
         {"tr": "evde yok", "en": "not at home"},
         {"tr": "arabam yok", "en": "I don't have a car"}
     ]},
]

# SORU EKLERİ (QUESTION PARTICLES)
QUESTION_PARTICLES_DATA = [
    {"suffixes": ["mı", "mi", "mu", "mü"],
     "harmony_type": "fourfold",
     "english_structure": "aux + subject + verb",
     "description": "Soru cümlesinde -mı/-mi eki ayrı yazılır",
     "examples": [
         {"tr": "Geldi mi?", "en": "Did he/she come?"},
         {"tr": "Güzel mi?", "en": "Is it beautiful?"},
         {"tr": "Gidiyor musun?", "en": "Are you going?"},
         {"tr": "Yapar mı?", "en": "Does he/she do?"}
     ]},
    # Ek-fiil ile birleşik soru
    {"suffixes": ["mıyım", "miyim", "muyum", "müyüm"],
     "person": 1, "plurality": "singular",
     "harmony_type": "fourfold",
     "description": "1. tekil şahıs soru",
     "examples": [{"tr": "Hasta mıyım?", "en": "Am I sick?"}]},
    {"suffixes": ["mısın", "misin", "musun", "müsün"],
     "person": 2, "plurality": "singular",
     "harmony_type": "fourfold",
     "description": "2. tekil şahıs soru",
     "examples": [{"tr": "Öğretmen misin?", "en": "Are you a teacher?"}]},
]

# EDATLAR (POSTPOSITIONS)
POSTPOSITIONS_DATA = [
    # Bitişik yazılan edatlar (-la/-le)
    {"tr": "ile", "suffixes": ["la", "le", "yla", "yle"],
     "english": "with/by", "type": "attached",
     "harmony_type": "back_front",
     "description": "Kelimeye bitişik veya ayrı yazılabilir",
     "examples": [
         {"tr": "seninle", "en": "with you", "attached": True},
         {"tr": "kalemle", "en": "with a pen", "attached": True},
         {"tr": "araba ile", "en": "by car", "attached": False}
     ]},
    
    # Ayrı yazılan edatlar
    {"tr": "için", "english": "for", "type": "separate",
     "case_required": "nominative",
     "examples": [{"tr": "senin için", "en": "for you"}]},
    
    {"tr": "kadar", "english": "until/as much as/up to", "type": "separate",
     "case_required": "dative",
     "examples": [
         {"tr": "akşama kadar", "en": "until evening"},
         {"tr": "benim kadar", "en": "as much as me"}
     ]},
    
    {"tr": "gibi", "english": "like/as", "type": "separate",
     "case_required": "nominative",
     "examples": [
         {"tr": "çocuk gibi", "en": "like a child"},
         {"tr": "su gibi", "en": "like water"}
     ]},
    
    {"tr": "göre", "english": "according to", "type": "separate",
     "case_required": "dative",
     "examples": [{"tr": "bana göre", "en": "according to me"}]},
    
    {"tr": "doğru", "english": "towards", "type": "separate",
     "case_required": "dative",
     "examples": [{"tr": "eve doğru", "en": "towards home"}]},
    
    {"tr": "karşı", "english": "against/opposite", "type": "separate",
     "case_required": "dative",
     "examples": [{"tr": "bana karşı", "en": "against me"}]},
    
    {"tr": "sonra", "english": "after", "type": "separate",
     "case_required": "ablative",
     "examples": [{"tr": "dersten sonra", "en": "after class"}]},
    
    {"tr": "önce", "english": "before", "type": "separate",
     "case_required": "ablative",
     "examples": [{"tr": "yemekten önce", "en": "before the meal"}]},
    
    {"tr": "beri", "english": "since", "type": "separate",
     "case_required": "ablative",
     "examples": [{"tr": "sabahtan beri", "en": "since morning"}]},
    
    {"tr": "rağmen", "english": "despite/although", "type": "separate",
     "case_required": "dative",
     "examples": [{"tr": "yağmura rağmen", "en": "despite the rain"}]},
]

# BAĞLAÇLAR (CONJUNCTIONS)
CONJUNCTIONS_DATA = [
    {"tr": "ve", "english": "and", "type": "coordinating",
     "position": "between", "examples": [{"tr": "sen ve ben", "en": "you and I"}]},
    
    {"tr": "ile", "english": "and/with", "type": "coordinating",
     "note": "Hem bağlaç hem edat olarak kullanılır",
     "examples": [{"tr": "Ali ile Ayşe", "en": "Ali and Ayşe"}]},
    
    {"tr": "ama", "english": "but", "type": "coordinating",
     "examples": [{"tr": "güzel ama pahalı", "en": "beautiful but expensive"}]},
    
    {"tr": "fakat", "english": "but/however", "type": "coordinating",
     "examples": [{"tr": "geldim fakat yoktun", "en": "I came but you were not there"}]},
    
    {"tr": "ancak", "english": "however/only", "type": "coordinating",
     "examples": [{"tr": "ancak yarın gelebilir", "en": "can only come tomorrow"}]},
    
    {"tr": "veya", "english": "or", "type": "coordinating",
     "examples": [{"tr": "çay veya kahve", "en": "tea or coffee"}]},
    
    {"tr": "ya da", "english": "or", "type": "coordinating",
     "examples": [{"tr": "gel ya da git", "en": "come or go"}]},
    
    {"tr": "çünkü", "english": "because", "type": "subordinating",
     "examples": [{"tr": "gelmedi çünkü hastaydı", "en": "didn't come because was sick"}]},
    
    {"tr": "zira", "english": "because/for", "type": "subordinating",
     "register": "formal",
     "examples": [{"tr": "yapamadım zira imkânsızdı", "en": "couldn't do it for it was impossible"}]},
    
    {"tr": "eğer", "english": "if", "type": "subordinating",
     "examples": [{"tr": "eğer gelirsen", "en": "if you come"}]},
    
    {"tr": "şayet", "english": "if", "type": "subordinating",
     "register": "formal",
     "examples": [{"tr": "şayet istersen", "en": "if you want"}]},
    
    {"tr": "ise", "english": "if/as for", "type": "subordinating",
     "note": "Genellikle kelimeye bitişik: 'buysa', 'giderse'",
     "examples": [{"tr": "o ise gelmedi", "en": "as for him, he didn't come"}]},
    
    {"tr": "ki", "english": "that/so that", "type": "subordinating",
     "examples": [{"tr": "biliyorum ki gelecek", "en": "I know that he will come"}]},
    
    {"tr": "hem...hem", "english": "both...and", "type": "correlative",
     "examples": [{"tr": "hem güzel hem akıllı", "en": "both beautiful and smart"}]},
    
    {"tr": "ne...ne", "english": "neither...nor", "type": "correlative",
     "examples": [{"tr": "ne çay ne kahve", "en": "neither tea nor coffee"}]},
    
    {"tr": "ya...ya", "english": "either...or", "type": "correlative",
     "examples": [{"tr": "ya gel ya git", "en": "either come or go"}]},
]

# EK-FİİL (COPULA SUFFIXES) - "To Be" karşılığı
COPULA_SUFFIXES_DATA = [
    # Şimdiki Zaman Ek-fiil
    {"person": 1, "plurality": "singular", "tense": "present",
     "suffixes": ["im", "ım", "um", "üm", "yim", "yım", "yum", "yüm"],
     "english": "am", "harmony_type": "fourfold",
     "examples": [
         {"tr": "öğrenciyim", "en": "I am a student", "base": "öğrenci"},
         {"tr": "hastayım", "en": "I am sick", "base": "hasta"}
     ]},
    
    {"person": 2, "plurality": "singular", "tense": "present",
     "suffixes": ["sin", "sın", "sun", "sün"],
     "english": "are", "harmony_type": "fourfold",
     "examples": [{"tr": "güzelsin", "en": "you are beautiful", "base": "güzel"}]},
    
    {"person": 3, "plurality": "singular", "tense": "present",
     "suffixes": ["dir", "dır", "dur", "dür", "tir", "tır", "tur", "tür", ""],
     "english": "is", "harmony_type": "fourfold_voiced",
     "note": "-dir genellikle konuşmada düşer: 'O öğrenci(dir)'",
     "examples": [
         {"tr": "güzeldir", "en": "is beautiful (formal)", "base": "güzel"},
         {"tr": "öğrenci", "en": "is a student (informal)", "base": "öğrenci"}
     ]},
    
    {"person": 1, "plurality": "plural", "tense": "present",
     "suffixes": ["iz", "ız", "uz", "üz", "yiz", "yız", "yuz", "yüz"],
     "english": "are", "harmony_type": "fourfold",
     "examples": [{"tr": "mutluyuz", "en": "we are happy", "base": "mutlu"}]},
    
    {"person": 2, "plurality": "plural", "tense": "present",
     "suffixes": ["siniz", "sınız", "sunuz", "sünüz"],
     "english": "are", "harmony_type": "fourfold",
     "examples": [{"tr": "öğrencisiniz", "en": "you are students", "base": "öğrenci"}]},
    
    {"person": 3, "plurality": "plural", "tense": "present",
     "suffixes": ["dirler", "dırlar", "durlar", "dürler", "tirler", "tırlar", "turlar", "türler", "ler", "lar"],
     "english": "are", "harmony_type": "fourfold_voiced",
     "examples": [{"tr": "öğrencilerdir", "en": "they are students", "base": "öğrenci"}]},
    
    # Geçmiş Zaman Ek-fiil (-di/-idi)
    {"person": 1, "plurality": "singular", "tense": "past",
     "suffixes": ["dim", "dım", "dum", "düm", "tim", "tım", "tum", "tüm", "ydim", "ydım", "ydum", "ydüm"],
     "english": "was", "harmony_type": "fourfold_voiced",
     "examples": [{"tr": "hastayım", "en": "I was sick", "base": "hasta"}]},
    
    {"person": 3, "plurality": "singular", "tense": "past",
     "suffixes": ["di", "dı", "du", "dü", "ti", "tı", "tu", "tü", "ydi", "ydı", "ydu", "ydü"],
     "english": "was", "harmony_type": "fourfold_voiced",
     "examples": [{"tr": "güzeldi", "en": "was beautiful", "base": "güzel"}]},
]

# ARTICLE KURALLARI (İngilizce a/an/the)
ARTICLE_RULES_DATA = [
    # Belirtme eki → the
    {"condition": "accusative_suffix", "article": "the",
     "description": "Türkçede belirtme eki (-i/-ı/-u/-ü) varsa → İngilizcede 'the'",
     "examples": [
         {"tr": "Kitabı okudum", "en": "I read the book"},
         {"tr": "Elmayı yedim", "en": "I ate the apple"}
     ]},
    
    # Belirtme eki yok → a/an
    {"condition": "no_accusative_suffix", "article": "a/an",
     "description": "Türkçede belirtme eki yoksa → İngilizcede 'a/an'",
     "examples": [
         {"tr": "Kitap okudum", "en": "I read a book"},
         {"tr": "Elma yedim", "en": "I ate an apple"}
     ]},
    
    # Sahiplik/Tamlama → the veya possessive
    {"condition": "possessive_construction", "article": "the/possessive",
     "description": "İyelik yapısı varsa → İngilizcede 'the' veya possessive",
     "examples": [
         {"tr": "Evin kapısı", "en": "the door of the house / the house's door"},
         {"tr": "Benim kitabım", "en": "my book"}
     ]},
    
    # Ünlü ile başlayan kelimeler → an
    {"condition": "vowel_initial", "article": "an",
     "vowels": ["a", "e", "i", "o", "u"],
     "description": "İngilizce kelime ünlü ile başlıyorsa 'an'",
     "examples": [
         {"en": "an apple"},
         {"en": "an egg"},
         {"en": "an umbrella"}
     ]},
    
    # Genel/soyut kavramlar
    {"condition": "generic_noun", "article": "no article/the",
     "description": "Genel kavramlar ve soyut isimler article almayabilir",
     "examples": [
         {"tr": "Su içiyorum", "en": "I am drinking water"},
         {"tr": "Aşk güzeldir", "en": "Love is beautiful"}
     ]},
]

# KAYNASTIRMA ÜNSÜZÜ İSTİSNALARI (Su, Ne vb.)
BUFFER_CONSONANT_EXCEPTIONS_DATA = [
    {"word": "su", "buffer_consonant": "y",
     "normal_rule": "n (tamlayan), s (iyelik)",
     "exception_cases": ["genitive", "possessive"],
     "description": "Su kelimesinde n yerine y gelir",
     "examples": [
         {"base": "su", "suffix": "genitive", "correct": "suyun", "wrong": "sunun"},
         {"base": "su", "suffix": "possessive_2sg", "correct": "suyun", "wrong": "sunun"},
         {"base": "su", "suffix": "dative", "correct": "suya", "wrong": "suna"}
     ]},
    
    {"word": "ne", "buffer_consonant": "y",
     "normal_rule": "n (tamlayan)",
     "exception_cases": ["genitive"],
     "description": "Ne kelimesinde n yerine y gelir",
     "examples": [
         {"base": "ne", "suffix": "genitive", "correct": "neyin", "wrong": "nenin"},
         {"base": "ne", "suffix": "dative", "correct": "neye", "wrong": "neye"}  # normal
     ]},
    
    # Bu, şu, o - işaret zamirleri
    {"word": "bu", "buffer_consonant": "n",
     "exception_cases": ["oblique_cases"],
     "description": "Bu zamiri: bunu, buna, bunun, bundan, bunda",
     "examples": [
         {"base": "bu", "suffix": "accusative", "result": "bunu"},
         {"base": "bu", "suffix": "dative", "result": "buna"},
         {"base": "bu", "suffix": "genitive", "result": "bunun"}
     ]},
    
    {"word": "şu", "buffer_consonant": "n",
     "exception_cases": ["oblique_cases"],
     "description": "Şu zamiri: şunu, şuna, şunun, şundan, şunda",
     "examples": [
         {"base": "şu", "suffix": "accusative", "result": "şunu"},
         {"base": "şu", "suffix": "dative", "result": "şuna"}
     ]},
    
    {"word": "o", "buffer_consonant": "n",
     "exception_cases": ["oblique_cases"],
     "description": "O zamiri: onu, ona, onun, ondan, onda",
     "examples": [
         {"base": "o", "suffix": "accusative", "result": "onu"},
         {"base": "o", "suffix": "dative", "result": "ona"},
         {"base": "o", "suffix": "genitive", "result": "onun"}
     ]},
]

# ÇOĞUL EKLERİ (PLURAL SUFFIXES)
PLURAL_SUFFIXES_DATA = [
    {"suffixes": ["ler", "lar"], "harmony_type": "back_front",
     "english_suffix": "s/es", "description": "Türkçe çoğul eki",
     "rules": {
         "back_vowels": ["a", "ı", "o", "u"],  # → -lar
         "front_vowels": ["e", "i", "ö", "ü"]   # → -ler
     },
     "examples": [
         {"tr": "evler", "en": "houses", "base": "ev"},
         {"tr": "kitaplar", "en": "books", "base": "kitap"},
         {"tr": "öğrenciler", "en": "students", "base": "öğrenci"},
         {"tr": "çocuklar", "en": "children", "base": "çocuk"}
     ]},
    
    # İstisna: ünlü uyumu bozulan kelimeler
    {"word_exceptions": [
         {"word": "saat", "plural": "saatler", "note": "Arapça - ince ek"},
         {"word": "hayal", "plural": "hayaller", "note": "Arapça - ince ek"},
         {"word": "rol", "plural": "roller", "note": "Fransızca - ince ek"},
         {"word": "gol", "plural": "goller", "note": "İngilizce - ince ek"}
     ],
     "rule": "loanword_exception",
     "description": "Yabancı kökenli kelimeler ünlü uyumuna uymaz"},
]

# İSİM KÖKLERİ (NOUN ROOTS)
NOUN_ROOTS_DATA = [
    # Ev/Mekan
    {"tr": "ev", "en": "house", "en_plural": "houses", "category": "place", "vowel_type": "front"},
    {"tr": "oda", "en": "room", "en_plural": "rooms", "category": "place", "vowel_type": "back"},
    {"tr": "okul", "en": "school", "en_plural": "schools", "category": "place", "vowel_type": "back"},
    {"tr": "hastane", "en": "hospital", "en_plural": "hospitals", "category": "place", "vowel_type": "front"},
    {"tr": "park", "en": "park", "en_plural": "parks", "category": "place", "vowel_type": "back"},
    {"tr": "şehir", "en": "city", "en_plural": "cities", "category": "place", "vowel_type": "front"},
    {"tr": "köy", "en": "village", "en_plural": "villages", "category": "place", "vowel_type": "front"},
    {"tr": "market", "en": "market", "en_plural": "markets", "category": "place", "vowel_type": "front"},
    {"tr": "bahçe", "en": "garden", "en_plural": "gardens", "category": "place", "vowel_type": "front"},
    {"tr": "mutfak", "en": "kitchen", "en_plural": "kitchens", "category": "place", "vowel_type": "back"},
    
    # Nesneler
    {"tr": "kitap", "en": "book", "en_plural": "books", "category": "object", "vowel_type": "back"},
    {"tr": "kalem", "en": "pen", "en_plural": "pens", "category": "object", "vowel_type": "front"},
    {"tr": "masa", "en": "table", "en_plural": "tables", "category": "object", "vowel_type": "back"},
    {"tr": "sandalye", "en": "chair", "en_plural": "chairs", "category": "object", "vowel_type": "front"},
    {"tr": "araba", "en": "car", "en_plural": "cars", "category": "object", "vowel_type": "back"},
    {"tr": "telefon", "en": "phone", "en_plural": "phones", "category": "object", "vowel_type": "back"},
    {"tr": "bilgisayar", "en": "computer", "en_plural": "computers", "category": "object", "vowel_type": "back"},
    {"tr": "kapı", "en": "door", "en_plural": "doors", "category": "object", "vowel_type": "back"},
    {"tr": "pencere", "en": "window", "en_plural": "windows", "category": "object", "vowel_type": "front"},
    {"tr": "anahtar", "en": "key", "en_plural": "keys", "category": "object", "vowel_type": "back"},
    
    # İnsanlar
    {"tr": "çocuk", "en": "child", "en_plural": "children", "category": "person", "vowel_type": "back"},
    {"tr": "adam", "en": "man", "en_plural": "men", "category": "person", "vowel_type": "back"},
    {"tr": "kadın", "en": "woman", "en_plural": "women", "category": "person", "vowel_type": "back"},
    {"tr": "öğrenci", "en": "student", "en_plural": "students", "category": "person", "vowel_type": "front"},
    {"tr": "öğretmen", "en": "teacher", "en_plural": "teachers", "category": "person", "vowel_type": "front"},
    {"tr": "doktor", "en": "doctor", "en_plural": "doctors", "category": "person", "vowel_type": "back"},
    {"tr": "arkadaş", "en": "friend", "en_plural": "friends", "category": "person", "vowel_type": "back"},
    {"tr": "anne", "en": "mother", "en_plural": "mothers", "category": "person", "vowel_type": "front"},
    {"tr": "baba", "en": "father", "en_plural": "fathers", "category": "person", "vowel_type": "back"},
    {"tr": "kardeş", "en": "sibling", "en_plural": "siblings", "category": "person", "vowel_type": "front"},
    
    # Hayvanlar
    {"tr": "kedi", "en": "cat", "en_plural": "cats", "category": "animal", "vowel_type": "front"},
    {"tr": "köpek", "en": "dog", "en_plural": "dogs", "category": "animal", "vowel_type": "front"},
    {"tr": "kuş", "en": "bird", "en_plural": "birds", "category": "animal", "vowel_type": "back"},
    {"tr": "balık", "en": "fish", "en_plural": "fish", "category": "animal", "vowel_type": "back"},
    {"tr": "at", "en": "horse", "en_plural": "horses", "category": "animal", "vowel_type": "back"},
    
    # Yiyecek/İçecek
    {"tr": "su", "en": "water", "en_plural": "waters", "category": "food", "vowel_type": "back"},
    {"tr": "ekmek", "en": "bread", "en_plural": "breads", "category": "food", "vowel_type": "front"},
    {"tr": "elma", "en": "apple", "en_plural": "apples", "category": "food", "vowel_type": "back"},
    {"tr": "yemek", "en": "food", "en_plural": "foods", "category": "food", "vowel_type": "front"},
    {"tr": "çay", "en": "tea", "en_plural": "teas", "category": "food", "vowel_type": "back"},
    {"tr": "kahve", "en": "coffee", "en_plural": "coffees", "category": "food", "vowel_type": "front"},
    
    # Soyut kavramlar
    {"tr": "iş", "en": "work", "en_plural": "works", "category": "abstract", "vowel_type": "front"},
    {"tr": "para", "en": "money", "en_plural": "money", "category": "abstract", "vowel_type": "back"},
    {"tr": "zaman", "en": "time", "en_plural": "times", "category": "abstract", "vowel_type": "back"},
    {"tr": "gün", "en": "day", "en_plural": "days", "category": "abstract", "vowel_type": "front"},
    {"tr": "yıl", "en": "year", "en_plural": "years", "category": "abstract", "vowel_type": "back"},
    {"tr": "ay", "en": "month", "en_plural": "months", "category": "abstract", "vowel_type": "back"},
    {"tr": "hafta", "en": "week", "en_plural": "weeks", "category": "abstract", "vowel_type": "back"},
    {"tr": "saat", "en": "hour", "en_plural": "hours", "category": "abstract", "vowel_type": "back"},
    
    # Vücut parçaları
    {"tr": "el", "en": "hand", "en_plural": "hands", "category": "body", "vowel_type": "front"},
    {"tr": "ayak", "en": "foot", "en_plural": "feet", "category": "body", "vowel_type": "back"},
    {"tr": "göz", "en": "eye", "en_plural": "eyes", "category": "body", "vowel_type": "front"},
    {"tr": "baş", "en": "head", "en_plural": "heads", "category": "body", "vowel_type": "back"},
    {"tr": "kalp", "en": "heart", "en_plural": "hearts", "category": "body", "vowel_type": "back"},
]

AUXILIARY_VERBS_DATA = [

     # --- Past Continuous (Was/Were) ---
    {"tense": "past_continuous", "person": 1, "plurality": "singular", "negation": False, "auxiliary": "was"},
    {"tense": "past_continuous", "person": 3, "plurality": "singular", "negation": False, "auxiliary": "was"},
    {"tense": "past_continuous", "person": 1, "plurality": "singular", "negation": True, "auxiliary": "was not"},
    {"tense": "past_continuous", "person": 3, "plurality": "singular", "negation": True, "auxiliary": "was not"},
    {"tense": "past_continuous", "person": 2, "plurality": "singular", "negation": False, "auxiliary": "were"},
    {"tense": "past_continuous", "person": None, "plurality": "plural", "negation": False, "auxiliary": "were"}, # Genel çoğul
    {"tense": "past_continuous", "person": 2, "plurality": "singular", "negation": True, "auxiliary": "were not"},
    {"tense": "past_continuous", "person": None, "plurality": "plural", "negation": True, "auxiliary": "were not"},



    # Present Continuous
    {"tense": "present_continuous", "person": 1, "plurality": "singular", "negation": False, "auxiliary": "am"},
    {"tense": "present_continuous", "person": 2, "plurality": "singular", "negation": False, "auxiliary": "are"},
    {"tense": "present_continuous", "person": 3, "plurality": "singular", "negation": False, "auxiliary": "is"},
    {"tense": "present_continuous", "person": 1, "plurality": "plural", "negation": False, "auxiliary": "are"},
    {"tense": "present_continuous", "person": 2, "plurality": "plural", "negation": False, "auxiliary": "are"},
    {"tense": "present_continuous", "person": 3, "plurality": "plural", "negation": False, "auxiliary": "are"},
    
    {"tense": "present_continuous", "person": 1, "plurality": "singular", "negation": True, "auxiliary": "am not"},
    {"tense": "present_continuous", "person": 2, "plurality": "singular", "negation": True, "auxiliary": "are not"},
    {"tense": "present_continuous", "person": 3, "plurality": "singular", "negation": True, "auxiliary": "is not"},
    {"tense": "present_continuous", "person": 1, "plurality": "plural", "negation": True, "auxiliary": "are not"},
    {"tense": "present_continuous", "person": 2, "plurality": "plural", "negation": True, "auxiliary": "are not"},
    {"tense": "present_continuous", "person": 3, "plurality": "plural", "negation": True, "auxiliary": "are not"},
    
    # Future
    {"tense": "future", "person": None, "plurality": None, "negation": False, "auxiliary": "will"},
    {"tense": "future", "person": None, "plurality": None, "negation": True, "auxiliary": "will not"},
    
    # Past Simple (olumsuz için)
    {"tense": "past_simple", "person": None, "plurality": None, "negation": True, "auxiliary": "did not"},
    
    # Present Simple / Aorist (olumsuz için)
    {"tense": "aorist", "person": 1, "plurality": "singular", "negation": True, "auxiliary": "do not"},
    {"tense": "aorist", "person": 2, "plurality": "singular", "negation": True, "auxiliary": "do not"},
    {"tense": "aorist", "person": 3, "plurality": "singular", "negation": True, "auxiliary": "does not"},
    {"tense": "aorist", "person": 1, "plurality": "plural", "negation": True, "auxiliary": "do not"},
    {"tense": "aorist", "person": 2, "plurality": "plural", "negation": True, "auxiliary": "do not"},
    {"tense": "aorist", "person": 3, "plurality": "plural", "negation": True, "auxiliary": "do not"},
    
    # Past Reported
    {"tense": "past_reported", "person": 1, "plurality": "singular", "negation": False, "auxiliary": "have"},
    {"tense": "past_reported", "person": 2, "plurality": "singular", "negation": False, "auxiliary": "have"},
    {"tense": "past_reported", "person": 3, "plurality": "singular", "negation": False, "auxiliary": "has"},
    {"tense": "past_reported", "person": 1, "plurality": "plural", "negation": False, "auxiliary": "have"},
    {"tense": "past_reported", "person": 3, "plurality": "singular", "negation": True, "auxiliary": "has not"},
    {"tense": "past_reported", "person": 1, "plurality": "singular", "negation": True, "auxiliary": "have not"},
    
    # Necessity
    {"tense": "necessity", "person": None, "plurality": None, "negation": False, "auxiliary": "should"},
    {"tense": "necessity", "person": None, "plurality": None, "negation": True, "auxiliary": "should not"},
    
    # Ability
    {"tense": "ability", "person": None, "plurality": None, "negation": False, "auxiliary": "can"},
    {"tense": "ability", "person": None, "plurality": None, "negation": True, "auxiliary": "cannot"},
]

# =============================================================================
# FONOLOJİ KURALLARI (SES BİLGİSİ)
# =============================================================================

# 12. PHONOLOGY RULES - Türkçe ve İngilizce Ses Bilgisi Kuralları
PHONOLOGY_RULES_DATA = [
    # =========================================================================
    # TÜRKÇE FONOLOJİ KURALLARI
    # =========================================================================
    
    # --- Büyük Ünlü Uyumu (Kalınlık-İncelik) ---
    {
        "language": "turkish",
        "rule_name": "buyuk_unlu_uyumu_back",
        "rule_type": "vowel_harmony",
        "context": "suffix_attachment",
        "condition": {"last_vowel": ["a", "ı", "o", "u"]},
        "action": {"select_suffix_vowel": {"e": "a", "i": "ı"}},
        "priority": 100,
        "description": "Kalın ünlülerden sonra kalın ünlü gelir (a/ı seçimi)"
    },
    {
        "language": "turkish",
        "rule_name": "buyuk_unlu_uyumu_front",
        "rule_type": "vowel_harmony",
        "context": "suffix_attachment",
        "condition": {"last_vowel": ["e", "i", "ö", "ü"]},
        "action": {"select_suffix_vowel": {"a": "e", "ı": "i"}},
        "priority": 100,
        "description": "İnce ünlülerden sonra ince ünlü gelir (e/i seçimi)"
    },
    
    # --- Küçük Ünlü Uyumu (Düzlük-Yuvarlaklık) ---
    {
        "language": "turkish",
        "rule_name": "kucuk_unlu_uyumu_rounded",
        "rule_type": "vowel_harmony",
        "context": "suffix_attachment",
        "condition": {"last_vowel": ["o", "u", "ö", "ü"]},
        "action": {"select_suffix_vowel": {"ı": "u", "i": "ü"}},
        "priority": 90,
        "description": "Yuvarlak ünlülerden sonra yuvarlak ünlü (u/ü seçimi)"
    },
    {
        "language": "turkish",
        "rule_name": "kucuk_unlu_uyumu_unrounded",
        "rule_type": "vowel_harmony",
        "context": "suffix_attachment",
        "condition": {"last_vowel": ["a", "e", "ı", "i"]},
        "action": {"select_suffix_vowel": {"u": "ı", "ü": "i"}},
        "priority": 90,
        "description": "Düz ünlülerden sonra düz ünlü (ı/i seçimi)"
    },
    
    # --- Ünsüz Yumuşaması (p, ç, t, k → b, c, d, ğ) ---
    {
        "language": "turkish",
        "rule_name": "unsuz_yumusamasi_p",
        "rule_type": "consonant_softening",
        "context": "before_vowel",
        "condition": {"final_consonant": "p", "following": "vowel"},
        "action": {"replace": {"from": "p", "to": "b"}},
        "priority": 80,
        "description": "p → b yumuşaması (kitap → kitabı)"
    },
    {
        "language": "turkish",
        "rule_name": "unsuz_yumusamasi_c",
        "rule_type": "consonant_softening",
        "context": "before_vowel",
        "condition": {"final_consonant": "ç", "following": "vowel"},
        "action": {"replace": {"from": "ç", "to": "c"}},
        "priority": 80,
        "description": "ç → c yumuşaması (ağaç → ağacı)"
    },
    {
        "language": "turkish",
        "rule_name": "unsuz_yumusamasi_t",
        "rule_type": "consonant_softening",
        "context": "before_vowel",
        "condition": {"final_consonant": "t", "following": "vowel"},
        "action": {"replace": {"from": "t", "to": "d"}},
        "priority": 80,
        "description": "t → d yumuşaması (git → gidiyor)"
    },
    {
        "language": "turkish",
        "rule_name": "unsuz_yumusamasi_k",
        "rule_type": "consonant_softening",
        "context": "before_vowel",
        "condition": {"final_consonant": "k", "following": "vowel"},
        "action": {"replace": {"from": "k", "to": "ğ"}},
        "priority": 80,
        "description": "k → ğ yumuşaması (bebek → bebeği)"
    },
    
    # --- Ünsüz Benzeşmesi (Sertleşme) ---
    {
        "language": "turkish",
        "rule_name": "unsuz_benzesmesi_t",
        "rule_type": "consonant_assimilation",
        "context": "suffix_attachment",
        "condition": {"final_consonant": ["p", "ç", "t", "k", "f", "h", "s", "ş"]},
        "action": {"select_suffix_consonant": {"d": "t", "c": "ç"}},
        "priority": 85,
        "description": "Sert ünsüzlerden sonra ek sertleşir (-di → -ti)"
    },
    
    # --- Kaynaştırma Ünsüzleri ---
    {
        "language": "turkish",
        "rule_name": "kaynastirma_y",
        "rule_type": "buffer_consonant",
        "context": "vowel_vowel",
        "condition": {"ends_with": "vowel", "suffix_starts": "vowel"},
        "action": {"insert": "y"},
        "priority": 70,
        "description": "İki ünlü arasına 'y' kaynaştırma ünsüzü (oku + yor → okuy + or)"
    },
    {
        "language": "turkish",
        "rule_name": "kaynastirma_n",
        "rule_type": "buffer_consonant",
        "context": "possessive",
        "condition": {"ends_with": "vowel", "suffix_type": "possessive_3rd"},
        "action": {"insert": "n"},
        "priority": 70,
        "description": "3. şahıs iyelik ekinden önce 'n' (kapı + ı → kapısı + n + ın)"
    },
    {
        "language": "turkish",
        "rule_name": "kaynastirma_s",
        "rule_type": "buffer_consonant",
        "context": "possessive",
        "condition": {"ends_with": "vowel", "suffix_type": "possessive"},
        "action": {"insert": "s"},
        "priority": 70,
        "description": "İyelik ekinden önce 's' (baba + ı → babasını)"
    },
    
    # --- Ünlü Düşmesi ---
    {
        "language": "turkish",
        "rule_name": "unlu_dusmesi",
        "rule_type": "vowel_drop",
        "context": "suffix_attachment",
        "condition": {"syllable_pattern": "CVC", "second_vowel_unstable": True},
        "action": {"drop_vowel": "second"},
        "priority": 75,
        "description": "İkinci hece ünlüsü düşer (burun → burnu, oğul → oğlu)"
    },
    
    # --- Ünlü Daralması (a/e → ı/i/u/ü + yor) ---
    {
        "language": "turkish",
        "rule_name": "unlu_daralmasi_a",
        "rule_type": "vowel_narrowing",
        "context": "before_yor",
        "condition": {"ends_with": "a", "following_suffix": "yor"},
        "action": {"replace": {"from": "a", "to": "ı"}},
        "priority": 95,
        "description": "a → ı daralması -yor önünde (başla + yor → başlıyor)"
    },
    {
        "language": "turkish",
        "rule_name": "unlu_daralmasi_e",
        "rule_type": "vowel_narrowing",
        "context": "before_yor",
        "condition": {"ends_with": "e", "following_suffix": "yor"},
        "action": {"replace": {"from": "e", "to": "i"}},
        "priority": 95,
        "description": "e → i daralması -yor önünde (bekle + yor → bekliyor)"
    },
    
    # =========================================================================
    # İNGİLİZCE FONOLOJİ KURALLARI
    # =========================================================================
    
    # --- CVC Ünsüz İkilemesi (-ing/-ed) ---
    {
        "language": "english",
        "rule_name": "cvc_doubling_ing",
        "rule_type": "consonant_doubling",
        "context": "suffix_ing",
        "condition": {
            "pattern": "CVC",
            "final_consonant": ["b", "d", "g", "l", "m", "n", "p", "r", "t"],
            "stressed_final": True,
            "not_ending": ["w", "x", "y"]
        },
        "action": {"double_final_consonant": True},
        "priority": 80,
        "description": "CVC kalıbında son ünsüz ikilemesi (run → running, sit → sitting)"
    },
    {
        "language": "english",
        "rule_name": "cvc_doubling_ed",
        "rule_type": "consonant_doubling",
        "context": "suffix_ed",
        "condition": {
            "pattern": "CVC",
            "final_consonant": ["b", "d", "g", "m", "n", "p", "t"],
            "stressed_final": True
        },
        "action": {"double_final_consonant": True},
        "priority": 80,
        "description": "CVC kalıbında son ünsüz ikilemesi (stop → stopped)"
    },
    
    # --- Sessiz-e Düşmesi ---
    {
        "language": "english",
        "rule_name": "silent_e_drop_ing",
        "rule_type": "vowel_drop",
        "context": "suffix_ing",
        "condition": {"ends_with": "e", "preceded_by": "consonant"},
        "action": {"drop_final": "e"},
        "priority": 85,
        "description": "Sessiz -e düşer -ing önünde (make → making, write → writing)"
    },
    {
        "language": "english",
        "rule_name": "silent_e_drop_ed",
        "rule_type": "vowel_drop",
        "context": "suffix_ed",
        "condition": {"ends_with": "e"},
        "action": {"drop_final": "e", "suffix": "d"},
        "priority": 85,
        "description": "Sessiz -e düşer -ed olur -d (love → loved, hope → hoped)"
    },
    
    # --- -ie → -ying ---
    {
        "language": "english",
        "rule_name": "ie_to_ying",
        "rule_type": "vowel_change",
        "context": "suffix_ing",
        "condition": {"ends_with": "ie"},
        "action": {"replace": {"from": "ie", "to": "y"}},
        "priority": 90,
        "description": "-ie → -ying dönüşümü (lie → lying, die → dying)"
    },
    
    # --- -y → -ied (ünsüz + y) ---
    {
        "language": "english",
        "rule_name": "y_to_ied",
        "rule_type": "vowel_change",
        "context": "suffix_ed",
        "condition": {"ends_with": "y", "preceded_by": "consonant"},
        "action": {"replace": {"from": "y", "to": "i"}},
        "priority": 85,
        "description": "Ünsüz + y → ied (carry → carried, try → tried)"
    },
    
    # --- -y → -ies (3. şahıs) ---
    {
        "language": "english",
        "rule_name": "y_to_ies",
        "rule_type": "vowel_change",
        "context": "third_person",
        "condition": {"ends_with": "y", "preceded_by": "consonant"},
        "action": {"replace": {"from": "y", "to": "ie"}, "add": "s"},
        "priority": 85,
        "description": "Ünsüz + y → ies (carry → carries, fly → flies)"
    },
    
    # --- -s/-es 3. şahıs kuralları ---
    {
        "language": "english",
        "rule_name": "es_after_sibilant",
        "rule_type": "suffix_selection",
        "context": "third_person",
        "condition": {"ends_with": ["s", "ss", "sh", "ch", "x", "z"]},
        "action": {"add_suffix": "es"},
        "priority": 80,
        "description": "Sibilant sonrası -es eklenir (watch → watches, pass → passes)"
    },
    {
        "language": "english",
        "rule_name": "s_default",
        "rule_type": "suffix_selection",
        "context": "third_person",
        "condition": {"default": True},
        "action": {"add_suffix": "s"},
        "priority": 70,
        "description": "Varsayılan 3. şahıs -s eki (run → runs, play → plays)"
    },
    
    # --- -ed Telaffuz Kuralları ---
    {
        "language": "english",
        "rule_name": "ed_id_pronunciation",
        "rule_type": "pronunciation",
        "context": "past_participle",
        "condition": {"ends_with": ["t", "d"]},
        "action": {"pronunciation": "/ɪd/"},
        "priority": 75,
        "description": "-ed /ɪd/ olarak okunur (wanted, needed)"
    },
    {
        "language": "english",
        "rule_name": "ed_t_pronunciation",
        "rule_type": "pronunciation",
        "context": "past_participle",
        "condition": {"ends_with_voiceless": ["p", "k", "f", "s", "ʃ", "tʃ"]},
        "action": {"pronunciation": "/t/"},
        "priority": 75,
        "description": "-ed /t/ olarak okunur (stopped, looked)"
    },
    {
        "language": "english",
        "rule_name": "ed_d_pronunciation",
        "rule_type": "pronunciation",
        "context": "past_participle",
        "condition": {"ends_with_voiced": True},
        "action": {"pronunciation": "/d/"},
        "priority": 75,
        "description": "-ed /d/ olarak okunur (played, loved)"
    },
]


# =============================================================================
# MONGODB İŞLEMLERİ
# =============================================================================

class MongoDBSetup:
    def __init__(self, uri: str = MONGO_URI, db_name: str = DB_NAME):
        self.uri = uri
        self.db_name = db_name
        self.client = None
        self.db = None
    
    def connect(self) -> bool:
        """MongoDB'ye bağlan."""
        if not PYMONGO_AVAILABLE:
            print("[HATA] pymongo yüklü değil!")
            return False
        
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            # Bağlantıyı test et
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            print(f"[OK] MongoDB'ye bağlandı: {self.uri}")
            print(f"[OK] Veritabanı: {self.db_name}")
            return True
        except ConnectionFailure as e:
            print(f"[HATA] MongoDB bağlantı hatası: {e}")
            print("[İPUCU] MongoDB servisinin çalıştığından emin olun:")
            print("        Windows: net start MongoDB")
            print("        Linux: sudo systemctl start mongod")
            return False
    
    def clear_all(self):
        """Tüm koleksiyonları temizle."""
        if self.db is None:
            print("[HATA] Önce bağlantı kurun!")
            return
        
        for name in COLLECTIONS.values():
            result = self.db[name].delete_many({})
            print(f"[TEMIZLIK] {name}: {result.deleted_count} kayıt silindi")
    
    def create_indexes(self):
        """Gerekli indexleri oluştur."""
        if self.db is None:
            return
        
        # Words koleksiyonu için index
        self.db[COLLECTIONS["words"]].create_index("tr_ascii", unique=True)
        self.db[COLLECTIONS["words"]].create_index("tr")
        
        # Collocations için bileşik index
        self.db[COLLECTIONS["collocations"]].create_index([("word1", 1), ("word2", 1)])
        
        # Semantic rules için index
        self.db[COLLECTIONS["semantic_rules"]].create_index([("subject_class", 1), ("verb_class", 1)])
        
        # Ngrams için index
        self.db[COLLECTIONS["ngrams"]].create_index("words")
        
        print("[OK] Indexler oluşturuldu")
    
    def insert_words(self):
        """Kelimeleri yükle."""
        col = self.db[COLLECTIONS["words"]]
        for word in WORDS_DATA:
            word["created_at"] = datetime.utcnow()
            word["updated_at"] = datetime.utcnow()
        
        result = col.insert_many(WORDS_DATA)
        print(f"[OK] Words: {len(result.inserted_ids)} kelime eklendi")
    
    def insert_collocations(self):
        """Eşdizimlikleri yükle."""
        col = self.db[COLLECTIONS["collocations"]]
        for coll in COLLOCATIONS_DATA:
            coll["created_at"] = datetime.utcnow()
        
        result = col.insert_many(COLLOCATIONS_DATA)
        print(f"[OK] Collocations: {len(result.inserted_ids)} eşdizimlilik eklendi")
    
    def insert_semantic_rules(self):
        """Anlam kurallarını yükle."""
        col = self.db[COLLECTIONS["semantic_rules"]]
        for rule in SEMANTIC_RULES_DATA:
            rule["created_at"] = datetime.utcnow()
        
        result = col.insert_many(SEMANTIC_RULES_DATA)
        print(f"[OK] Semantic Rules: {len(result.inserted_ids)} kural eklendi")
    
    def insert_ngrams(self):
        """N-gramları yükle."""
        col = self.db[COLLECTIONS["ngrams"]]
        for ngram in NGRAMS_DATA:
            ngram["created_at"] = datetime.utcnow()
        
        result = col.insert_many(NGRAMS_DATA)
        print(f"[OK] N-grams: {len(result.inserted_ids)} n-gram eklendi")
    
    def insert_grammar_rules(self):
        """Dilbilgisi kurallarını yükle."""
        col = self.db[COLLECTIONS["grammar_rules"]]
        for rule in GRAMMAR_RULES_DATA:
            rule["created_at"] = datetime.utcnow()
        
        result = col.insert_many(GRAMMAR_RULES_DATA)
        print(f"[OK] Grammar Rules: {len(result.inserted_ids)} kural eklendi")
    
    def insert_verb_roots(self):
        """Fiil köklerini yükle."""
        col = self.db[COLLECTIONS["verb_roots"]]
        for root in VERB_ROOTS_DATA:
            root["created_at"] = datetime.utcnow()
        
        result = col.insert_many(VERB_ROOTS_DATA)
        print(f"[OK] Verb Roots: {len(result.inserted_ids)} fiil kökü eklendi")
    
    def insert_irregular_verbs(self):
        """İngilizce düzensiz fiilleri yükle."""
        col = self.db[COLLECTIONS["irregular_verbs"]]
        for verb in IRREGULAR_VERBS_DATA:
            verb["created_at"] = datetime.utcnow()
        
        result = col.insert_many(IRREGULAR_VERBS_DATA)
        print(f"[OK] Irregular Verbs: {len(result.inserted_ids)} düzensiz fiil eklendi")
    
    def insert_tense_suffixes(self):
        """Türkçe zaman eklerini yükle."""
        col = self.db[COLLECTIONS["tense_suffixes"]]
        for suffix in TENSE_SUFFIXES_DATA:
            suffix["created_at"] = datetime.utcnow()
        
        result = col.insert_many(TENSE_SUFFIXES_DATA)
        print(f"[OK] Tense Suffixes: {len(result.inserted_ids)} zaman eki eklendi")
    
    def insert_person_suffixes(self):
        """Türkçe şahıs eklerini yükle."""
        col = self.db[COLLECTIONS["person_suffixes"]]
        for suffix in PERSON_SUFFIXES_DATA:
            suffix["created_at"] = datetime.utcnow()
        
        result = col.insert_many(PERSON_SUFFIXES_DATA)
        print(f"[OK] Person Suffixes: {len(result.inserted_ids)} şahıs eki eklendi")
    
    def insert_turkish_irregular_roots(self):
        """Türkçe düzensiz kök değişimlerini yükle."""
        col = self.db[COLLECTIONS["turkish_irregular_roots"]]
        for root in TURKISH_IRREGULAR_ROOTS_DATA:
            root["created_at"] = datetime.utcnow()
        
        result = col.insert_many(TURKISH_IRREGULAR_ROOTS_DATA)
        print(f"[OK] Turkish Irregular Roots: {len(result.inserted_ids)} kök değişimi eklendi")
    
    def insert_auxiliary_verbs(self):
        """İngilizce yardımcı fiilleri yükle."""
        col = self.db[COLLECTIONS["auxiliary_verbs"]]
        for verb in AUXILIARY_VERBS_DATA:
            verb["created_at"] = datetime.utcnow()
        
        result = col.insert_many(AUXILIARY_VERBS_DATA)
        print(f"[OK] Auxiliary Verbs: {len(result.inserted_ids)} yardımcı fiil eklendi")
    
    def insert_phonology_rules(self):
        """Fonoloji kurallarını yükle."""
        col = self.db[COLLECTIONS["phonology_rules"]]
        for rule in PHONOLOGY_RULES_DATA:
            rule["created_at"] = datetime.utcnow()
        
        result = col.insert_many(PHONOLOGY_RULES_DATA)
        print(f"[OK] Phonology Rules: {len(result.inserted_ids)} fonoloji kuralı eklendi")
    
    def insert_aorist_irregular_verbs(self):
        """Geniş zaman istisna fiillerini yükle (13 önemli fiil)."""
        col = self.db[COLLECTIONS["aorist_irregular_verbs"]]
        for verb in AORIST_IRREGULAR_VERBS_DATA:
            verb["created_at"] = datetime.utcnow()
        
        result = col.insert_many(AORIST_IRREGULAR_VERBS_DATA)
        print(f"[OK] Aorist Irregular Verbs: {len(result.inserted_ids)} geniş zaman istisna fiili eklendi")
    
    def insert_vowel_harmony_exceptions(self):
        """Ünlü uyumu istisnalarını yükle (alıntı kelimeler)."""
        col = self.db[COLLECTIONS["vowel_harmony_exceptions"]]
        for word in VOWEL_HARMONY_EXCEPTIONS_DATA:
            word["created_at"] = datetime.utcnow()
        
        result = col.insert_many(VOWEL_HARMONY_EXCEPTIONS_DATA)
        print(f"[OK] Vowel Harmony Exceptions: {len(result.inserted_ids)} ünlü uyumu istisnası eklendi")
    
    def insert_consonant_mutation_exceptions(self):
        """Ünsüz yumuşaması istisnalarını yükle."""
        col = self.db[COLLECTIONS["consonant_mutation_exceptions"]]
        for word in CONSONANT_MUTATION_EXCEPTIONS_DATA:
            word["created_at"] = datetime.utcnow()
        
        result = col.insert_many(CONSONANT_MUTATION_EXCEPTIONS_DATA)
        print(f"[OK] Consonant Mutation Exceptions: {len(result.inserted_ids)} ünsüz yumuşaması istisnası eklendi")
    
    def insert_vowel_drop_words(self):
        """Ünlü düşmesi olan kelimeleri yükle."""
        col = self.db[COLLECTIONS["vowel_drop_words"]]
        for word in VOWEL_DROP_DATA:
            word["created_at"] = datetime.utcnow()
        
        result = col.insert_many(VOWEL_DROP_DATA)
        print(f"[OK] Vowel Drop Words: {len(result.inserted_ids)} ünlü düşmesi kelimesi eklendi")
    
    def insert_case_suffixes(self):
        """İsim çekim eklerini yükle."""
        col = self.db[COLLECTIONS["case_suffixes"]]
        for suffix in CASE_SUFFIXES_DATA:
            suffix["created_at"] = datetime.utcnow()
        
        result = col.insert_many(CASE_SUFFIXES_DATA)
        print(f"[OK] Case Suffixes: {len(result.inserted_ids)} isim çekim eki eklendi")
    
    def insert_possessive_suffixes(self):
        """İyelik eklerini yükle."""
        col = self.db[COLLECTIONS["possessive_suffixes"]]
        for suffix in POSSESSIVE_SUFFIXES_DATA:
            suffix["created_at"] = datetime.utcnow()
        
        result = col.insert_many(POSSESSIVE_SUFFIXES_DATA)
        print(f"[OK] Possessive Suffixes: {len(result.inserted_ids)} iyelik eki eklendi")
    
    def insert_negation_suffixes(self):
        """Olumsuzluk eklerini yükle."""
        col = self.db[COLLECTIONS["negation_suffixes"]]
        for suffix in NEGATION_SUFFIXES_DATA:
            suffix["created_at"] = datetime.utcnow()
        
        result = col.insert_many(NEGATION_SUFFIXES_DATA)
        print(f"[OK] Negation Suffixes: {len(result.inserted_ids)} olumsuzluk eki eklendi")
    
    def insert_question_particles(self):
        """Soru eklerini yükle."""
        col = self.db[COLLECTIONS["question_particles"]]
        for particle in QUESTION_PARTICLES_DATA:
            particle["created_at"] = datetime.utcnow()
        
        result = col.insert_many(QUESTION_PARTICLES_DATA)
        print(f"[OK] Question Particles: {len(result.inserted_ids)} soru eki eklendi")
    
    def insert_postpositions(self):
        """Edatları yükle."""
        col = self.db[COLLECTIONS["postpositions"]]
        for pp in POSTPOSITIONS_DATA:
            pp["created_at"] = datetime.utcnow()
        
        result = col.insert_many(POSTPOSITIONS_DATA)
        print(f"[OK] Postpositions: {len(result.inserted_ids)} edat eklendi")
    
    def insert_conjunctions(self):
        """Bağlaçları yükle."""
        col = self.db[COLLECTIONS["conjunctions"]]
        for conj in CONJUNCTIONS_DATA:
            conj["created_at"] = datetime.utcnow()
        
        result = col.insert_many(CONJUNCTIONS_DATA)
        print(f"[OK] Conjunctions: {len(result.inserted_ids)} bağlaç eklendi")
    
    def insert_copula_suffixes(self):
        """Ek-fiil eklerini yükle."""
        col = self.db[COLLECTIONS["copula_suffixes"]]
        for suffix in COPULA_SUFFIXES_DATA:
            suffix["created_at"] = datetime.utcnow()
        
        result = col.insert_many(COPULA_SUFFIXES_DATA)
        print(f"[OK] Copula Suffixes: {len(result.inserted_ids)} ek-fiil eki eklendi")
    
    def insert_article_rules(self):
        """Article kurallarını yükle."""
        col = self.db[COLLECTIONS["article_rules"]]
        for rule in ARTICLE_RULES_DATA:
            rule["created_at"] = datetime.utcnow()
        
        result = col.insert_many(ARTICLE_RULES_DATA)
        print(f"[OK] Article Rules: {len(result.inserted_ids)} article kuralı eklendi")
    
    def insert_buffer_consonant_exceptions(self):
        """Kaynaştırma ünsüzü istisnalarını yükle."""
        col = self.db[COLLECTIONS["buffer_consonant_exceptions"]]
        for exc in BUFFER_CONSONANT_EXCEPTIONS_DATA:
            exc["created_at"] = datetime.utcnow()
        
        result = col.insert_many(BUFFER_CONSONANT_EXCEPTIONS_DATA)
        print(f"[OK] Buffer Consonant Exceptions: {len(result.inserted_ids)} kaynaştırma istisnası eklendi")
    
    def insert_plural_suffixes(self):
        """Çoğul eklerini yükle."""
        col = self.db[COLLECTIONS["plural_suffixes"]]
        for suffix in PLURAL_SUFFIXES_DATA:
            suffix["created_at"] = datetime.utcnow()
        
        result = col.insert_many(PLURAL_SUFFIXES_DATA)
        print(f"[OK] Plural Suffixes: {len(result.inserted_ids)} çoğul eki eklendi")
    
    def insert_noun_roots(self):
        """İsim köklerini yükle."""
        col = self.db[COLLECTIONS["noun_roots"]]
        for noun in NOUN_ROOTS_DATA:
            noun["created_at"] = datetime.utcnow()
        
        result = col.insert_many(NOUN_ROOTS_DATA)
        print(f"[OK] Noun Roots: {len(result.inserted_ids)} isim kökü eklendi")
    
    def init_all(self):
        """Tüm koleksiyonları oluştur ve doldur."""
        print("\n" + "="*60)
        print("MongoDB Veritabanı Kurulumu Başlıyor...")
        print("="*60 + "\n")
        
        if not self.connect():
            return False
        
        print("\n--- Mevcut verileri temizleme ---")
        self.clear_all()
        
        print("\n--- Indexleri oluşturma ---")
        self.create_indexes()
        
        print("\n--- Verileri yükleme ---")
        self.insert_words()
        self.insert_collocations()
        self.insert_semantic_rules()
        self.insert_ngrams()
        self.insert_grammar_rules()
        # Morfoloji verileri
        self.insert_verb_roots()
        self.insert_irregular_verbs()
        self.insert_tense_suffixes()
        self.insert_person_suffixes()
        self.insert_turkish_irregular_roots()
        self.insert_auxiliary_verbs()
        # Fonoloji kuralları
        self.insert_phonology_rules()
        # Türkçe morfoloji istisnaları
        self.insert_aorist_irregular_verbs()
        self.insert_vowel_harmony_exceptions()
        self.insert_consonant_mutation_exceptions()
        self.insert_vowel_drop_words()
        # Yeni eklenen koleksiyonlar
        self.insert_case_suffixes()
        self.insert_possessive_suffixes()
        self.insert_negation_suffixes()
        self.insert_question_particles()
        self.insert_postpositions()
        self.insert_conjunctions()
        self.insert_copula_suffixes()
        self.insert_article_rules()
        self.insert_buffer_consonant_exceptions()
        self.insert_plural_suffixes()
        self.insert_noun_roots()
        
        print("\n" + "="*60)
        print("✓ Veritabanı kurulumu tamamlandı!")
        print("="*60)
        
        # İstatistikler
        print("\n--- Koleksiyon İstatistikleri ---")
        for name, col_name in COLLECTIONS.items():
            count = self.db[col_name].count_documents({})
            print(f"  {name}: {count} kayıt")
        
        return True
    
    def export_to_json(self, output_dir: str = "."):
        """Mock data'yı JSON dosyalarına export et."""
        import os
        
        export_dir = os.path.join(output_dir, "db_export")
        os.makedirs(export_dir, exist_ok=True)
        
        exports = {
            "words.json": WORDS_DATA,
            "collocations.json": COLLOCATIONS_DATA,
            "semantic_rules.json": SEMANTIC_RULES_DATA,
            "ngrams.json": NGRAMS_DATA,
            "grammar_rules.json": GRAMMAR_RULES_DATA,
            # Morfoloji verileri
            "verb_roots.json": VERB_ROOTS_DATA,
            "irregular_verbs.json": IRREGULAR_VERBS_DATA,
            "tense_suffixes.json": TENSE_SUFFIXES_DATA,
            "person_suffixes.json": PERSON_SUFFIXES_DATA,
            "turkish_irregular_roots.json": TURKISH_IRREGULAR_ROOTS_DATA,
            "auxiliary_verbs.json": AUXILIARY_VERBS_DATA,
            # Fonoloji kuralları
            "phonology_rules.json": PHONOLOGY_RULES_DATA,
            # Türkçe morfoloji istisnaları
            "aorist_irregular_verbs.json": AORIST_IRREGULAR_VERBS_DATA,
            "vowel_harmony_exceptions.json": VOWEL_HARMONY_EXCEPTIONS_DATA,
            "consonant_mutation_exceptions.json": CONSONANT_MUTATION_EXCEPTIONS_DATA,
            "vowel_drop_words.json": VOWEL_DROP_DATA,
            # Yeni eklenen koleksiyonlar
            "case_suffixes.json": CASE_SUFFIXES_DATA,
            "possessive_suffixes.json": POSSESSIVE_SUFFIXES_DATA,
            "negation_suffixes.json": NEGATION_SUFFIXES_DATA,
            "question_particles.json": QUESTION_PARTICLES_DATA,
            "postpositions.json": POSTPOSITIONS_DATA,
            "conjunctions.json": CONJUNCTIONS_DATA,
            "copula_suffixes.json": COPULA_SUFFIXES_DATA,
            "article_rules.json": ARTICLE_RULES_DATA,
            "buffer_consonant_exceptions.json": BUFFER_CONSONANT_EXCEPTIONS_DATA,
            "plural_suffixes.json": PLURAL_SUFFIXES_DATA,
            "noun_roots.json": NOUN_ROOTS_DATA,
        }
        
        for filename, data in exports.items():
            filepath = os.path.join(export_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[OK] Exported: {filepath}")
        
        print(f"\n✓ Tüm veriler {export_dir}/ klasörüne export edildi")


# =============================================================================
# AI MODEL KURULUMU (HUGGING FACE)
# =============================================================================

# Hugging Face model ayarları
HF_MODEL_ID = "g0rkm/final_marian_model"
LOCAL_MODEL_PATH = "./final_marian_model"

def setup_ai_model(model_id: str = HF_MODEL_ID, local_path: str = LOCAL_MODEL_PATH) -> bool:
    """
    Hugging Face'den MarianMT modelini indirir ve yerel klasöre kaydeder.
    
    Bu model Türkçe → İngilizce çeviri için fine-tuned edilmiş bir
    MarianMT (Neural Machine Translation) modelidir.
    
    Args:
        model_id: Hugging Face model ID (örn: "g0rkm/final_marian_model")
        local_path: Modelin kaydedileceği yerel klasör
        
    Returns:
        bool: Başarılı ise True, değilse False
    """
    print("="*60)
    print("AI MODEL KURULUMU")
    print("="*60)
    print(f"Model ID: {model_id}")
    print(f"Hedef klasör: {local_path}")
    print()
    
    # Gerekli kütüphaneleri kontrol et
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        import torch
        print("[OK] transformers ve torch kütüphaneleri yüklü")
    except ImportError as e:
        print(f"[HATA] Gerekli kütüphaneler eksik: {e}")
        print("\nYüklemek için:")
        print("  pip install transformers torch sentencepiece")
        return False
    
    # Mevcut model kontrolü
    if os.path.exists(local_path):
        config_file = os.path.join(local_path, "config.json")
        if os.path.exists(config_file):
            print(f"[UYARI] Model zaten mevcut: {local_path}")
            response = input("Yeniden indirmek ister misiniz? (e/h): ").strip().lower()
            if response != 'e':
                print("[INFO] Mevcut model korunuyor.")
                return True
            print("[INFO] Model yeniden indirilecek...")
    
    # Model indirme
    print(f"\n[DOWNLOAD] Model indiriliyor: {model_id}")
    print("Bu işlem birkaç dakika sürebilir...")
    print()
    
    try:
        # Tokenizer indir
        print("[1/3] Tokenizer indiriliyor...")
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        print("      ✓ Tokenizer başarıyla indirildi")
        
        # Model indir
        print("[2/3] Model ağırlıkları indiriliyor (bu biraz zaman alabilir)...")
        model = AutoModelForSeq2SeqLM.from_pretrained(model_id)
        print("      ✓ Model başarıyla indirildi")
        
        # Yerel klasöre kaydet
        print(f"[3/3] Model yerel klasöre kaydediliyor: {local_path}")
        os.makedirs(local_path, exist_ok=True)
        tokenizer.save_pretrained(local_path)
        model.save_pretrained(local_path)
        print("      ✓ Model başarıyla kaydedildi")
        
        # Model bilgilerini göster
        print("\n" + "="*60)
        print("MODEL BİLGİLERİ")
        print("="*60)
        print(f"Model tipi: MarianMT (Seq2Seq)")
        print(f"Kaynak dil: Türkçe (tr)")
        print(f"Hedef dil: İngilizce (en)")
        print(f"Parametre sayısı: ~{sum(p.numel() for p in model.parameters()) / 1e6:.1f}M")
        print(f"Dosya konumu: {os.path.abspath(local_path)}")
        
        # Dosya boyutlarını göster
        total_size = 0
        for root, dirs, files in os.walk(local_path):
            for file in files:
                file_path = os.path.join(root, file)
                size = os.path.getsize(file_path)
                total_size += size
                print(f"  - {file}: {size / 1024 / 1024:.2f} MB")
        print(f"Toplam boyut: {total_size / 1024 / 1024:.2f} MB")
        
        # Test çevirisi
        print("\n" + "="*60)
        print("MODEL TESTİ")
        print("="*60)
        
        test_sentences = [
            "merhaba dünya",
            "ben okula gidiyorum",
            "bugün hava çok güzel"
        ]
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Cihaz: {device}")
        model = model.to(device)
        
        print("\nTest çevirileri:")
        for sentence in test_sentences:
            inputs = tokenizer(sentence, return_tensors="pt").to(device)
            outputs = model.generate(**inputs, max_length=128)
            translation = tokenizer.decode(outputs[0], skip_special_tokens=True)
            print(f"  TR: {sentence}")
            print(f"  EN: {translation}")
            print()
        
        print("="*60)
        print("✓ AI MODEL KURULUMU TAMAMLANDI!")
        print("="*60)
        print(f"\nModel şu konumda kullanıma hazır: {os.path.abspath(local_path)}")
        print("main.py bu modeli otomatik olarak yükleyecektir.")
        
        return True
        
    except Exception as e:
        print(f"\n[HATA] Model indirme başarısız: {e}")
        print("\nOlası çözümler:")
        print("1. İnternet bağlantınızı kontrol edin")
        print("2. Hugging Face erişilebilir mi kontrol edin: https://huggingface.co/")
        print(f"3. Model ID'nin doğru olduğundan emin olun: {model_id}")
        print("4. Yeterli disk alanı olduğundan emin olun (~500MB)")
        return False


def check_ai_model(local_path: str = LOCAL_MODEL_PATH) -> bool:
    """AI modelinin mevcut olup olmadığını kontrol eder."""
    required_files = ["config.json", "pytorch_model.bin", "tokenizer_config.json"]
    
    if not os.path.exists(local_path):
        return False
    
    # En az config.json olmalı (bazı modellerde pytorch_model.bin yerine model.safetensors olabilir)
    config_path = os.path.join(local_path, "config.json")
    return os.path.exists(config_path)


# =============================================================================
# ANA FONKSİYON
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="MongoDB Translator Veritabanı ve AI Model Kurulumu",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python setup_mongodb.py --init      # MongoDB veritabanını kur
  python setup_mongodb.py --model     # AI modelini indir (Hugging Face)
  python setup_mongodb.py --all       # Her ikisini de kur
  python setup_mongodb.py --check     # Kurulum durumunu kontrol et
        """
    )
    parser.add_argument("--init", action="store_true", help="MongoDB veritabanını oluştur ve doldur")
    parser.add_argument("--clear", action="store_true", help="Tüm veritabanı verilerini sil")
    parser.add_argument("--export", action="store_true", help="Mock data'yı JSON olarak export et")
    parser.add_argument("--model", action="store_true", help="AI modelini Hugging Face'den indir")
    parser.add_argument("--all", action="store_true", help="Hem veritabanı hem AI model kurulumu")
    parser.add_argument("--check", action="store_true", help="Kurulum durumunu kontrol et")
    parser.add_argument("--uri", default=MONGO_URI, help="MongoDB URI")
    parser.add_argument("--db", default=DB_NAME, help="Veritabanı adı")
    parser.add_argument("--model-id", default=HF_MODEL_ID, help="Hugging Face model ID")
    parser.add_argument("--model-path", default=LOCAL_MODEL_PATH, help="Model kayıt klasörü")
    
    args = parser.parse_args()
    
    # Hiçbir argüman verilmediyse yardım göster
    if not any([args.init, args.clear, args.export, args.model, args.all, args.check]):
        parser.print_help()
        print("\n" + "="*60)
        print("HIZLI BAŞLANGIÇ")
        print("="*60)
        print("\n[İPUCU] Tam kurulum için: python setup_mongodb.py --all")
        print("[İPUCU] Sadece AI model için: python setup_mongodb.py --model")
        return
    
    # Kurulum durumu kontrolü
    if args.check:
        print("="*60)
        print("KURULUM DURUMU KONTROLÜ")
        print("="*60)
        
        # MongoDB kontrolü
        print("\n--- MongoDB ---")
        setup = MongoDBSetup(args.uri, args.db)
        if setup.connect():
            print(f"[OK] MongoDB bağlantısı başarılı: {args.uri}")
            total_docs = 0
            for name, col_name in COLLECTIONS.items():
                count = setup.db[col_name].count_documents({})
                total_docs += count
            print(f"[OK] Toplam kayıt sayısı: {total_docs}")
        else:
            print("[HATA] MongoDB bağlantısı başarısız")
        
        # AI Model kontrolü
        print("\n--- AI Model ---")
        if check_ai_model(args.model_path):
            print(f"[OK] AI model mevcut: {os.path.abspath(args.model_path)}")
            # Model boyutunu göster
            total_size = 0
            for root, dirs, files in os.walk(args.model_path):
                for file in files:
                    total_size += os.path.getsize(os.path.join(root, file))
            print(f"[OK] Model boyutu: {total_size / 1024 / 1024:.2f} MB")
        else:
            print(f"[UYARI] AI model bulunamadı: {args.model_path}")
            print("[İPUCU] İndirmek için: python setup_mongodb.py --model")
        
        print("\n" + "="*60)
        return
    
    # Export işlemi
    if args.export:
        setup = MongoDBSetup(args.uri, args.db)
        setup.export_to_json()
        return
    
    # Veritabanı silme
    if args.clear:
        setup = MongoDBSetup(args.uri, args.db)
        if setup.connect():
            setup.clear_all()
        return
    
    # Tam kurulum (--all)
    if args.all:
        print("="*60)
        print("TAM KURULUM BAŞLATILIYOR")
        print("="*60)
        print()
        
        # 1. MongoDB kurulumu
        print("[ADIM 1/2] MongoDB Veritabanı Kurulumu")
        print("-"*40)
        setup = MongoDBSetup(args.uri, args.db)
        db_success = setup.init_all()
        
        print()
        
        # 2. AI Model kurulumu
        print("[ADIM 2/2] AI Model Kurulumu")
        print("-"*40)
        model_success = setup_ai_model(args.model_id, args.model_path)
        
        # Sonuç özeti
        print("\n" + "="*60)
        print("KURULUM ÖZETI")
        print("="*60)
        print(f"MongoDB: {'✓ Başarılı' if db_success else '✗ Başarısız'}")
        print(f"AI Model: {'✓ Başarılı' if model_success else '✗ Başarısız'}")
        
        if db_success and model_success:
            print("\n🎉 Tüm kurulum tamamlandı!")
            print("Sistemi test etmek için: python main.py merhaba dünya")
        return
    
    # Sadece veritabanı kurulumu
    if args.init:
        setup = MongoDBSetup(args.uri, args.db)
        setup.init_all()
        return
    
    # Sadece AI model kurulumu
    if args.model:
        setup_ai_model(args.model_id, args.model_path)
        return


if __name__ == "__main__":
    main()

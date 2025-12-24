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

Kullanım:
    python setup_mongodb.py --init     # Tüm koleksiyonları oluştur ve doldur
    python setup_mongodb.py --clear    # Tüm verileri sil
    python setup_mongodb.py --export   # Mock data'yı JSON olarak export et
"""

import sys
import json
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
    "auxiliary_verbs": "auxiliary_verbs"
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
    {"tr": "ic", "en": "drink", "type": "irregular"},
    {"tr": "yap", "en": "do", "type": "irregular"},
    {"tr": "al", "en": "take", "type": "irregular"},
    {"tr": "ver", "en": "give", "type": "irregular"},
    {"tr": "oku", "en": "read", "type": "irregular"},
    {"tr": "yaz", "en": "write", "type": "irregular"},
    {"tr": "sev", "en": "love", "type": "regular"},
    {"tr": "gor", "en": "see", "type": "irregular"},
    {"tr": "bil", "en": "know", "type": "irregular"},
    {"tr": "de", "en": "say", "type": "irregular"},
    {"tr": "soyle", "en": "tell", "type": "irregular"},
    {"tr": "dusun", "en": "think", "type": "irregular"},
    {"tr": "anla", "en": "understand", "type": "irregular"},
    {"tr": "bul", "en": "find", "type": "irregular"},
    {"tr": "birak", "en": "leave", "type": "irregular"},
    {"tr": "hisset", "en": "feel", "type": "irregular"},
    {"tr": "koy", "en": "put", "type": "irregular"},
    {"tr": "otur", "en": "sit", "type": "irregular"},
    {"tr": "kalk", "en": "stand", "type": "irregular"},
    {"tr": "uyu", "en": "sleep", "type": "irregular"},
    {"tr": "uyan", "en": "wake", "type": "irregular"},
    {"tr": "kos", "en": "run", "type": "irregular"},
    {"tr": "yuz", "en": "swim", "type": "irregular"},
    {"tr": "sat", "en": "sell", "type": "irregular"},
    {"tr": "yika", "en": "wash", "type": "regular"},
    {"tr": "oyna", "en": "play", "type": "regular"},
    {"tr": "calis", "en": "work", "type": "regular"},
    {"tr": "konus", "en": "speak", "type": "irregular"},
    {"tr": "dinle", "en": "listen", "type": "regular"},
    {"tr": "bekle", "en": "wait", "type": "regular"},
    {"tr": "basla", "en": "start", "type": "regular"},
    {"tr": "bitir", "en": "finish", "type": "regular"},
    {"tr": "ac", "en": "open", "type": "regular"},
    {"tr": "kapat", "en": "close", "type": "regular"},
    {"tr": "ogren", "en": "learn", "type": "regular"},
    {"tr": "ogret", "en": "teach", "type": "irregular"},
    {"tr": "hatirla", "en": "remember", "type": "regular"},
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
    # Şimdiki Zaman (-yor)
    {"suffix": "iyor", "tense": "present_continuous", "priority": 1, "description": "Şimdiki zaman"},
    {"suffix": "uyor", "tense": "present_continuous", "priority": 1, "description": "Şimdiki zaman"},
    {"suffix": "yor", "tense": "present_continuous", "priority": 2, "description": "Şimdiki zaman (kısa)"},
    
    # Geçmiş Zaman (-di)
    {"suffix": "di", "tense": "past_simple", "priority": 1, "description": "Geçmiş zaman"},
    {"suffix": "du", "tense": "past_simple", "priority": 1, "description": "Geçmiş zaman"},
    {"suffix": "ti", "tense": "past_simple", "priority": 1, "description": "Geçmiş zaman (sert ünsüz)"},
    {"suffix": "tu", "tense": "past_simple", "priority": 1, "description": "Geçmiş zaman (sert ünsüz)"},
    
    # Gelecek Zaman (-ecek/-acak)
    {"suffix": "ecek", "tense": "future", "priority": 1, "description": "Gelecek zaman"},
    {"suffix": "acak", "tense": "future", "priority": 1, "description": "Gelecek zaman"},
    {"suffix": "eceg", "tense": "future", "priority": 1, "description": "Gelecek zaman (yumuşama)"},
    {"suffix": "acag", "tense": "future", "priority": 1, "description": "Gelecek zaman (yumuşama)"},
    
    # Geniş Zaman (-er/-ar/-ir/-ır/-ur/-ür/-r)
    {"suffix": "er", "tense": "aorist", "priority": 1, "description": "Geniş zaman"},
    {"suffix": "ar", "tense": "aorist", "priority": 1, "description": "Geniş zaman"},
    {"suffix": "ir", "tense": "aorist", "priority": 1, "description": "Geniş zaman"},
    {"suffix": "ur", "tense": "aorist", "priority": 1, "description": "Geniş zaman"},
    
    # Duyulan Geçmiş (-miş)
    {"suffix": "mis", "tense": "past_reported", "priority": 1, "description": "Duyulan geçmiş"},
    {"suffix": "mus", "tense": "past_reported", "priority": 1, "description": "Duyulan geçmiş"},
    
    # Gereklilik (-meli/-malı)
    {"suffix": "meli", "tense": "necessity", "priority": 1, "description": "Gereklilik"},
    {"suffix": "mali", "tense": "necessity", "priority": 1, "description": "Gereklilik"},
    
    # Yeterlilik (-ebil/-abil)
    {"suffix": "ebil", "tense": "ability", "priority": 1, "description": "Yeterlilik"},
    {"suffix": "abil", "tense": "ability", "priority": 1, "description": "Yeterlilik"},
]

# 9. PERSON SUFFIXES - Türkçe Şahıs Ekleri
PERSON_SUFFIXES_DATA = [
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
    
    # Geniş Zaman
    {"suffix": "im", "person": 1, "plurality": "singular", "tense": "aorist"},
    {"suffix": "sin", "person": 2, "plurality": "singular", "tense": "aorist"},
    {"suffix": "", "person": 3, "plurality": "singular", "tense": "aorist"},
    {"suffix": "iz", "person": 1, "plurality": "plural", "tense": "aorist"},
    {"suffix": "lar", "person": 3, "plurality": "plural", "tense": "aorist"},
    
    # Gereklilik
    {"suffix": "yim", "person": 1, "plurality": "singular", "tense": "necessity"},
    {"suffix": "sin", "person": 2, "plurality": "singular", "tense": "necessity"},
    {"suffix": "", "person": 3, "plurality": "singular", "tense": "necessity"},
    {"suffix": "yiz", "person": 1, "plurality": "plural", "tense": "necessity"},
    {"suffix": "siniz", "person": 2, "plurality": "plural", "tense": "necessity"},
]

# 10. TURKISH IRREGULAR ROOTS - Türkçe Düzensiz Kök Değişimleri
TURKISH_IRREGULAR_ROOTS_DATA = [
    # Yemek fiili: ye → yi (şimdiki zamanda)
    {"alternate": "y", "canonical": "ye", "context": "present_continuous", "description": "ye→yi bağlayıcı ünlü düşmesi"},
    {"alternate": "yi", "canonical": "ye", "context": "general", "description": "ye→yi değişimi"},
    {"alternate": "yiy", "canonical": "ye", "context": "general", "description": "ye→yiy değişimi"},
    
    # Demek fiili: de → di
    {"alternate": "d", "canonical": "de", "context": "present_continuous", "description": "de→di bağlayıcı ünlü düşmesi"},
    {"alternate": "di", "canonical": "de", "context": "general", "description": "de→di değişimi"},
    {"alternate": "diy", "canonical": "de", "context": "general", "description": "de→diy değişimi"},
    
    # Gitmek: git → gid (yumuşama)
    {"alternate": "gid", "canonical": "git", "context": "before_vowel", "description": "t→d yumuşaması"},
    
    # Etmek: et → ed (yumuşama)
    {"alternate": "ed", "canonical": "et", "context": "before_vowel", "description": "t→d yumuşaması"},
    
    # Tatmak: tat → tad
    {"alternate": "tad", "canonical": "tat", "context": "before_vowel", "description": "t→d yumuşaması"},
    
    # Okumak: oku → okuy (ünlü kaynaşması)
    {"alternate": "okuy", "canonical": "oku", "context": "before_vowel", "description": "ünlü+yor kaynaşması"},
    
    # Başlamak: başla → başlı (şimdiki zaman)
    {"alternate": "basliy", "canonical": "basla", "context": "present_continuous", "description": "a→ı ünlü değişimi"},
    
    # Anlamak: anla → anlı
    {"alternate": "anliy", "canonical": "anla", "context": "present_continuous", "description": "a→ı ünlü değişimi"},
    
    # Oynamak: oyna → oynu
    {"alternate": "oynuy", "canonical": "oyna", "context": "present_continuous", "description": "a→u ünlü değişimi"},
]

# 11. AUXILIARY VERBS - İngilizce Yardımcı Fiiller
AUXILIARY_VERBS_DATA = [
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
        }
        
        for filename, data in exports.items():
            filepath = os.path.join(export_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[OK] Exported: {filepath}")
        
        print(f"\n✓ Tüm veriler {export_dir}/ klasörüne export edildi")


# =============================================================================
# ANA FONKSİYON
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="MongoDB Translator Veritabanı Kurulumu")
    parser.add_argument("--init", action="store_true", help="Veritabanını oluştur ve doldur")
    parser.add_argument("--clear", action="store_true", help="Tüm verileri sil")
    parser.add_argument("--export", action="store_true", help="Mock data'yı JSON olarak export et")
    parser.add_argument("--uri", default=MONGO_URI, help="MongoDB URI")
    parser.add_argument("--db", default=DB_NAME, help="Veritabanı adı")
    
    args = parser.parse_args()
    
    if not any([args.init, args.clear, args.export]):
        parser.print_help()
        print("\n[İPUCU] Kurulum için: python setup_mongodb.py --init")
        return
    
    setup = MongoDBSetup(args.uri, args.db)
    
    if args.export:
        setup.export_to_json()
        return
    
    if args.clear:
        if setup.connect():
            setup.clear_all()
        return
    
    if args.init:
        setup.init_all()


if __name__ == "__main__":
    main()

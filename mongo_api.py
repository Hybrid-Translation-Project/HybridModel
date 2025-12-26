import sys
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import math

sys.stdout.reconfigure(encoding='utf-8')

# Flag to use mock data instead of MongoDB
USE_MOCK_DATA = True

# Try to import pymongo, but don't fail if not available
try:
    from pymongo import MongoClient
    from bson.objectid import ObjectId
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    if not USE_MOCK_DATA:
        print("[WARNING] pymongo not installed. Switching to mock mode.")
        USE_MOCK_DATA = False

# -----------------------------
# MongoDB bağlantısı fonksiyonu
# -----------------------------
def get_mongo_collection(db_name="testdb", collection_name="dictionary"):
    """
    MongoDB bağlantısını oluşturur ve koleksiyonu döndürür.
    """
    client = MongoClient("mongodb://localhost:27017/")
    return client[db_name][collection_name]


# =============================================================================
# GELIŞMIŞ MOCK DATA SİSTEMİ
# =============================================================================

# -----------------------------
# 1. WORDS KOLEKSIYONU (Kelimeler)
# frequency: Türkçe corpus frekansı (normalize 1-100)
# domain: Kullanım alanları
# register: formal/informal/neutral
# -----------------------------
MOCK_WORDS = {
    "yuz": {
        "tr": "yüz",
        "meanings": [
            {
                "en": "face",
                "pos": "noun",
                "frequency": 85,
                "domain": ["body", "general", "emotion"],
                "register": "neutral",
                "semantic_class": "body_part"
            },
            {
                "en": "hundred",
                "pos": "noun", 
                "frequency": 72,
                "domain": ["number", "math", "quantity"],
                "register": "neutral",
                "semantic_class": "number"
            },
            {
                "en": "swim",
                "pos": "verb",
                "frequency": 35,
                "domain": ["sport", "action", "water"],
                "register": "neutral",
                "semantic_class": "motion"
            }
        ]
    },
    "ben": {
        "tr": "ben",
        "meanings": [
            {
                "en": "I",
                "pos": "pronoun",
                "frequency": 98,
                "domain": ["general"],
                "register": "neutral",
                "semantic_class": "animate"
            }
        ]
    },
    "sen": {
        "tr": "sen",
        "meanings": [
            {
                "en": "you",
                "pos": "pronoun",
                "frequency": 95,
                "domain": ["general"],
                "register": "neutral",
                "semantic_class": "animate"
            }
        ]
    },
    "o": {
        "tr": "o",
        "meanings": [
            {
                "en": "he",
                "pos": "pronoun",
                "frequency": 90,
                "domain": ["general"],
                "register": "neutral",
                "semantic_class": "animate"
            },
            {
                "en": "she",
                "pos": "pronoun",
                "frequency": 90,
                "domain": ["general"],
                "register": "neutral",
                "semantic_class": "animate"
            },
            {
                "en": "it",
                "pos": "pronoun",
                "frequency": 85,
                "domain": ["general"],
                "register": "neutral",
                "semantic_class": "inanimate"
            }
        ]
    },
    "sev": {
        "tr": "sev",
        "meanings": [
            {
                "en": "love",
                "pos": "verb",
                "frequency": 78,
                "domain": ["emotion", "relationship"],
                "register": "neutral",
                "semantic_class": "emotion"
            },
            {
                "en": "like",
                "pos": "verb",
                "frequency": 82,
                "domain": ["emotion", "preference"],
                "register": "neutral",
                "semantic_class": "emotion"
            }
        ]
    },
    "ye": {
        "tr": "ye",
        "meanings": [
            {
                "en": "eat",
                "pos": "verb",
                "frequency": 75,
                "domain": ["food", "action"],
                "register": "neutral",
                "semantic_class": "consumption"
            }
        ]
    },
    "ic": {
        "tr": "iç",
        "meanings": [
            {
                "en": "drink",
                "pos": "verb",
                "frequency": 70,
                "domain": ["food", "action"],
                "register": "neutral",
                "semantic_class": "consumption"
            },
            {
                "en": "inside",
                "pos": "noun",
                "frequency": 45,
                "domain": ["location", "space"],
                "register": "neutral",
                "semantic_class": "location"
            }
        ]
    },
    "git": {
        "tr": "git",
        "meanings": [
            {
                "en": "go",
                "pos": "verb",
                "frequency": 88,
                "domain": ["motion", "action"],
                "register": "neutral",
                "semantic_class": "motion"
            }
        ]
    },
    "gel": {
        "tr": "gel",
        "meanings": [
            {
                "en": "come",
                "pos": "verb",
                "frequency": 86,
                "domain": ["motion", "action"],
                "register": "neutral",
                "semantic_class": "motion"
            }
        ]
    },
    "oku": {
        "tr": "oku",
        "meanings": [
            {
                "en": "read",
                "pos": "verb",
                "frequency": 65,
                "domain": ["education", "action"],
                "register": "neutral",
                "semantic_class": "cognitive"
            }
        ]
    },
    "yaz": {
        "tr": "yaz",
        "meanings": [
            {
                "en": "write",
                "pos": "verb",
                "frequency": 60,
                "domain": ["education", "action"],
                "register": "neutral",
                "semantic_class": "cognitive"
            },
            {
                "en": "summer",
                "pos": "noun",
                "frequency": 55,
                "domain": ["season", "time"],
                "register": "neutral",
                "semantic_class": "time"
            }
        ]
    },
    "yika": {
        "tr": "yıka",
        "meanings": [
            {
                "en": "wash",
                "pos": "verb",
                "frequency": 50,
                "domain": ["cleaning", "action"],
                "register": "neutral",
                "semantic_class": "action"
            }
        ]
    },
    "elma": {
        "tr": "elma",
        "meanings": [
            {
                "en": "apple",
                "pos": "noun",
                "frequency": 45,
                "domain": ["food", "fruit"],
                "register": "neutral",
                "semantic_class": "food"
            }
        ]
    },
    "kitap": {
        "tr": "kitap",
        "meanings": [
            {
                "en": "book",
                "pos": "noun",
                "frequency": 70,
                "domain": ["education", "object"],
                "register": "neutral",
                "semantic_class": "object"
            }
        ]
    },
    "ev": {
        "tr": "ev",
        "meanings": [
            {
                "en": "house",
                "pos": "noun",
                "frequency": 80,
                "domain": ["building", "home"],
                "register": "neutral",
                "semantic_class": "location"
            },
            {
                "en": "home",
                "pos": "noun",
                "frequency": 78,
                "domain": ["building", "family"],
                "register": "neutral",
                "semantic_class": "location"
            }
        ]
    },
    "kedi": {
        "tr": "kedi",
        "meanings": [
            {
                "en": "cat",
                "pos": "noun",
                "frequency": 55,
                "domain": ["animal"],
                "register": "neutral",
                "semantic_class": "animate"
            }
        ]
    },
    "kopek": {
        "tr": "köpek",
        "meanings": [
            {
                "en": "dog",
                "pos": "noun",
                "frequency": 52,
                "domain": ["animal"],
                "register": "neutral",
                "semantic_class": "animate"
            }
        ]
    },
    "su": {
        "tr": "su",
        "meanings": [
            {
                "en": "water",
                "pos": "noun",
                "frequency": 75,
                "domain": ["liquid", "nature"],
                "register": "neutral",
                "semantic_class": "liquid"
            }
        ]
    },
    "para": {
        "tr": "para",
        "meanings": [
            {
                "en": "money",
                "pos": "noun",
                "frequency": 72,
                "domain": ["finance", "economy"],
                "register": "neutral",
                "semantic_class": "abstract"
            }
        ]
    },
    "al": {
        "tr": "al",
        "meanings": [
            {
                "en": "take",
                "pos": "verb",
                "frequency": 80,
                "domain": ["action", "transaction"],
                "register": "neutral",
                "semantic_class": "action"
            },
            {
                "en": "buy",
                "pos": "verb",
                "frequency": 65,
                "domain": ["transaction", "commerce"],
                "register": "neutral",
                "semantic_class": "transaction"
            },
            {
                "en": "red",
                "pos": "adjective",
                "frequency": 40,
                "domain": ["color"],
                "register": "neutral",
                "semantic_class": "property"
            }
        ]
    },
    "ver": {
        "tr": "ver",
        "meanings": [
            {
                "en": "give",
                "pos": "verb",
                "frequency": 78,
                "domain": ["action", "transaction"],
                "register": "neutral",
                "semantic_class": "action"
            }
        ]
    },
    "guzel": {
        "tr": "güzel",
        "meanings": [
            {
                "en": "beautiful",
                "pos": "adjective",
                "frequency": 70,
                "domain": ["appearance", "emotion"],
                "register": "neutral",
                "semantic_class": "property"
            },
            {
                "en": "nice",
                "pos": "adjective",
                "frequency": 68,
                "domain": ["quality", "emotion"],
                "register": "neutral",
                "semantic_class": "property"
            }
        ]
    },
    "buyuk": {
        "tr": "büyük",
        "meanings": [
            {
                "en": "big",
                "pos": "adjective",
                "frequency": 75,
                "domain": ["size", "quality"],
                "register": "neutral",
                "semantic_class": "property"
            },
            {
                "en": "large",
                "pos": "adjective",
                "frequency": 70,
                "domain": ["size", "quality"],
                "register": "neutral",
                "semantic_class": "property"
            }
        ]
    },
    "kucuk": {
        "tr": "küçük",
        "meanings": [
            {
                "en": "small",
                "pos": "adjective",
                "frequency": 72,
                "domain": ["size", "quality"],
                "register": "neutral",
                "semantic_class": "property"
            }
        ]
    }
}

# -----------------------------
# 2. COLLOCATIONS (Eşdizimlilik)
# İki kelimenin birlikte kullanım gücü
# strength: 0-1 arası PMI benzeri skor
# -----------------------------
MOCK_COLLOCATIONS = {
    ("yuz", "yika"): {
        "pattern": "NOUN + VERB",
        "meaning_hint": {"yuz": "face", "yika": "wash"},
        "frequency": 3200,
        "strength": 0.92,
        "example": "yüzünü yıka"
    },
    ("yuz", "metre"): {
        "pattern": "NUM + NOUN",
        "meaning_hint": {"yuz": "hundred"},
        "frequency": 2800,
        "strength": 0.88
    },
    ("yuz", "lira"): {
        "pattern": "NUM + NOUN",
        "meaning_hint": {"yuz": "hundred"},
        "frequency": 4500,
        "strength": 0.95
    },
    ("su", "ic"): {
        "pattern": "NOUN + VERB",
        "meaning_hint": {"su": "water", "ic": "drink"},
        "frequency": 5000,
        "strength": 0.94
    },
    ("elma", "ye"): {
        "pattern": "NOUN + VERB",
        "meaning_hint": {"elma": "apple", "ye": "eat"},
        "frequency": 2500,
        "strength": 0.90
    },
    ("kitap", "oku"): {
        "pattern": "NOUN + VERB",
        "meaning_hint": {"kitap": "book", "oku": "read"},
        "frequency": 4200,
        "strength": 0.93
    },
    ("mektup", "yaz"): {
        "pattern": "NOUN + VERB",
        "meaning_hint": {"yaz": "write"},
        "frequency": 1800,
        "strength": 0.85
    },
    ("eve", "git"): {
        "pattern": "NOUN + VERB",
        "meaning_hint": {"ev": "home", "git": "go"},
        "frequency": 3800,
        "strength": 0.89
    },
    ("para", "al"): {
        "pattern": "NOUN + VERB",
        "meaning_hint": {"para": "money", "al": "take"},
        "frequency": 2200,
        "strength": 0.82
    },
    ("para", "ver"): {
        "pattern": "NOUN + VERB",
        "meaning_hint": {"para": "money", "ver": "give"},
        "frequency": 2000,
        "strength": 0.80
    }
}

# -----------------------------
# 3. SEMANTIC COMPATIBILITY (Anlam Uyumu)
# Özne-fiil, nesne-fiil uyumlulukları
# -----------------------------
MOCK_SEMANTIC_COMPATIBILITY = {
    # Canlı özne + Duygu fiili = Yüksek uyum
    ("animate", "emotion"): {
        "compatibility": 0.95,
        "description": "Living beings can have emotions",
        "examples": ["ben seviyorum", "o seviyor"]
    },
    # Cansız özne + Duygu fiili = Düşük uyum
    ("inanimate", "emotion"): {
        "compatibility": 0.15,
        "description": "Objects cannot have emotions",
        "examples": ["masa seviyor (wrong)"]
    },
    # Canlı özne + Hareket fiili = Yüksek uyum
    ("animate", "motion"): {
        "compatibility": 0.90,
        "description": "Living beings can move",
        "examples": ["ben gidiyorum", "kedi geliyor"]
    },
    # Canlı özne + Tüketim fiili = Yüksek uyum
    ("animate", "consumption"): {
        "compatibility": 0.95,
        "description": "Living beings eat and drink",
        "examples": ["ben yiyorum", "o içiyor"]
    },
    # Yiyecek nesnesi + Tüketim fiili = Yüksek uyum
    ("food", "consumption"): {
        "compatibility": 0.98,
        "description": "Food is consumed",
        "examples": ["elma ye", "su iç"]
    },
    # Sıvı + İçme = Yüksek uyum
    ("liquid", "consumption"): {
        "compatibility": 0.95,
        "description": "Liquids are drunk",
        "examples": ["su iç", "çay iç"]
    },
    # Nesne + Bilişsel fiil = Orta uyum
    ("object", "cognitive"): {
        "compatibility": 0.85,
        "description": "Objects can be read/written",
        "examples": ["kitap oku", "mektup yaz"]
    },
    # Vücut parçası + Aksiyon = Orta-yüksek uyum
    ("body_part", "action"): {
        "compatibility": 0.75,
        "description": "Body parts can be acted upon",
        "examples": ["yüz yıka", "el yıka"]
    },
    # Sayı + Hareket = Düşük uyum
    ("number", "motion"): {
        "compatibility": 0.10,
        "description": "Numbers cannot move",
        "examples": []
    },
    # Konum + Hareket = Yüksek uyum (hedef olarak)
    ("location", "motion"): {
        "compatibility": 0.88,
        "description": "Locations are motion targets",
        "examples": ["eve git", "okula gel"]
    }
}

# -----------------------------
# 4. ENGLISH NGRAMS (İngilizce N-gram)
# İngilizce çevirilerin doğallık skoru
# -----------------------------
MOCK_ENGLISH_NGRAMS = {
    # Bigrams
    ("I", "love"): {"frequency": 125000, "type": "bigram"},
    ("I", "like"): {"frequency": 180000, "type": "bigram"},
    ("I", "eat"): {"frequency": 45000, "type": "bigram"},
    ("I", "drink"): {"frequency": 32000, "type": "bigram"},
    ("I", "go"): {"frequency": 95000, "type": "bigram"},
    ("I", "come"): {"frequency": 28000, "type": "bigram"},
    ("I", "read"): {"frequency": 38000, "type": "bigram"},
    ("I", "write"): {"frequency": 35000, "type": "bigram"},
    ("I", "wash"): {"frequency": 12000, "type": "bigram"},
    ("you", "love"): {"frequency": 85000, "type": "bigram"},
    ("you", "like"): {"frequency": 120000, "type": "bigram"},
    ("he", "loves"): {"frequency": 42000, "type": "bigram"},
    ("she", "loves"): {"frequency": 48000, "type": "bigram"},
    ("love", "face"): {"frequency": 8500, "type": "bigram"},
    ("love", "you"): {"frequency": 95000, "type": "bigram"},
    ("wash", "face"): {"frequency": 18000, "type": "bigram"},
    ("eat", "apple"): {"frequency": 12000, "type": "bigram"},
    ("drink", "water"): {"frequency": 25000, "type": "bigram"},
    ("read", "book"): {"frequency": 35000, "type": "bigram"},
    ("go", "home"): {"frequency": 55000, "type": "bigram"},
    ("go", "house"): {"frequency": 8000, "type": "bigram"},
    # Trigrams
    ("I", "love", "you"): {"frequency": 85000, "type": "trigram"},
    ("I", "like", "you"): {"frequency": 45000, "type": "trigram"},
    ("I", "wash", "face"): {"frequency": 5500, "type": "trigram"},
    ("I", "eat", "apple"): {"frequency": 3200, "type": "trigram"},
    ("I", "drink", "water"): {"frequency": 8500, "type": "trigram"},
    ("I", "read", "book"): {"frequency": 12000, "type": "trigram"},
    ("I", "go", "home"): {"frequency": 25000, "type": "trigram"}
}

# -----------------------------
# 5. GRAMMAR RULES (Dilbilgisi Kuralları)
# -----------------------------
MOCK_GRAMMAR_RULES = [
    {
        "id": "sov_to_svo",
        "pattern": "PRONOUN + NOUN + VERB",
        "tr_order": ["subject", "object", "predicate"],
        "en_order": ["subject", "predicate", "object"],
        "score_bonus": 20,
        "description": "Standard SOV to SVO conversion"
    },
    {
        "id": "sv_basic",
        "pattern": "PRONOUN + VERB",
        "tr_order": ["subject", "predicate"],
        "en_order": ["subject", "predicate"],
        "score_bonus": 15,
        "description": "Simple subject-verb sentence"
    },
    {
        "id": "sov_adj",
        "pattern": "PRONOUN + ADJECTIVE + NOUN + VERB",
        "tr_order": ["subject", "modifier", "object", "predicate"],
        "en_order": ["subject", "predicate", "modifier", "object"],
        "score_bonus": 25,
        "description": "SOV with adjective modifier"
    }
]


# =============================================================================
# SCORING FUNCTIONS (Puanlama Fonksiyonları)
# =============================================================================

# Ağırlıklar
SCORE_WEIGHTS = {
    "frequency": 0.25,        # Frekans: %25
    "collocation": 0.25,      # Eşdizim: %25
    "semantic": 0.20,         # Anlam uyumu: %20
    "pos_match": 0.15,        # Tür uyumu: %15
    "ngram": 0.15             # İngilizce doğallık: %15
}


def get_frequency_score(word: str, meaning_en: str) -> float:
    """Frekans tabanlı skor (0-100)."""
    if word in MOCK_WORDS:
        for m in MOCK_WORDS[word]["meanings"]:
            if m["en"] == meaning_en:
                return m["frequency"]
    return 10  # Bilinmeyen kelime için düşük skor


def get_collocation_score(word1: str, word2: str, meaning1: str = None) -> float:
    """Eşdizimlilik skoru (0-100)."""
    key = (word1, word2)
    reverse_key = (word2, word1)
    
    if key in MOCK_COLLOCATIONS:
        coll = MOCK_COLLOCATIONS[key]
        base_score = coll["strength"] * 100
        
        # Eğer anlam ipucu eşleşiyorsa bonus
        if meaning1 and "meaning_hint" in coll:
            if coll["meaning_hint"].get(word1) == meaning1:
                base_score *= 1.2  # %20 bonus
        
        return min(base_score, 100)
    
    if reverse_key in MOCK_COLLOCATIONS:
        return MOCK_COLLOCATIONS[reverse_key]["strength"] * 100 * 0.8  # Ters sıra için %80
    
    return 20  # Eşdizim bulunamadı


def get_semantic_compatibility_score(subject_class: str, verb_class: str) -> float:
    """Anlam uyumu skoru (0-100)."""
    key = (subject_class, verb_class)
    
    if key in MOCK_SEMANTIC_COMPATIBILITY:
        return MOCK_SEMANTIC_COMPATIBILITY[key]["compatibility"] * 100
    
    return 50  # Nötr uyum


def get_pos_match_score(word: str, meaning_en: str, expected_pos: str) -> float:
    """Tür uyumu skoru (0-100)."""
    if word in MOCK_WORDS:
        for m in MOCK_WORDS[word]["meanings"]:
            if m["en"] == meaning_en:
                if m["pos"] == expected_pos:
                    return 100
                elif m["pos"] in ["noun", "pronoun"] and expected_pos in ["noun", "pronoun"]:
                    return 80  # Yakın türler
                else:
                    return 30  # Tür uyumsuzluğu
    return 50


def get_ngram_score(words: List[str]) -> float:
    """İngilizce n-gram doğallık skoru (0-100)."""
    if len(words) < 2:
        return 50
    
    total_score = 0
    count = 0
    
    # Bigram skorları
    for i in range(len(words) - 1):
        key = (words[i], words[i+1])
        if key in MOCK_ENGLISH_NGRAMS:
            # Log frekans normalize
            freq = MOCK_ENGLISH_NGRAMS[key]["frequency"]
            score = min(100, math.log(freq + 1) * 10)
            total_score += score
            count += 1
    
    # Trigram skorları (bonus)
    for i in range(len(words) - 2):
        key = (words[i], words[i+1], words[i+2])
        if key in MOCK_ENGLISH_NGRAMS:
            freq = MOCK_ENGLISH_NGRAMS[key]["frequency"]
            score = min(100, math.log(freq + 1) * 12)  # Trigram bonus
            total_score += score
            count += 1
    
    return total_score / count if count > 0 else 30


def calculate_advanced_score(
    tr_words: List[str],
    en_translation: List[str],
    word_meanings: Dict[str, str]  # {tr_word: en_meaning}
) -> Tuple[float, Dict[str, float]]:
    """
    Gelişmiş puanlama: Tüm faktörleri birleştir.
    
    Returns:
        (total_score, score_breakdown)
    """
    scores = {}
    
    # 1. Frekans skoru
    freq_scores = []
    for tr_word, en_meaning in word_meanings.items():
        freq_scores.append(get_frequency_score(tr_word, en_meaning))
    scores["frequency"] = sum(freq_scores) / len(freq_scores) if freq_scores else 0
    
    # 2. Eşdizimlilik skoru
    coll_scores = []
    for i in range(len(tr_words) - 1):
        meaning = word_meanings.get(tr_words[i])
        coll_scores.append(get_collocation_score(tr_words[i], tr_words[i+1], meaning))
    scores["collocation"] = sum(coll_scores) / len(coll_scores) if coll_scores else 50
    
    # 3. Anlam uyumu skoru
    sem_scores = []
    if len(tr_words) >= 2:
        # Özne ve fiil sınıflarını bul
        subject_word = tr_words[0]
        verb_word = tr_words[-1]  # Türkçe'de fiil sonda
        
        subj_class = get_semantic_class(subject_word, word_meanings.get(subject_word, ""))
        verb_class = get_semantic_class(verb_word, word_meanings.get(verb_word, ""))
        
        sem_scores.append(get_semantic_compatibility_score(subj_class, verb_class))
        
        # Nesne-fiil uyumu
        if len(tr_words) >= 3:
            for obj_word in tr_words[1:-1]:
                obj_class = get_semantic_class(obj_word, word_meanings.get(obj_word, ""))
                sem_scores.append(get_semantic_compatibility_score(obj_class, verb_class))
    
    scores["semantic"] = sum(sem_scores) / len(sem_scores) if sem_scores else 50
    
    # 4. POS uyumu skoru
    pos_scores = []
    if len(tr_words) >= 1:
        # İlk kelime özne olmalı (pronoun/noun)
        pos_scores.append(get_pos_match_score(
            tr_words[0], 
            word_meanings.get(tr_words[0], ""),
            "pronoun"
        ))
    if len(tr_words) >= 2:
        # Son kelime fiil olmalı
        pos_scores.append(get_pos_match_score(
            tr_words[-1],
            word_meanings.get(tr_words[-1], ""),
            "verb"
        ))
    scores["pos_match"] = sum(pos_scores) / len(pos_scores) if pos_scores else 50
    
    # 5. N-gram skoru
    scores["ngram"] = get_ngram_score(en_translation)
    
    # Ağırlıklı toplam
    total = sum(scores[key] * SCORE_WEIGHTS[key] for key in scores)
    
    return total, scores


def get_semantic_class(word: str, meaning: str) -> str:
    """Kelimenin anlam sınıfını döndür."""
    if word in MOCK_WORDS:
        for m in MOCK_WORDS[word]["meanings"]:
            if m["en"] == meaning:
                return m.get("semantic_class", "unknown")
    return "unknown"


# =============================================================================
# ANA API FONKSİYONLARI
# =============================================================================

def find_word(word: str) -> Dict[str, Any]:
    """Kelimeyi bul ve tüm anlamları döndür."""
    if word in MOCK_WORDS:
        entry = MOCK_WORDS[word]
        return {
            "found": True,
            "tr": entry["tr"],
            "meanings": [
                {
                    "meaning": m["en"],
                    "type": m["pos"],
                    "score": m["frequency"],
                    "domain": m.get("domain", []),
                    "semantic_class": m.get("semantic_class", "unknown")
                }
                for m in entry["meanings"]
            ]
        }
    return {"found": False, "tr": word, "meanings": []}


def find_all_meanings(word: str) -> List[Dict[str, Any]]:
    """Kelimenin tüm anlamlarını skora göre sıralı döndür."""
    result = find_word(word)
    if result["found"]:
        meanings = result["meanings"]
        return sorted(meanings, key=lambda x: x["score"], reverse=True)
    return []


def get_collocation_hint(word1: str, word2: str) -> Optional[Dict[str, str]]:
    """İki kelime arasındaki eşdizim ipucunu döndür."""
    key = (word1, word2)
    if key in MOCK_COLLOCATIONS:
        return MOCK_COLLOCATIONS[key].get("meaning_hint")
    return None


def score_translation(
    tr_words: List[str],
    en_words: List[str],
    word_map: Dict[str, str]
) -> Dict[str, Any]:
    """
    Bir çeviriyi puanla.
    
    Args:
        tr_words: Türkçe kelime listesi
        en_words: İngilizce çeviri kelime listesi
        word_map: {türkçe: ingilizce} eşleşmeleri
    
    Returns:
        {total_score, breakdown, normalized_score}
    """
    total, breakdown = calculate_advanced_score(tr_words, en_words, word_map)
    
    return {
        "total_score": round(total, 2),
        "normalized_score": round(total / 100, 3),
        "breakdown": {k: round(v, 2) for k, v in breakdown.items()},
        "weights": SCORE_WEIGHTS
    }


# -----------------------------
# CLI için main fonksiyonu
# -----------------------------
def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "no_word"}))
        return

    word = sys.argv[1]
    result = find_word(word)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
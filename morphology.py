"""
Türkçe-İngilizce Morfoloji Modülü
=================================

Türkçe fiil çekimlerini analiz eder ve İngilizce'ye dönüştürür.

Örnek:
    geliyorum → I am coming
    gittim    → I went
    yapacak   → he/she will do
"""

from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict
import re


# =============================================================================
# VERİ YAPILARI
# =============================================================================

@dataclass
class TurkishMorpheme:
    """Türkçe morfolojik analiz sonucu."""
    root: str                    # Fiil kökü: gel, git, yap
    tense: str                   # Zaman: present_cont, past_simple, future, aorist
    person: int                  # Şahıs: 1, 2, 3
    plurality: str               # Tekil/Çoğul: singular, plural
    negation: bool               # Olumsuz mu: gelmiyor
    question: bool               # Soru mu: geliyor mu
    original: str                # Orijinal kelime


@dataclass
class EnglishConjugation:
    """İngilizce fiil çekimi sonucu."""
    subject: str                 # I, you, he/she/it, we, they
    auxiliary: Optional[str]     # am, is, are, will, did, have
    verb: str                    # come, coming, came, gone
    full_form: str               # "I am coming", "he went"


# =============================================================================
# TÜRKÇE ZAMAN EKLERİ
# =============================================================================

# Zaman ekleri (regex pattern → zaman adı)
TURKISH_TENSE_SUFFIXES = [
    # Present Continuous: -iyor, -ıyor, -uyor, -üyor
    (r'[iıuü]yor', 'present_continuous'),
    
    # Past Simple: -di, -dı, -du, -dü, -ti, -tı, -tu, -tü
    (r'[dt][iıuü]', 'past_simple'),
    
    # Future: -ecek, -acak
    (r'[ea]cek', 'future'),
    (r'[ea]cağ', 'future'),  # gelecağım gibi
    
    # Reported Past: -miş, -mış, -muş, -müş
    (r'm[iıuü]ş', 'past_reported'),
    
    # Aorist (Geniş Zaman): -er, -ar, -ır, -ir, -ur, -ür, -r
    (r'[eaıiuü]r', 'aorist'),
    
    # Necessity: -meli, -malı
    (r'm[ea]l[iı]', 'necessity'),
    
    # Ability: -ebil, -abil
    (r'[ea]bil', 'ability'),
]

# Şahıs ekleri (zaman sonrası)
TURKISH_PERSON_SUFFIXES = {
    # Present Continuous için: -um, -sun, -, -uz, -sunuz, -lar
    'present_continuous': [
        (r'um$', 1, 'singular'),
        (r'ım$', 1, 'singular'),
        (r'sun$', 2, 'singular'),
        (r'sın$', 2, 'singular'),
        (r'$', 3, 'singular'),  # geliyor (ek yok)
        (r'uz$', 1, 'plural'),
        (r'sunuz$', 2, 'plural'),
        (r'sınız$', 2, 'plural'),
        (r'lar$', 3, 'plural'),
        (r'ler$', 3, 'plural'),
    ],
    # Past Simple için: -m, -n, -, -k, -nız, -lar
    'past_simple': [
        (r'm$', 1, 'singular'),
        (r'n$', 2, 'singular'),
        (r'$', 3, 'singular'),
        (r'k$', 1, 'plural'),
        (r'n[iı]z$', 2, 'plural'),
        (r'lar$', 3, 'plural'),
        (r'ler$', 3, 'plural'),
    ],
    # Future için: -ım, -sın, -, -ız, -sınız, -lar
    'future': [
        (r'[iıuü]m$', 1, 'singular'),
        (r's[iıuü]n$', 2, 'singular'),
        (r'$', 3, 'singular'),
        (r'[iıuü]z$', 1, 'plural'),
        (r's[iıuü]n[iı]z$', 2, 'plural'),
        (r'lar$', 3, 'plural'),
        (r'ler$', 3, 'plural'),
    ],
    # Aorist için: -ım, -sın, -, -ız, -sınız, -lar  
    'aorist': [
        (r'[iıuü]m$', 1, 'singular'),
        (r's[iıuü]n$', 2, 'singular'),
        (r'$', 3, 'singular'),
        (r'[iıuü]z$', 1, 'plural'),
        (r's[iıuü]n[iı]z$', 2, 'plural'),
        (r'lar$', 3, 'plural'),
        (r'ler$', 3, 'plural'),
    ],
}

# Olumsuzluk eki
NEGATION_SUFFIX = r'm[iıuü]yor|m[ea]|m[iıuü]ş|m[ea]z'


# =============================================================================
# İNGİLİZCE DÜZENSİZ FİİLLER
# =============================================================================

IRREGULAR_VERBS = {
    # base: (past_simple, past_participle, present_participle)
    'be': ('was/were', 'been', 'being'),
    'come': ('came', 'come', 'coming'),
    'go': ('went', 'gone', 'going'),
    'eat': ('ate', 'eaten', 'eating'),
    'drink': ('drank', 'drunk', 'drinking'),
    'give': ('gave', 'given', 'giving'),
    'take': ('took', 'taken', 'taking'),
    'make': ('made', 'made', 'making'),
    'do': ('did', 'done', 'doing'),
    'see': ('saw', 'seen', 'seeing'),
    'have': ('had', 'had', 'having'),
    'get': ('got', 'gotten', 'getting'),
    'read': ('read', 'read', 'reading'),
    'write': ('wrote', 'written', 'writing'),
    'run': ('ran', 'run', 'running'),
    'swim': ('swam', 'swum', 'swimming'),
    'buy': ('bought', 'bought', 'buying'),
    'sell': ('sold', 'sold', 'selling'),
    'say': ('said', 'said', 'saying'),
    'tell': ('told', 'told', 'telling'),
    'think': ('thought', 'thought', 'thinking'),
    'know': ('knew', 'known', 'knowing'),
    'understand': ('understood', 'understood', 'understanding'),
    'find': ('found', 'found', 'finding'),
    'leave': ('left', 'left', 'leaving'),
    'feel': ('felt', 'felt', 'feeling'),
    'put': ('put', 'put', 'putting'),
    'sit': ('sat', 'sat', 'sitting'),
    'stand': ('stood', 'stood', 'standing'),
    'sleep': ('slept', 'slept', 'sleeping'),
    'wake': ('woke', 'woken', 'waking'),
}


# =============================================================================
# TÜRKÇE MORFOLOJİ ANALİZİ
# =============================================================================

class TurkishMorphologyAnalyzer:
    """Türkçe fiil morfolojisi analiz sınıfı."""
    
    def __init__(self):
        self.verb_roots = self._load_verb_roots()
    
    def _load_verb_roots(self) -> Dict[str, str]:
        """Bilinen fiil köklerini yükle (Türkçe → İngilizce)."""
        return {
            'gel': 'come',
            'git': 'go',
            'ye': 'eat',
            'iç': 'drink',
            'ic': 'drink',
            'yap': 'do',
            'al': 'take',
            'ver': 'give',
            'oku': 'read',
            'yaz': 'write',
            'sev': 'love',
            'gör': 'see',
            'gor': 'see',
            'bil': 'know',
            'de': 'say',
            'söyle': 'tell',
            'soyle': 'tell',
            'düşün': 'think',
            'dusun': 'think',
            'anla': 'understand',
            'bul': 'find',
            'bırak': 'leave',
            'birak': 'leave',
            'hisset': 'feel',
            'koy': 'put',
            'otur': 'sit',
            'kalk': 'stand',
            'uyu': 'sleep',
            'uyan': 'wake',
            'koş': 'run',
            'kos': 'run',
            'yüz': 'swim',
            'yuz': 'swim',
            'satın al': 'buy',
            'sat': 'sell',
            'yıka': 'wash',
            'yika': 'wash',
            'oyna': 'play',
            'çalış': 'work',
            'calis': 'work',
            'konuş': 'speak',
            'konus': 'speak',
            'dinle': 'listen',
            'bekle': 'wait',
            'başla': 'start',
            'basla': 'start',
            'bitir': 'finish',
            'aç': 'open',
            'ac': 'open',
            'kapat': 'close',
            'öğren': 'learn',
            'ogren': 'learn',
            'öğret': 'teach',
            'ogret': 'teach',
            'hatırla': 'remember',
            'hatirla': 'remember',
            'unut': 'forget',
        }
    
    def analyze(self, word: str) -> Optional[TurkishMorpheme]:
        """
        Türkçe fiili analiz et.
        
        Args:
            word: Çekimli Türkçe fiil (ör: "geliyorum")
            
        Returns:
            TurkishMorpheme veya None
        """
        original = word
        word = word.lower()
        
        # Olumsuzluk kontrolü
        negation = False
        if re.search(NEGATION_SUFFIX, word):
            negation = True
            # Olumsuzluk ekini kaldır (basit yaklaşım)
            word = re.sub(r'm(?=[iıuü]yor|[ea]|[iıuü]ş|[ea]z)', '', word, count=1)
        
        # Zaman ekini bul
        tense = None
        tense_match_end = len(word)
        
        for pattern, tense_name in TURKISH_TENSE_SUFFIXES:
            match = re.search(pattern, word)
            if match:
                tense = tense_name
                tense_match_end = match.start()
                break
        
        if not tense:
            # Zaman eki bulunamadı, mastar olabilir
            return None
        
        # Kökü çıkar
        potential_root = word[:tense_match_end]
        
        # Bilinen köklerle eşleştir
        root = None
        for known_root in sorted(self.verb_roots.keys(), key=len, reverse=True):
            if potential_root.endswith(known_root) or potential_root == known_root:
                root = known_root
                break
            # Ünlü uyumu nedeniyle değişmiş olabilir
            if self._vowel_harmony_match(potential_root, known_root):
                root = known_root
                break
        
        if not root:
            # Kök bulunamadı, potential_root'u kullan
            root = potential_root if potential_root else word[:2]
        
        # Şahıs ekini bul
        person = 3
        plurality = 'singular'
        
        suffix_after_tense = word[tense_match_end:]
        person_patterns = TURKISH_PERSON_SUFFIXES.get(tense, TURKISH_PERSON_SUFFIXES['present_continuous'])
        
        for pattern, p, plur in person_patterns:
            if re.search(pattern, suffix_after_tense):
                person = p
                plurality = plur
                break
        
        return TurkishMorpheme(
            root=root,
            tense=tense,
            person=person,
            plurality=plurality,
            negation=negation,
            question=False,  # TODO: soru eki analizi
            original=original
        )
    
    def _vowel_harmony_match(self, word: str, root: str) -> bool:
        """Ünlü uyumu kontrolü."""
        # Basit kontrol: ilk birkaç karakter eşleşiyor mu
        min_len = min(len(word), len(root), 3)
        return word[:min_len] == root[:min_len]


# =============================================================================
# İNGİLİZCE FİİL ÇEKİMİ
# =============================================================================

class EnglishConjugator:
    """İngilizce fiil çekim sınıfı."""
    
    def __init__(self):
        self.irregular = IRREGULAR_VERBS
    
    def get_subject(self, person: int, plurality: str) -> str:
        """Şahıs zamirine dönüştür."""
        if plurality == 'singular':
            return {1: 'I', 2: 'you', 3: 'he/she'}[person]
        else:
            return {1: 'we', 2: 'you', 3: 'they'}[person]
    
    def get_present_participle(self, verb: str) -> str:
        """Present participle (V-ing) formu."""
        if verb in self.irregular:
            return self.irregular[verb][2]
        
        # Düzenli kurallar
        if verb.endswith('e') and not verb.endswith('ee'):
            return verb[:-1] + 'ing'
        elif verb.endswith('ie'):
            return verb[:-2] + 'ying'
        elif len(verb) >= 2 and verb[-1] in 'bdfglmnprst' and verb[-2] in 'aeiou':
            # CVC pattern - son harfi ikile
            return verb + verb[-1] + 'ing'
        else:
            return verb + 'ing'
    
    def get_past_simple(self, verb: str, person: int = 3) -> str:
        """Past simple formu."""
        if verb in self.irregular:
            past = self.irregular[verb][0]
            # was/were özel durumu
            if '/' in past:
                if person == 1 or person == 3:
                    return past.split('/')[0]  # was
                else:
                    return past.split('/')[1]  # were
            return past
        
        # Düzenli fiiller
        if verb.endswith('e'):
            return verb + 'd'
        elif verb.endswith('y') and len(verb) > 1 and verb[-2] not in 'aeiou':
            return verb[:-1] + 'ied'
        elif len(verb) >= 2 and verb[-1] in 'bdfglmnprst' and verb[-2] in 'aeiou':
            return verb + verb[-1] + 'ed'
        else:
            return verb + 'ed'
    
    def get_third_person_singular(self, verb: str) -> str:
        """3. tekil şahıs present simple (he goes, she watches)."""
        if verb in ['have']:
            return 'has'
        elif verb in ['be']:
            return 'is'
        elif verb in ['do']:
            return 'does'
        elif verb.endswith(('s', 'sh', 'ch', 'x', 'z', 'o')):
            return verb + 'es'
        elif verb.endswith('y') and len(verb) > 1 and verb[-2] not in 'aeiou':
            return verb[:-1] + 'ies'
        else:
            return verb + 's'
    
    def conjugate(self, verb: str, tense: str, person: int, plurality: str, 
                  negation: bool = False) -> EnglishConjugation:
        """
        İngilizce fiil çekimi yap.
        
        Args:
            verb: Fiil kökü (come, go, eat)
            tense: Zaman (present_continuous, past_simple, future, aorist)
            person: Şahıs (1, 2, 3)
            plurality: Tekil/Çoğul (singular, plural)
            negation: Olumsuz mu
            
        Returns:
            EnglishConjugation
        """
        subject = self.get_subject(person, plurality)
        auxiliary = None
        conjugated_verb = verb
        
        # Zaman bazlı çekim
        if tense == 'present_continuous':
            # I am coming, you are going
            if person == 1 and plurality == 'singular':
                auxiliary = "am not" if negation else "am"
            elif person == 3 and plurality == 'singular':
                auxiliary = "is not" if negation else "is"
            else:
                auxiliary = "are not" if negation else "are"
            conjugated_verb = self.get_present_participle(verb)
            
        elif tense == 'past_simple':
            # I went, you ate
            if negation:
                auxiliary = "did not"
                conjugated_verb = verb  # did not go
            else:
                conjugated_verb = self.get_past_simple(verb, person)
                
        elif tense == 'future':
            # I will come, you will go
            auxiliary = "will not" if negation else "will"
            conjugated_verb = verb
            
        elif tense == 'aorist':
            # Present simple: I go, he goes
            if negation:
                if person == 3 and plurality == 'singular':
                    auxiliary = "does not"
                else:
                    auxiliary = "do not"
                conjugated_verb = verb
            else:
                if person == 3 and plurality == 'singular':
                    conjugated_verb = self.get_third_person_singular(verb)
                else:
                    conjugated_verb = verb
                    
        elif tense == 'past_reported':
            # Turkish -miş → English present perfect or past
            if negation:
                if person == 3 and plurality == 'singular':
                    auxiliary = "has not"
                else:
                    auxiliary = "have not"
            else:
                if person == 3 and plurality == 'singular':
                    auxiliary = "has"
                else:
                    auxiliary = "have"
            # Past participle
            if verb in self.irregular:
                conjugated_verb = self.irregular[verb][1]
            else:
                conjugated_verb = self.get_past_simple(verb)
                
        elif tense == 'necessity':
            # -meli/-malı → should
            auxiliary = "should not" if negation else "should"
            conjugated_verb = verb
            
        elif tense == 'ability':
            # -ebil/-abil → can
            auxiliary = "cannot" if negation else "can"
            conjugated_verb = verb
        
        # Tam formu oluştur
        if auxiliary:
            full_form = f"{subject} {auxiliary} {conjugated_verb}"
        else:
            full_form = f"{subject} {conjugated_verb}"
        
        return EnglishConjugation(
            subject=subject,
            auxiliary=auxiliary,
            verb=conjugated_verb,
            full_form=full_form
        )


# =============================================================================
# ANA TRANSLATOR
# =============================================================================

class MorphologyTranslator:
    """Morfoloji tabanlı çevirmen."""
    
    def __init__(self, verb_dictionary: Optional[Dict[str, str]] = None):
        self.analyzer = TurkishMorphologyAnalyzer()
        self.conjugator = EnglishConjugator()
        
        # Özel sözlük varsa ekle
        if verb_dictionary:
            self.analyzer.verb_roots.update(verb_dictionary)
    
    def translate_verb(self, turkish_verb: str) -> Optional[Tuple[str, dict]]:
        """
        Çekimli Türkçe fiili İngilizce'ye çevir.
        
        Args:
            turkish_verb: Çekimli Türkçe fiil (ör: "geliyorum")
            
        Returns:
            (İngilizce çeviri, analiz detayları) veya None
        """
        # Morfolojik analiz
        morpheme = self.analyzer.analyze(turkish_verb)
        
        if not morpheme:
            return None
        
        # Türkçe kökü İngilizce'ye çevir
        english_root = self.analyzer.verb_roots.get(morpheme.root)
        
        if not english_root:
            return None
        
        # İngilizce çekim yap
        conjugation = self.conjugator.conjugate(
            verb=english_root,
            tense=morpheme.tense,
            person=morpheme.person,
            plurality=morpheme.plurality,
            negation=morpheme.negation
        )
        
        details = {
            'turkish_root': morpheme.root,
            'english_root': english_root,
            'tense': morpheme.tense,
            'person': morpheme.person,
            'plurality': morpheme.plurality,
            'negation': morpheme.negation,
            'subject': conjugation.subject,
            'auxiliary': conjugation.auxiliary,
            'verb_form': conjugation.verb
        }
        
        return (conjugation.full_form, details)
    
    def translate_sentence(self, sentence: str) -> str:
        """
        Basit cümle çevirisi.
        Şimdilik sadece fiil çekimini işler.
        """
        words = sentence.lower().split()
        translations = []
        
        for word in words:
            result = self.translate_verb(word)
            if result:
                translations.append(result[0])
            else:
                # Fiil değilse olduğu gibi bırak (veya sözlükten ara)
                translations.append(word)
        
        return ' '.join(translations)


# =============================================================================
# TEST
# =============================================================================

def test_morphology():
    """Morfoloji modülünü test et."""
    translator = MorphologyTranslator()
    
    test_cases = [
        # Present Continuous
        "geliyorum",      # I am coming
        "gidiyorsun",     # you are going
        "yiyor",          # he/she is eating
        "yapıyoruz",      # we are doing
        "okuyorlar",      # they are reading
        
        # Past Simple
        "geldim",         # I came
        "gittin",         # you went
        "yedi",           # he/she ate
        "yaptık",         # we did
        "okudular",       # they read
        
        # Future
        "geleceğim",      # I will come
        "gideceksin",     # you will go
        "yapacak",        # he/she will do
        
        # Aorist (Present Simple)
        "gelirim",        # I come
        "gidersin",       # you go
        "yapar",          # he/she does
        
        # Negation
        "gelmiyorum",     # I am not coming
        "gitmedim",       # I did not go
        "yapmayacak",     # he/she will not do
        
        # Necessity
        "gelmeliyim",     # I should come
        "gitmelisin",     # you should go
    ]
    
    print("="*70)
    print("MORFOLOJİ TESTİ")
    print("="*70)
    
    for word in test_cases:
        result = translator.translate_verb(word)
        if result:
            translation, details = result
            print(f"\n{word:15} → {translation}")
            print(f"   Kök: {details['turkish_root']} → {details['english_root']}")
            print(f"   Zaman: {details['tense']}, Şahıs: {details['person']}, {details['plurality']}")
            if details['negation']:
                print(f"   [OLUMSUZ]")
        else:
            print(f"\n{word:15} → [Analiz edilemedi]")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    test_morphology()

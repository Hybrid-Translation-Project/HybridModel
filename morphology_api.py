"""
Morfoloji API - MongoDB Entegrasyonu
====================================

Bu modül, morfoloji verilerini MongoDB'den okur ve Prolog'a sağlar.

Kullanım:
    from morphology_api import MorphologyDB
    
    db = MorphologyDB()
    verb_roots = db.get_all_verb_roots()
    tense_suffixes = db.get_all_tense_suffixes()
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json

# MongoDB bağlantısı
try:
    from pymongo import MongoClient
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False

# =============================================================================
# VERİ YAPILARI
# =============================================================================

@dataclass
class VerbRoot:
    """Fiil kökü."""
    tr: str
    en: str
    type: str  # regular, irregular
    note: str = ""

@dataclass
class IrregularVerb:
    """İngilizce düzensiz fiil."""
    base: str
    past: str
    past_participle: str
    present_participle: str

@dataclass
class TenseSuffix:
    """Türkçe zaman eki."""
    suffix: str
    tense: str
    priority: int
    description: str = ""

@dataclass
class PersonSuffix:
    """Türkçe şahıs eki."""
    suffix: str
    person: int
    plurality: str
    tense: str

@dataclass
class TurkishIrregularRoot:
    """Türkçe düzensiz kök değişimi."""
    alternate: str
    canonical: str
    context: str
    description: str = ""

@dataclass
class AuxiliaryVerb:
    """İngilizce yardımcı fiil."""
    tense: str
    person: Optional[int]
    plurality: Optional[str]
    negation: bool
    auxiliary: str

@dataclass
class PhonologyRule:
    """Ses bilgisi kuralı (Türkçe ve İngilizce)."""
    language: str           # "turkish" veya "english"
    rule_name: str          # Kural adı: "vowel_harmony", "consonant_softening"
    rule_type: str          # Kural tipi: "vowel", "consonant", "buffer"
    context: str            # Uygulama bağlamı: "before_vowel", "suffix_attachment"
    condition: Dict[str, Any]   # Koşul: {"last_vowel": ["a", "ı"], "final_consonant": ["p", "t"]}
    action: Dict[str, Any]      # Eylem: {"replace": {"from": "t", "to": "d"}}
    priority: int           # Öncelik (yüksek = önce uygula)
    description: str = ""   # Açıklama

@dataclass
class AoristIrregularVerb:
    """Geniş zaman istisna fiili (13 önemli fiil)."""
    root: str               # Fiil kökü: "al", "gel", "gör"
    aorist_suffix: str      # Aldığı ek: "ır", "ir", "ur", "ür"
    example: str            # Örnek: "alır", "gelir"
    en: str                 # İngilizce karşılığı
    note: str = ""          # Not

@dataclass
class VowelHarmonyException:
    """Ünlü uyumu istisnası (alıntı kelimeler)."""
    word: str               # Kelime: "saat", "hayal"
    plural: str = ""        # Çoğul: "saatler"
    possessive: str = ""    # İyelik: "kalbi"
    wrong: str = ""         # Yanlış form: "saatlar"
    origin: str = ""        # Köken: "arabic", "french"
    exception_type: str = ""  # Tip: "plural", "possessive"

@dataclass
class ConsonantMutationException:
    """Ünsüz yumuşaması istisnası."""
    word: str               # Kelime: "top", "hukuk"
    with_suffix: str        # Ekli hali: "topu", "hukuku"
    wrong: str              # Yanlış form: "tobu", "hukuğu"
    rule: str               # Kural: "monosyllable", "loanword"
    description: str = ""   # Açıklama

@dataclass
class VowelDropWord:
    """Ünlü düşmesi olan kelime."""
    base: str               # Tam hali: "burun"
    stem: str               # Kök: "burn"
    example_suffix: str     # Örnek ek: "u"
    result: str             # Sonuç: "burnu"
    wrong: str              # Yanlış: "burunu"
    vowel_dropped: str      # Düşen ünlü: "u"
    type: str = "noun"      # Tip: "noun" veya "verb"


# YENİ DATACLASSLAR

@dataclass
class CaseSuffix:
    """İsim çekim eki (hal eki)."""
    case: str               # nominative, dative, locative, ablative, accusative, genitive
    suffixes: List[str]     # ["e", "a", "ye", "ya"]
    english_prep: str       # "to", "in/on/at", "from", "the", "of"
    harmony_type: str       # back_front, fourfold
    description: str = ""

@dataclass
class PossessiveSuffix:
    """İyelik eki."""
    person: int             # 1, 2, 3
    plurality: str          # singular, plural
    suffixes: List[str]     # ["im", "ım", "um", "üm"]
    english: str            # my, your, his/her/its, our, their
    harmony_type: str

@dataclass
class NegationSuffix:
    """Olumsuzluk eki."""
    type: str               # verb_general, aorist_negative, copula_negative, existential_negative
    suffixes: List[str] = None  # ["me", "ma"] veya ["mez", "maz"]
    word: str = ""          # "değil", "yok"
    english_aux: str = ""   # "not", "does not"
    harmony_type: str = ""

@dataclass
class QuestionParticle:
    """Soru eki."""
    suffixes: List[str]     # ["mı", "mi", "mu", "mü"]
    harmony_type: str
    person: int = None
    plurality: str = None
    description: str = ""

@dataclass
class Postposition:
    """Edat."""
    tr: str                 # ile, için, kadar
    english: str            # with/by, for, until
    type: str               # attached, separate
    suffixes: List[str] = None  # ["la", "le"] (bitişik için)
    case_required: str = "" # nominative, dative, ablative

@dataclass
class Conjunction:
    """Bağlaç."""
    tr: str                 # ve, ama, çünkü
    english: str            # and, but, because
    type: str               # coordinating, subordinating, correlative

@dataclass
class CopulaSuffix:
    """Ek-fiil eki (isim cümlelerinde 'to be' karşılığı)."""
    person: int             # 1, 2, 3
    plurality: str          # singular, plural
    tense: str              # present, past
    suffixes: List[str]     # ["im", "ım", "um", "üm"]
    english: str            # am, are, is, was, were
    harmony_type: str

@dataclass
class ArticleRule:
    """İngilizce article (a/an/the) kuralı."""
    condition: str          # accusative_suffix, no_accusative_suffix, vowel_initial
    article: str            # a, an, the, no article
    description: str

@dataclass
class BufferConsonantException:
    """Kaynaştırma ünsüzü istisnası (su, ne, bu, şu, o)."""
    word: str               # su, ne
    buffer_consonant: str   # y, n
    normal_rule: str        # Normalde hangi kural
    exception_cases: List[str]  # genitive, possessive, oblique_cases

@dataclass
class PluralSuffix:
    """Çoğul eki."""
    suffixes: List[str]     # ["ler", "lar"]
    harmony_type: str       # back_front
    english_suffix: str     # s/es
    back_vowels: List[str] = None
    front_vowels: List[str] = None


@dataclass
class NounRoot:
    """İsim kökü."""
    tr: str                 # ev, kitap, okul
    en: str                 # house, book, school
    en_plural: str          # houses, books, schools
    category: str           # place, object, person, animal, food, abstract, body
    vowel_type: str         # front, back


# =============================================================================
# MONGODB BAĞLANTISI
# =============================================================================

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "translator_db"


class MorphologyDB:
    """Morfoloji veritabanı erişim sınıfı."""
    
    def __init__(self, uri: str = MONGO_URI, db_name: str = DB_NAME, use_mock: bool = False):
        self.use_mock = use_mock or not PYMONGO_AVAILABLE
        self.client = None
        self.db = None
        
        if not self.use_mock:
            try:
                self.client = MongoClient(uri, serverSelectionTimeoutMS=2000)
                self.client.admin.command('ping')
                self.db = self.client[db_name]
            except Exception as e:
                print(f"[UYARI] MongoDB bağlantısı kurulamadı: {e}")
                print("[INFO] Mock data kullanılacak.")
                self.use_mock = True
    
    # =========================================================================
    # VERB ROOTS
    # =========================================================================
    
    def get_all_verb_roots(self) -> List[VerbRoot]:
        """Tüm fiil köklerini getir."""
        if self.use_mock:
            return self._mock_verb_roots()
        
        cursor = self.db.verb_roots.find({})
        return [VerbRoot(
            tr=doc["tr"],
            en=doc["en"],
            type=doc["type"],
            note=doc.get("note", "")
        ) for doc in cursor]
    
    def get_verb_root(self, tr: str) -> Optional[VerbRoot]:
        """Belirli bir Türkçe kökün İngilizce karşılığını getir."""
        if self.use_mock:
            roots = [r for r in self._mock_verb_roots() if r.tr == tr]
            return roots[0] if roots else None
        
        doc = self.db.verb_roots.find_one({"tr": tr})
        if doc:
            return VerbRoot(
                tr=doc["tr"],
                en=doc["en"],
                type=doc["type"],
                note=doc.get("note", "")
            )
        return None
    
    # =========================================================================
    # IRREGULAR VERBS
    # =========================================================================
    
    def get_all_irregular_verbs(self) -> List[IrregularVerb]:
        """Tüm düzensiz fiilleri getir."""
        if self.use_mock:
            return self._mock_irregular_verbs()
        
        cursor = self.db.irregular_verbs.find({})
        return [IrregularVerb(
            base=doc["base"],
            past=doc["past"],
            past_participle=doc["past_participle"],
            present_participle=doc["present_participle"]
        ) for doc in cursor]
    
    def get_irregular_verb(self, base: str) -> Optional[IrregularVerb]:
        """Belirli bir düzensiz fiili getir."""
        if self.use_mock:
            verbs = [v for v in self._mock_irregular_verbs() if v.base == base]
            return verbs[0] if verbs else None
        
        doc = self.db.irregular_verbs.find_one({"base": base})
        if doc:
            return IrregularVerb(
                base=doc["base"],
                past=doc["past"],
                past_participle=doc["past_participle"],
                present_participle=doc["present_participle"]
            )
        return None
    
    # =========================================================================
    # TENSE SUFFIXES
    # =========================================================================
    
    def get_all_tense_suffixes(self) -> List[TenseSuffix]:
        """Tüm zaman eklerini getir (öncelik sırasına göre)."""
        if self.use_mock:
            return self._mock_tense_suffixes()
        # DÜZELTME BURADA: 1 yerine -1 yaptık (Descending/Azalan sıralama)
        # Böylece Priority yüksek olanlar en üste çıkacak yoksa was were çalışmıyordu.
        cursor = self.db.tense_suffixes.find({}).sort("priority", -1)
        return [TenseSuffix(
            suffix=doc["suffix"],
            tense=doc["tense"],
            priority=doc["priority"],
            description=doc.get("description", "")
        ) for doc in cursor]
    
    def get_tense_suffixes_by_tense(self, tense: str) -> List[TenseSuffix]:
        """Belirli bir zaman için tüm ekleri getir."""
        all_suffixes = self.get_all_tense_suffixes()
        return [s for s in all_suffixes if s.tense == tense]
    
    # =========================================================================
    # PERSON SUFFIXES
    # =========================================================================
    
    def get_all_person_suffixes(self) -> List[PersonSuffix]:
        """Tüm şahıs eklerini getir."""
        if self.use_mock:
            return self._mock_person_suffixes()
        
        cursor = self.db.person_suffixes.find({})
        return [PersonSuffix(
            suffix=doc["suffix"],
            person=doc["person"],
            plurality=doc["plurality"],
            tense=doc["tense"]
        ) for doc in cursor]
    
    def get_person_suffixes_by_tense(self, tense: str) -> List[PersonSuffix]:
        """Belirli bir zaman için şahıs eklerini getir."""
        all_suffixes = self.get_all_person_suffixes()
        return [s for s in all_suffixes if s.tense == tense]
    
    # =========================================================================
    # TURKISH IRREGULAR ROOTS
    # =========================================================================
    
    def get_all_turkish_irregular_roots(self) -> List[TurkishIrregularRoot]:
        """Tüm Türkçe düzensiz kök değişimlerini getir."""
        if self.use_mock:
            return self._mock_turkish_irregular_roots()
        
        cursor = self.db.turkish_irregular_roots.find({})
        return [TurkishIrregularRoot(
            alternate=doc["alternate"],
            canonical=doc["canonical"],
            context=doc["context"],
            description=doc.get("description", "")
        ) for doc in cursor]
    
    def get_canonical_root(self, alternate: str) -> Optional[str]:
        """Alternatif kökten kanonik köke dönüştür."""
        if self.use_mock:
            roots = [r for r in self._mock_turkish_irregular_roots() if r.alternate == alternate]
            return roots[0].canonical if roots else None
        
        doc = self.db.turkish_irregular_roots.find_one({"alternate": alternate})
        return doc["canonical"] if doc else None
    
    # =========================================================================
    # AUXILIARY VERBS
    # =========================================================================
    
    def get_all_auxiliary_verbs(self) -> List[AuxiliaryVerb]:
        """Tüm yardımcı fiilleri getir."""
        if self.use_mock:
            return self._mock_auxiliary_verbs()
        
        cursor = self.db.auxiliary_verbs.find({})
        return [AuxiliaryVerb(
            tense=doc["tense"],
            person=doc.get("person"),
            plurality=doc.get("plurality"),
            negation=doc["negation"],
            auxiliary=doc["auxiliary"]
        ) for doc in cursor]
    
    def get_auxiliary(self, tense: str, person: int, plurality: str, negation: bool) -> Optional[str]:
        """Belirli durum için yardımcı fiili getir."""
        all_aux = self.get_all_auxiliary_verbs()
        for aux in all_aux:
            if aux.tense == tense and aux.negation == negation:
                if aux.person is None or (aux.person == person and aux.plurality == plurality):
                    return aux.auxiliary
        return None
    
    # =========================================================================
    # PHONOLOGY RULES
    # =========================================================================
    
    def get_all_phonology_rules(self) -> List[PhonologyRule]:
        """Tüm fonoloji kurallarını getir (öncelik sırasına göre)."""
        if self.use_mock:
            return self._mock_phonology_rules()
        
        cursor = self.db.phonology_rules.find({}).sort("priority", -1)  # Yüksek öncelik önce
        return [PhonologyRule(
            language=doc["language"],
            rule_name=doc["rule_name"],
            rule_type=doc["rule_type"],
            context=doc["context"],
            condition=doc["condition"],
            action=doc["action"],
            priority=doc["priority"],
            description=doc.get("description", "")
        ) for doc in cursor]
    
    def get_phonology_rules_by_language(self, language: str) -> List[PhonologyRule]:
        """Belirli bir dil için fonoloji kurallarını getir."""
        all_rules = self.get_all_phonology_rules()
        return [r for r in all_rules if r.language == language]
    
    def get_phonology_rules_by_type(self, rule_type: str) -> List[PhonologyRule]:
        """Belirli bir kural tipi için fonoloji kurallarını getir."""
        all_rules = self.get_all_phonology_rules()
        return [r for r in all_rules if r.rule_type == rule_type]
    
    # =========================================================================
    # AORIST IRREGULAR VERBS (13 Önemli Fiil)
    # =========================================================================
    
    def get_all_aorist_irregular_verbs(self) -> List[AoristIrregularVerb]:
        """Geniş zaman istisna fiillerini getir."""
        if self.use_mock:
            return []  # Mock için boş liste
        
        cursor = self.db.aorist_irregular_verbs.find({})
        return [AoristIrregularVerb(
            root=doc["root"],
            aorist_suffix=doc["aorist_suffix"],
            example=doc["example"],
            en=doc["en"],
            note=doc.get("note", "")
        ) for doc in cursor]
    
    def is_aorist_irregular(self, root: str) -> bool:
        """Verilen kökün geniş zaman istisnası olup olmadığını kontrol et."""
        irregulars = self.get_all_aorist_irregular_verbs()
        return any(v.root == root for v in irregulars)
    
    def get_aorist_suffix_for_irregular(self, root: str) -> Optional[str]:
        """İstisna fiil için doğru geniş zaman ekini döndür."""
        irregulars = self.get_all_aorist_irregular_verbs()
        for v in irregulars:
            if v.root == root:
                return v.aorist_suffix
        return None
    
    # =========================================================================
    # VOWEL HARMONY EXCEPTIONS (Alıntı Kelimeler)
    # =========================================================================
    
    def get_all_vowel_harmony_exceptions(self) -> List[VowelHarmonyException]:
        """Ünlü uyumu istisnalarını getir."""
        if self.use_mock:
            return []
        
        cursor = self.db.vowel_harmony_exceptions.find({})
        return [VowelHarmonyException(
            word=doc["word"],
            plural=doc.get("plural", ""),
            possessive=doc.get("possessive", ""),
            wrong=doc.get("wrong", ""),
            origin=doc.get("origin", ""),
            exception_type=doc.get("exception_type", "")
        ) for doc in cursor]
    
    def is_vowel_harmony_exception(self, word: str) -> bool:
        """Kelimenin ünlü uyumu istisnası olup olmadığını kontrol et."""
        exceptions = self.get_all_vowel_harmony_exceptions()
        return any(e.word == word.lower() for e in exceptions)
    
    # =========================================================================
    # CONSONANT MUTATION EXCEPTIONS
    # =========================================================================
    
    def get_all_consonant_mutation_exceptions(self) -> List[ConsonantMutationException]:
        """Ünsüz yumuşaması istisnalarını getir."""
        if self.use_mock:
            return []
        
        cursor = self.db.consonant_mutation_exceptions.find({})
        return [ConsonantMutationException(
            word=doc["word"],
            with_suffix=doc["with_suffix"],
            wrong=doc["wrong"],
            rule=doc["rule"],
            description=doc.get("description", "")
        ) for doc in cursor]
    
    def should_not_mutate(self, word: str) -> bool:
        """Kelimenin yumuşama yapmaması gerekip gerekmediğini kontrol et."""
        exceptions = self.get_all_consonant_mutation_exceptions()
        return any(e.word == word.lower() for e in exceptions)
    
    # =========================================================================
    # VOWEL DROP WORDS
    # =========================================================================
    
    def get_all_vowel_drop_words(self) -> List[VowelDropWord]:
        """Ünlü düşmesi olan kelimeleri getir."""
        if self.use_mock:
            return []
        
        cursor = self.db.vowel_drop_words.find({})
        return [VowelDropWord(
            base=doc["base"],
            stem=doc["stem"],
            example_suffix=doc["example_suffix"],
            result=doc["result"],
            wrong=doc["wrong"],
            vowel_dropped=doc["vowel_dropped"],
            type=doc.get("type", "noun")
        ) for doc in cursor]
    
    def get_stem_for_vowel_drop(self, word: str) -> Optional[str]:
        """Ünlü düşen kelime için gövdeyi döndür."""
        words = self.get_all_vowel_drop_words()
        for w in words:
            if w.base == word.lower():
                return w.stem
        return None
    
    def reconstruct_base_from_stem(self, stem: str) -> Optional[str]:
        """Gövdeden tam kelimeyi geri oluştur (morfolojik geri yapım)."""
        words = self.get_all_vowel_drop_words()
        for w in words:
            if w.stem == stem.lower():
                return w.base
        return None
    
    # =========================================================================
    # CASE SUFFIXES (İsim Çekim Ekleri)
    # =========================================================================
    
    def get_all_case_suffixes(self) -> List[CaseSuffix]:
        """Tüm isim çekim eklerini getir."""
        if self.use_mock:
            return []
        
        cursor = self.db.case_suffixes.find({})
        return [CaseSuffix(
            case=doc["case"],
            suffixes=doc["suffixes"],
            english_prep=doc["english_prep"],
            harmony_type=doc["harmony_type"],
            description=doc.get("description", "")
        ) for doc in cursor]
    
    def get_case_suffix_by_case(self, case: str) -> Optional[CaseSuffix]:
        """Belirli bir hal için ekleri getir."""
        all_suffixes = self.get_all_case_suffixes()
        for s in all_suffixes:
            if s.case == case:
                return s
        return None
    
    # =========================================================================
    # POSSESSIVE SUFFIXES (İyelik Ekleri)
    # =========================================================================
    
    def get_all_possessive_suffixes(self) -> List[PossessiveSuffix]:
        """Tüm iyelik eklerini getir."""
        if self.use_mock:
            return []
        
        cursor = self.db.possessive_suffixes.find({})
        return [PossessiveSuffix(
            person=doc["person"],
            plurality=doc["plurality"],
            suffixes=doc["suffixes"],
            english=doc["english"],
            harmony_type=doc["harmony_type"]
        ) for doc in cursor]
    
    def get_possessive_suffix(self, person: int, plurality: str) -> Optional[PossessiveSuffix]:
        """Belirli şahıs için iyelik eklerini getir."""
        all_suffixes = self.get_all_possessive_suffixes()
        for s in all_suffixes:
            if s.person == person and s.plurality == plurality:
                return s
        return None
    
    # =========================================================================
    # NEGATION SUFFIXES (Olumsuzluk Ekleri)
    # =========================================================================
    
    def get_all_negation_suffixes(self) -> List[NegationSuffix]:
        """Tüm olumsuzluk eklerini getir."""
        if self.use_mock:
            return []
        
        cursor = self.db.negation_suffixes.find({})
        return [NegationSuffix(
            type=doc["type"],
            suffixes=doc.get("suffixes"),
            word=doc.get("word", ""),
            english_aux=doc.get("english_aux", ""),
            harmony_type=doc.get("harmony_type", "")
        ) for doc in cursor]
    
    def is_negation_suffix(self, suffix: str) -> bool:
        """Verilen ekin olumsuzluk eki olup olmadığını kontrol et."""
        negations = self.get_all_negation_suffixes()
        for neg in negations:
            if neg.suffixes and suffix in neg.suffixes:
                return True
        return False
    
    # =========================================================================
    # QUESTION PARTICLES (Soru Ekleri)
    # =========================================================================
    
    def get_all_question_particles(self) -> List[QuestionParticle]:
        """Tüm soru eklerini getir."""
        if self.use_mock:
            return []
        
        cursor = self.db.question_particles.find({})
        return [QuestionParticle(
            suffixes=doc["suffixes"],
            harmony_type=doc["harmony_type"],
            person=doc.get("person"),
            plurality=doc.get("plurality"),
            description=doc.get("description", "")
        ) for doc in cursor]
    
    def is_question_particle(self, word: str) -> bool:
        """Kelimenin soru eki içerip içermediğini kontrol et."""
        particles = self.get_all_question_particles()
        for p in particles:
            for suffix in p.suffixes:
                if word.endswith(suffix) or f" {suffix}" in word:
                    return True
        return False
    
    # =========================================================================
    # POSTPOSITIONS (Edatlar)
    # =========================================================================
    
    def get_all_postpositions(self) -> List[Postposition]:
        """Tüm edatları getir."""
        if self.use_mock:
            return []
        
        cursor = self.db.postpositions.find({})
        return [Postposition(
            tr=doc["tr"],
            english=doc["english"],
            type=doc["type"],
            suffixes=doc.get("suffixes"),
            case_required=doc.get("case_required", "")
        ) for doc in cursor]
    
    def get_postposition(self, tr: str) -> Optional[Postposition]:
        """Belirli bir edatı getir."""
        all_pps = self.get_all_postpositions()
        for pp in all_pps:
            if pp.tr == tr:
                return pp
        return None
    
    # =========================================================================
    # CONJUNCTIONS (Bağlaçlar)
    # =========================================================================
    
    def get_all_conjunctions(self) -> List[Conjunction]:
        """Tüm bağlaçları getir."""
        if self.use_mock:
            return []
        
        cursor = self.db.conjunctions.find({})
        return [Conjunction(
            tr=doc["tr"],
            english=doc["english"],
            type=doc["type"]
        ) for doc in cursor]
    
    def get_conjunction(self, tr: str) -> Optional[Conjunction]:
        """Belirli bir bağlacı getir."""
        all_conjs = self.get_all_conjunctions()
        for conj in all_conjs:
            if conj.tr == tr:
                return conj
        return None
    
    # =========================================================================
    # COPULA SUFFIXES (Ek-Fiil Ekleri)
    # =========================================================================
    
    def get_all_copula_suffixes(self) -> List[CopulaSuffix]:
        """Tüm ek-fiil eklerini getir."""
        if self.use_mock:
            return []
        
        cursor = self.db.copula_suffixes.find({})
        return [CopulaSuffix(
            person=doc["person"],
            plurality=doc["plurality"],
            tense=doc["tense"],
            suffixes=doc["suffixes"],
            english=doc["english"],
            harmony_type=doc["harmony_type"]
        ) for doc in cursor]
    
    def get_copula_suffix(self, person: int, plurality: str, tense: str = "present") -> Optional[CopulaSuffix]:
        """Belirli şahıs ve zaman için ek-fiil eklerini getir."""
        all_suffixes = self.get_all_copula_suffixes()
        for s in all_suffixes:
            if s.person == person and s.plurality == plurality and s.tense == tense:
                return s
        return None
    
    # =========================================================================
    # ARTICLE RULES (İngilizce Article Kuralları)
    # =========================================================================
    
    def get_all_article_rules(self) -> List[ArticleRule]:
        """Tüm article kurallarını getir."""
        if self.use_mock:
            return []
        
        cursor = self.db.article_rules.find({})
        return [ArticleRule(
            condition=doc["condition"],
            article=doc["article"],
            description=doc.get("description", "")
        ) for doc in cursor]
    
    def get_article_for_condition(self, condition: str) -> Optional[str]:
        """Belirli bir koşul için article'ı döndür."""
        rules = self.get_all_article_rules()
        for rule in rules:
            if rule.condition == condition:
                return rule.article
        return None
    
    # =========================================================================
    # BUFFER CONSONANT EXCEPTIONS (Kaynaştırma İstisnaları)
    # =========================================================================
    
    def get_all_buffer_consonant_exceptions(self) -> List[BufferConsonantException]:
        """Kaynaştırma ünsüzü istisnalarını getir."""
        if self.use_mock:
            return []
        
        cursor = self.db.buffer_consonant_exceptions.find({})
        return [BufferConsonantException(
            word=doc["word"],
            buffer_consonant=doc["buffer_consonant"],
            normal_rule=doc.get("normal_rule", ""),
            exception_cases=doc.get("exception_cases", [])
        ) for doc in cursor]
    
    def get_buffer_consonant_for_word(self, word: str) -> Optional[str]:
        """Kelime için özel kaynaştırma ünsüzünü döndür (su → y)."""
        exceptions = self.get_all_buffer_consonant_exceptions()
        for exc in exceptions:
            if exc.word == word.lower():
                return exc.buffer_consonant
        return None
    
    # =========================================================================
    # PLURAL SUFFIXES (Çoğul Ekleri)
    # =========================================================================
    
    def get_all_plural_suffixes(self) -> List[PluralSuffix]:
        """Tüm çoğul eklerini getir."""
        if self.use_mock:
            return []
        
        cursor = self.db.plural_suffixes.find({})
        result = []
        for doc in cursor:
            # Sadece suffixes içeren dokümanları al
            if "suffixes" in doc:
                result.append(PluralSuffix(
                    suffixes=doc["suffixes"],
                    harmony_type=doc["harmony_type"],
                    english_suffix=doc["english_suffix"],
                    back_vowels=doc.get("rules", {}).get("back_vowels"),
                    front_vowels=doc.get("rules", {}).get("front_vowels")
                ))
        return result
    
    def get_plural_suffix_for_word(self, word: str) -> str:
        """Kelime için doğru çoğul ekini döndür (ünlü uyumuna göre)."""
        back_vowels = ['a', 'ı', 'o', 'u']
        
        # Son ünlüyü bul
        last_vowel = None
        for char in reversed(word.lower()):
            if char in ['a', 'e', 'ı', 'i', 'o', 'ö', 'u', 'ü']:
                last_vowel = char
                break
        
        if last_vowel in back_vowels:
            return "lar"
        return "ler"
    
    # =========================================================================
    # NOUN ROOTS (İsim Kökleri)
    # =========================================================================
    
    def get_all_noun_roots(self) -> List[NounRoot]:
        """Tüm isim köklerini getir."""
        if self.use_mock:
            return self._mock_noun_roots()
        
        cursor = self.db.noun_roots.find({})
        return [NounRoot(
            tr=doc["tr"],
            en=doc["en"],
            en_plural=doc["en_plural"],
            category=doc["category"],
            vowel_type=doc["vowel_type"]
        ) for doc in cursor]
    
    def get_noun_root(self, tr: str) -> Optional[NounRoot]:
        """Belirli bir Türkçe ismin İngilizce karşılığını getir."""
        if self.use_mock:
            roots = [r for r in self._mock_noun_roots() if r.tr == tr]
            return roots[0] if roots else None
        
        doc = self.db.noun_roots.find_one({"tr": tr})
        if doc:
            return NounRoot(
                tr=doc["tr"],
                en=doc["en"],
                en_plural=doc["en_plural"],
                category=doc["category"],
                vowel_type=doc["vowel_type"]
            )
        return None
    
    def _mock_noun_roots(self) -> List[NounRoot]:
        """Mock isim kökleri."""
        return [
            NounRoot("ev", "house", "houses", "place", "front"),
            NounRoot("kitap", "book", "books", "object", "back"),
            NounRoot("okul", "school", "schools", "place", "back"),
            NounRoot("su", "water", "waters", "food", "back"),
            NounRoot("çocuk", "child", "children", "person", "back"),
            NounRoot("kedi", "cat", "cats", "animal", "front"),
            NounRoot("köpek", "dog", "dogs", "animal", "front"),
        ]
    
    # =========================================================================
    # PROLOG FORMAT EXPORT
    # =========================================================================
    
    def export_to_prolog_format(self) -> str:
        """Tüm verileri Prolog fact formatında export et."""
        
        lines = []

                # =============================================================
        # MODULE HEADER (ÇOK KRİTİK)
        # =============================================================
        lines.append(":- encoding(utf8).")
        lines.append("")
        lines.append(":- module(morphology_data, [")
        lines.append("    noun_root/5,")
        lines.append("    verb_root/3,")
        lines.append("    irregular_verb/4,")
        lines.append("    tense_suffix/2,")
        lines.append("    person_suffix/4,")
        lines.append("    turkish_irregular_root/2,")
        lines.append("    auxiliary_verb/5,")
        lines.append("    case_suffix/4,")
        lines.append("    possessive_suffix/4,")
        lines.append("    negation_suffix/3,")
        lines.append("    question_particle/4,")
        lines.append("    postposition/4,")
        lines.append("    conjunction/3,")
        lines.append("    copula_suffix/5,")
        lines.append("    plural_suffix/2")
        lines.append("]).")
        lines.append("")

        
        lines.append("% =============================================================================")
        lines.append("% MORPHOLOGY DATA - MongoDB'den Otomatik Oluşturuldu")
        lines.append("% =============================================================================")
        lines.append("% Bu dosya morphology_api.py tarafından oluşturulmuştur.")
        lines.append("% Manuel düzenleme yapmayın - veriler MongoDB'den gelir.")
        lines.append("% =============================================================================")
        lines.append(":- encoding(utf8).")
        lines.append("")
        lines.append("% Discontiguous declarations for phonology facts")
        lines.append(":- discontiguous phonology_condition/3.")
        lines.append(":- discontiguous phonology_action/3.")
        lines.append(":- discontiguous postposition/4.")
        lines.append("")
        
        # Verb roots
        lines.append("% =============================================================================")
        lines.append("% FİİL KÖKLERİ: verb_root(TurkishRoot, EnglishRoot, Type).")
        lines.append("% =============================================================================")
        for root in self.get_all_verb_roots():
            lines.append(f"verb_root({root.tr}, {root.en}, {root.type}).")
        lines.append("")
        
        # Irregular verbs
        lines.append("% =============================================================================")
        lines.append("% DÜZENSİZ FİİLLER: irregular_verb(Base, Past, PastParticiple, PresentParticiple).")
        lines.append("% =============================================================================")
        for verb in self.get_all_irregular_verbs():
            # was/were gibi durumlar için
            past = verb.past.replace("/", "_")
            lines.append(f"irregular_verb({verb.base}, '{past}', {verb.past_participle}, {verb.present_participle}).")
        lines.append("")
        
        # Tense suffixes
        lines.append("% =============================================================================")
        lines.append("% ZAMAN EKLERİ: tense_suffix(Suffix, Tense).")
        lines.append("% =============================================================================")
        for suffix in self.get_all_tense_suffixes():
            lines.append(f"tense_suffix({suffix.suffix}, {suffix.tense}).")
        lines.append("")
        
        # Person suffixes
        lines.append("% =============================================================================")
        lines.append("% ŞAHIS EKLERİ: person_suffix(Suffix, Person, Plurality, Tense).")
        lines.append("% =============================================================================")
        for suffix in self.get_all_person_suffixes():
            suf = f"'{suffix.suffix}'" if suffix.suffix == "" else suffix.suffix
            lines.append(f"person_suffix({suf}, {suffix.person}, {suffix.plurality}, {suffix.tense}).")
        lines.append("")
        
        # Turkish irregular roots
        lines.append("% =============================================================================")
        lines.append("% TÜRKÇE DÜZENSİZ KÖKLER: turkish_irregular_root(Alternate, Canonical).")
        lines.append("% =============================================================================")
        for root in self.get_all_turkish_irregular_roots():
            lines.append(f'turkish_irregular_root("{root.alternate}", {root.canonical}).')
        lines.append("")
        
        # Auxiliary verbs
        lines.append("% =============================================================================")
        lines.append("% YARDIMCI FİİLLER: auxiliary_verb(Tense, Person, Plurality, Negation, Auxiliary).")
        lines.append("% =============================================================================")
        for aux in self.get_all_auxiliary_verbs():
            person = aux.person if aux.person is not None else "_"
            plurality = aux.plurality if aux.plurality is not None else "_"
            negation = "true" if aux.negation else "false"
            # Boşluklu yardımcı fiiller için tırnak
            auxiliary = f"'{aux.auxiliary}'" if " " in aux.auxiliary else aux.auxiliary
            lines.append(f"auxiliary_verb({aux.tense}, {person}, {plurality}, {negation}, {auxiliary}).")
        lines.append("")
        
        # Phonology rules
        lines.append("% =============================================================================")
        lines.append("% FONOLOJİ KURALLARI: phonology_rule(Language, RuleName, RuleType, Context, Priority).")
        lines.append("% =============================================================================")
        for rule in self.get_all_phonology_rules():
            lines.append(f'phonology_rule({rule.language}, {rule.rule_name}, {rule.rule_type}, {rule.context}, {rule.priority}).')
        lines.append("")
        
        # Phonology rule details (ayrı fact olarak condition ve action)
        lines.append("% =============================================================================")
        lines.append("% FONOLOJİ KURAL DETAYLARI: phonology_condition(RuleName, Key, Value).")
        lines.append("%                           phonology_action(RuleName, Key, Value).")
        lines.append("% =============================================================================")
        for rule in self.get_all_phonology_rules():
            # Condition facts
            for key, value in rule.condition.items():
                if isinstance(value, list):
                    value_str = "[" + ", ".join(f"'{v}'" if isinstance(v, str) else str(v) for v in value) + "]"
                elif isinstance(value, str):
                    value_str = f"'{value}'"
                elif isinstance(value, bool):
                    value_str = "true" if value else "false"
                else:
                    value_str = str(value)
                lines.append(f"phonology_condition({rule.rule_name}, {key}, {value_str}).")
            # Action facts
            for key, value in rule.action.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        sub_val_str = f"'{sub_value}'" if isinstance(sub_value, str) else str(sub_value)
                        lines.append(f"phonology_action({rule.rule_name}, {key}_{sub_key}, {sub_val_str}).")
                elif isinstance(value, bool):
                    value_str = "true" if value else "false"
                    lines.append(f"phonology_action({rule.rule_name}, {key}, {value_str}).")
                else:
                    value_str = f"'{value}'" if isinstance(value, str) else str(value)
                    lines.append(f"phonology_action({rule.rule_name}, {key}, {value_str}).")
        lines.append("")
        
        # Aorist Irregular Verbs (13 önemli fiil)
        lines.append("% =============================================================================")
        lines.append("% GENİŞ ZAMAN İSTİSNA FİİLLER: aorist_irregular(Root, Suffix, Example, English).")
        lines.append("% Normalde tek heceli fiiller -ar/-er alır, ama bu 13 fiil -ır/-ir/-ur/-ür alır")
        lines.append("% =============================================================================")
        for verb in self.get_all_aorist_irregular_verbs():
            lines.append(f"aorist_irregular({verb.root}, {verb.aorist_suffix}, {verb.example}, {verb.en}).")
        lines.append("")
        
        # Vowel Harmony Exceptions (alıntı kelimeler)
        lines.append("% =============================================================================")
        lines.append("% ÜNLÜ UYUMU İSTİSNALARI: vowel_harmony_exception(Word, Correct, Wrong, Origin).")
        lines.append("% Arapça, Farsça, Fransızca kökenli kelimeler")
        lines.append("% =============================================================================")
        for exc in self.get_all_vowel_harmony_exceptions():
            correct = exc.plural if exc.plural else exc.possessive
            lines.append(f"vowel_harmony_exception({exc.word}, {correct}, {exc.wrong}, {exc.origin}).")
        lines.append("")
        
        # Consonant Mutation Exceptions
        lines.append("% =============================================================================")
        lines.append("% ÜNSÜZ YUMUŞAMASI İSTİSNALARI: consonant_no_mutation(Word, WithSuffix, Rule).")
        lines.append("% Tek heceli ve yabancı kelimeler yumuşama yapmaz")
        lines.append("% =============================================================================")
        for exc in self.get_all_consonant_mutation_exceptions():
            # Kesme işareti içeren kelimeler için özel handling
            if "'" in exc.with_suffix:
                # Kesme işaretini escape et: ' -> ''
                with_suffix = f'"{exc.with_suffix}"'  # Çift tırnak kullan
            elif "'" in exc.word or exc.word[0].isupper():
                word = f"'{exc.word}'"
                with_suffix = f"'{exc.with_suffix}'" if exc.with_suffix[0].isupper() else exc.with_suffix
                lines.append(f"consonant_no_mutation({word}, {with_suffix}, {exc.rule}).")
                continue
            else:
                with_suffix = exc.with_suffix
            word = f"'{exc.word}'" if exc.word[0].isupper() else exc.word
            lines.append(f"consonant_no_mutation({word}, {with_suffix}, {exc.rule}).")
        lines.append("")
        
        # Vowel Drop Words
        lines.append("% =============================================================================")
        lines.append("% ÜNLÜ DÜŞMESİ: vowel_drop(Base, Stem, Result, DroppedVowel).")
        lines.append("% İkinci hecedeki dar ünlü düşer: burun → burnu")
        lines.append("% =============================================================================")
        for word in self.get_all_vowel_drop_words():
            lines.append(f"vowel_drop({word.base}, {word.stem}, {word.result}, '{word.vowel_dropped}').")
        lines.append("")
        
        # Case Suffixes (İsim Çekim Ekleri)
        lines.append("% =============================================================================")
        lines.append("% İSİM ÇEKİM EKLERİ: case_suffix(Case, Suffixes, EnglishPrep, HarmonyType).")
        lines.append("% Yönelme (to), Bulunma (in/on/at), Ayrılma (from), Belirtme (the), Tamlayan (of)")
        lines.append("% =============================================================================")
        for suffix in self.get_all_case_suffixes():
            suffixes_str = "[" + ", ".join(f"'{s}'" for s in suffix.suffixes) + "]"
            prep = f"'{suffix.english_prep}'" if "/" in suffix.english_prep or " " in suffix.english_prep else suffix.english_prep
            if suffix.english_prep == "":
                prep = "''"
            lines.append(f"case_suffix({suffix.case}, {suffixes_str}, {prep}, {suffix.harmony_type}).")
        lines.append("")
        
        # Possessive Suffixes (İyelik Ekleri)
        lines.append("% =============================================================================")
        lines.append("% İYELİK EKLERİ: possessive_suffix(Person, Plurality, Suffixes, English).")
        lines.append("% my, your, his/her/its, our, their")
        lines.append("% =============================================================================")
        for suffix in self.get_all_possessive_suffixes():
            suffixes_str = "[" + ", ".join(f"'{s}'" for s in suffix.suffixes) + "]"
            # Parantez veya özel karakterler için tırnak
            eng = f"'{suffix.english}'" if "/" in suffix.english or "(" in suffix.english or " " in suffix.english else suffix.english
            lines.append(f"possessive_suffix({suffix.person}, {suffix.plurality}, {suffixes_str}, {eng}).")
        lines.append("")
        
        # Negation Suffixes (Olumsuzluk Ekleri)
        lines.append("% =============================================================================")
        lines.append("% OLUMSUZLUK EKLERİ: negation_suffix(Type, Pattern, EnglishAux).")
        lines.append("% -me/-ma, -mez/-maz, değil, yok")
        lines.append("% =============================================================================")
        for neg in self.get_all_negation_suffixes():
            if neg.suffixes:
                pattern = "[" + ", ".join(f"'{s}'" for s in neg.suffixes) + "]"
            else:
                pattern = f"'{neg.word}'"
            eng_aux = f"'{neg.english_aux}'" if neg.english_aux and " " in neg.english_aux else (neg.english_aux or "''")
            lines.append(f"negation_suffix({neg.type}, {pattern}, {eng_aux}).")
        lines.append("")
        
        # Question Particles (Soru Ekleri)
        lines.append("% =============================================================================")
        lines.append("% SORU EKLERİ: question_particle(Suffixes, HarmonyType).")
        lines.append("% -mı/-mi/-mu/-mü")
        lines.append("% =============================================================================")
        for particle in self.get_all_question_particles():
            suffixes_str = "[" + ", ".join(f"'{s}'" for s in particle.suffixes) + "]"
            person = particle.person if particle.person else "_"
            plurality = particle.plurality if particle.plurality else "_"
            lines.append(f"question_particle({suffixes_str}, {particle.harmony_type}, {person}, {plurality}).")
        lines.append("")
        
        # Postpositions (Edatlar)
        lines.append("% =============================================================================")
        lines.append("% EDATLAR: postposition(Turkish, English, Type, CaseRequired).")
        lines.append("% ile (with), için (for), kadar (until), gibi (like)")
        lines.append("% =============================================================================")
        for pp in self.get_all_postpositions():
            english = f"'{pp.english}'" if "/" in pp.english or " " in pp.english else pp.english
            case_req = pp.case_required if pp.case_required else "none"
            lines.append(f"postposition('{pp.tr}', {english}, {pp.type}, {case_req}).")
            # Bitişik yazılan edatlar için suffix bilgisi
            if pp.suffixes:
                suffixes_str = "[" + ", ".join(f"'{s}'" for s in pp.suffixes) + "]"
                lines.append(f"postposition_suffixes('{pp.tr}', {suffixes_str}).")
        lines.append("")
        
        # Conjunctions (Bağlaçlar)
        lines.append("% =============================================================================")
        lines.append("% BAĞLAÇLAR: conjunction(Turkish, English, Type).")
        lines.append("% ve (and), ama (but), çünkü (because)")
        lines.append("% =============================================================================")
        for conj in self.get_all_conjunctions():
            # Nokta veya özel karakterler için tırnak
            tr = f"'{conj.tr}'" if " " in conj.tr or "." in conj.tr else conj.tr
            english = f"'{conj.english}'" if "/" in conj.english or " " in conj.english or "." in conj.english else conj.english
            lines.append(f"conjunction({tr}, {english}, {conj.type}).")
        lines.append("")
        
        # Copula Suffixes (Ek-Fiil Ekleri)
        lines.append("% =============================================================================")
        lines.append("% EK-FİİL EKLERİ: copula_suffix(Person, Plurality, Tense, Suffixes, English).")
        lines.append("% İsim cümlelerinde 'to be' karşılığı: öğrenciyim → I am a student")
        lines.append("% =============================================================================")
        for cop in self.get_all_copula_suffixes():
            suffixes_str = "[" + ", ".join(f"'{s}'" for s in cop.suffixes) + "]"
            lines.append(f"copula_suffix({cop.person}, {cop.plurality}, {cop.tense}, {suffixes_str}, {cop.english}).")
        lines.append("")
        
        # Article Rules
        lines.append("% =============================================================================")
        lines.append("% ARTICLE KURALLARI: article_rule(Condition, Article).")
        lines.append("% Türkçe belirtme eki → İngilizce 'the'; belirtmesiz → 'a/an'")
        lines.append("% =============================================================================")
        for rule in self.get_all_article_rules():
            article = f"'{rule.article}'" if "/" in rule.article or " " in rule.article else rule.article
            lines.append(f"article_rule({rule.condition}, {article}).")
        lines.append("")
        
        # Buffer Consonant Exceptions
        lines.append("% =============================================================================")
        lines.append("% KAYNASTIRMA İSTİSNALARI: buffer_exception(Word, BufferConsonant, Cases).")
        lines.append("% su → suyun (n yerine y), ne → neyin")
        lines.append("% =============================================================================")
        for exc in self.get_all_buffer_consonant_exceptions():
            cases_str = "[" + ", ".join(f"'{c}'" for c in exc.exception_cases) + "]"
            lines.append(f"buffer_exception({exc.word}, '{exc.buffer_consonant}', {cases_str}).")
        lines.append("")
        
        # Plural Suffixes
        lines.append("% =============================================================================")
        lines.append("% ÇOĞUL EKLERİ: plural_suffix(Suffixes, HarmonyType).")
        lines.append("% -ler (ince ünlü), -lar (kalın ünlü)")
        lines.append("% =============================================================================")
        for pl in self.get_all_plural_suffixes():
            suffixes_str = "[" + ", ".join(f"'{s}'" for s in pl.suffixes) + "]"
            lines.append(f"plural_suffix({suffixes_str}, {pl.harmony_type}).")
            if pl.back_vowels:
                back_str = "[" + ", ".join(f"'{v}'" for v in pl.back_vowels) + "]"
                lines.append(f"plural_harmony(back_vowels, {back_str}, lar).")
            if pl.front_vowels:
                front_str = "[" + ", ".join(f"'{v}'" for v in pl.front_vowels) + "]"
                lines.append(f"plural_harmony(front_vowels, {front_str}, ler).")
        lines.append("")
        
        # Noun Roots
        lines.append("% =============================================================================")
        lines.append("% İSİM KÖKLERİ: noun_root(Turkish, English, EnglishPlural, Category, VowelType).")
        lines.append("% ev → house, kitap → book, okul → school")
        lines.append("% =============================================================================")
        for noun in self.get_all_noun_roots():
            lines.append(f"noun_root({noun.tr}, {noun.en}, {noun.en_plural}, {noun.category}, {noun.vowel_type}).")
        lines.append("")
        
        return "\n".join(lines)
    
    def export_to_prolog_file(self, filepath: str = None) -> bool:
        """MongoDB'den okunan verileri Prolog dosyasına yaz."""
        try:
            import os

            if filepath is None:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                prolog_dir = os.path.join(script_dir, "prolog", "morphology", "data")
                os.makedirs(prolog_dir, exist_ok=True)
                filepath = os.path.join(prolog_dir, "morphology_data.pl")

            prolog_content = self.export_to_prolog_format()

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(prolog_content)

            print(f"[OK] Prolog facts dosyası oluşturuldu: {filepath}")
            return True

        except Exception as e:
            print(f"[HATA] Dosya yazılamadı: {e}")
            return False
    
    def export_to_json(self) -> Dict[str, Any]:
        """Tüm verileri JSON formatında export et."""
        return {
            "verb_roots": [asdict(r) for r in self.get_all_verb_roots()],
            "irregular_verbs": [asdict(v) for v in self.get_all_irregular_verbs()],
            "tense_suffixes": [asdict(s) for s in self.get_all_tense_suffixes()],
            "person_suffixes": [asdict(s) for s in self.get_all_person_suffixes()],
            "turkish_irregular_roots": [asdict(r) for r in self.get_all_turkish_irregular_roots()],
            "auxiliary_verbs": [asdict(a) for a in self.get_all_auxiliary_verbs()],
            "phonology_rules": [asdict(r) for r in self.get_all_phonology_rules()],
        }
    
    # =========================================================================
    # MOCK DATA (MongoDB bağlantısı yoksa)
    # =========================================================================
    
    def _mock_verb_roots(self) -> List[VerbRoot]:
        return [
            VerbRoot("gel", "come", "irregular"),
            VerbRoot("git", "go", "irregular"),
            VerbRoot("gid", "go", "irregular", "yumuşama"),
            VerbRoot("ye", "eat", "irregular"),
            VerbRoot("yi", "eat", "irregular", "değişim"),
            VerbRoot("ic", "drink", "irregular"),
            VerbRoot("yap", "do", "irregular"),
            VerbRoot("oku", "read", "irregular"),
            VerbRoot("sev", "love", "regular"),
            VerbRoot("yika", "wash", "regular"),
        ]
    
    def _mock_irregular_verbs(self) -> List[IrregularVerb]:
        return [
            IrregularVerb("come", "came", "come", "coming"),
            IrregularVerb("go", "went", "gone", "going"),
            IrregularVerb("eat", "ate", "eaten", "eating"),
            IrregularVerb("drink", "drank", "drunk", "drinking"),
            IrregularVerb("do", "did", "done", "doing"),
            IrregularVerb("read", "read", "read", "reading"),
        ]
    
    def _mock_tense_suffixes(self) -> List[TenseSuffix]:
        return [
            TenseSuffix("iyor", "present_continuous", 1),
            TenseSuffix("uyor", "present_continuous", 1),
            TenseSuffix("yor", "present_continuous", 2),
            TenseSuffix("di", "past_simple", 1),
            TenseSuffix("du", "past_simple", 1),
            TenseSuffix("ecek", "future", 1),
            TenseSuffix("acak", "future", 1),
            TenseSuffix("er", "aorist", 1),
            TenseSuffix("ar", "aorist", 1),
        ]
    
    def _mock_person_suffixes(self) -> List[PersonSuffix]:
        return [
            PersonSuffix("um", 1, "singular", "present_continuous"),
            PersonSuffix("sun", 2, "singular", "present_continuous"),
            PersonSuffix("", 3, "singular", "present_continuous"),
            PersonSuffix("uz", 1, "plural", "present_continuous"),
            PersonSuffix("lar", 3, "plural", "present_continuous"),
            PersonSuffix("m", 1, "singular", "past_simple"),
            PersonSuffix("n", 2, "singular", "past_simple"),
            PersonSuffix("", 3, "singular", "past_simple"),
            PersonSuffix("k", 1, "plural", "past_simple"),
        ]
    
    def _mock_turkish_irregular_roots(self) -> List[TurkishIrregularRoot]:
        return [
            TurkishIrregularRoot("y", "ye", "present_continuous"),
            TurkishIrregularRoot("yi", "ye", "general"),
            TurkishIrregularRoot("gid", "git", "before_vowel"),
            TurkishIrregularRoot("okuy", "oku", "before_vowel"),
        ]
    
    def _mock_auxiliary_verbs(self) -> List[AuxiliaryVerb]:
        return [
            AuxiliaryVerb("present_continuous", 1, "singular", False, "am"),
            AuxiliaryVerb("present_continuous", 2, "singular", False, "are"),
            AuxiliaryVerb("present_continuous", 3, "singular", False, "is"),
            AuxiliaryVerb("present_continuous", 1, "plural", False, "are"),
            AuxiliaryVerb("present_continuous", 3, "plural", False, "are"),
            AuxiliaryVerb("future", None, None, False, "will"),
            AuxiliaryVerb("past_simple", None, None, True, "did not"),
        ]
    
    def _mock_phonology_rules(self) -> List[PhonologyRule]:
        """Fonoloji kuralları mock data."""
        return [
            # Türkçe kuralları
            PhonologyRule(
                language="turkish",
                rule_name="buyuk_unlu_uyumu_back",
                rule_type="vowel_harmony",
                context="suffix_attachment",
                condition={"last_vowel": ["a", "ı", "o", "u"]},
                action={"select_suffix_vowel": {"e": "a", "i": "ı"}},
                priority=100,
                description="Kalın ünlülerden sonra kalın ünlü gelir"
            ),
            PhonologyRule(
                language="turkish",
                rule_name="buyuk_unlu_uyumu_front",
                rule_type="vowel_harmony",
                context="suffix_attachment",
                condition={"last_vowel": ["e", "i", "ö", "ü"]},
                action={"select_suffix_vowel": {"a": "e", "ı": "i"}},
                priority=100,
                description="İnce ünlülerden sonra ince ünlü gelir"
            ),
            PhonologyRule(
                language="turkish",
                rule_name="unsuz_yumusamasi_t",
                rule_type="consonant_softening",
                context="before_vowel",
                condition={"final_consonant": "t", "following": "vowel"},
                action={"replace": {"from": "t", "to": "d"}},
                priority=80,
                description="t → d yumuşaması (git → gidiyor)"
            ),
            PhonologyRule(
                language="turkish",
                rule_name="unlu_daralmasi_a",
                rule_type="vowel_narrowing",
                context="before_yor",
                condition={"ends_with": "a", "following_suffix": "yor"},
                action={"replace": {"from": "a", "to": "ı"}},
                priority=95,
                description="a → ı daralması -yor önünde"
            ),
            # İngilizce kuralları
            PhonologyRule(
                language="english",
                rule_name="cvc_doubling_ing",
                rule_type="consonant_doubling",
                context="suffix_ing",
                condition={"pattern": "CVC", "stressed_final": True},
                action={"double_final_consonant": True},
                priority=80,
                description="CVC kalıbında son ünsüz ikilemesi (run → running)"
            ),
            PhonologyRule(
                language="english",
                rule_name="silent_e_drop_ing",
                rule_type="vowel_drop",
                context="suffix_ing",
                condition={"ends_with": "e", "preceded_by": "consonant"},
                action={"drop_final": "e"},
                priority=85,
                description="Sessiz -e düşer -ing önünde (make → making)"
            ),
        ]


# =============================================================================
# TEST VE ANA FONKSİYON
# =============================================================================

def test_morphology_db():
    """Morfoloji veritabanını test et."""
    db = MorphologyDB()
    
    print("="*60)
    print("MORFOLOJİ VERİTABANI TESTİ")
    print("="*60)
    print(f"MongoDB Bağlantısı: {'Mock' if db.use_mock else 'Aktif'}")
    print()
    
    # Verb roots
    roots = db.get_all_verb_roots()
    print(f"Fiil Kökleri: {len(roots)} adet")
    for r in roots[:5]:
        print(f"  {r.tr} → {r.en} ({r.type})")
    print("  ...")
    print()
    
    # Irregular verbs
    irregulars = db.get_all_irregular_verbs()
    print(f"Düzensiz Fiiller: {len(irregulars)} adet")
    for v in irregulars[:3]:
        print(f"  {v.base} → {v.past} → {v.past_participle}")
    print("  ...")
    print()
    
    # Tense suffixes
    tenses = db.get_all_tense_suffixes()
    print(f"Zaman Ekleri: {len(tenses)} adet")
    
    # Person suffixes
    persons = db.get_all_person_suffixes()
    print(f"Şahıs Ekleri: {len(persons)} adet")
    
    # Turkish irregular roots
    irregular_roots = db.get_all_turkish_irregular_roots()
    print(f"Düzensiz Kök Değişimleri: {len(irregular_roots)} adet")
    
    # Auxiliary verbs
    aux_verbs = db.get_all_auxiliary_verbs()
    print(f"Yardımcı Fiiller: {len(aux_verbs)} adet")
    
    # Phonology rules
    phono_rules = db.get_all_phonology_rules()
    print(f"Fonoloji Kuralları: {len(phono_rules)} adet")
    for r in phono_rules[:3]:
        print(f"  [{r.language}] {r.rule_name}: {r.description}")
    print("  ...")
    print()


def generate_prolog_data():
    """MongoDB'den Prolog facts dosyası oluştur."""
    db = MorphologyDB()

    print("="*60)
    print("PROLOG FACTS DOSYASI OLUŞTURUCU")
    print("="*60)
    print(f"Veri Kaynağı: {'Mock Data' if db.use_mock else 'MongoDB'}")
    print()

    stats = {
        "Fiil Kökleri": len(db.get_all_verb_roots()),
        "Düzensiz Fiiller": len(db.get_all_irregular_verbs()),
        "Zaman Ekleri": len(db.get_all_tense_suffixes()),
        "Şahıs Ekleri": len(db.get_all_person_suffixes()),
        "Düzensiz Kökler": len(db.get_all_turkish_irregular_roots()),
        "Yardımcı Fiiller": len(db.get_all_auxiliary_verbs()),
        "Fonoloji Kuralları": len(db.get_all_phonology_rules()),
    }

    print("Veri İstatistikleri:")
    for k, v in stats.items():
        print(f"  {k}: {v} adet")
    print()

    if db.export_to_prolog_file():
        print(f"\nToplam {sum(stats.values())} fact oluşturuldu.")
        print("Artık prolog/morphology/data/morphology_data.pl kullanılıyor.")
    else:
        print("\n[HATA] Dosya oluşturulamadı!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--generate":
        generate_prolog_data()
    else:
        test_morphology_db()
        print()
        print("Prolog dosyası oluşturmak için: python morphology_api.py --generate")

% =============================================================================
% MORPHOLOGY DATA - MongoDB'den Otomatik Oluşturuldu
% =============================================================================
% Bu dosya morphology_api.py tarafından oluşturulmuştur.
% Manuel düzenleme yapmayın - veriler MongoDB'den gelir.
% =============================================================================

:- module(morphology_data, [
    verb_root/3,
    verb_root/2,
    noun_root/5,
    tense_suffix/2,
    person_suffix/4,
    irregular_verb/4,
    auxiliary_verb/5,
    phonology_rule/5,
    phonology_condition/3,
    phonology_action/3,
    turkish_irregular_root/2,
    %plural_suffix/2,
    %article_rule/2,
    %buffer_exception/3,
    postposition/4
]).

:- encoding(utf8).


% Discontiguous declarations for phonology facts
:- discontiguous phonology_condition/3.
:- discontiguous phonology_action/3.
:- discontiguous postposition/4.

% =============================================================================
% FİİL KÖKLERİ: verb_root(TurkishRoot, EnglishRoot, Type).
% =============================================================================
verb_root(gel, come, irregular).
verb_root(git, go, irregular).
verb_root(gid, go, irregular).
verb_root(ye, eat, irregular).
verb_root(yi, eat, irregular).
verb_root(ic, drink, irregular).
verb_root(yap, do, irregular).
verb_root(oku, read, irregular).
verb_root(sev, love, regular).
verb_root(yika, wash, regular).
verb_root(iste, "want", "regular").
verb_root(bekle, "wait", "regular").
verb_root(soyle, "tell", "regular").
verb_root(anla, "understand", "irregular").
verb_root(oyna, "play", "regular").
verb_root(basla, "start", "regular").
verb_root(agla, "cry", "regular").
verb_root(izle, "watch", "regular").
verb_root(ozle, "miss", "regular").
verb_root(dinle, "listen", "regular").
verb_root(sucla, "accuse", "regular").
verb_root(sakla, "hide", "irregular").
verb_root(ye, "eat", "irregular").
verb_root(de, "say", "irregular").
verb_root(bak, "look", "regular").

% =============================================================================
% DÜZENSİZ FİİLLER: irregular_verb(Base, Past, PastParticiple, PresentParticiple).
% =============================================================================
irregular_verb(come, 'came', come, coming).
irregular_verb(go, 'went', gone, going).
irregular_verb(eat, 'ate', eaten, eating).
irregular_verb(drink, 'drank', drunk, drinking).
irregular_verb(do, 'did', done, doing).
irregular_verb(read, 'read', read, reading).

% =============================================================================
% ZAMAN EKLERİ: tense_suffix(Suffix, Tense).
% =============================================================================
tense_suffix(iyor, present_continuous).
tense_suffix(uyor, present_continuous).
tense_suffix(yor, present_continuous).
tense_suffix(di, past_simple).
tense_suffix(du, past_simple).
tense_suffix(ecek, future).
tense_suffix(acak, future).
tense_suffix(er, aorist).
tense_suffix(ar, aorist).

% =============================================================================
% ŞAHIS EKLERİ: person_suffix(Suffix, Person, Plurality, Tense).
% =============================================================================
person_suffix(um, 1, singular, present_continuous).
person_suffix(sun, 2, singular, present_continuous).
person_suffix('', 3, singular, present_continuous).
person_suffix(uz, 1, plural, present_continuous).
person_suffix(lar, 3, plural, present_continuous).
person_suffix(m, 1, singular, past_simple).
person_suffix(n, 2, singular, past_simple).
person_suffix('', 3, singular, past_simple).
person_suffix(k, 1, plural, past_simple).

% =============================================================================
% TÜRKÇE DÜZENSİZ KÖKLER: turkish_irregular_root(Alternate, Canonical).
% =============================================================================
turkish_irregular_root("y", ye).
turkish_irregular_root("yi", ye).
turkish_irregular_root("gid", git).
turkish_irregular_root("okuy", oku).

% =============================================================================
% YARDIMCI FİİLLER: auxiliary_verb(Tense, Person, Plurality, Negation, Auxiliary).
% =============================================================================
auxiliary_verb(present_continuous, 1, singular, false, am).
auxiliary_verb(present_continuous, 2, singular, false, are).
auxiliary_verb(present_continuous, 3, singular, false, is).
auxiliary_verb(present_continuous, 1, plural, false, are).
auxiliary_verb(present_continuous, 3, plural, false, are).
auxiliary_verb(future, _, _, false, will).
auxiliary_verb(past_simple, _, _, true, 'did not').

% =============================================================================
% FONOLOJİ KURALLARI: phonology_rule(Language, RuleName, RuleType, Context, Priority).
% =============================================================================
phonology_rule(turkish, buyuk_unlu_uyumu_back, vowel_harmony, suffix_attachment, 100).
phonology_rule(turkish, buyuk_unlu_uyumu_front, vowel_harmony, suffix_attachment, 100).
phonology_rule(turkish, unsuz_yumusamasi_t, consonant_softening, before_vowel, 80).
phonology_rule(turkish, unlu_daralmasi_a, vowel_narrowing, before_yor, 95).
phonology_rule(english, cvc_doubling_ing, consonant_doubling, suffix_ing, 80).
phonology_rule(english, silent_e_drop_ing, vowel_drop, suffix_ing, 85).

% =============================================================================
% FONOLOJİ KURAL DETAYLARI: phonology_condition(RuleName, Key, Value).
%                           phonology_action(RuleName, Key, Value).
% =============================================================================
phonology_condition(buyuk_unlu_uyumu_back, last_vowel, ['a', 'ı', 'o', 'u']).
phonology_action(buyuk_unlu_uyumu_back, select_suffix_vowel_e, 'a').
phonology_action(buyuk_unlu_uyumu_back, select_suffix_vowel_i, 'ı').
phonology_condition(buyuk_unlu_uyumu_front, last_vowel, ['e', 'i', 'ö', 'ü']).
phonology_action(buyuk_unlu_uyumu_front, select_suffix_vowel_a, 'e').
phonology_action(buyuk_unlu_uyumu_front, select_suffix_vowel_ı, 'i').
phonology_condition(unsuz_yumusamasi_t, final_consonant, 't').
phonology_condition(unsuz_yumusamasi_t, following, 'vowel').
phonology_action(unsuz_yumusamasi_t, replace_from, 't').
phonology_action(unsuz_yumusamasi_t, replace_to, 'd').
phonology_condition(unlu_daralmasi_a, ends_with, 'a').
phonology_condition(unlu_daralmasi_a, following_suffix, 'yor').
phonology_action(unlu_daralmasi_a, replace_from, 'a').
phonology_action(unlu_daralmasi_a, replace_to, 'ı').
phonology_condition(cvc_doubling_ing, pattern, 'CVC').
phonology_condition(cvc_doubling_ing, stressed_final, true).
phonology_action(cvc_doubling_ing, double_final_consonant, true).
phonology_condition(silent_e_drop_ing, ends_with, 'e').
phonology_condition(silent_e_drop_ing, preceded_by, 'consonant').
phonology_action(silent_e_drop_ing, drop_final, 'e').

% =============================================================================
% GENİŞ ZAMAN İSTİSNA FİİLLER: aorist_irregular(Root, Suffix, Example, English).
% Normalde tek heceli fiiller -ar/-er alır, ama bu 13 fiil -ır/-ir/-ur/-ür alır
% =============================================================================

% =============================================================================
% ÜNLÜ UYUMU İSTİSNALARI: vowel_harmony_exception(Word, Correct, Wrong, Origin).
% Arapça, Farsça, Fransızca kökenli kelimeler
% =============================================================================

% =============================================================================
% ÜNSÜZ YUMUŞAMASI İSTİSNALARI: consonant_no_mutation(Word, WithSuffix, Rule).
% Tek heceli ve yabancı kelimeler yumuşama yapmaz
% =============================================================================

% =============================================================================
% ÜNLÜ DÜŞMESİ: vowel_drop(Base, Stem, Result, DroppedVowel).
% İkinci hecedeki dar ünlü düşer: burun → burnu
% =============================================================================

% =============================================================================
% İSİM ÇEKİM EKLERİ: case_suffix(Case, Suffixes, EnglishPrep, HarmonyType).
% Yönelme (to), Bulunma (in/on/at), Ayrılma (from), Belirtme (the), Tamlayan (of)
% =============================================================================

% =============================================================================
% İYELİK EKLERİ: possessive_suffix(Person, Plurality, Suffixes, English).
% my, your, his/her/its, our, their
% =============================================================================

% =============================================================================
% OLUMSUZLUK EKLERİ: negation_suffix(Type, Pattern, EnglishAux).
% -me/-ma, -mez/-maz, değil, yok
% =============================================================================

% =============================================================================
% SORU EKLERİ: question_particle(Suffixes, HarmonyType).
% -mı/-mi/-mu/-mü
% =============================================================================

% =============================================================================
% EDATLAR: postposition(Turkish, English, Type, CaseRequired).
% ile (with), için (for), kadar (until), gibi (like)
% =============================================================================

% =============================================================================
% BAĞLAÇLAR: conjunction(Turkish, English, Type).
% ve (and), ama (but), çünkü (because)
% =============================================================================

% =============================================================================
% EK-FİİL EKLERİ: copula_suffix(Person, Plurality, Tense, Suffixes, English).
% İsim cümlelerinde 'to be' karşılığı: öğrenciyim → I am a student
% =============================================================================

% =============================================================================
% ARTICLE KURALLARI: article_rule(Condition, Article).
% Türkçe belirtme eki → İngilizce 'the'; belirtmesiz → 'a/an'
% =============================================================================

% =============================================================================
% KAYNASTIRMA İSTİSNALARI: buffer_exception(Word, BufferConsonant, Cases).
% su → suyun (n yerine y), ne → neyin
% =============================================================================

% =============================================================================
% ÇOĞUL EKLERİ: plural_suffix(Suffixes, HarmonyType).
% -ler (ince ünlü), -lar (kalın ünlü)
% =============================================================================

% =============================================================================
% İSİM KÖKLERİ: noun_root(Turkish, English, EnglishPlural, Category, VowelType).
% ev → house, kitap → book, okul → school
% =============================================================================
noun_root(ev, house, houses, place, front).
noun_root(kitap, book, books, object, back).
noun_root(okul, school, schools, place, back).
noun_root(su, water, waters, food, back).
noun_root(çocuk, child, children, person, back).
noun_root(kedi, cat, cats, animal, front).
noun_root(köpek, dog, dogs, animal, front).

verb_root(TR, EN) :- verb_root(TR, EN, _).



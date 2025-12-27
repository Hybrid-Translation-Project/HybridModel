% =============================================================================
% DOSYA: tr_phonology.pl
% GÖREV: SES BİLİMİ (PHONOLOGY)
% AÇIKLAMA:
%   - Türkçenin ses kurallarını matematiksel olarak tanımlar.
%   - Büyük Ünlü Uyumu (2'li: a->a, e->e) ve Küçük Ünlü Uyumu (4'lü) kuralları.
%   - Ünsüz Yumuşaması (p->b, k->ğ...) ve Benzeşme kurallarını yönetir.
%   - Diğer modüller "Bu ek buraya uyar mı?" diye buraya sorar.
% =============================================================================

:- module(tr_phonology, [
    is_vowel/1,
    is_consonant/1,
    reverse_narrowing/2,
    unsoften_consonant/2,
    is_question_particle/1,
    turkish_back_vowel/1,
    turkish_front_vowel/1
]).

% --- TEMEL YARDIMCILAR ---
is_vowel("a"). is_vowel("e"). is_vowel("i"). is_vowel("o"). is_vowel("u").
is_vowel("ı"). is_vowel("ö"). is_vowel("ü").

is_consonant(Char) :-
    \+ is_vowel(Char),
    string_length(Char, 1).

% --- DARALMA TERSİNE ÇEVİRME (Fiiller için) ---
reverse_narrowing("i", "e").  % bekli -> bekle
reverse_narrowing("i", "a").  % basli -> basla
reverse_narrowing("ı", "a").  % ağlı -> ağla
reverse_narrowing("u", "a").  % oynu -> oyna
reverse_narrowing("u", "e").  % soylu -> soyle
reverse_narrowing("ü", "e").  % özlü -> özle

% --- ÜNSÜZ SERTLEŞTİRME (İsimler için: b->p) ---
unsoften_consonant("b", "p").
unsoften_consonant("c", "ç").
unsoften_consonant("d", "t").
unsoften_consonant("ğ", "k").
unsoften_consonant("g", "k").

% --- SORU EKİ KONTROLÜ ---
is_question_particle(Word) :-
    atom_string(Word, WordStr),
    member(WordStr, ["mı", "mi", "mu", "mü"]).

% --- ÜNLÜ SINIFLANDIRMASI ---
turkish_back_vowel("a"). turkish_back_vowel("ı"). 
turkish_back_vowel("o"). turkish_back_vowel("u").
turkish_front_vowel("e"). turkish_front_vowel("i").
turkish_front_vowel("ö"). turkish_front_vowel("ü").
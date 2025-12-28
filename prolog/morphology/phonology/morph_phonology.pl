
% =============================================================================
% MORPH PHONOLOGY
% =============================================================================
% Bu dosya TÜRKÇE ve İNGİLİZCE için
% SES BİLGİSİ (FONOLOJİ) kurallarını içerir.
%
% AMAÇ:
% - Eklerin köke doğru biçimde bağlanmasını sağlamak
% - Ünlü uyumu, ünsüz yumuşaması, daralma vb. işlemleri yapmak
%
% KAPSAM:
% - Büyük ünlü uyumu
% - Ünsüz yumuşaması / sertleşmesi
% - Ünlü daralması (-yor öncesi)
% - Kaynaştırma ünsüzleri (y)
% - İngilizce -ing, -ed fonolojik kuralları
%
% NOT:
% - Burada ZAMAN veya ŞAHIS analizi YOKTUR
% - Karar mekanizması yoktur
% - morphology_core.pl bu dosyayı KULLANIR
% Ayrı modül – morphology_core.pl tarafından consult edilir
% =============================================================================
:- module(morph_phonology, [
    apply_vowel_harmony/3,
    apply_consonant_softening/2,
    apply_consonant_assimilation/3,
    apply_vowel_narrowing/3,
    apply_buffer_consonant/3,
    apply_english_doubling/3,
    apply_silent_e_drop/2,
    apply_ie_to_y/2,
    apply_y_to_i/2,
    get_last_vowel/2,
    get_last_consonant/2,
    is_cvc_pattern/1
]).

:- encoding(utf8).
% Utils klasörüne erişmek için bir üste çıkıyoruz (..)
:- use_module('../utils/morph_utils').
% =============================================================================
% FONOLOJİ MOTORU (SES BİLGİSİ KURALLARI)
% =============================================================================

    % Türkçe ünlü sınıflandırması
    turkish_back_vowel("a"). turkish_back_vowel("ı"). 
    turkish_back_vowel("o"). turkish_back_vowel("u").

    turkish_front_vowel("e"). turkish_front_vowel("i").
    turkish_front_vowel("ö"). turkish_front_vowel("ü").

    turkish_rounded_vowel("o"). turkish_rounded_vowel("u").
    turkish_rounded_vowel("ö"). turkish_rounded_vowel("ü").

    turkish_unrounded_vowel("a"). turkish_unrounded_vowel("e").
    turkish_unrounded_vowel("ı"). turkish_unrounded_vowel("i").

    % Sert ünsüzler (ses benzeşmesi için)
    turkish_hard_consonant("p"). turkish_hard_consonant("ç").
    turkish_hard_consonant("t"). turkish_hard_consonant("k").
    turkish_hard_consonant("f"). turkish_hard_consonant("h").
    turkish_hard_consonant("s"). turkish_hard_consonant("ş").

    % Son ünlüyü bul
    get_last_vowel(Word, Vowel) :-
        atom_string(Word, WordStr),
        string_chars(WordStr, Chars),
        reverse(Chars, RevChars),
        member(Char, RevChars),
        atom_string(CharAtom, [Char]),
        (is_vowel([Char]) ; is_vowel(CharAtom)),
        Vowel = [Char],
        !.

    % Son ünsüzü bul
    get_last_consonant(Word, Consonant) :-
        atom_string(Word, WordStr),
        string_length(WordStr, Len),
        Len > 0,
        LastIdx is Len - 1,
        sub_string(WordStr, LastIdx, 1, 0, Consonant),
        is_consonant(Consonant).

    % --- BÜYÜK ÜNLÜ UYUMU ---
    % Kalın ünlülerden sonra kalın, ince ünlülerden sonra ince ünlü gelir

    apply_vowel_harmony(Root, SuffixTemplate, HarmonizedSuffix) :-
        get_last_vowel(Root, LastVowel),
        (   turkish_back_vowel(LastVowel)
        ->  harmonize_to_back(SuffixTemplate, HarmonizedSuffix)
        ;   harmonize_to_front(SuffixTemplate, HarmonizedSuffix)
        ).

    harmonize_to_back(Suffix, Harmonized) :-
        atom_string(Suffix, SuffixStr),
        string_replace(SuffixStr, "e", "a", Temp1),
        string_replace(Temp1, "i", "ı", Harmonized).

    harmonize_to_front(Suffix, Harmonized) :-
        atom_string(Suffix, SuffixStr),
        string_replace(SuffixStr, "a", "e", Temp1),
        string_replace(Temp1, "ı", "i", Harmonized).



    % --- ÜNSÜZ YUMUŞAMASI ---
    % p→b, ç→c, t→d, k→ğ (ünlü ile başlayan eklerden önce)

    apply_consonant_softening(Root, SoftenedRoot) :-
        atom_string(Root, RootStr),
        string_length(RootStr, Len),
        Len > 0,
        LastIdx is Len - 1,
        sub_string(RootStr, LastIdx, 1, 0, LastChar),
        soften_consonant(LastChar, SoftenedChar),
        sub_string(RootStr, 0, LastIdx, 1, RootBase),
        string_concat(RootBase, SoftenedChar, SoftenedRootStr),
        atom_string(SoftenedRoot, SoftenedRootStr).

    apply_consonant_softening(Root, Root) :-
        \+ needs_softening(Root).

    needs_softening(Root) :-
        atom_string(Root, RootStr),
        string_length(RootStr, Len),
        Len > 0,
        LastIdx is Len - 1,
        sub_string(RootStr, LastIdx, 1, 0, LastChar),
        member(LastChar, ["p", "ç", "t", "k"]).

    soften_consonant("p", "b").
    soften_consonant("ç", "c").
    soften_consonant("t", "d").
    soften_consonant("k", "ğ").

    % --- ÜNSÜZ BENZEŞMESİ (SERTLEŞMESİ) ---
    % Sert ünsüzlerden sonra ek ünsüzü sertleşir: -di → -ti

    apply_consonant_assimilation(Root, SuffixTemplate, AssimilatedSuffix) :-
        get_last_consonant(Root, LastConsonant),
        (   turkish_hard_consonant(LastConsonant)
        ->  harden_suffix(SuffixTemplate, AssimilatedSuffix)
        ;   AssimilatedSuffix = SuffixTemplate
        ).

    harden_suffix(Suffix, Hardened) :-
        atom_string(Suffix, SuffixStr),
        string_replace(SuffixStr, "d", "t", Temp1),
        string_replace(Temp1, "c", "ç", Hardened).

    % --- ÜNLÜ DARALMASI ---
    % a/e → ı/i -yor önünde (başla + yor → başlıyor)

    apply_vowel_narrowing(Root, before_yor, NarrowedRoot) :-
        atom_string(Root, RootStr),
        string_length(RootStr, Len),
        Len > 0,
        LastIdx is Len - 1,
        sub_string(RootStr, LastIdx, 1, 0, LastChar),
        narrow_vowel(LastChar, NarrowedChar),
        sub_string(RootStr, 0, LastIdx, 1, RootBase),
        string_concat(RootBase, NarrowedChar, NarrowedRootStr),
        atom_string(NarrowedRoot, NarrowedRootStr).

    apply_vowel_narrowing(Root, _, Root) :-
        \+ needs_narrowing(Root).

    needs_narrowing(Root) :-
        atom_string(Root, RootStr),
        string_length(RootStr, Len),
        Len > 0,
        LastIdx is Len - 1,
        sub_string(RootStr, LastIdx, 1, 0, LastChar),
        member(LastChar, ["a", "e"]).

    narrow_vowel("a", "ı").
    narrow_vowel("e", "i").

    % --- KAYNASTIRMA ÜNSÜZLERİ ---
    % İki ünlü arasına y, n, s eklenir

    apply_buffer_consonant(Root, SuffixStart, BufferedRoot) :-
        atom_string(Root, RootStr),
        string_length(RootStr, Len),
        Len > 0,
        LastIdx is Len - 1,
        sub_string(RootStr, LastIdx, 1, 0, LastChar),
        is_vowel(LastChar),
        is_vowel(SuffixStart),
        string_concat(RootStr, "y", BufferedRootStr),
        atom_string(BufferedRoot, BufferedRootStr).

    apply_buffer_consonant(Root, _, Root).

    % --- İNGİLİZCE FONOLOJİ KURALLARI ---

    % CVC pattern kontrolü (ünsüz-ünlü-ünsüz)
    is_cvc_pattern(Word) :-
        atom_string(Word, WordStr),
        string_length(WordStr, Len),
        Len >= 3,
        Idx1 is Len - 3,
        Idx2 is Len - 2,
        Idx3 is Len - 1,
        sub_string(WordStr, Idx1, 1, _, Char1),
        sub_string(WordStr, Idx2, 1, _, Char2),
        sub_string(WordStr, Idx3, 1, _, Char3),
        is_consonant(Char1),
        is_vowel(Char2),
        is_consonant(Char3),
        \+ member(Char3, ["w", "x", "y"]).

    % İngilizce son ünsüz ikilemesi
    apply_english_doubling(Word, Context, Doubled) :-
        member(Context, [suffix_ing, suffix_ed]),
        is_cvc_pattern(Word),
        atom_string(Word, WordStr),
        string_length(WordStr, Len),
        LastIdx is Len - 1,
        sub_string(WordStr, LastIdx, 1, 0, LastChar),
        string_concat(WordStr, LastChar, DoubledStr),
        atom_string(Doubled, DoubledStr).

    apply_english_doubling(Word, _, Word) :-
        \+ is_cvc_pattern(Word).

    % İngilizce sessiz-e düşmesi
    apply_silent_e_drop(Word, Trimmed) :-
        atom_string(Word, WordStr),
        string_length(WordStr, Len),
        Len > 1,
        LastIdx is Len - 1,
        sub_string(WordStr, LastIdx, 1, 0, "e"),
        PrevIdx is Len - 2,
        sub_string(WordStr, PrevIdx, 1, 0, PrevChar),
        is_consonant(PrevChar),
        sub_string(WordStr, 0, LastIdx, 1, TrimmedStr),
        atom_string(Trimmed, TrimmedStr).

    apply_silent_e_drop(Word, Word) :-
        atom_string(Word, WordStr),
        string_length(WordStr, Len),
        (   Len =< 1
        ;   LastIdx is Len - 1,
            sub_string(WordStr, LastIdx, 1, 0, LastChar),
            LastChar \= "e"
        ).

    % İngilizce -ie → -ying dönüşümü
    apply_ie_to_y(Word, Transformed) :-
        atom_string(Word, WordStr),
        sub_string(WordStr, _, 2, 0, "ie"),
        string_length(WordStr, Len),
        BaseLen is Len - 2,
        sub_string(WordStr, 0, BaseLen, 2, Base),
        string_concat(Base, "y", TransformedStr),
        atom_string(Transformed, TransformedStr).

    apply_ie_to_y(Word, Word) :-
        atom_string(Word, WordStr),
        \+ sub_string(WordStr, _, 2, 0, "ie").

    % İngilizce y → i dönüşümü (ünsüz + y)
    apply_y_to_i(Word, Transformed) :-
        atom_string(Word, WordStr),
        string_length(WordStr, Len),
        Len >= 2,
        LastIdx is Len - 1,
        sub_string(WordStr, LastIdx, 1, 0, "y"),
        PrevIdx is Len - 2,
        sub_string(WordStr, PrevIdx, 1, 0, PrevChar),
        is_consonant(PrevChar),
        sub_string(WordStr, 0, LastIdx, 1, Base),
        string_concat(Base, "i", TransformedStr),
        atom_string(Transformed, TransformedStr).

    apply_y_to_i(Word, Word) :-
        atom_string(Word, WordStr),
        string_length(WordStr, Len),
        (   Len < 2
        ;   LastIdx is Len - 1,
            sub_string(WordStr, LastIdx, 1, 0, LastChar),
            LastChar \= "y"
        ;   LastIdx is Len - 1,
            sub_string(WordStr, LastIdx, 1, 0, "y"),
            PrevIdx is Len - 2,
            sub_string(WordStr, PrevIdx, 1, 0, PrevChar),
            is_vowel(PrevChar)
        ).

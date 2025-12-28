:- module(morph_tense, [
    find_tense_and_root/4,
    find_matching_root/2
]).

:- encoding(utf8).

:- use_module('../data/morphology_data', [
    tense_suffix/2,
    verb_root/3,
    turkish_irregular_root/2
]).

% morphology_core importunu KALDIRDIK. Artık ihtiyaç yok.

find_tense_and_root(Word, Root, Tense, Remainder) :-
    atom_string(Word, WordStr),
    tense_suffix(TenseSuffix, Tense),
    atom_string(TenseSuffix, TenseSuffixStr),
    string_length(TenseSuffixStr, TenseLen),
    TenseLen > 0,
    sub_string(WordStr, Before, TenseLen, After, TenseSuffixStr),
    Before > 0,
    sub_string(WordStr, 0, Before, _, RootStr),
    sub_string(WordStr, _, After, 0, RemainderStr),
    find_matching_root(RootStr, Root),
    atom_string(Remainder, RemainderStr).

find_tense_and_root(Word, Root, present_continuous, Remainder) :-
    atom_string(Word, WordStr),
    sub_string(WordStr, Before, 3, After, "yor"),
    Before > 0,
    sub_string(WordStr, 0, Before, _, RootWithVowelStr),
    sub_string(WordStr, _, After, 0, RemainderStr),
    string_length(RootWithVowelStr, Len),
    Prev is Len - 1,
    sub_string(RootWithVowelStr, Prev, 1, 0, Last),
    member(Last, ["i","ı","u","ü"]),
    sub_string(RootWithVowelStr, 0, Prev, _, TrueRoot),
    find_matching_root(TrueRoot, Root),
    atom_string(Remainder, RemainderStr),
    !.

% =============================================================================
% KÖK EŞLEŞTİRME (CORE'DAN BURAYA TAŞINDI)
% =============================================================================

% Kök eşleştirme
find_matching_root(RootStr, Root) :-
    % Önce Türkçe düzensiz fiil alternatifleri kontrol et
    turkish_irregular_root(RootStr, Root),
    !.

% (Ünlü Daralması Kurtarma)
find_matching_root(RootStr, Root) :-
    % Ünlü daralması: dinl -> dinle, başl -> başla
    member(Vowel, ["e", "a"]),
    string_concat(RootStr, Vowel, RecoveredStr),
    atom_string(RecoveredAtom, RecoveredStr),
    verb_root(RecoveredAtom, _, _),
    Root = RecoveredAtom,
    !.
% ------------------------------------------------

find_matching_root(RootStr, Root) :-
    verb_root(Root, _, _),
    atom_string(Root, RootAtomStr),
    (   RootStr = RootAtomStr
    ;   % Ünlü uyumu - son birkaç karakter eşleşebilir
        string_length(RootAtomStr, RootLen),
        string_length(RootStr, InputLen),
        InputLen >= RootLen,
        Diff is InputLen - RootLen,
        Diff =< 2,
        sub_string(RootStr, Diff, RootLen, 0, RootAtomStr)
    ),
    !.

find_matching_root(RootStr, Root) :-
    atom_string(Root, RootStr).
% =============================================================================
% DOSYA: tr_verbs.pl
% GÖREV: FİİL ANALİZİ
% AÇIKLAMA:
%   - Hareket ve iş bildiren kelimeleri analiz eder.
%   - KAPSADIĞI TÜRLER: Fiiller (Verb).
%   - Zaman ekleri (Geçmiş, Şimdiki, Gelecek...) ve Şahıs eklerini çözer.
%   - Olumsuzluk ekleri (-ma/-me) ve Çatı eklerini yönetir.
%   - Fiil kökünden başlayıp ek zincirini takip eder.
% =============================================================================

% =============================================================================
% DOSYA: tr_verbs.pl
% GÖREV: FİİL ANALİZİ
% =============================================================================

:- module(tr_verbs, [
    analyze_turkish/2,
    find_tense_and_root/4,
    check_negation/3,
    find_person/4
]).

% DÜZELTME: Morphology klasöründen yukarı çıkıp morphology_data klasörüne girer.
:- use_module('../morphology_data/morphology_data').
:- use_module(tr_phonology).

% --- FİİL ANALİZİ ---
analyze_turkish(Word, Analysis) :-
    atom_string(Word, WordStr),
    string_lower(WordStr, LowerStr),
    atom_string(LowerWord, LowerStr),
    
    check_negation(LowerWord, CleanWord, Negation),
    find_tense_and_root(CleanWord, Root, Tense, Remainder),
    find_person(Remainder, Tense, Person, Plurality),
    
    Analysis = [root:Root, tense:Tense, person:Person, plurality:Plurality, negation:Negation].

% --- OLUMSUZLUK KONTROLÜ ---
check_negation(Word, CleanWord, true) :-
    atom_string(Word, WordStr),
    (sub_string(WordStr, B, _, A, "miyor"); sub_string(WordStr, B, _, A, "muyor")), B>0,
    sub_string(WordStr, 0, B, _, RootPart), sub_string(WordStr, _, A, 0, PersonPart),
    string_concat(RootPart, "iyor", Temp), string_concat(Temp, PersonPart, New),
    atom_string(CleanWord, New), !.

check_negation(Word, CleanWord, true) :-
    atom_string(Word, WordStr),
    (sub_string(WordStr, B, 4, A, "medi"); sub_string(WordStr, B, 4, A, "madı"); sub_string(WordStr, B, 4, A, "madi")), B>0,
    sub_string(WordStr, 0, B, _, RootPart), sub_string(WordStr, _, A, 0, PersonPart),
    string_concat(RootPart, "di", Temp), string_concat(Temp, PersonPart, New),
    atom_string(CleanWord, New), !.

check_negation(Word, CleanWord, true) :-
    atom_string(Word, WordStr),
    (sub_string(WordStr, B, 7, A, "meyecek"); sub_string(WordStr, B, 7, A, "mayacak")), B>0,
    sub_string(WordStr, 0, B, _, RootPart), sub_string(WordStr, _, A, 0, PersonPart),
    (sub_string(WordStr, _, _, _, "meyecek") -> string_concat(RootPart, "ecek", Temp); string_concat(RootPart, "acak", Temp)),
    string_concat(Temp, PersonPart, New), atom_string(CleanWord, New), !.

check_negation(Word, CleanWord, true) :-
    atom_string(Word, WordStr),
    (sub_string(WordStr, B, 3, A, "mez"); sub_string(WordStr, B, 3, A, "maz")), B>0,
    sub_string(WordStr, 0, B, _, RootPart), sub_string(WordStr, _, A, 0, PersonPart),
    (sub_string(WordStr, _, _, _, "mez") -> string_concat(RootPart, "er", Temp); string_concat(RootPart, "ar", Temp)),
    string_concat(Temp, PersonPart, New), atom_string(CleanWord, New), !.

check_negation(Word, Word, false).

% --- ZAMAN VE KÖK BULMA ---
find_tense_and_root(Word, Root, Tense, Remainder) :-
    atom_string(Word, WordStr),
    sub_string(WordStr, Before, 3, After, "yor"), Before > 0,
    sub_string(WordStr, 0, Before, _, RootNarrowStr),
    string_length(RootNarrowStr, Len), Last is Len - 1,
    sub_string(RootNarrowStr, Last, 1, 0, LastChar),
    reverse_narrowing(LastChar, WideChar),
    sub_string(RootNarrowStr, 0, Last, 1, Base),
    string_concat(Base, WideChar, RealRootStr),
    atom_string(RealRootAtom, RealRootStr),
    
    % Veritabanı 3 parametreli (Kök, İngilizce, Tür) ama biz ilkini istiyoruz.
    verb_root(RealRootAtom, _, _),
    
    Root = RealRootAtom, Tense = present_continuous,
    sub_string(WordStr, _, After, 0, RemStr), atom_string(Remainder, RemStr), !.

find_tense_and_root(Word, Root, Tense, Remainder) :-
    atom_string(Word, WordStr),
    tense_suffix(Suffix, Tense), atom_string(Suffix, SufStr), string_length(SufStr, L), L > 0,
    sub_string(WordStr, Before, L, After, SufStr), Before > 0,
    sub_string(WordStr, 0, Before, _, RootStr), sub_string(WordStr, _, After, 0, RemStr),
    find_matching_root(RootStr, Root),
    atom_string(Remainder, RemStr).

find_tense_and_root(Word, Root, Tense, Remainder) :-
    atom_string(Word, WordStr),
    sub_string(WordStr, Before, 3, After, "yor"), Before > 0,
    sub_string(WordStr, 0, Before, _, RootWithVowel),
    sub_string(WordStr, _, After, 0, RemStr),
    string_length(RootWithVowel, RL), RL > 0, PL is RL - 1,
    sub_string(RootWithVowel, PL, 1, 0, LC), member(LC, ["i","u","ı","ü"]),
    sub_string(RootWithVowel, 0, PL, _, TrueRoot),
    find_matching_root(TrueRoot, Root),
    Tense = present_continuous,
    atom_string(Remainder, RemStr), !.

find_matching_root(Str, Root) :- turkish_irregular_root(Str, Root), !.
find_matching_root(Str, Root) :- verb_root(Root, _, _), atom_string(Root, R), (Str=R), !.
find_matching_root(Str, Root) :- atom_string(Root, Str).

% --- ŞAHIS BULMA ---
find_person(Rem, Tense, Person, Plural) :-
    person_suffix(Suffix, Person, Plural, Tense), atom_string(Suffix, S), atom_string(Rem, R),
    (S="" -> R=""; sub_string(R, _, _, 0, S)), !.
find_person(_, _, 3, singular).""
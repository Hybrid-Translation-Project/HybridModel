:- module(morph_gerund, [
    analyze_gerund/2,
    translate_gerund/3
]).

:- encoding(utf8).

% Circular dependency yerine direkt import
:- use_module('../utils/morph_eng_utils', [
    get_present_participle/2
]).

:- use_module('../data/morphology_data', [
    verb_root/3,
    turkish_irregular_root/2
]).

% =============================================================================
% ZARF-FİİL (GERUND/ADVERBIAL) ANALİZİ
% =============================================================================

% analyze_gerund(+Word, -Analysis)
% Analysis = [root:Root, english_root:EnRoot, gerund_type:Type, translation:Trans]
analyze_gerund(Word, Analysis) :-
    atom_string(Word, WordStr),
    string_lower(WordStr, LowerStr),
    check_gerund_suffix(LowerStr, RootStr, GerundType),
    atom_string(RootAtom, RootStr),
    find_verb_root_safe(RootAtom, TrRoot, EnRoot),
    get_gerund_translation(EnRoot, GerundType, Translation),
    Analysis = [
        root:TrRoot,
        english_root:EnRoot,
        gerund_type:GerundType,
        translation:Translation
    ].

% -----------------------------------------------------------------------------
% Fiil kökü bulma (güvenli)
% -----------------------------------------------------------------------------

find_verb_root_safe(RootAtom, TrRoot, EnRoot) :-
    atom_string(RootAtom, RootStr),
    turkish_irregular_root(RootStr, TrRoot),
    verb_root(TrRoot, EnRoot, _),
    !.

find_verb_root_safe(RootAtom, TrRoot, EnRoot) :-
    verb_root(RootAtom, EnRoot, _),
    TrRoot = RootAtom,
    !.

find_verb_root_safe(RootAtom, TrRoot, EnRoot) :-
    atom_string(RootAtom, RootStr),
    member(Vowel, ["u", "ü", "ı", "i", "a", "e"]),
    string_concat(RootStr, Vowel, ExtendedStr),
    atom_string(ExtendedAtom, ExtendedStr),
    verb_root(ExtendedAtom, EnRoot, _),
    TrRoot = ExtendedAtom,
    !.

find_verb_root_safe(RootAtom, RootAtom, RootAtom).

% -----------------------------------------------------------------------------
% Zarf-fiil ekleri
% -----------------------------------------------------------------------------

check_gerund_suffix(WordStr, RootStr, while) :-
    string_length(WordStr, Len),
    Len > 5,
    (   sub_string(WordStr, _, 5, 0, "arken")
    ;   sub_string(WordStr, _, 5, 0, "erken")
    ;   sub_string(WordStr, _, 5, 0, "ırken")
    ;   sub_string(WordStr, _, 5, 0, "irken")
    ;   sub_string(WordStr, _, 5, 0, "urken")
    ;   sub_string(WordStr, _, 5, 0, "ürken")
    ),
    BaseLen is Len - 5,
    sub_string(WordStr, 0, BaseLen, 5, RootStr),
    !.

check_gerund_suffix(WordStr, RootStr, while) :-
    string_length(WordStr, Len),
    Len > 6,
    sub_string(WordStr, _, 6, 0, "yorken"),
    BaseLen is Len - 6,
    sub_string(WordStr, 0, BaseLen, 6, TempRootStr),
    (   string_length(TempRootStr, TempLen),
        TempLen > 0,
        LastIdx is TempLen - 1,
        sub_string(TempRootStr, LastIdx, 1, 0, LastChar),
        member(LastChar, ["i", "ı", "u", "ü"])
    ->  sub_string(TempRootStr, 0, LastIdx, 1, RootStr)
    ;   RootStr = TempRootStr
    ),
    !.

check_gerund_suffix(WordStr, RootStr, while) :-
    string_length(WordStr, Len),
    Len > 3,
    sub_string(WordStr, _, 3, 0, "ken"),
    \+ sub_string(WordStr, _, 5, 0, "arken"),
    \+ sub_string(WordStr, _, 5, 0, "erken"),
    \+ sub_string(WordStr, _, 6, 0, "yorken"),
    BaseLen is Len - 3,
    sub_string(WordStr, 0, BaseLen, 3, BeforeKen),
    remove_aorist_suffix(BeforeKen, RootStr),
    !.

check_gerund_suffix(WordStr, RootStr, by) :-
    string_length(WordStr, Len),
    Len > 5,
    (   sub_string(WordStr, _, 5, 0, "yarak")
    ;   sub_string(WordStr, _, 5, 0, "yerek")
    ),
    BaseLen is Len - 5,
    sub_string(WordStr, 0, BaseLen, 5, RootStr),
    !.

check_gerund_suffix(WordStr, RootStr, by) :-
    string_length(WordStr, Len),
    Len > 4,
    (   sub_string(WordStr, _, 4, 0, "arak")
    ;   sub_string(WordStr, _, 4, 0, "erek")
    ),
    BaseLen is Len - 4,
    sub_string(WordStr, 0, BaseLen, 4, RootStr),
    !.

check_gerund_suffix(WordStr, RootStr, when) :-
    string_length(WordStr, Len),
    Len > 4,
    (   sub_string(WordStr, _, 4, 0, "ınca")
    ;   sub_string(WordStr, _, 4, 0, "ince")
    ;   sub_string(WordStr, _, 4, 0, "unca")
    ;   sub_string(WordStr, _, 4, 0, "ünce")
    ),
    BaseLen is Len - 4,
    sub_string(WordStr, 0, BaseLen, 4, RootStr),
    !.

check_gerund_suffix(WordStr, RootStr, without) :-
    string_length(WordStr, Len),
    Len > 5,
    (   sub_string(WordStr, _, 5, 0, "madan")
    ;   sub_string(WordStr, _, 5, 0, "meden")
    ),
    BaseLen is Len - 5,
    sub_string(WordStr, 0, BaseLen, 5, RootStr),
    !.

% -----------------------------------------------------------------------------
% Geniş zaman eki silme
% -----------------------------------------------------------------------------

remove_aorist_suffix(WordStr, RootStr) :-
    string_length(WordStr, Len),
    Len > 2,
    (   sub_string(WordStr, _, 2, 0, "ar")
    ;   sub_string(WordStr, _, 2, 0, "er")
    ;   sub_string(WordStr, _, 2, 0, "ır")
    ;   sub_string(WordStr, _, 2, 0, "ir")
    ;   sub_string(WordStr, _, 2, 0, "ur")
    ;   sub_string(WordStr, _, 2, 0, "ür")
    ),
    BaseLen is Len - 2,
    sub_string(WordStr, 0, BaseLen, 2, RootStr),
    !.

remove_aorist_suffix(WordStr, RootStr) :-
    string_length(WordStr, Len),
    Len > 1,
    sub_string(WordStr, _, 1, 0, "r"),
    BaseLen is Len - 1,
    sub_string(WordStr, 0, BaseLen, 1, RootStr),
    !.

remove_aorist_suffix(WordStr, WordStr).

% -----------------------------------------------------------------------------
% Zarf-fiil tipine göre İngilizce çeviri
% -----------------------------------------------------------------------------

get_gerund_translation(EnRoot, while, Translation) :-
    get_present_participle(EnRoot, Participle),
    format(atom(Translation), "while ~w", [Participle]).

get_gerund_translation(EnRoot, by, Translation) :-
    get_present_participle(EnRoot, Participle),
    format(atom(Translation), "by ~w", [Participle]).

get_gerund_translation(EnRoot, when, Translation) :-
    get_present_participle(EnRoot, Participle),
    format(atom(Translation), "when ~w", [Participle]).

get_gerund_translation(EnRoot, without, Translation) :-
    get_present_participle(EnRoot, Participle),
    format(atom(Translation), "without ~w", [Participle]).

% -----------------------------------------------------------------------------
% translate_gerund/3
% -----------------------------------------------------------------------------

translate_gerund(TurkishWord, EnglishTranslation, Details) :-
    analyze_gerund(TurkishWord, Analysis),
    member(translation:EnglishTranslation, Analysis),
    Details = Analysis.

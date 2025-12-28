:- module(morph_utils, [
    is_vowel/1,
    is_consonant/1,
    unsoften_consonant/2,
    string_replace/4
]).

:- encoding(utf8).

% =============================================================================
% UTILS
% =============================================================================

% Atom olarak ünlüler (string_chars sonucu için)
is_vowel(a). is_vowel(e). is_vowel(i). is_vowel(o). is_vowel(u).
is_vowel(ı). is_vowel(ö). is_vowel(ü).
is_vowel('A'). is_vowel('E'). is_vowel('I'). is_vowel('O'). is_vowel('U').
is_vowel('İ'). is_vowel('Ö'). is_vowel('Ü').

% String olarak ünlüler (eski kod uyumluluğu için)
is_vowel("a"). is_vowel("e"). is_vowel("i"). is_vowel("o"). is_vowel("u").
is_vowel("ı"). is_vowel("ö"). is_vowel("ü").
is_vowel("A"). is_vowel("E"). is_vowel("I"). is_vowel("O"). is_vowel("U").
is_vowel("İ"). is_vowel("Ö"). is_vowel("Ü").

% Consonant - hem atom hem string kabul eder
is_consonant(Char) :-
    % Atom ise
    (   atom(Char)
    ->  atom_length(Char, 1),
        \+ is_vowel(Char),
        % Harf kontrolü
        atom_codes(Char, [Code]),
        (   (Code >= 65, Code =< 90)   % A-Z
        ;   (Code >= 97, Code =< 122)  % a-z
        ;   Code = 231  % ç
        ;   Code = 199  % Ç
        ;   Code = 287  % ğ
        ;   Code = 286  % Ğ
        ;   Code = 305  % ı
        ;   Code = 304  % İ
        ;   Code = 246  % ö
        ;   Code = 214  % Ö
        ;   Code = 252  % ü
        ;   Code = 220  % Ü
        ;   Code = 351  % ş
        ;   Code = 350  % Ş
        )
    % String ise
    ;   string(Char)
    ->  string_length(Char, 1),
        \+ is_vowel(Char)
    ).

% Reverse softening (ünsüz yumuşamasını geri al)
unsoften_consonant("b", "p").
unsoften_consonant("c", "ç").
unsoften_consonant("d", "t").
unsoften_consonant("ğ", "k").
unsoften_consonant("g", "k").

% String replace helper
string_replace(String, From, To, Result) :-
    split_string(String, From, "", Parts),
    atomics_to_string(Parts, To, Result).
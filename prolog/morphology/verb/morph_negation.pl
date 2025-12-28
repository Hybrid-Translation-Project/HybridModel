% =============================================================================
% MORPH NEGATION
% =============================================================================
% Türkçe fiillerde olumsuzluk eklerini ayıklar
% Örn:
%   gelmiyorum -> geliyorum + negation:true
%   gelmez     -> gelir + negation:true
%
% SADECE ANALİZ YAPAR
% =============================================================================

:- module(morph_negation, [
    check_negation/3
]).

:- encoding(utf8).
% strip_negation(+Word, -CleanWord, -Negation)
% Negation = true | false

    % Olumsuzluk kontrolü
    check_negation(Word, CleanWord, true) :-
        atom_string(Word, WordStr),
        % -miyor, -mıyor pattern + şahıs ekleri
        (   sub_string(WordStr, Before, _, After, "miyor")
        ;   sub_string(WordStr, Before, _, After, "muyor")
        ),
        Before > 0,
        sub_string(WordStr, 0, Before, _, RootPart),
        sub_string(WordStr, _, After, 0, PersonPart),
        % 'm' harfini kaldır ve 'iyor' + şahıs ekleri
        string_concat(RootPart, "iyor", TempStr),
        string_concat(TempStr, PersonPart, NewWordStr),
        atom_string(CleanWord, NewWordStr),
        !.

    check_negation(Word, CleanWord, true) :-
        atom_string(Word, WordStr),
        % -medi, -madı pattern
        (   sub_string(WordStr, Before, 4, After, "medi")
        ;   sub_string(WordStr, Before, 4, After, "madı")
        ;   sub_string(WordStr, Before, 4, After, "madi")
        ),
        Before > 0,
        sub_string(WordStr, 0, Before, _, RootPart),
        sub_string(WordStr, _, After, 0, PersonPart),
        string_concat(RootPart, "di", TempStr),
        string_concat(TempStr, PersonPart, NewWordStr),
        atom_string(CleanWord, NewWordStr),
        !.

    check_negation(Word, CleanWord, true) :-
        atom_string(Word, WordStr),
        % -meyecek, -mayacak pattern
        (   sub_string(WordStr, Before, 7, After, "meyecek")
        ;   sub_string(WordStr, Before, 7, After, "mayacak")
        ),
        Before > 0,
        sub_string(WordStr, 0, Before, _, RootPart),
        sub_string(WordStr, _, After, 0, PersonPart),
        (   sub_string(WordStr, _, _, _, "meyecek") 
        ->  string_concat(RootPart, "ecek", TempStr)
        ;   string_concat(RootPart, "acak", TempStr)
        ),
        string_concat(TempStr, PersonPart, NewWordStr),
        atom_string(CleanWord, NewWordStr),
        !.

    check_negation(Word, CleanWord, true) :-
        atom_string(Word, WordStr),
        % -mez, -maz pattern (geniş zaman olumsuz)
        (   sub_string(WordStr, Before, 3, After, "mez")
        ;   sub_string(WordStr, Before, 3, After, "maz")
        ),
        Before > 0,
        sub_string(WordStr, 0, Before, _, RootPart),
        sub_string(WordStr, _, After, 0, PersonPart),
        (   sub_string(WordStr, _, _, _, "mez")
        ->  string_concat(RootPart, "er", TempStr)
        ;   string_concat(RootPart, "ar", TempStr)
        ),
        string_concat(TempStr, PersonPart, NewWordStr),
        atom_string(CleanWord, NewWordStr),
        !.

    check_negation(Word, Word, false).
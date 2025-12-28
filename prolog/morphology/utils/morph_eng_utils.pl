:- module(morph_eng_utils, [
    subject_pronoun/3,
    get_present_participle/2,
    is_vowel_en/1,
    is_consonant_en/1
]).

:- encoding(utf8).

% Eğer morph_utils içinden bir şey kullanmayacaksan bu importu silebilirsin
% ama durmasının bir zararı yok.
:- use_module('./morph_utils', [
    is_vowel/1,
    is_consonant/1
]). 

subject_pronoun(1, singular, 'I').
subject_pronoun(2, singular, you).
subject_pronoun(3, singular, 'he/she').
subject_pronoun(1, plural, we).
subject_pronoun(2, plural, you).
subject_pronoun(3, plural, they).

get_present_participle(Verb, Participle) :-
    atom_string(Verb, VerbStr),
    (   
        % 1. -e ile bitenler (ee hariç)
        string_concat(Base, "e", VerbStr),
        \+ string_concat(_, "ee", VerbStr)
    ->  string_concat(Base, "ing", PartStr)
    ;   
        % 2. -ie ile bitenler
        string_concat(Base, "ie", VerbStr)
    ->  string_concat(Base, "ying", PartStr)
    ;   
        % 3. Çift ünlü + ünsüz (wait -> waiting) - İkizleme YOK
        string_length(VerbStr, Len), Len >= 3,
        sub_string(VerbStr, _, 3, 0, LastThree),
        string_chars(LastThree, [V1, V2, C]),
        % V1, V2, C atom olarak geliyor, is_vowel_en/is_consonant_en kullanıyoruz
        is_vowel_en(V1),
        is_vowel_en(V2),
        is_consonant_en(C)
    ->  string_concat(VerbStr, "ing", PartStr)
    ;   
        % 4. Sonu 'en', 'on', 'er' ile bitenler - İkizleme YOK
        (   sub_string(VerbStr, _, 2, 0, "en")
        ;   sub_string(VerbStr, _, 2, 0, "on") 
        ;   sub_string(VerbStr, _, 2, 0, "er")
        )
    ->  string_concat(VerbStr, "ing", PartStr)
    ;   
        % 5. CVC Kuralı (Sessiz-Sesli-Sessiz) -> İkizle
        string_length(VerbStr, Len2), Len2 >= 2,
        string_concat(Init, LastChar, VerbStr),
        atom_string(LastCharAtom, LastChar),
        is_consonant_en(LastCharAtom),
        \+ member(LastCharAtom, [w, x, y]), 
        string_length(Init, InitLen), InitLen > 0,
        string_concat(_, SecondLast, Init),
        string_length(SecondLast, 1),
        atom_string(SecondLastAtom, SecondLast),
        is_vowel_en(SecondLastAtom)
    ->  string_concat(VerbStr, LastChar, Doubled),
        string_concat(Doubled, "ing", PartStr)
    ;   
        % 6. Varsayılan durum
        string_concat(VerbStr, "ing", PartStr)
    ),
    atom_string(Participle, PartStr).

% İngilizce ünlüler - atom versiyonu
is_vowel_en(Char) :- member(Char, [a, e, i, o, u, 'A', 'E', 'I', 'O', 'U']).

% İngilizce ünsüzler - atom versiyonu
is_consonant_en(Char) :- 
    atom(Char),
    atom_length(Char, 1),
    \+ is_vowel_en(Char),
    % Sadece harflere izin ver (sayı veya noktalama değil)
    atom_codes(Char, [Code]),
    (   (Code >= 65, Code =< 90)   % A-Z
    ;   (Code >= 97, Code =< 122)  % a-z
    ).
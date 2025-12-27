% =============================================================================
% DOSYA: en_rules.pl
% GÖREV: İngilizce Cümle Sentezi (English Synthesis)
% AÇIKLAMA:
%   - Türkçe analizden gelen kök, zaman ve şahıs bilgilerini alır.
%   - İngilizce dilbilgisi kurallarına (SVO yapısı) göre cümleyi kurar.
%   - Fiil çekimlerini (V-ing, V-ed, V-s) ve düzensiz fiilleri yönetir.
%   - Soru cümlesi oluşturma mantığını içerir.
% =============================================================================

:- module(en_rules, [
    conjugate_english/6,
    build_question/5,
    get_present_participle/2,
    get_past_simple/3,
    get_past_participle/2,
    subject_pronoun/3
]).

% Veritabanı bağlantısı (2 klasör yukarı, sonra database)
:- use_module('../../database/morphology_data').

% Sesli/Sessiz harf kontrolü için ortak fonoloji modülü (1 klasör yukarı, sonra turkish)
:- use_module('../turkish/tr_phonology'). 

% =============================================================================
% İNGİLİZCE FİİL ÇEKİMİ (MAIN LOGIC)
% =============================================================================

% conjugate_english(+Verb, +Tense, +Person, +Plurality, +Negation, -Conjugated)
conjugate_english(Verb, Tense, Person, Plurality, Negation, Result) :-
    % 1. Fiilin doğru formunu bul (going, went, goes...)
    get_verb_form(Verb, Tense, Person, Plurality, Negation, VerbForm),
    
    % 2. Özneyi bul (I, You, We...)
    subject_pronoun(Person, Plurality, Subject),
    
    % 3. Cümleyi birleştir (Yardımcı fiil varsa ekle)
    build_sentence(Subject, Tense, Person, Plurality, Negation, VerbForm, Result).

% Cümle İnşası
build_sentence(Subject, Tense, Person, Plurality, Negation, VerbForm, Result) :-
    (   auxiliary_verb(Tense, Person, Plurality, Negation, Aux)
    ->  format(atom(Result), "~w ~w ~w", [Subject, Aux, VerbForm])
    ;   format(atom(Result), "~w ~w", [Subject, VerbForm])
    ).

% =============================================================================
% FİİL FORMLARI SEÇİCİSİ (Zamana Göre)
% =============================================================================

% Şimdiki Zaman (V-ing)
get_verb_form(Verb, present_continuous, _, _, _, VerbForm) :-
    get_present_participle(Verb, VerbForm).

% Geçmiş Zaman (V2 / V-ed) - Olumlu
get_verb_form(Verb, past_simple, Person, _, false, VerbForm) :-
    get_past_simple(Verb, Person, VerbForm).

% Geçmiş Zaman - Olumsuz (Did not + V1)
get_verb_form(Verb, past_simple, _, _, true, Verb).

% Gelecek Zaman (Will + V1)
get_verb_form(Verb, future, _, _, _, Verb).

% Geniş Zaman - Olumlu (V1 veya V-s)
get_verb_form(Verb, aorist, Person, Plurality, false, VerbForm) :-
    get_present_simple(Verb, Person, Plurality, VerbForm).

% Geniş Zaman - Olumsuz (Don't/Doesn't + V1)
get_verb_form(Verb, aorist, _, _, true, Verb).

% Duyulan Geçmiş (Have/Has + V3)
get_verb_form(Verb, past_reported, _, _, _, VerbForm) :-
    get_past_participle(Verb, VerbForm).

% Gereklilik ve Yeterlilik (Modal + V1)
get_verb_form(Verb, necessity, _, _, _, Verb).
get_verb_form(Verb, ability, _, _, _, Verb).

% Fallback (Bilinmeyen durumlar için yalın hal)
get_verb_form(Verb, _, _, _, _, Verb).

% =============================================================================
% MORFOLOJİK KURALLAR (EKLEME MANTIĞI)
% =============================================================================

% --- Present Participle (V-ing) ---
get_present_participle(Verb, Participle) :-
    irregular_verb(Verb, _, _, Participle), !.  % Varsa düzensiz halini al

get_present_participle(Verb, Participle) :-
    atom_string(Verb, VerbStr),
    (   % Kural 1: -e ile biten (make -> making) ama -ee değil (see -> seeing)
        string_concat(Base, "e", VerbStr),
        \+ string_concat(_, "ee", VerbStr)
    ->  string_concat(Base, "ing", PartStr)
    
    ;   % Kural 2: -ie ile biten (lie -> lying)
        string_concat(Base, "ie", VerbStr)
    ->  string_concat(Base, "ying", PartStr)
    
    ;   % Kural 3: CVC kuralı (run -> running) - Son harfi ikile
        is_cvc_pattern(Verb)
    ->  string_length(VerbStr, Len),
        LastIdx is Len - 1,
        sub_string(VerbStr, LastIdx, 1, 0, LastChar),
        string_concat(VerbStr, LastChar, Doubled),
        string_concat(Doubled, "ing", PartStr)
        
    ;   % Kural 4: Normal ekleme (go -> going)
        string_concat(VerbStr, "ing", PartStr)
    ),
    atom_string(Participle, PartStr).

% CVC (Ünsüz-Ünlü-Ünsüz) Kontrolü
is_cvc_pattern(Word) :-
    atom_string(Word, WordStr),
    string_length(WordStr, Len),
    Len >= 3,
    Idx1 is Len - 3,
    Idx2 is Len - 2,
    Idx3 is Len - 1,
    sub_string(WordStr, Idx1, 1, _, C1),
    sub_string(WordStr, Idx2, 1, _, V),
    sub_string(WordStr, Idx3, 1, _, C2),
    is_consonant(C1),
    is_vowel(V),
    is_consonant(C2),
    \+ member(C2, ["w", "x", "y"]). % w,x,y ile bitenlerde ikileme olmaz (play -> playing)

% --- Past Simple (V2) ---
get_past_simple(Verb, _, Past) :-
    irregular_verb(Verb, Past, _, _), !.

get_past_simple(Verb, _, Past) :-
    atom_string(Verb, VerbStr),
    (   % Kural 1: -e ile biten (love -> loved)
        string_concat(_, "e", VerbStr)
    ->  string_concat(VerbStr, "d", PastStr)
    
    ;   % Kural 2: Ünsüz + y (cry -> cried)
        string_concat(Base, "y", VerbStr),
        string_length(Base, BL), BL > 0,
        sub_string(Base, _, 1, 0, LastOfBase),
        \+ is_vowel(LastOfBase)
    ->  string_concat(Base, "ied", PastStr)
    
    ;   % Kural 3: Normal (walk -> walked)
        string_concat(VerbStr, "ed", PastStr)
    ),
    atom_string(Past, PastStr).

% --- Past Participle (V3) ---
get_past_participle(Verb, Participle) :-
    irregular_verb(Verb, _, Participle, _), !.

get_past_participle(Verb, Participle) :-
    get_past_simple(Verb, 3, Participle). % Düzenli fiillerde V2 = V3

% --- Present Simple (3. Tekil Şahıs -s takısı) ---
get_present_simple(Verb, 3, singular, Conjugated) :- !,
    atom_string(Verb, VerbStr),
    (   Verb = have -> Conjugated = has
    ;   Verb = be   -> Conjugated = is
    ;   Verb = do   -> Conjugated = does
    ;   % -s, -sh, -ch, -x, -o ile bitenlere -es gelir
        (string_concat(_, "s", VerbStr); string_concat(_, "sh", VerbStr);
         string_concat(_, "ch", VerbStr); string_concat(_, "x", VerbStr);
         string_concat(_, "o", VerbStr))
    ->  string_concat(VerbStr, "es", ConjStr), atom_string(Conjugated, ConjStr)
    ;   % Ünsüz + y -> -ies
        string_concat(Base, "y", VerbStr),
        string_length(Base, BL), BL > 0,
        sub_string(Base, _, 1, 0, LastOfBase),
        \+ is_vowel(LastOfBase)
    ->  string_concat(Base, "ies", ConjStr), atom_string(Conjugated, ConjStr)
    ;   % Normal -s
        string_concat(VerbStr, "s", ConjStr), atom_string(Conjugated, ConjStr)
    ).
get_present_simple(Verb, _, _, Verb). % Diğer şahıslarda fiil yalın kalır

% =============================================================================
% SORU CÜMLESİ OLUŞTURMA
% =============================================================================

build_question(Verb, past_simple, Person, Plurality, Question) :-
    subject_pronoun(Person, Plurality, Subject),
    format(atom(Question), "Did ~w ~w?", [Subject, Verb]).

build_question(Verb, present_continuous, Person, Plurality, Question) :-
    subject_pronoun(Person, Plurality, Subject),
    auxiliary_verb(present_continuous, Person, Plurality, false, Aux),
    get_present_participle(Verb, VerbForm),
    format(atom(Question), "~w ~w ~w?", [Aux, Subject, VerbForm]).

build_question(Verb, future, Person, Plurality, Question) :-
    subject_pronoun(Person, Plurality, Subject),
    format(atom(Question), "Will ~w ~w?", [Subject, Verb]).

build_question(Verb, aorist, Person, Plurality, Question) :-
    subject_pronoun(Person, Plurality, Subject),
    (Person = 3, Plurality = singular -> Aux = 'Does' ; Aux = 'Do'),
    format(atom(Question), "~w ~w ~w?", [Aux, Subject, Verb]), !.

% Bilinmeyen zamanlar için varsayılan (Geniş zaman gibi davran)
build_question(Verb, unknown, Person, Plurality, Question) :-
    build_question(Verb, aorist, Person, Plurality, Question).

% =============================================================================
% ÖZNE ZAMİRLERİ
% =============================================================================
subject_pronoun(1, singular, 'I').
subject_pronoun(2, singular, you).
subject_pronoun(3, singular, 'he/she').
subject_pronoun(1, plural, we).
subject_pronoun(2, plural, you).
subject_pronoun(3, plural, they).
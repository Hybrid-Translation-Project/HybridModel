
:- module(morphology_core, [
    translate_word/2,
    analyze_turkish/2,
    translate_verb/3,
    translate_sentence/2,
    conjugate_english/6,
    test_morphology/0
]).

:- encoding(utf8).

% MODÜLLER - Explicit Import (Açıkça belirterek)
:- use_module('../data/morphology_data', [
    person_suffix/4,
    verb_root/3,
    irregular_verb/4,
    auxiliary_verb/5
]).

:- use_module('../utils/morph_utils', [
    is_vowel/1,
    is_consonant/1
]).

:- use_module('../utils/morph_eng_utils', [
    subject_pronoun/3,
    get_present_participle/2
]).

:- use_module('../phonology/morph_phonology').

:- use_module('../verb/morph_tense', [
    find_tense_and_root/4,
    find_matching_root/2 
]).

:- use_module('../verb/morph_negation', [
    check_negation/3
]).

:- use_module('../noun/morph_noun', [
    translate_noun/3,
    analyze_noun/2
]).

:- use_module('../verb/morph_gerund', [
    analyze_gerund/2,
    translate_gerund/3
]).

    % =============================================================================
    % GENEL KELİME ÇEVİRİSİ (FİİL VEYA İSİM VEYA ZARF-FİİL)
    % =============================================================================

    % translate_word(+TurkishWord, -EnglishTranslation)
    translate_word(TurkishWord, EnglishTranslation) :-
        % Önce zarf-fiil olarak dene (-ken, -arak, vs.) - Modülden geliyor
        (   translate_gerund(TurkishWord, EnglishTranslation, _)
        ->  true
        % Sonra fiil olarak dene
        ;   translate_verb(TurkishWord, EnglishTranslation, _)
        ->  true
        % Sonra isim olarak dene
        ;   translate_noun(TurkishWord, EnglishTranslation, _)
        ->  true
        % Hiçbiri değilse olduğu gibi döndür
        ;   EnglishTranslation = TurkishWord
        ).

    % =============================================================================
    % TÜRKÇE MORFOLOJİK ANALİZ
    % =============================================================================

    % analyze_turkish(+Word, -Analysis)
    % Analysis = [root:Root, tense:Tense, person:Person, plurality:Plurality, negation:Neg]

    analyze_turkish(Word, Analysis) :-
        atom_string(Word, WordStr),
        string_lower(WordStr, LowerStr),
        atom_string(LowerWord, LowerStr),
        
        % Olumsuzluk kontrolü (morph_negation modülünden)
        check_negation(LowerWord, CleanWord, Negation),
        
        % Zaman ve kök analizi (morph_tense modülünden)
        find_tense_and_root(CleanWord, Root, Tense, Remainder),
        
        % Şahıs analizi
        find_person(Remainder, Tense, Person, Plurality),
        
        Analysis = [
            root:Root,
            tense:Tense,
            person:Person,
            plurality:Plurality,
            negation:Negation
        ].

    % Şahıs bulma
    find_person(Remainder, Tense, Person, Plurality) :-
        person_suffix(Suffix, Person, Plurality, Tense), % data modülünden
        atom_string(Suffix, SuffixStr),
        atom_string(Remainder, RemainderStr),
        (   SuffixStr = ""
        ->  RemainderStr = ""
        ;   sub_string(RemainderStr, _, _, 0, SuffixStr)
        ),
        !.

    find_person(_, _, 3, singular).  % Default: 3. tekil şahıs

    % =============================================================================
    % İNGİLİZCE FİİL ÇEKİMİ
    % =============================================================================

    % conjugate_english(+Verb, +Tense, +Person, +Plurality, +Negation, -Conjugated)
    conjugate_english(Verb, Tense, Person, Plurality, Negation, Result) :-
        get_verb_form(Verb, Tense, Person, Plurality, Negation, VerbForm),
        subject_pronoun(Person, Plurality, Subject), % morph_eng_utils modülünden
        build_sentence(Subject, Tense, Person, Plurality, Negation, VerbForm, Result).

    % Fiil formunu al
    get_verb_form(Verb, present_continuous, _, _, _, VerbForm) :-
        get_present_participle(Verb, VerbForm). % morph_eng_utils modülünden

    get_verb_form(Verb, past_simple, Person, _, false, VerbForm) :-
        get_past_simple(Verb, Person, VerbForm).

    get_verb_form(Verb, past_simple, _, _, true, Verb).  % did not + base form

    get_verb_form(Verb, future, _, _, _, Verb).  % will + base form

    get_verb_form(Verb, aorist, Person, Plurality, false, VerbForm) :-
        get_present_simple(Verb, Person, Plurality, VerbForm).

    get_verb_form(Verb, aorist, _, _, true, Verb).  % do/does not + base form

    get_verb_form(Verb, past_reported, _, _, _, VerbForm) :-
        get_past_participle(Verb, VerbForm).

    get_verb_form(Verb, necessity, _, _, _, Verb).  % should + base form

    get_verb_form(Verb, ability, _, _, _, Verb).  % can + base form

    % Past Continuous: was/were + V-ing (Present Participle kullanılır)
    get_verb_form(Verb, past_continuous, _, _, _, VerbForm) :-
        get_present_participle(Verb, VerbForm).

    % Past Simple
    get_past_simple(Verb, _, Past) :-
        irregular_verb(Verb, Past, _, _), % data modülünden
        !.

    get_past_simple(Verb, _, Past) :-
        atom_string(Verb, VerbStr),
        (   % -e ile biten: love -> loved
            string_concat(_, "e", VerbStr)
        ->  string_concat(VerbStr, "d", PastStr)
        ;   % -y ile biten (ünsüz+y): carry -> carried
            string_concat(Base, "y", VerbStr),
            string_length(Base, BaseLen),
            BaseLen > 0,
            string_concat(_, LastOfBase, Base),
            string_length(LastOfBase, 1),
            \+ is_vowel(LastOfBase) % morph_utils modülünden
        ->  string_concat(Base, "ied", PastStr)
        ;   string_concat(VerbStr, "ed", PastStr)
        ),
        atom_string(Past, PastStr).

    % Past Participle
    get_past_participle(Verb, Participle) :-
        irregular_verb(Verb, _, Participle, _),
        !.

    get_past_participle(Verb, Participle) :-
        get_past_simple(Verb, 3, Participle).

    % Present Simple (3rd person singular)
    get_present_simple(Verb, 3, singular, Conjugated) :-
        !,
        atom_string(Verb, VerbStr),
        (   Verb = have
        ->  Conjugated = has
        ;   Verb = be
        ->  Conjugated = is
        ;   Verb = do
        ->  Conjugated = does
        ;   % -s, -sh, -ch, -x, -z, -o ile biten: +es
            (   string_concat(_, "s", VerbStr)
            ;   string_concat(_, "sh", VerbStr)
            ;   string_concat(_, "ch", VerbStr)
            ;   string_concat(_, "x", VerbStr)
            ;   string_concat(_, "z", VerbStr)
            ;   string_concat(_, "o", VerbStr)
            )
        ->  string_concat(VerbStr, "es", ConjStr),
            atom_string(Conjugated, ConjStr)
        ;   % ünsüz + y: carry -> carries
            string_concat(Base, "y", VerbStr),
            string_length(Base, BaseLen),
            BaseLen > 0,
            string_concat(_, LastOfBase, Base),
            string_length(LastOfBase, 1),
            \+ is_vowel(LastOfBase)
        ->  string_concat(Base, "ies", ConjStr),
            atom_string(Conjugated, ConjStr)
        ;   string_concat(VerbStr, "s", ConjStr),
            atom_string(Conjugated, ConjStr)
        ).

    get_present_simple(Verb, _, _, Verb).

    % Cümle oluşturma
    build_sentence(Subject, Tense, Person, Plurality, Negation, VerbForm, Result) :-
        (   auxiliary_verb(Tense, Person, Plurality, Negation, Aux) % data modülünden
        ->  format(atom(Result), "~w ~w ~w", [Subject, Aux, VerbForm])
        ;   format(atom(Result), "~w ~w", [Subject, VerbForm])
        ).

    % =============================================================================
    % ANA ÇEVİRİ PREDİKATI
    % =============================================================================

    % translate_verb(+TurkishVerb, -EnglishTranslation, -Details)
    translate_verb(TurkishVerb, EnglishTranslation, Details) :-
        analyze_turkish(TurkishVerb, Analysis),
        
        % Analiz sonuçlarını çıkar
        member(root:TrRoot, Analysis),
        member(tense:Tense, Analysis),
        member(person:Person, Analysis),
        member(plurality:Plurality, Analysis),
        member(negation:Negation, Analysis),
        
        % Türkçe kökü İngilizce'ye çevir
        verb_root(TrRoot, EnRoot, _), % data modülünden
        
        % İngilizce çekim yap
        conjugate_english(EnRoot, Tense, Person, Plurality, Negation, EnglishTranslation),
        
        Details = [
            turkish_root:TrRoot,
            english_root:EnRoot,
            tense:Tense,
            person:Person,
            plurality:Plurality,
            negation:Negation
        ].

    % =============================================================================
    % CÜMLE ÇEVİRİSİ
    % =============================================================================

    % translate_sentence(+TurkishSentence, -EnglishSentence)
    translate_sentence(TurkishSentence, EnglishSentence) :-
        atom_string(TurkishSentence, SentenceStr),
        split_string(SentenceStr, " ", "", WordStrs),
        maplist(atom_string, Words, WordStrs),
        translate_words(Words, TranslatedWords),
        atomic_list_concat(TranslatedWords, ' ', EnglishSentence).

    translate_words([], []).
    translate_words([Word|Rest], [Translation|TransRest]) :-
        translate_word(Word, Translation),
        translate_words(Rest, TransRest).

    % =============================================================================
    % TEST PREDİKATLARI
    % =============================================================================

    test_morphology :-
        writeln('================================================================='),
        writeln('              TÜRKÇE-İNGİLİZCE MORFOLOJİ TESTİ'),
        writeln('================================================================='),
        nl,
        
        % Present Continuous testleri
        writeln('--- Şimdiki Zaman (Present Continuous) ---'),
        test_verb(geliyorum),
        test_verb(gidiyorsun),
        test_verb(yiyor),
        test_verb(yapiyoruz),
        test_verb(okuyorlar),
        nl,
        
        % Past Simple testleri
        writeln('--- Geçmiş Zaman (Past Simple) ---'),
        test_verb(geldim),
        test_verb(gittin),
        test_verb(yedi),
        test_verb(yaptik),
        test_verb(okudular),
        nl,
        
        % Future testleri
        writeln('--- Gelecek Zaman (Future) ---'),
        test_verb(gelecegim),
        test_verb(gideceksin),
        test_verb(yapacak),
        nl,
        
        % Aorist testleri
        writeln('--- Geniş Zaman (Aorist/Present Simple) ---'),
        test_verb(gelirim),
        test_verb(gidersin),
        test_verb(yapar),
        nl,
        
        % Olumsuz testler
        writeln('--- Olumsuz Formlar ---'),
        test_verb(gelmiyorum),
        test_verb(gitmedim),
        test_verb(yapmayacak),
        test_verb(gelmez),
        nl,
        
        % Necessity testleri
        writeln('--- Gereklilik (Necessity) ---'),
        test_verb(gelmeliyim),
        test_verb(gitmelisin),
        nl,
        
        writeln('================================================================='),
        writeln('                      TEST TAMAMLANDI'),
        writeln('=================================================================').

    test_verb(Verb) :-
        (   translate_verb(Verb, Translation, Details)
        ->  member(turkish_root:TrRoot, Details),
            member(english_root:EnRoot, Details),
            member(tense:Tense, Details),
            member(negation:Neg, Details),
            format('  ~w~n', [Verb]),
            format('      -> ~w~n', [Translation]),
            format('      Kök: ~w -> ~w | Zaman: ~w', [TrRoot, EnRoot, Tense]),
            (Neg = true -> write(' [OLUMSUZ]') ; true),
            nl
        ;   format('  ~w -> [Analiz edilemedi]~n', [Verb])
        ).
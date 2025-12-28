:- module(morph_question, [
    translate_question/2
]).

:- encoding(utf8).

% Core'dan SADECE gerekli ana çeviri fonksiyonları
:- use_module('../core/morphology_core', [
    translate_verb/3,
    translate_sentence/2
]).

% İngilizce yardımcıları Utils'den al (DOĞRU YER)
:- use_module('../utils/morph_eng_utils', [
    subject_pronoun/3,
    get_present_participle/2
]).

:- use_module('../data/morphology_data').

% =============================================================================
% SORU CÜMLESİ ÇEVİRİSİ
% =============================================================================

% translate_question(+TurkishQuestion, -EnglishQuestion)
% Örnek: "geldi mi" → "Did he/she come?"
translate_question(TurkishQuestion, EnglishQuestion) :-
    atom_string(TurkishQuestion, QuestionStr),
    split_string(QuestionStr, " ", "", WordStrs),
    maplist(atom_string, Words, WordStrs),

    % Soru eki kontrolü
    (   append(VerbWords, [QuestionParticle], Words),
        is_question_particle(QuestionParticle)
    ->  % Soru cümlesi
        (   VerbWords = [Verb]
        ->  translate_verb(Verb, _VerbTranslation, Details),
            member(tense:Tense, Details),
            member(person:Person, Details),
            member(plurality:Plurality, Details),
            member(english_root:EnRoot, Details),
            build_question(EnRoot, Tense, Person, Plurality, EnglishQuestion)
        ;   translate_sentence(TurkishQuestion, EnglishQuestion)
        )
    ;   % Normal cümle
        translate_sentence(TurkishQuestion, EnglishQuestion)
    ).

% -----------------------------------------------------------------------------
% Soru eki kontrolü
% -----------------------------------------------------------------------------
is_question_particle(Word) :-
    atom_string(Word, WordStr),
    member(WordStr, ["mı", "mi", "mu", "mü"]).

% -----------------------------------------------------------------------------
% Soru cümlesi oluşturma
% -----------------------------------------------------------------------------

% Past Simple
build_question(Verb, past_simple, Person, Plurality, Question) :-
    subject_pronoun(Person, Plurality, Subject),
    format(atom(Question), "Did ~w ~w?", [Subject, Verb]).

% Present Continuous
build_question(Verb, present_continuous, Person, Plurality, Question) :-
    subject_pronoun(Person, Plurality, Subject),
    auxiliary_verb(present_continuous, Person, Plurality, false, Aux),
    get_present_participle(Verb, VerbForm),
    format(atom(Question), "~w ~w ~w?", [Aux, Subject, VerbForm]).

% Future
build_question(Verb, future, Person, Plurality, Question) :-
    subject_pronoun(Person, Plurality, Subject),
    format(atom(Question), "Will ~w ~w?", [Subject, Verb]).

% Aorist (Simple Present)
build_question(Verb, aorist, Person, Plurality, Question) :-
    subject_pronoun(Person, Plurality, Subject),
    (Person = 3, Plurality = singular -> Aux = 'Does' ; Aux = 'Do'),
    format(atom(Question), "~w ~w ~w?", [Aux, Subject, Verb]),
    !.

% Unknown tense fallback
build_question(Verb, unknown, Person, Plurality, Question) :-
    subject_pronoun(Person, Plurality, Subject),
    (Person = 3, Plurality = singular -> Aux = 'Does' ; Aux = 'Do'),
    format(atom(Question), "~w ~w ~w?", [Aux, Subject, Verb]),
    !.

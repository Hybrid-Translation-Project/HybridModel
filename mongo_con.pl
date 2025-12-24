:- module(mongo_con, [
    lookup_word/3,
    lookup_all_meanings/2,
    get_meaning_with_score/4,
    get_meaning_with_details/6,
    get_collocation_hint/4,
    get_semantic_compatibility/3,
    get_ngram_frequency/2,
    get_word_semantic_class/3,
    mock_word/5
]).
:- use_module(library(process)).
:- use_module(library(http/json)).

/* ---------------------------------------------------------
   MOCK DATA MODE
   When USE_MOCK = true, uses built-in facts instead of Python
   Set to false to use MongoDB via Python subprocess
---------------------------------------------------------- */
use_mock(true).

/* =========================================================
   GELIŞMIŞ MOCK DATA SİSTEMİ
========================================================= */

/* ---------------------------------------------------------
   1. WORDS - Kelimeler (Polysemy + Semantic Class + Frequency)
   Format: mock_word(Tr, En, POS, Frequency, SemanticClass)
---------------------------------------------------------- */

% yuz - çok anlamlı
mock_word(yuz, face, noun, 85, body_part).
mock_word(yuz, hundred, noun, 72, number).
mock_word(yuz, swim, verb, 35, motion).

% zamirler
mock_word(ben, 'I', pronoun, 98, animate).
mock_word(sen, you, pronoun, 95, animate).
mock_word(o, he, pronoun, 90, animate).
mock_word(o, she, pronoun, 90, animate).
mock_word(o, it, pronoun, 85, inanimate).
mock_word(biz, we, pronoun, 92, animate).
mock_word(siz, you, pronoun, 90, animate).
mock_word(onlar, they, pronoun, 88, animate).

% fiiller - duygu
mock_word(sev, love, verb, 78, emotion).
mock_word(sev, like, verb, 82, emotion).

% fiiller - tüketim
mock_word(ye, eat, verb, 75, consumption).
mock_word(ic, drink, verb, 70, consumption).

% fiiller - hareket
mock_word(git, go, verb, 88, motion).
mock_word(gel, come, verb, 86, motion).

% fiiller - aksiyon
mock_word(yika, wash, verb, 50, action).
mock_word(oku, read, verb, 65, cognitive).
mock_word(yaz, write, verb, 60, cognitive).
mock_word(yaz, summer, noun, 55, time).
mock_word(al, take, verb, 80, action).
mock_word(al, buy, verb, 65, transaction).
mock_word(al, red, adjective, 40, property).
mock_word(ver, give, verb, 78, action).
mock_word(yap, do, verb, 82, action).
mock_word(yap, make, verb, 75, action).
mock_word(oyna, play, verb, 70, action).

% isimler - yiyecek
mock_word(elma, apple, noun, 45, food).
mock_word(su, water, noun, 75, liquid).

% isimler - nesneler
mock_word(kitap, book, noun, 70, object).
mock_word(ev, house, noun, 80, location).
mock_word(ev, home, noun, 78, location).
mock_word(para, money, noun, 72, abstract).

% isimler - canlılar
mock_word(kedi, cat, noun, 55, animate).
mock_word(kopek, dog, noun, 52, animate).

% sıfatlar
mock_word(guzel, beautiful, adjective, 70, property).
mock_word(guzel, nice, adjective, 68, property).
mock_word(buyuk, big, adjective, 75, property).
mock_word(kucuk, small, adjective, 72, property).

/* ---------------------------------------------------------
   2. COLLOCATIONS - Eşdizimlilik
   Format: collocation(Word1, Word2, Strength, MeaningHint1, MeaningHint2)
   Strength: 0-100 arası
---------------------------------------------------------- */

collocation(yuz, yika, 92, face, wash).      % yüz yıka -> wash face
collocation(yuz, metre, 88, hundred, _).     % yüz metre -> hundred meters
collocation(yuz, lira, 95, hundred, _).      % yüz lira -> hundred lira
collocation(su, ic, 94, water, drink).       % su iç -> drink water
collocation(elma, ye, 90, apple, eat).       % elma ye -> eat apple
collocation(kitap, oku, 93, book, read).     % kitap oku -> read book
collocation(mektup, yaz, 85, _, write).      % mektup yaz -> write letter
collocation(ev, git, 89, home, go).          % eve git -> go home
collocation(para, al, 82, money, take).      % para al -> take money
collocation(para, ver, 80, money, give).     % para ver -> give money

/* ---------------------------------------------------------
   3. SEMANTIC COMPATIBILITY - Anlam Uyumu
   Format: semantic_compat(SubjectClass, VerbClass, Compatibility)
   Compatibility: 0-100 arası
---------------------------------------------------------- */

% Canlı özne uyumları
semantic_compat(animate, emotion, 95).       % canlı + duygu = çok uyumlu
semantic_compat(animate, motion, 90).        % canlı + hareket = uyumlu
semantic_compat(animate, consumption, 95).   % canlı + tüketim = çok uyumlu
semantic_compat(animate, cognitive, 85).     % canlı + bilişsel = uyumlu
semantic_compat(animate, action, 88).        % canlı + aksiyon = uyumlu

% Cansız özne uyumları (düşük)
semantic_compat(inanimate, emotion, 15).     % cansız + duygu = uyumsuz
semantic_compat(inanimate, motion, 25).      % cansız + hareket = düşük
semantic_compat(inanimate, consumption, 10). % cansız + tüketim = çok uyumsuz

% Nesne-fiil uyumları
semantic_compat(food, consumption, 98).      % yiyecek + tüketim = mükemmel
semantic_compat(liquid, consumption, 95).    % sıvı + tüketim = çok iyi
semantic_compat(object, cognitive, 85).      % nesne + bilişsel = iyi
semantic_compat(body_part, action, 75).      % vücut parçası + aksiyon = orta
semantic_compat(location, motion, 88).       % konum + hareket = iyi (hedef olarak)

% Sayılar genelde fiillerle uyumsuz
semantic_compat(number, motion, 10).
semantic_compat(number, emotion, 5).
semantic_compat(number, action, 15).

% Varsayılan
semantic_compat(_, _, 50).                   % tanımlanmamış = nötr

/* ---------------------------------------------------------
   4. ENGLISH NGRAMS - İngilizce N-gram frekansları
   Format: en_ngram(WordList, Frequency)
---------------------------------------------------------- */

% Bigrams (en sık kullanılanlar)
en_ngram(['I', love], 125000).
en_ngram(['I', like], 180000).
en_ngram(['I', eat], 45000).
en_ngram(['I', drink], 32000).
en_ngram(['I', go], 95000).
en_ngram(['I', come], 28000).
en_ngram(['I', read], 38000).
en_ngram(['I', write], 35000).
en_ngram(['I', wash], 12000).
en_ngram([you, love], 85000).
en_ngram([you, like], 120000).
en_ngram([wash, face], 18000).
en_ngram([eat, apple], 12000).
en_ngram([drink, water], 25000).
en_ngram([read, book], 35000).
en_ngram([go, home], 55000).
en_ngram([go, house], 8000).
en_ngram([love, face], 8500).

% Trigrams
en_ngram(['I', love, you], 85000).
en_ngram(['I', like, you], 45000).
en_ngram(['I', wash, face], 5500).
en_ngram(['I', eat, apple], 3200).
en_ngram(['I', drink, water], 8500).
en_ngram(['I', read, book], 12000).
en_ngram(['I', go, home], 25000).

/* ---------------------------------------------------------
   lookup_word/3 - Legacy compatibility (returns first meaning)
---------------------------------------------------------- */
lookup_word(Tr, En, Durum) :-
    lookup_all_meanings(Tr, Meanings),
    ( Meanings = [FirstMeaning|_] ->
        En = FirstMeaning.meaning,
        Durum = found
    ;
        En = '',
        Durum = not_found
    ).

/* ---------------------------------------------------------
   lookup_all_meanings/2 - Returns ALL meanings with scores
   Result: List of dicts [{meaning: X, type: Y, score: Z}, ...]
---------------------------------------------------------- */
lookup_all_meanings(Tr, Meanings) :-
    use_mock(true),
    !,
    lookup_all_meanings_mock(Tr, Meanings).

lookup_all_meanings(Tr, Meanings) :-
    lookup_all_meanings_python(Tr, Meanings).

%% Mock implementation using built-in facts
lookup_all_meanings_mock(Tr, Meanings) :-
    findall(
        _{meaning: En, type: Type, score: Score, semantic_class: SemClass},
        mock_word(Tr, En, Type, Score, SemClass),
        Meanings
    ).

%% Python subprocess implementation
lookup_all_meanings_python(Tr, Meanings) :-
    process_create(
        path(python),
        ['mongo_api.py', Tr],
        [ stdout(pipe(Out)), process(PID) ]
    ),
    set_stream(Out, encoding(utf8)),
    catch(
        json_read_dict(Out, Dict),
        Hata,
        ( 
            format('~n[HATA DETAYI] JSON Parse hatasi: ~w~n', [Hata]), 
            Dict = error 
        )
    ),
    close(Out),
    process_wait(PID, _),
    ( Dict = error ->
        Meanings = []
    ; Dict.get(found) == true ->
        Meanings = Dict.get(meanings)
    ;
        Meanings = []
    ).

/* ---------------------------------------------------------
   get_meaning_with_score/4 - Backtrackable predicate
   Returns one meaning at a time for use with findall
---------------------------------------------------------- */
get_meaning_with_score(Tr, En, Type, Score) :-
    use_mock(true),
    !,
    mock_word(Tr, En, Type, Score, _).

get_meaning_with_score(Tr, En, Type, Score) :-
    lookup_all_meanings(Tr, Meanings),
    member(M, Meanings),
    En = M.meaning,
    Type = M.type,
    Score = M.score.

/* ---------------------------------------------------------
   get_meaning_with_details/6 - Full details with semantic class
---------------------------------------------------------- */
get_meaning_with_details(Tr, En, Type, Frequency, SemanticClass, Details) :-
    use_mock(true),
    !,
    mock_word(Tr, En, Type, Frequency, SemanticClass),
    Details = _{tr: Tr, en: En, pos: Type, freq: Frequency, sem_class: SemanticClass}.

/* ---------------------------------------------------------
   get_collocation_hint/4 - Eşdizimlilik ipucu
   Collocation varsa, hangi anlamların tercih edileceğini belirtir
---------------------------------------------------------- */
get_collocation_hint(Word1, Word2, Strength, MeaningHints) :-
    ( collocation(Word1, Word2, Strength, Hint1, Hint2) ->
        MeaningHints = hints(Hint1, Hint2)
    ; collocation(Word2, Word1, Strength, Hint2, Hint1) ->
        MeaningHints = hints(Hint1, Hint2)
    ;
        Strength = 0,
        MeaningHints = none
    ).

/* ---------------------------------------------------------
   get_semantic_compatibility/3 - Anlam uyumu skoru
---------------------------------------------------------- */
get_semantic_compatibility(SubjectClass, VerbClass, Score) :-
    ( semantic_compat(SubjectClass, VerbClass, Score) -> true
    ; Score = 50  % varsayılan nötr değer
    ).

/* ---------------------------------------------------------
   get_ngram_frequency/2 - İngilizce n-gram frekansı
---------------------------------------------------------- */
get_ngram_frequency(WordList, Frequency) :-
    ( en_ngram(WordList, Frequency) -> true
    ; Frequency = 0
    ).

/* ---------------------------------------------------------
   Helper predicates for scoring and filtering
---------------------------------------------------------- */

%% Get all meanings as a scored list
get_scored_meanings(Tr, ScoredList) :-
    findall(
        scored(En, Type, Score),
        get_meaning_with_score(Tr, En, Type, Score),
        ScoredList
    ).

%% Filter meanings by type
get_meanings_by_type(Tr, TargetType, FilteredList) :-
    findall(
        scored(En, Score),
        (get_meaning_with_score(Tr, En, Type, Score), Type == TargetType),
        FilteredList
    ).

%% Get best meaning (highest score)
get_best_meaning(Tr, En, Score) :-
    get_scored_meanings(Tr, ScoredList),
    ScoredList \= [],
    sort(3, @>=, ScoredList, [scored(En, _, Score)|_]).

/* ---------------------------------------------------------
   ADVANCED SCORING HELPERS
---------------------------------------------------------- */

%% Calculate collocation bonus for a word pair
calc_collocation_bonus(Word1, Word2, Meaning1, Bonus) :-
    get_collocation_hint(Word1, Word2, Strength, MeaningHints),
    ( Strength > 0, MeaningHints = hints(Hint, _), Meaning1 == Hint ->
        Bonus is Strength * 0.5  % Collocation match bonus
    ;
        Bonus = 0
    ).

%% Get semantic class for a word+meaning pair
get_word_semantic_class(Word, Meaning, SemanticClass) :-
    mock_word(Word, Meaning, _, _, SemanticClass), !.
get_word_semantic_class(_, _, unknown).
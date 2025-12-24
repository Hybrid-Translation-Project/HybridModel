:- encoding(utf8).
:- use_module(library(process)).
:- use_module(mongo_con).
:- use_module(morphology).  % Fiil morfolojisi için

/* =========================================================
   HYBRID PROBABILISTIC TRANSLATOR v2.0
   
   Gelişmiş puanlama sistemi:
   - Frekans tabanlı skorlama (%25)
   - Eşdizimlilik (Collocation) analizi (%25)
   - Anlam uyumu (Semantic compatibility) (%20)
   - POS (tür) uyumu (%15)
   - İngilizce n-gram doğallık (%15)
   
   Output format: List of (Translation, Score, Breakdown) 
========================================================= */

/* ---------------------------------------------------------
   SCORING WEIGHTS (Ağırlıklar)
---------------------------------------------------------- */
weight_frequency(0.25).     % Frekans: %25
weight_collocation(0.25).   % Eşdizim: %25
weight_semantic(0.20).      % Anlam uyumu: %20
weight_pos_match(0.15).     % Tür uyumu: %15
weight_ngram(0.15).         % İng doğallık: %15

/* ---------------------------------------------------------
   WORD TRANSLATION WITH ADVANCED SCORING
---------------------------------------------------------- */

%% translate_word_advanced/5
%% Kelimeyi çevir, frekans ve semantic class ile birlikte döndür
translate_word_advanced(Tr, En, Type, Frequency, SemanticClass) :-
    get_meaning_with_details(Tr, En, Type, Frequency, SemanticClass, _).

%% Bilinmeyen kelime fallback
translate_word_advanced(Tr, Tr, unknown, 1, unknown) :-
    \+ mock_word(Tr, _, _, _, _).

%% isim_cevir_advanced/5 - İsim çevirisi (detaylı)
isim_cevir_advanced(Tr, En, Frequency, SemanticClass, Type) :-
    translate_word_advanced(Tr, En, Type, Frequency, SemanticClass),
    member(Type, [noun, pronoun, determiner, adjective]).

%% Ek çözümleme ile çeviri
isim_cevir_advanced(Tr, EnFinal, Frequency, SemanticClass, Type) :-
    member(Ek, ['a','e','de','da','den','dan','i','yi','te','ta']),
    atom_concat(Kok, Ek, Tr),
    atom_length(Kok, Len), Len > 1,
    translate_word_advanced(Kok, EnKok, Type, Frequency, SemanticClass),
    ( member(Ek, ['a','e']) -> OnEk = 'to '
    ; member(Ek, ['de','da','te','ta']) -> OnEk = 'at '
    ; member(Ek, ['den','dan']) -> OnEk = 'from '
    ; member(Ek, ['i','yi']) -> OnEk = 'the '
    ),
    atom_concat(OnEk, EnKok, EnFinal).

%% fiil_cevir_advanced/5 - Fiil çevirisi (detaylı)
%% Önce morfoloji modülünü kullan
fiil_cevir_advanced(Tr, EnFinal, Frequency, SemanticClass, verb) :-
    morphology:translate_verb(Tr, EnFinal, Details),
    % Details'den bilgileri çıkar
    ( member(english_root:EnRoot, Details) -> true ; EnRoot = unknown ),
    ( mock_word(_, EnRoot, verb, Frequency, SemanticClass) -> true 
    ; Frequency = 50, SemanticClass = action ),
    !.

%% Morfoloji başarısız olursa mock'tan dene
fiil_cevir_advanced(Tr, EnFinal, Frequency, SemanticClass, verb) :-
    translate_word_advanced(Tr, En, verb, Frequency, SemanticClass),
    format_verb_english(En, EnFinal).

%% Fiil eki çözümleme (fallback)
fiil_cevir_advanced(Tr, EnFinal, Frequency, SemanticClass, verb) :-
    member(Ek, ['yor','iyor','uyor','mak','mek']),
    atom_concat(Kok, Ek, Tr),
    atom_length(Kok, Len), Len > 1,
    translate_word_advanced(Kok, En, verb, Frequency, SemanticClass),
    format_verb_english(En, EnFinal).

%% Fiili İngilizce formatına çevir
format_verb_english(En, EnFinal) :-
    atom_concat(En, 's', EnFinal).  % Basit 3. tekil (I love -> loves için değil, genel)
    % Alternatif: atom_concat('is ', En, T1), atom_concat(T1, 'ing', EnFinal).

/* ---------------------------------------------------------
   COLLOCATION-AWARE TRANSLATION
   Eşdizimlilik bilgisine göre anlam seçimi
---------------------------------------------------------- */

%% get_collocation_preferred_meaning/4
%% İki kelime arasında collocation varsa tercih edilen anlamı döndür
get_collocation_preferred_meaning(Word1, Word2, PreferredMeaning1, CollocationStrength) :-
    get_collocation_hint(Word1, Word2, CollocationStrength, Hints),
    CollocationStrength > 0,
    Hints = hints(PreferredMeaning1, _).

get_collocation_preferred_meaning(_, _, none, 0).

/* ---------------------------------------------------------
   ADVANCED SENTENCE SCORING
---------------------------------------------------------- */

%% calculate_sentence_score/5
%% Tüm skorlama faktörlerini hesapla
calculate_sentence_score(TrWords, EnWords, WordMeanings, TotalScore, Breakdown) :-
    % 1. Frekans skoru
    calc_frequency_score(TrWords, WordMeanings, FreqScore),
    
    % 2. Collocation skoru
    calc_collocation_score(TrWords, WordMeanings, CollScore),
    
    % 3. Semantic uyum skoru
    calc_semantic_score(TrWords, WordMeanings, SemScore),
    
    % 4. POS uyum skoru
    calc_pos_score(TrWords, WordMeanings, PosScore),
    
    % 5. N-gram skoru
    calc_ngram_score(EnWords, NgramScore),
    
    % Ağırlıklı toplam
    weight_frequency(WF),
    weight_collocation(WC),
    weight_semantic(WS),
    weight_pos_match(WP),
    weight_ngram(WN),
    
    TotalScore is (FreqScore * WF) + (CollScore * WC) + (SemScore * WS) + 
                 (PosScore * WP) + (NgramScore * WN),
    
    Breakdown = breakdown{
        frequency: FreqScore,
        collocation: CollScore,
        semantic: SemScore,
        pos_match: PosScore,
        ngram: NgramScore
    }.

%% calc_frequency_score/3 - Frekans ortalaması
calc_frequency_score(TrWords, WordMeanings, AvgScore) :-
    findall(Freq, (
        member(TrWord, TrWords),
        member(TrWord-EnMeaning, WordMeanings),
        ( mock_word(TrWord, EnMeaning, _, Freq, _) -> true ; Freq = 10 )
    ), Freqs),
    ( Freqs \= [] -> 
        sum_list(Freqs, Sum), length(Freqs, Len), AvgScore is Sum / Len
    ; AvgScore = 10 ).

%% calc_collocation_score/3 - Eşdizimlilik skoru
calc_collocation_score(TrWords, WordMeanings, Score) :-
    findall(Strength, (
        append(_, [W1, W2|_], TrWords),
        member(W1-M1, WordMeanings),
        get_collocation_hint(W1, W2, Strength, hints(Hint, _)),
        Strength > 0,
        M1 == Hint
    ), Strengths),
    ( Strengths \= [] ->
        sum_list(Strengths, Sum), length(Strengths, Len), Score is Sum / Len
    ; Score = 20 ).  % Nötr başlangıç

%% calc_semantic_score/3 - Anlam uyumu skoru
calc_semantic_score(TrWords, WordMeanings, Score) :-
    ( TrWords = [Subject|Rest], Rest \= [] ->
        last(Rest, Verb),
        member(Subject-SubjMeaning, WordMeanings),
        member(Verb-VerbMeaning, WordMeanings),
        get_word_semantic_class(Subject, SubjMeaning, SubjClass),
        get_word_semantic_class(Verb, VerbMeaning, VerbClass),
        get_semantic_compatibility(SubjClass, VerbClass, Score)
    ; Score = 50 ).

%% calc_pos_score/3 - Tür uyumu skoru
calc_pos_score(TrWords, WordMeanings, Score) :-
    ( TrWords = [First|Rest] ->
        % İlk kelime özne olmalı (pronoun/noun)
        member(First-FirstMeaning, WordMeanings),
        ( mock_word(First, FirstMeaning, Type1, _, _) -> true ; Type1 = unknown ),
        ( member(Type1, [pronoun, noun]) -> Score1 = 100 ; Score1 = 30 ),
        
        % Son kelime fiil olmalı
        ( Rest \= [], last(Rest, LastWord) ->
            member(LastWord-LastMeaning, WordMeanings),
            ( mock_word(LastWord, LastMeaning, Type2, _, _) -> true ; Type2 = unknown ),
            ( Type2 == verb -> Score2 = 100 ; Score2 = 30 ),
            Score is (Score1 + Score2) / 2
        ; Score = Score1 )
    ; Score = 50 ).

%% calc_ngram_score/2 - İngilizce n-gram skoru
calc_ngram_score(EnWords, Score) :-
    ( EnWords = [W1, W2|_] ->
        ( get_ngram_frequency([W1, W2], Freq), Freq > 0 ->
            Score is min(100, log(Freq + 1) * 10)
        ; Score = 30 )
    ; Score = 50 ).

/* ---------------------------------------------------------
   CANDIDATE GENERATION WITH ADVANCED SCORING
---------------------------------------------------------- */

%% generate_candidate_advanced/4
%% Gelişmiş skorlamayla aday üret
generate_candidate_advanced(TrWords, Translation, Score, Breakdown) :-
    length(TrWords, Len),
    ( Len == 1 ->
        generate_single_advanced(TrWords, Translation, Score, Breakdown)
    ; Len > 1 ->
        generate_sov_advanced(TrWords, Translation, Score, Breakdown)
    ).

%% generate_single_advanced/4 - Tek kelime
%% Önce fiil olarak dene (morfoloji ile)
generate_single_advanced([Tr], Translation, Score, Breakdown) :-
    morphology:translate_verb(Tr, Translation, _Details),
    Score = 80,  % Fiil çekimi başarılı
    Breakdown = breakdown{frequency: 80, collocation: 0, semantic: 70, pos_match: 100, ngram: 60},
    !.

%% Fiil değilse diğer kelime türlerini dene
generate_single_advanced([Tr], Translation, Score, Breakdown) :-
    translate_word_advanced(Tr, Translation, _Type, Freq, _SemClass),
    Score is Freq,
    Breakdown = breakdown{frequency: Freq, collocation: 0, semantic: 50, pos_match: 50, ngram: 50}.

%% generate_sov_advanced/4 - SOV cümle
%% Fiil morfolojisi ile çalışan yeni versiyon
generate_sov_advanced(TrWords, Translation, Score, Breakdown) :-
    TrWords = [Subject|Rest],
    Rest \= [],
    last(Rest, Verb),
    ( Rest = [Verb] -> Objects = [] ; append(Objects, [Verb], Rest) ),
    
    % Fiil çevirisi (morfoloji ile - şahıs ve zaman dahil)
    fiil_cevir_advanced(Verb, EnVerb, _VerbFreq, _VerbSem, _),
    
    % Özne çevirisi ve fiildeki özne karşılaştırması
    isim_cevir_advanced(Subject, EnSubject, _SubjFreq, _SubjSem, SubjType),
    
    % Fiil zaten özne içeriyor mu kontrol et (I am coming gibi)
    ( atom_string(EnVerb, EnVerbStr),
      ( sub_string(EnVerbStr, 0, 2, _, "I ")
      ; sub_string(EnVerbStr, 0, 4, _, "you ")
      ; sub_string(EnVerbStr, 0, 5, _, "they ")
      ; sub_string(EnVerbStr, 0, 3, _, "we ")
      ; sub_string(EnVerbStr, 0, 7, _, "he/she ")
      )
    ->
      % Fiil zaten özne içeriyor, zamir özneyi atla
      ( SubjType == pronoun 
      -> FinalSubject = ''  % Zamir özneyi atla, fiildeki özneyi kullan
      ;  FinalSubject = EnSubject  % İsim özneyi tut (Ali geliyorum -> Ali am coming? - semantik hata, ama koruyalım)
      ),
      % Cümleyi oluştur
      ( FinalSubject == ''
      -> BaseTranslation = EnVerb
      ;  atomic_list_concat([FinalSubject, ' ', EnVerb], BaseTranslation)
      )
    ;
      % Fiil özne içermiyor (sade fiil), özneyi ekle
      atomic_list_concat([EnSubject, ' ', EnVerb], BaseTranslation)
    ),
    
    % Nesneleri çevir
    translate_objects(Objects, EnObjects, ObjMeanings),
    
    % Word meanings listesi oluştur
    append([[Subject-EnSubject, Verb-EnVerb], ObjMeanings], AllMeanings),
    
    % İngilizce cümle oluştur (SVO) - nesneleri ekle
    ( EnObjects \= []
    -> atomic_list_concat(EnObjects, ' ', ObjStr),
       atomic_list_concat([BaseTranslation, ' ', ObjStr], Translation)
    ;  Translation = BaseTranslation
    ),
    
    % Gelişmiş skorlama
    EnWordsList = [EnSubject, EnVerb|EnObjects],
    calculate_sentence_score(TrWords, EnWordsList, AllMeanings, Score, Breakdown).

%% translate_objects/3 - Nesneleri çevir
translate_objects([], [], []).
translate_objects([Obj|Rest], [EnObj|EnRest], [Obj-EnObj|MeaningsRest]) :-
    isim_cevir_advanced(Obj, EnObj, _, _, _),
    translate_objects(Rest, EnRest, MeaningsRest).

%% add_object_parts/2 - Nesne parçalarını ekle
add_object_parts([], []).
add_object_parts([Obj|Rest], [' ', Obj|RestParts]) :-
    add_object_parts(Rest, RestParts).

/* ---------------------------------------------------------
   MAIN CANDIDATE GENERATION PREDICATE
---------------------------------------------------------- */

generate_candidates(InputList, Candidates) :-
    findall(
        candidate(Translation, Score, Breakdown),
        generate_candidate_advanced(InputList, Translation, Score, Breakdown),
        RawCandidates
    ),
    sort_candidates_by_score(RawCandidates, Candidates).

%% sort_candidates_by_score/2 - Skora göre sırala (azalan)
sort_candidates_by_score(Candidates, Sorted) :-
    map_list_to_pairs(get_candidate_score, Candidates, Pairs),
    keysort(Pairs, SortedPairs),
    reverse(SortedPairs, ReversedPairs),
    pairs_values(ReversedPairs, Sorted).

get_candidate_score(candidate(_, Score, _), Score).

/* ---------------------------------------------------------
   PROLOG QUERY INTERFACE (For pyswip)
---------------------------------------------------------- */

translate_with_scores(InputList, Results) :-
    generate_candidates(InputList, Candidates),
    maplist(candidate_to_result, Candidates, Results).

candidate_to_result(candidate(T, S, B), [T, S, B]).

/* ---------------------------------------------------------
   LEGACY SUPPORT & TESTING
---------------------------------------------------------- */

cevir(InputList) :-
    generate_candidates(InputList, Candidates),
    format('~n--- Translation Candidates (Advanced Scoring) ---~n', []),
    format('Input: ~w~n~n', [InputList]),
    format_candidates_advanced(Candidates).

format_candidates_advanced([]).
format_candidates_advanced([candidate(T, S, B)|Rest]) :-
    format('Translation: ~w~n', [T]),
    format('  Total Score: ~2f~n', [S]),
    format('  Breakdown:~n'),
    format('    - Frequency:   ~2f~n', [B.frequency]),
    format('    - Collocation: ~2f~n', [B.collocation]),
    format('    - Semantic:    ~2f~n', [B.semantic]),
    format('    - POS Match:   ~2f~n', [B.pos_match]),
    format('    - N-gram:      ~2f~n', [B.ngram]),
    format('~n'),
    format_candidates_advanced(Rest).

/* ---------------------------------------------------------
   HELPER PREDICATES
---------------------------------------------------------- */

sum_list([], 0).
sum_list([H|T], Sum) :- sum_list(T, Rest), Sum is H + Rest.

last([X], X).
last([_|T], X) :- last(T, X).

/* ---------------------------------------------------------
   STARTUP (Only for standalone Prolog use)
---------------------------------------------------------- */
baslat :-
    writeln('--- Hybrid Probabilistic Translator v2.0 Ready ---'),
    writeln('Advanced scoring with:'),
    writeln('  - Frequency analysis'),
    writeln('  - Collocation detection'),
    writeln('  - Semantic compatibility'),
    writeln('  - N-gram naturalness'),
    nl,
    sor_bakalim.

sor_bakalim :-
    nl, write('Cumleniz: '), read(Girdi),
    ( Girdi == son -> writeln('Cikis.')
    ; catch(cevir(Girdi), E, (format('Hata: ~w~n', [E]))), 
      sor_bakalim
    ).

%% NOTE: Removed auto-start (:- baslat.) to allow pyswip to load without blocking.
%% To use interactively in Prolog, manually call: ?- baslat.

sor_bakalim :-
    nl, write('Cumleniz: '), read(Girdi),
    ( Girdi == son -> writeln('Cikis.')
    ; catch(cevir(Girdi), _, writeln('Bir hata oldu, tekrar deneyin.')), 
      sor_bakalim
    ).

%% NOTE: Removed auto-start (:- baslat.) to allow pyswip to load without blocking.
%% To use interactively in Prolog, manually call: ?- baslat.
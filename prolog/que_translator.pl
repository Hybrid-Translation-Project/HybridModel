:- encoding(utf8).
:- use_module(library(process)).
:- use_module('../mongo_con').      % mongo_con.pl üst klasörde
:- use_module('morphology_main').   % morphology_main.pl bu klasörde
:- discontiguous sor_bakalim/0.  % Warning'i sustur

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
    \+ get_meaning_with_details(Tr, _, _, _, _, _).

%% isim_cevir_advanced/5 - İsim çevirisi (detaylı)
%% Önce morfoloji modülünü kullan (hal ekleri, iyelik ekleri, çoğul ekleri)
isim_cevir_advanced(Tr, EnFinal, Frequency, SemanticClass, noun) :-
    morphology:translate_noun(Tr, EnFinal, Details),
    % Details'den bilgileri çıkar - sadece bilinen kategoriler için kabul et
    member(category:Cat, Details),
    Cat \= unknown,  % Unknown kategorili isimleri reddet
    ( member(english:EnRoot, Details) -> true ; EnRoot = unknown ),
    SemanticClass = Cat,
    ( mock_word(_, EnRoot, noun, Frequency, _) -> true ; Frequency = 50 ),
    !.

%% Morfoloji başarısız olursa mock'tan dene (zamirler, sıfatlar vb.)
isim_cevir_advanced(Tr, En, Frequency, SemanticClass, Type) :-
    translate_word_advanced(Tr, En, Type, Frequency, SemanticClass),
    member(Type, [noun, pronoun, determiner, adjective]).

%% Ek çözümleme ile çeviri (fallback)
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

%% Fiil eki çözümleme (fallback) - GENİŞLETİLDİ
fiil_cevir_advanced(Tr, EnFinal, Frequency, SemanticClass, verb) :-
    member(Ek, ['yorum','ıyorum','iyorum','uyorum',   % 1sg prog
                'yor','ıyor','iyor','uyor',           % prog kök
                'mak','mek']),
    atom_concat(Kok, Ek, Tr),
    atom_length(Kok, Len), Len > 1,
    translate_word_advanced(Kok, En, verb, Frequency, SemanticClass),
    format_verb_english(En, EnFinal).

%% Fiili İngilizce formatına çevir
format_verb_english(En, EnFinal) :-
    atom_concat(En, 's', EnFinal).  % Basit 3. tekil (I love -> loves için değil, genel)
    % Alternatif: atom_concat('is ', En, T1), atom_concat(T1, 'ing', EnFinal).

%% gerund_cevir_advanced/5 - Zarf-fiil çevirisi (detaylı)
%% koşarken → while running, koşarak → by running
gerund_cevir_advanced(Tr, EnFinal, Frequency, SemanticClass, gerund) :-
    morphology:translate_gerund(Tr, EnFinal, Details),
    % Details'den bilgileri çıkar
    ( member(english_root:EnRoot, Details) -> true ; EnRoot = unknown ),
    ( mock_word(_, EnRoot, verb, Frequency, SemanticClass) -> true 
    ; Frequency = 70, SemanticClass = action ),
    !.

%% is_gerund/1 - Kelime zarf-fiil mi kontrol et
is_gerund(Word) :-
    gerund_cevir_advanced(Word, _, _, _, gerund),
    !.

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
    
    Breakdown = [
        frequency-FreqScore,
        collocation-CollScore,
        semantic-SemScore,
        pos_match-PosScore,
        ngram-NgramScore
    ].

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
    % Önce soru cümlesi mi kontrol et
    ( is_question_sentence(TrWords) ->
        generate_question_advanced(TrWords, Translation, Score, Breakdown)
    ; Len == 1 ->
        generate_single_advanced(TrWords, Translation, Score, Breakdown)
    ; Len > 1 ->
        generate_sov_advanced(TrWords, Translation, Score, Breakdown)
    ).

%% is_question_sentence/1 - Soru cümlesi mi kontrol et
is_question_sentence(TrWords) :-
    last(TrWords, LastWord),
    atom_string(LastWord, LastStr),
    member(LastStr, ["mi", "mı", "mu", "mü"]).

%% generate_question_advanced/4 - Soru cümlesi çevir
generate_question_advanced(TrWords, Translation, Score, Breakdown) :-
    % Soru ekini çıkar
    append(VerbWords, [_QuestionParticle], TrWords),
    VerbWords \= [],
    % Atomik cümle oluştur
    atomic_list_concat(VerbWords, ' ', VerbPhrase),
    atom_concat(VerbPhrase, ' mi', QuestionAtom),
    % Morfoloji ile çevir
    morphology:translate_question(QuestionAtom, Translation),
    Score = 85,
    Breakdown = breakdown{frequency: 85, collocation: 0, semantic: 80, pos_match: 100, ngram: 70}.

%% generate_single_advanced/4 - Tek kelime
%% Önce zarf-fiil olarak dene (koşarken → while running)
generate_single_advanced([Tr], Translation, Score, Breakdown) :-
    morphology:translate_gerund(Tr, Translation, _Details),
    Score = 85,  % Zarf-fiil çevirisi başarılı
    Breakdown = breakdown{frequency: 85, collocation: 0, semantic: 80, pos_match: 100, ngram: 70},
    !.

%% Hal ekli isim kontrolü - hal eki varsa isim öncelikli (yere → to ground)
generate_single_advanced([Tr], Translation, Score, Breakdown) :-
    morphology:translate_noun(Tr, Translation, Details),
    member(case:CaseInfo, Details),
    CaseInfo \= nominative,  % Hal eki var
    member(category:Category, Details),
    Category \= unknown,
    Score = 78,  % Hal ekli isim
    Breakdown = breakdown{frequency: 78, collocation: 0, semantic: 75, pos_match: 95, ngram: 65},
    !.

%% Sonra fiil olarak dene (morfoloji ile)
generate_single_advanced([Tr], Translation, Score, Breakdown) :-
    morphology:translate_verb(Tr, Translation, _Details),
    Score = 80,  % Fiil çekimi başarılı
    Breakdown = breakdown{frequency: 80, collocation: 0, semantic: 70, pos_match: 100, ngram: 60},
    !.

%% Sonra isim olarak dene (morfoloji ile - hal ekleri, iyelik, çoğul)
generate_single_advanced([Tr], Translation, Score, Breakdown) :-
    morphology:translate_noun(Tr, Translation, Details),
    % İsim çevirisi başarılı oldu mu kontrol et (kök bulundu mu?)
    member(category:Category, Details),
    Category \= unknown,
    Score = 75,  % İsim morfolojisi başarılı
    Breakdown = breakdown{frequency: 75, collocation: 0, semantic: 70, pos_match: 90, ngram: 60},
    !.

%% Fiil ve isim değilse diğer kelime türlerini dene
generate_single_advanced([Tr], Translation, Score, Breakdown) :-
    translate_word_advanced(Tr, Translation, _Type, Freq, _SemClass),
    Score is Freq,
    Breakdown = breakdown{frequency: Freq, collocation: 0, semantic: 50, pos_match: 50, ngram: 50}.

%% is_case_marked/2 - Kelime hal eki içeriyor mu kontrol et
is_case_marked(Word, CaseInfo) :-
    morphology:translate_noun(Word, _, Details),
    member(case:CaseInfo, Details),
    CaseInfo \= nominative.

%% generate_sov_advanced/4 - SOV → SVO dönüşümü
%% Türkçe SOV (Özne-Nesne-Fiil) → İngilizce SVO (Subject-Verb-Object)

%% KURAL 0: Zarf-fiil ile başlayan cümle
%% Örnek: "koşarken yere düştüm" → "While running, I fell to the ground"
generate_sov_advanced(TrWords, Translation, Score, Breakdown) :-
    TrWords = [FirstWord|Rest],
    Rest \= [],
    % İlk kelime zarf-fiil mi kontrol et
    is_gerund(FirstWord),
    gerund_cevir_advanced(FirstWord, EnGerund, GerundFreq, _, _),
    % Geri kalan cümleyi ayrı çevir (tek kelime veya çoklu)
    ( Rest = [SingleWord] 
    -> generate_single_advanced([SingleWord], RestTranslation, RestScore, _)
    ;  generate_sov_advanced(Rest, RestTranslation, RestScore, _)
    ),
    % Zarf-fiili başa koy, virgül ekle
    upcase_atom_first(EnGerund, EnGerundCap),
    atomic_list_concat([EnGerundCap, ', ', RestTranslation], Translation),
    % Skorlama
    Score is (GerundFreq + RestScore) / 2,
    Breakdown = breakdown{frequency: Score, collocation: 10, semantic: 70, pos_match: 90, ngram: 70},
    !.

%% KURAL 1: İlk kelime hal ekli (nesne/tümleç) - özne fiilde gömülü
%% Örnek: "okula gidiyorum" → "I am going to school"
generate_sov_advanced(TrWords, Translation, Score, Breakdown) :-
    TrWords = [FirstWord|Rest],
    Rest \= [],
    last(Rest, Verb),
    % İlk kelime hal ekli mi kontrol et
    is_case_marked(FirstWord, _CaseInfo),
    % Tüm kelimeleri nesne/tümleç olarak al
    ( Rest = [Verb] -> AllObjects = [FirstWord] ; append([FirstWord|Objects], [Verb], TrWords), AllObjects = [FirstWord|Objects] ),
    
    % Fiil çevirisi (özne fiilde gömülü - "I am going" gibi)
    fiil_cevir_advanced(Verb, EnVerb, _VerbFreq, _VerbSem, _),
    
    % Nesneleri/tümleçleri çevir
    translate_objects(AllObjects, EnObjects, ObjMeanings),
    
    % SVO: Verb + Objects (fiil zaten özne içeriyor)
    ( EnObjects \= []
    -> atomic_list_concat(EnObjects, ' ', ObjStr),
       atomic_list_concat([EnVerb, ' ', ObjStr], Translation)
    ;  Translation = EnVerb
    ),
    
    % Skorlama
    append([[Verb-EnVerb], ObjMeanings], AllMeanings),
    EnWordsList = [EnVerb|EnObjects],
    calculate_sentence_score(TrWords, EnWordsList, AllMeanings, Score, Breakdown),
    !.

%% KURAL 2: Normal SOV - ilk kelime özne
%% Örnek: "ben okula gidiyorum" → "I am going to school"
generate_sov_advanced(TrWords, Translation, Score, Breakdown) :-
    TrWords = [Subject|Rest],
    Rest \= [],
    last(Rest, Verb),
    ( Rest = [Verb] -> Objects = [] ; append(Objects, [Verb], Rest) ),
    
    % Fiil çevirisi (morfoloji ile - şahıs ve zaman dahil)
    fiil_cevir_advanced(Verb, EnVerb, _VerbFreq, _VerbSem, _),
    
    % Özne çevirisi
    isim_cevir_advanced(Subject, EnSubject, _SubjFreq, _SubjSem, SubjType),
    
    % Nesneleri çevir
    translate_objects(Objects, EnObjects, ObjMeanings),
    
    % Fiil zaten özne içeriyor mu kontrol et (I am going gibi)
    atom_string(EnVerb, EnVerbStr),
    ( ( sub_string(EnVerbStr, 0, 2, _, "I ")
      ; sub_string(EnVerbStr, 0, 4, _, "you ")
      ; sub_string(EnVerbStr, 0, 5, _, "they ")
      ; sub_string(EnVerbStr, 0, 3, _, "we ")
      ; sub_string(EnVerbStr, 0, 7, _, "he/she ")
      ; sub_string(EnVerbStr, 0, 3, _, "it ")     % <-- o geliyordu gibi cümleler için it was coming
      )
    ->
      % Fiil zaten özne içeriyor (I am going)
      ( SubjType == pronoun 
      -> % Zamir özneyi atla - SVO: Verb + Objects
         ( EnObjects \= []
         -> atomic_list_concat(EnObjects, ' ', ObjStr),
            atomic_list_concat([EnVerb, ' ', ObjStr], Translation)
         ;  Translation = EnVerb
         )
      ;  % İsim özne var - SVO: Subject + Verb + Objects
         ( EnObjects \= []
         -> atomic_list_concat(EnObjects, ' ', ObjStr),
            atomic_list_concat([EnSubject, ' ', EnVerb, ' ', ObjStr], Translation)
         ;  atomic_list_concat([EnSubject, ' ', EnVerb], Translation)
         )
      )
    ;
      % Fiil özne içermiyor - SVO: Subject + Verb + Objects
      ( EnObjects \= []
      -> atomic_list_concat(EnObjects, ' ', ObjStr),
         atomic_list_concat([EnSubject, ' ', EnVerb, ' ', ObjStr], Translation)
      ;  atomic_list_concat([EnSubject, ' ', EnVerb], Translation)
      )
    ),
    
    % Word meanings listesi oluştur
    append([[Subject-EnSubject, Verb-EnVerb], ObjMeanings], AllMeanings),
    
    % Gelişmiş skorlama
    EnWordsList = [EnSubject, EnVerb|EnObjects],
    calculate_sentence_score(TrWords, EnWordsList, AllMeanings, Score, Breakdown).

%% KURAL 3: Fiilsiz cümle - özne + yüklem (bulunma hali)
%% Örnek: "kedimiz evde" → "our cat is at home"
generate_sov_advanced(TrWords, Translation, Score, Breakdown) :-
    TrWords = [Subject, Predicate],
    % Yüklem bulunma halinde mi kontrol et
    is_case_marked(Predicate, locative),
    % Özne çevirisi
    isim_cevir_advanced(Subject, EnSubject, _, _, _),
    % Yüklem çevirisi
    isim_cevir_advanced(Predicate, EnPredicate, _, _, _),
    % Özneye göre copula seç (is/are)
    get_copula_for_subject(EnSubject, Copula),
    % SVO: Subject + is/are + Predicate
    atomic_list_concat([EnSubject, ' ', Copula, ' ', EnPredicate], Translation),
    Score = 75,
    Breakdown = breakdown{frequency: 75, collocation: 5, semantic: 70, pos_match: 85, ngram: 65},
    !.

%% KURAL 4: Fiilsiz cümle - özne + yüklem (yönelme hali)
%% Örnek: "o okula" → "he/she is at school" (going implied)
generate_sov_advanced(TrWords, Translation, Score, Breakdown) :-
    TrWords = [Subject, Predicate],
    % Yüklem yönelme halinde mi kontrol et
    is_case_marked(Predicate, dative),
    % Özne çevirisi
    isim_cevir_advanced(Subject, EnSubject, _, _, SubjType),
    % Yüklem çevirisi
    isim_cevir_advanced(Predicate, EnPredicate, _, _, _),
    % Zamir mi isim mi kontrol et
    ( SubjType == pronoun 
    -> % Zamir - "is going" ile
       atomic_list_concat([EnSubject, ' is going ', EnPredicate], Translation)
    ;  % İsim - "Subject is going" ile
       atomic_list_concat([EnSubject, ' is going ', EnPredicate], Translation)
    ),
    Score = 70,
    Breakdown = breakdown{frequency: 70, collocation: 5, semantic: 65, pos_match: 80, ngram: 60},
    !.

%% get_copula_for_subject/2 - Özneye göre copula seç
get_copula_for_subject(EnSubject, Copula) :-
    atom_string(EnSubject, SubjStr),
    % Çoğul özne kontrolü
    ( sub_string(SubjStr, 0, 2, _, "we")
    ; sub_string(SubjStr, 0, 4, _, "they")
    ; sub_string(SubjStr, 0, 3, _, "you")
    ; sub_string(SubjStr, 0, 3, _, "our")  % our cat → tekil gibi davran
    )
    -> Copula = is  % Aslında "our cat" tekil
    ; Copula = is.

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

%% upcase_atom_first/2 - İlk harfi büyük yap
upcase_atom_first(Atom, Result) :-
    atom_string(Atom, Str),
    string_length(Str, Len),
    Len > 0,
    sub_string(Str, 0, 1, _, First),
    upcase_atom(First, FirstUpper),
    atom_string(FirstUpper, FirstUpperStr),
    sub_string(Str, 1, _, 0, Rest),
    string_concat(FirstUpperStr, Rest, ResultStr),
    atom_string(Result, ResultStr),
    !.
upcase_atom_first(Atom, Atom).

%% NOTE: Removed auto-start (:- baslat.) to allow pyswip to load without blocking.
%% To use interactively in Prolog, manually call: ?- baslat.
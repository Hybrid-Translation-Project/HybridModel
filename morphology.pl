% ==============================================================================
%   PROLOGPLUS - MASTER FIX (GERUND / İSİM-FİİL DESTEKLİ)
% ==============================================================================

:- encoding(utf8).
:- module(morphology, [
    translate_verb/3, translate_sentence/2, analyze_turkish/2,
    conjugate_english/6, test_morphology/0, reload_morphology_data/0
]).

:- use_module(library(lists)).

% ==============================================================================
%   BÖLÜM 1: VERİTABANI
% ==============================================================================
:- consult(morphology_data).

reload_morphology_data :-
    abolish(verb_root/3), abolish(irregular_verb/4), 
    abolish(tense_suffix/2), abolish(person_suffix/4), 
    abolish(turkish_irregular_root/2), abolish(auxiliary_verb/5),
    consult(morphology_data), 
    writeln('[SİSTEM] Veri tabanı güncellendi.').

% ==============================================================================
%   BÖLÜM 2: CÜMLE ÇEVİRİ MOTORU
% ==============================================================================
translate_sentence(TurkishSentence, EnglishSentence) :-
    atom_string(TurkishSentence, SentenceStr),
    split_string(SentenceStr, " ", "", WordStrs),
    maplist(atom_string, Words, WordStrs),
    translate_words(Words, TranslatedList),
    ( reorder_english(TranslatedList, ReorderedList) -> true ; ReorderedList = TranslatedList ),
    clean_duplicates(ReorderedList, FinalList),
    atomic_list_concat(FinalList, ' ', EnglishSentence).

translate_words([], []).
translate_words([Word|Rest], [Translation|TransRest]) :-
    ( translate_verb(Word, Translation, _) -> true
    ; translate_noun(Word, Translation)    -> true
    ; Translation = Word ),
    translate_words(Rest, TransRest).

reorder_english(List, Ordered) :-
    last(List, Verb),
    append(Rest, [Verb], List),
    ( Rest = [Subject | Objects]
    -> append([Subject], [Verb], Temp), append(Temp, Objects, Ordered)
    ; Ordered = [Verb | Rest] ).

clean_duplicates([Subject, VerbPhrase | Rest], Result) :-
    atom_string(Subject, S_Str), string_lower(S_Str, S_Low),
    atom_string(VerbPhrase, V_Str), string_lower(V_Str, V_Low),
    string_concat(S_Low, " ", Check), sub_string(V_Low, 0, _, _, Check), !, 
    Result = [VerbPhrase | Rest].
clean_duplicates([Subject, VerbPhrase | Rest], Result) :-
    atom_string(VerbPhrase, V_Str),
    ( sub_string(V_Str, 0, _, _, "he/she ") ; sub_string(V_Str, 0, _, _, "they ") ), !, 
    ( sub_string(V_Str, 0, _, _, "he/she ") -> sub_string(V_Str, 7, _, 0, CleanStr)
    ; sub_string(V_Str, 0, _, _, "they ")   -> sub_string(V_Str, 5, _, 0, CleanStr)
    ; CleanStr = V_Str ),
    atom_string(CleanVerb, CleanStr), Result = [Subject, CleanVerb | Rest].
clean_duplicates(List, List).

% ==============================================================================
%   BÖLÜM 3: FİİL ANALİZİ
% ==============================================================================
translate_verb(TurkishVerb, EnglishTranslation, Details) :-
    analyze_turkish(TurkishVerb, Analysis),
    member(root:TrRoot, Analysis), member(tense:Tense, Analysis),
    member(person:Person, Analysis), member(plurality:Plurality, Analysis),
    member(negation:Negation, Analysis),
    verb_root(TrRoot, EnRoot, _),
    conjugate_english(EnRoot, Tense, Person, Plurality, Negation, EnglishTranslation),
    Details = [turkish_root:TrRoot, english_root:EnRoot, tense:Tense, person:Person, plurality:Plurality, negation:Negation].

analyze_turkish(Word, Analysis) :-
    atom_string(Word, WordStr), string_lower(WordStr, LowerStr), atom_string(LowerWord, LowerStr),
    check_negation(LowerWord, CleanWord, Negation),
    find_tense_and_root(CleanWord, Root, Tense, Remainder),
    find_person(Remainder, Tense, Person, Plurality),
    Analysis = [root:Root, tense:Tense, person:Person, plurality:Plurality, negation:Negation].

% ==============================================================================
%   BÖLÜM 4: İSİM VE EK ANALİZİ (GÜNCELLENDİ) 🚀
% ==============================================================================

% 1. HAL EKLERİ
translate_noun(Word, Tr) :- atom_string(Word, S), (sub_string(S,_,3,0,"dan");sub_string(S,_,3,0,"den");sub_string(S,_,3,0,"tan");sub_string(S,_,3,0,"ten")), string_length(S,L), B is L-3, B>0, sub_string(S,0,B,_,R), atom_string(Rem,R), translate_noun(Rem,IT), format(atom(Tr), "from ~w", [IT]), !.
translate_noun(Word, Tr) :- atom_string(Word, S), (sub_string(S,_,2,0,"da");sub_string(S,_,2,0,"de");sub_string(S,_,2,0,"ta");sub_string(S,_,2,0,"te")), string_length(S,L), B is L-2, B>0, sub_string(S,0,B,_,R), atom_string(Rem,R), translate_noun(Rem,IT), format(atom(Tr), "at ~w", [IT]), !.
translate_noun(Word, Tr) :- atom_string(Word, S), (sub_string(S,_,1,0,"a");sub_string(S,_,1,0,"e")), string_length(S,L), B is L-1, B>0, sub_string(S,0,B,_,TR), (string_concat(RR,"y",TR)->true;RR=TR), atom_string(Rem,RR), translate_noun(Rem,IT), format(atom(Tr), "to ~w", [IT]), !.
translate_noun(Word, Tr) :- atom_string(Word, S), (sub_string(S,_,1,0,"i");sub_string(S,_,1,0,"ı");sub_string(S,_,1,0,"u");sub_string(S,_,1,0,"ü")), string_length(S,L), B is L-1, B>0, sub_string(S,0,B,_,TR), (string_concat(RR,"y",TR)->true;RR=TR), atom_string(Rem,RR), translate_noun(Rem,IT), format(atom(Tr), "the ~w", [IT]), !.

% 2. İYELİK EKLERİ
translate_noun(Word, Tr) :- atom_string(Word, S), (sub_string(S,_,2,0,"im");sub_string(S,_,2,0,"ım");sub_string(S,_,2,0,"um");sub_string(S,_,2,0,"üm")), string_length(S,L), B is L-2, B>0, sub_string(S,0,B,_,R), atom_string(Rem,R), translate_noun(Rem,IT), format(atom(Tr), "my ~w", [IT]), !.
translate_noun(Word, Tr) :- atom_string(Word, S), (sub_string(S,_,2,0,"in");sub_string(S,_,2,0,"ın");sub_string(S,_,2,0,"un");sub_string(S,_,2,0,"ün")), string_length(S,L), B is L-2, B>0, sub_string(S,0,B,_,R), atom_string(Rem,R), translate_noun(Rem,IT), format(atom(Tr), "your ~w", [IT]), !.

% 3. ÇOĞUL EKLERİ
translate_noun(Word, Tr) :- atom_string(Word, S), (sub_string(S,_,3,0,"lar");sub_string(S,_,3,0,"ler")), string_length(S,L), B is L-3, B>0, sub_string(S,0,B,_,R), atom_string(Rem,R), translate_noun(Rem,IT), format(atom(Tr), "~ws", [IT]), !.

% 4. YENİ: İSİM-FİİL (GERUNDS) -> "SEVME" -> "LOVING" 🌟
translate_noun(Word, Tr) :-
    atom_string(Word, S),
    (string_concat(RootStr, "me", S) ; string_concat(RootStr, "ma", S)),
    atom_string(RootAtom, RootStr),
    verb_root(RootAtom, EnRoot, _), % Eğer bu bir fiil kökü ise (yüz-me)
    get_present_participle(EnRoot, Tr), !. % 'swimming' olarak çevir.

% 5. YALIN KÖK
translate_noun(Word, Tr) :- atom_string(WA, Word), noun(WA, Tr), !.

% ==============================================================================
%   BÖLÜM 5: KÖK BULMA & SES OLAYLARI
% ==============================================================================
find_matching_root(Str, Root) :- (sub_string(Str,_,4,0,"ebil");sub_string(Str,_,4,0,"abil")), string_length(Str,L), B is L-4, B>0, sub_string(Str,0,B,_,R), find_matching_root(R,Root), !.
find_matching_root(Str, Root) :- (sub_string(Str,_,3,0,"dir");sub_string(Str,_,3,0,"dır");sub_string(Str,_,3,0,"tir");sub_string(Str,_,3,0,"tır")), string_length(Str,L), B is L-3, B>0, sub_string(Str,0,B,_,R), find_matching_root(R,Root), !.
find_matching_root(Str, Root) :- sub_string(Str,_,1,0,"t"), string_length(Str,L), B is L-1, B>0, sub_string(Str,0,B,_,R), verb_root(RA,_,_), atom_string(RA,R), Root=RA, !.
find_matching_root(Str, Root) :- string_length(Str,L), L>0, LI is L-1, sub_string(Str,0,LI,_,Base), sub_string(Str,LI,1,0,Soft), soften_mapping(Hard,Soft), string_concat(Base,Hard,Cand), verb_root(Root,_,_), atom_string(Root,Cand), !.
soften_mapping("p","b"). soften_mapping("ç","c"). soften_mapping("t","d"). soften_mapping("k","ğ"). soften_mapping("k","g").
find_matching_root(Str, Root) :- turkish_irregular_root(Str, Root), !.
find_matching_root(Str, Root) :- verb_root(Root,_,_), atom_string(Root,RA), (Str=RA ; string_length(RA,RL), string_length(Str,IL), IL>=RL, D is IL-RL, D=<2, sub_string(Str,D,RL,0,RA)), !.
find_matching_root(Str, Root) :- atom_string(Root, Str).

% ==============================================================================
%   BÖLÜM 6: OLUMSUZLUK VE ZAMAN
% ==============================================================================
check_negation(W, C, true) :- atom_string(W,S), (sub_string(S,B,_,A,"miyor");sub_string(S,B,_,A,"muyor")), B>0, sub_string(S,0,B,_,R), sub_string(S,_,A,0,P), string_concat(R,"iyor",T), string_concat(T,P,N), atom_string(C,N), !.
check_negation(W, C, true) :- atom_string(W,S), (sub_string(S,B,4,A,"medi");sub_string(S,B,4,A,"madı")), B>0, sub_string(S,0,B,_,R), sub_string(S,_,A,0,P), string_concat(R,"di",T), string_concat(T,P,N), atom_string(C,N), !.
check_negation(W, C, true) :- atom_string(W,S), (sub_string(S,B,7,A,"meyecek");sub_string(S,B,7,A,"mayacak")), B>0, sub_string(S,0,B,_,R), sub_string(S,_,A,0,P), (sub_string(S,_,_,_,"meyecek")->string_concat(R,"ecek",T);string_concat(R,"acak",T)), string_concat(T,P,N), atom_string(C,N), !.
check_negation(W, C, true) :- atom_string(W,S), (sub_string(S,B,3,A,"mez");sub_string(S,B,3,A,"maz")), B>0, sub_string(S,0,B,_,R), sub_string(S,_,A,0,P), (sub_string(S,_,_,_,"mez")->string_concat(R,"er",T);string_concat(R,"ar",T)), string_concat(T,P,N), atom_string(C,N), !.
check_negation(W, W, false).
find_tense_and_root(W, R, T, Rem) :- atom_string(W,S), tense_suffix(TS,T), atom_string(TS,TSS), string_length(TSS,TL), TL>0, sub_string(S,B,TL,A,TSS), B>0, sub_string(S,0,B,_,RS), sub_string(S,_,A,0,RemS), find_matching_root(RS,R), atom_string(Rem,RemS).
find_tense_and_root(W, R, T, Rem) :- atom_string(W,S), sub_string(S,B,3,A,"yor"), B>0, sub_string(S,0,B,_,RVS), sub_string(S,_,A,0,RemS), string_length(RVS,RL), RL>0, PL is RL-1, sub_string(RVS,PL,1,0,LC), member(LC,["i","u","ı","ü"]), sub_string(RVS,0,PL,_,TRS), find_matching_root(TRS,R), T=present_continuous, atom_string(Rem,RemS), !.
find_person(Rem, T, P, Plu) :- person_suffix(S,P,Plu,T), atom_string(S,SS), atom_string(Rem,RS), (SS=""->RS="";sub_string(RS,_,_,0,SS)), !.
find_person(_, _, 3, singular).

% ==============================================================================
%   BÖLÜM 7: YARDIMCI FİİLLER
% ==============================================================================
aux_verb(present_continuous, 1, singular, false, "am").
aux_verb(present_continuous, 3, singular, false, "is").
aux_verb(present_continuous, _, _, false, "are").
aux_verb(present_continuous, 1, singular, true, "am not").
aux_verb(present_continuous, 3, singular, true, "is not").
aux_verb(present_continuous, _, _, true, "are not").
aux_verb(past_simple, _, _, true, "did not").
aux_verb(future, _, _, false, "will").
aux_verb(future, _, _, true, "will not").
aux_verb(aorist, 3, singular, true, "does not").
aux_verb(aorist, _, _, true, "do not").

% ==============================================================================
%   BÖLÜM 8: ÇEKİMLEME
% ==============================================================================
conjugate_english(V, T, P, Pl, N, R) :- get_verb_form(V,T,P,Pl,N,VF), subject_pronoun(P,Pl,S), build_sentence(S,T,P,Pl,N,VF,R).
subject_pronoun(1, singular, 'I'). subject_pronoun(2, singular, you). subject_pronoun(3, singular, 'he/she').
subject_pronoun(1, plural, we). subject_pronoun(2, plural, you). subject_pronoun(3, plural, they).
build_sentence(S,T,P,Pl,N,V,R) :- (aux_verb(T,P,Pl,N,A) -> format(atom(R),"~w ~w ~w",[S,A,V]) ; format(atom(R),"~w ~w",[S,V])).
get_verb_form(V, present_continuous, _, _, _, VF) :- get_present_participle(V, VF).
get_verb_form(V, past_simple, P, _, false, VF) :- get_past_simple(V, P, VF).
get_verb_form(V, past_simple, _, _, true, V).
get_verb_form(V, future, _, _, _, V).
get_verb_form(V, aorist, P, Pl, false, VF) :- get_present_simple(V, P, Pl, VF).
get_verb_form(V, aorist, _, _, true, V).
get_verb_form(V, past_reported, _, _, _, VF) :- get_past_participle(V, VF).
get_verb_form(V, necessity, _, _, _, V). get_verb_form(V, ability, _, _, _, V).
get_present_participle(V, P) :- irregular_verb(V,_,_,P), !.
get_present_participle(V, P) :- atom_string(V,S), (string_concat(B,"e",S), \+ string_concat(_,"ee",S) -> string_concat(B,"ing",PS);string_concat(S,"ing",PS)), atom_string(P,PS).
get_past_simple(V,_,P) :- irregular_verb(V,P,_,_), !.
get_past_simple(V,_,P) :- atom_string(V,S), string_concat(S,"ed",PS), atom_string(P,PS).
get_present_simple(V,3,singular,C) :- !, atom_string(V,S), (V=have->CS="has";V=be->CS="is";string_concat(S,"s",CS)), atom_string(C,CS).
get_present_simple(V,_,_,V).
get_past_participle(V, P) :- irregular_verb(V,_,P,_), !.
get_past_participle(V, P) :- get_past_simple(V,3,P).

test_morphology :- writeln('TEST: Samet gelmiyor -> Samet is not coming'), translate_sentence("Samet gelmiyor", X), writeln(X).
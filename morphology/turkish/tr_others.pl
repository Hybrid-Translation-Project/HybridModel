% =============================================================================
% DOSYA: tr_others.pl
% GÖREV: DİĞER KELİME TÜRLERİ (YALIN KELİMELER)
% AÇIKLAMA:
%   - Genellikle çekim eki almayan veya yalın kullanılan türleri kapsar.
%   - KAPSADIĞI TÜRLER:
%     1. Sıfatlar (Adjective): Güzel, Kırmızı...
%     2. Zarflar (Adverb): Hızlı, Yarın...
%     3. Edatlar (Preposition): İçin, Gibi...
%     4. Bağlaçlar (Conjunction): Ve, Ama...
%   - Bu kelimeler için genellikle tam eşleşme (exact match) yapar.
% =============================================================================

:- module(tr_others, [
    analyze_gerund/2,
    translate_gerund/3
]).

:- use_module('../../database/morphology_data').
:- use_module('../english/en_rules'). % get_present_participle için

analyze_gerund(Word, Analysis) :-
    atom_string(Word, WordStr), string_lower(WordStr, LowerStr),
    check_gerund_suffix(LowerStr, RootStr, Type),
    atom_string(RootAtom, RootStr),
    find_verb_root_safe(RootAtom, Tr, En),
    get_gerund_translation(En, Type, Trans),
    Analysis = [root:Tr, english_root:En, gerund_type:Type, translation:Trans].

find_verb_root_safe(Root, Tr, En) :- atom_string(Root, S), turkish_irregular_root(S, Tr), verb_root(Tr, En, _), !.
find_verb_root_safe(Root, Tr, En) :- verb_root(Root, En, _), Tr=Root, !.
find_verb_root_safe(Root, Tr, En) :- atom_string(Root, S), member(V, ["u","ü","ı","i","a","e"]), string_concat(S, V, Ext), atom_string(ExtAtom, Ext), verb_root(ExtAtom, En, _), Tr=ExtAtom, !.
find_verb_root_safe(R, R, R).

check_gerund_suffix(W, R, while) :- string_length(W,L), L>5, (sub_string(W,_,5,0,"arken"); sub_string(W,_,5,0,"erken"); sub_string(W,_,5,0,"ırken"); sub_string(W,_,5,0,"irken"); sub_string(W,_,5,0,"urken"); sub_string(W,_,5,0,"ürken")), B is L-5, sub_string(W,0,B,5,R), !.
check_gerund_suffix(W, R, while) :- string_length(W,L), L>6, sub_string(W,_,6,0,"yorken"), B is L-6, sub_string(W,0,B,6,T), (string_length(T,TL), TL>0, LI is TL-1, sub_string(T,LI,1,0,LC), member(LC,["i","ı","u","ü"]) -> sub_string(T,0,LI,1,R) ; R=T), !.
check_gerund_suffix(W, R, while) :- string_length(W,L), L>3, sub_string(W,_,3,0,"ken"), \+ sub_string(W,_,5,0,"arken"), B is L-3, sub_string(W,0,B,3,Bk), remove_aorist(Bk, R), !.
check_gerund_suffix(W, R, by) :- string_length(W,L), L>5, (sub_string(W,_,5,0,"yarak"); sub_string(W,_,5,0,"yerek")), B is L-5, sub_string(W,0,B,5,R), !.
check_gerund_suffix(W, R, by) :- string_length(W,L), L>4, (sub_string(W,_,4,0,"arak"); sub_string(W,_,4,0,"erek")), B is L-4, sub_string(W,0,B,4,R), !.
check_gerund_suffix(W, R, when) :- string_length(W,L), L>4, (sub_string(W,_,4,0,"ınca"); sub_string(W,_,4,0,"ince"); sub_string(W,_,4,0,"unca"); sub_string(W,_,4,0,"ünce")), B is L-4, sub_string(W,0,B,4,R), !.
check_gerund_suffix(W, R, without) :- string_length(W,L), L>5, (sub_string(W,_,5,0,"madan"); sub_string(W,_,5,0,"meden")), B is L-5, sub_string(W,0,B,5,R), !.

remove_aorist(W, R) :- string_length(W,L), L>2, (sub_string(W,_,2,0,"ar"); sub_string(W,_,2,0,"er"); sub_string(W,_,2,0,"ır"); sub_string(W,_,2,0,"ir"); sub_string(W,_,2,0,"ur"); sub_string(W,_,2,0,"ür")), B is L-2, sub_string(W,0,B,2,R), !.
remove_aorist(W, R) :- string_length(W,L), L>1, sub_string(W,_,1,0,"r"), B is L-1, sub_string(W,0,B,1,R), !.
remove_aorist(W, W).

get_gerund_translation(En, while, T) :- get_present_participle(En, P), format(atom(T), "while ~w", [P]).
get_gerund_translation(En, by, T) :- get_present_participle(En, P), format(atom(T), "by ~w", [P]).
get_gerund_translation(En, when, T) :- get_present_participle(En, P), format(atom(T), "when ~w", [P]).
get_gerund_translation(En, without, T) :- get_present_participle(En, P), format(atom(T), "without ~w", [P]).

translate_gerund(W, E, D) :- analyze_gerund(W, A), member(translation:E, A), D=A.
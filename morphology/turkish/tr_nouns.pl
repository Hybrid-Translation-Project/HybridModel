% =============================================================================
% DOSYA: tr_nouns.pl
% GÖREV: İSİM SOYLU KELİME ANALİZİ
% AÇIKLAMA:
%   - İsim çekim eklerini alan tüm kelime türlerini analiz eder.
%   - KAPSADIĞI TÜRLER:
%     1. İsimler (Noun): Kitap, Masa...
%     2. Zamirler (Pronoun): Ben, Sen, O... (İsim gibi çekimlenirler)
%     3. Sayılar (Number): Bir, İki... (İsim gibi çekimlenirler)
%   - İsim kökünden başlayıp hal, çoğul, iyelik eklerini zincirleme çözer.
%   - İsim tamlamalarını ve birleşik isimleri de kapsar. 
% =============================================================================

:- module(tr_nouns, [
    analyze_noun/2,
    find_noun_root/5
]).

% Veritabanı ve Fonoloji
:- use_module('../morphology_data/morphology_data').

% --- İSİM ANALİZİ ---
analyze_noun(Word, Analysis) :-
    atom_string(Word, WordStr),
    string_lower(WordStr, LowerStr),
    atom_string(LowerWord, LowerStr),
    
    % 1. Adım: Çoğul eki kontrolü (evler -> ev)
    check_plural(LowerWord, Stem1, PluralSuffix),
    
    % 2. Adım: İyelik eki kontrolü (kitabım -> kitab)
    check_possessive(Stem1, Stem2, PossessiveSuffix),

    % 3. Adım: Kök Bulma (kitab -> kitap)
    find_noun_root(Stem2, Root, Eng, Type, Vowel),
    
    Analysis = [root:Root, eng:Eng, type:Type, plural:PluralSuffix, possessive:PossessiveSuffix].

% --- KÖK BULMA ---
find_noun_root(WordAtom, Root, Eng, Type, Vowel) :-
    % A) Doğrudan Eşleşme (kalem -> kalem)
    noun_root(WordAtom, Eng, _, Type, Vowel),
    Root = WordAtom.

find_noun_root(WordAtom, Root, Eng, Type, Vowel) :-
    % B) Yumuşama Düzeltmesi (kitab -> kitap)
    atom_chars(WordAtom, Chars),
    append(Body, [LastChar], Chars),
    yumusama_tersi(LastChar, OrgChar), % b->p, c->ç dönüşümü
    append(Body, [OrgChar], NewChars),
    atom_chars(Candidate, NewChars),
    noun_root(Candidate, Eng, _, Type, Vowel),
    Root = Candidate.

% Yumuşama Ters Çevirme Tablosu
yumusama_tersi('b', 'p').
yumusama_tersi('c', 'ç').
yumusama_tersi('d', 't').
yumusama_tersi('ğ', 'k').

% --- EKLERİ AYIKLAMA ---
check_plural(Word, Stem, "lar") :-
    atom_string(Word, Str),
    (string_concat(StemStr, "lar", Str); string_concat(StemStr, "ler", Str)),
    atom_string(Stem, StemStr), !.
check_plural(Word, Word, "yok").

check_possessive(Word, Stem, "1s") :-
    atom_string(Word, Str),
    % kitab-ım, ev-im, yol-um, üzüm-üm
    (string_concat(StemStr, "im", Str); string_concat(StemStr, "ım", Str); 
     string_concat(StemStr, "um", Str); string_concat(StemStr, "üm", Str)),
    atom_string(Stem, StemStr), !.
check_possessive(Word, Word, "yok").
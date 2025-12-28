:- module(morphology, [
    translate_verb/3,
    translate_noun/3,
    translate_gerund/3,
    translate_question/2,
    translate_word/2,
    translate_sentence/2,
    analyze_turkish/2,
    analyze_noun/2,
    analyze_gerund/2,
    conjugate_english/6,
    test_morphology/0,
    reload_morphology_data/0,
    tense_suffix/2,
    find_matching_root/2
]).

:- encoding(utf8).

% =============================================================================
% ALT KLASÖRLERDEN MODÜLLERİ YÜKLE VE DIŞARI AKTAR (RE-EXPORT)
% Dosya yapın: prolog/morphology_main.pl olduğu için
% Alt modülleri 'morphology/...' şeklinde çağırmalıyız.
% =============================================================================

% Data klasöründen
:- reexport('morphology/data/morphology_data').

% Core klasöründen (Ana mantık)
:- reexport('morphology/core/morphology_core').

% Noun klasöründen
:- reexport('morphology/noun/morph_noun').

% Verb klasöründen
:- reexport('morphology/verb/morph_gerund').
:- reexport('morphology/verb/morph_tense').

% Question klasöründen
:- reexport('morphology/question/morph_question').


% =============================================================================
% YENİDEN YÜKLEME
% =============================================================================

reload_morphology_data :-
    unload_file('morphology/data/morphology_data'),
    use_module('morphology/data/morphology_data'),
    writeln('[OK] morphology_data.pl yeniden yüklendi.').

% =============================================================================
% BİLGİ
% =============================================================================

:- writeln('Morfoloji ana modülü (morphology_main.pl) yüklendi.').
:- writeln('Python bu dosyayi consult ediyor.').
:- writeln('Veri güncellenirse reload_morphology_data/0 çağrılmalıdır.').
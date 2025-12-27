% =============================================================================
% DOSYA: tr_sentence.pl
% GÖREV: Cümle ve Kelime Çeviri Koordinatörü
% AÇIKLAMA:
%   - Cümleyi kelimelere böler.
%   - Soru cümlelerini (mi/mı) tespit edip İngilizce soru formatına çevirir.
%   - Her kelime için doğru analizciyi (fiil/isim/zarf) çağırır.
% =============================================================================

:- module(tr_sentence, [
    analyze_sentence/2
]).

% Diğer modülleri çağırıyoruz
:- use_module(tr_verbs).
:- use_module(tr_nouns).

% --- CÜMLE ANALİZİ ---
% Girdi: ["ben", "geliyorum"] (Liste formatında bekler)
% Çıktı: Her kelimenin analizi
analyze_sentence([], []).

analyze_sentence([Word|Rest], [Analysis|RestAnalysis]) :-
    analyze_word_wrapper(Word, Analysis),
    analyze_sentence(Rest, RestAnalysis).

% Kelimeyi sırayla kontrol et: Önce Fiil mi? Sonra İsim mi?
analyze_word_wrapper(Word, Result) :-
    % 1. Fiil Analizi Dene
    (   tr_verbs:analyze_turkish(Word, Res)
    ->  Result = Res
    ;   
        % 2. İsim Analizi Dene
        (   tr_nouns:analyze_noun(Word, Res)
        ->  Result = Res
        ;   
            % 3. Bulunamazsa
            Result = unknown(Word)
        )
    ).
% =============================================================================
% DOSYA: tr_main.pl
% GÖREV: YÖNETİCİ (ORCHESTRATOR)
% AÇIKLAMA:
%   - Bu dosya projenin giriş kapısıdır.
%   - Diğer tüm modülleri (database, nouns, verbs, phonology...) yükler.
%   - Kullanıcıdan gelen kelimeyi analiz etmek için doğru modüle yönlendirir.
%   - Tek bir 'analyze_turkish/2' komutuyla tüm sistemi çalıştırır.
% =============================================================================

:- module(tr_main, [
    verify_system/0
]).

% --- MODÜL BAĞLANTILARI ---
:- use_module(tr_verbs).
:- use_module(tr_nouns).
:- use_module(tr_sentence).

% --- GENEL SİSTEM TESTİ ---
verify_system :-
    writeln('================================================='),
    writeln('      HIBIT SISTEM - TAM KAPSAMLI TEST           '),
    writeln('================================================='),
    
    test_verbs,
    nl,
    test_nouns,
    nl,
    test_sentences,
    
    writeln('================================================='),
    writeln('            TEST TAMAMLANDI                      '),
    writeln('=================================================').

% -----------------------------------------------------------------------------
% 1. MODÜL TESTİ: FİİLLER
% -----------------------------------------------------------------------------
test_verbs :-
    writeln('--- [TEST 1] FIIL MODULU (tr_verbs) ---'),
    % DÜZELTME: Çağırırken 2. parametreye (Sonuç) '_' koyduk.
    run_test(tr_verbs:analyze_turkish("geliyorum", _), "Standard (geliyorum)"),
    run_test(tr_verbs:analyze_turkish("gitmedi", _),   "Olumsuz (gitmedi)").

% -----------------------------------------------------------------------------
% 2. MODÜL TESTİ: İSİMLER
% -----------------------------------------------------------------------------
test_nouns :-
    writeln('--- [TEST 2] ISIM MODULU (tr_nouns) ---'),
    catch(
        % DÜZELTME: 2. parametre eklendi
        run_test(tr_nouns:analyze_noun("evler", _), "Cogul (evler)"),
        error(existence_error(procedure, _), _),
        writeln('[UYARI] tr_nouns:analyze_noun/2 tanimli degil veya dosya bos.')
    ),
    catch(
        % DÜZELTME: 2. parametre eklendi
        run_test(tr_nouns:analyze_noun("kitabım", _), "Iyelik (kitabim)"),
        error(existence_error(procedure, _), _),
        writeln('[UYARI] tr_nouns:analyze_noun/2 tanimli degil.')
    ).

% -----------------------------------------------------------------------------
% 3. MODÜL TESTİ: CÜMLELER
% -----------------------------------------------------------------------------
test_sentences :-
    writeln('--- [TEST 3] CUMLE MODULU (tr_sentence) ---'),
    catch(
        % DÜZELTME: 2. parametre eklendi
        run_test(tr_sentence:analyze_sentence(["ben", "geliyorum"], _), "Basit Cumle"),
        error(existence_error(procedure, _), _),
        writeln('[UYARI] tr_sentence:analyze_sentence/2 tanimli degil veya dosya bos.')
    ).

% --- YARDIMCI TEST FONKSİYONU ---
run_test(Goal, Description) :-
    format('Testing: ~w... ', [Description]),
    catch(
        (Goal -> 
            arg(2, Goal, Result), % Hedefin 2. argümanını (Sonucu) çeker alır
            format('OK.~n   -> Sonuc: ~w~n', [Result])
        ;
            writeln('FAIL (Basarisiz).')
        ),
        Error,
        format('ERROR (Hata): ~w~n', [Error])
    ).
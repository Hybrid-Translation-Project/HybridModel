% =============================================================================
% MORPHOLOGY DATA - MongoDB'den Otomatik Oluşturuldu
% =============================================================================
% Bu dosya morphology_api.py tarafından oluşturulmuştur.
% Manuel düzenleme yapmayın - veriler MongoDB'den gelir.
% =============================================================================
:- encoding(utf8).

% Discontiguous declarations for phonology facts
:- discontiguous phonology_condition/3.
:- discontiguous phonology_action/3.
:- discontiguous postposition/4.

% =============================================================================
% FİİL KÖKLERİ: verb_root(TurkishRoot, EnglishRoot, Type).
% =============================================================================
verb_root(gel, come, irregular).
verb_root(git, go, irregular).
verb_root(gid, go, irregular).
verb_root(ye, eat, irregular).
verb_root(yi, eat, irregular).
verb_root(iç, drink, irregular).
verb_root(yap, do, irregular).
verb_root(al, take, irregular).
verb_root(ver, give, irregular).
verb_root(oku, read, irregular).
verb_root(yaz, write, irregular).
verb_root(sev, love, regular).
verb_root(gör, see, irregular).
verb_root(bil, know, irregular).
verb_root(de, say, irregular).
verb_root(söyle, tell, irregular).
verb_root(düşün, think, irregular).
verb_root(anla, understand, irregular).
verb_root(bul, find, irregular).
verb_root(bırak, leave, irregular).
verb_root(hisset, feel, irregular).
verb_root(koy, put, irregular).
verb_root(otur, sit, irregular).
verb_root(kalk, stand, irregular).
verb_root(uyu, sleep, irregular).
verb_root(uyan, wake, irregular).
verb_root(koş, run, irregular).
verb_root(yüz, swim, irregular).
verb_root(sat, sell, irregular).
verb_root(yıka, wash, regular).
verb_root(oyna, play, regular).
verb_root(konuş, speak, irregular).
verb_root(dinle, listen, regular).
verb_root(bekle, wait, regular).
verb_root(başla, start, regular).
verb_root(bitir, finish, regular).
verb_root(aç, open, regular).
verb_root(kapat, close, regular).
verb_root(öğren, learn, regular).
verb_root(öğret, teach, irregular).
verb_root(hatırla, remember, regular).
verb_root(unut, forget, irregular).
verb_root(ol, be, irregular).
verb_root(et, do, irregular).
verb_root(iste, want, regular).
verb_root(duy, hear, irregular).
verb_root(tut, hold, irregular).
verb_root(bak, look, regular).
verb_root(dene, try, regular).
verb_root(kullan, use, regular).
verb_root(düş, fall, irregular).
verb_root(kal, stay, regular).
verb_root(dur, stop, regular).
verb_root(gir, enter, regular).
verb_root(çık, exit, regular).
verb_root(dön, turn, regular).
verb_root(atla, jump, regular).
verb_root(yürü, walk, regular).
verb_root(ara, search, regular).
verb_root(ara, call, regular).
verb_root(ağla, cry, regular).
verb_root(gül, laugh, regular).
verb_root(düşür, drop, regular).
verb_root(kır, break, regular).
verb_root(aç, open, regular).
verb_root(kapa, close, regular).
verb_root(seç, choose, regular).
verb_root(kaç, escape, regular).
verb_root(kes, cut, regular).
verb_root(çiz, draw, regular).
verb_root(sil, wipe, regular).
verb_root(temizle, clean, regular).
verb_root(çalış,work,regular).

% =============================================================================
% DÜZENSİZ FİİLLER: irregular_verb(Base, Past, PastParticiple, PresentParticiple).
% =============================================================================
irregular_verb(be, 'was_were', been, being).
irregular_verb(come, 'came', come, coming).
irregular_verb(go, 'went', gone, going).
irregular_verb(eat, 'ate', eaten, eating).
irregular_verb(drink, 'drank', drunk, drinking).
irregular_verb(give, 'gave', given, giving).
irregular_verb(take, 'took', taken, taking).
irregular_verb(make, 'made', made, making).
irregular_verb(do, 'did', done, doing).
irregular_verb(see, 'saw', seen, seeing).
irregular_verb(have, 'had', had, having).
irregular_verb(get, 'got', gotten, getting).
irregular_verb(read, 'read', read, reading).
irregular_verb(write, 'wrote', written, writing).
irregular_verb(run, 'ran', run, running).
irregular_verb(swim, 'swam', swum, swimming).
irregular_verb(buy, 'bought', bought, buying).
irregular_verb(sell, 'sold', sold, selling).
irregular_verb(say, 'said', said, saying).
irregular_verb(tell, 'told', told, telling).
irregular_verb(think, 'thought', thought, thinking).
irregular_verb(know, 'knew', known, knowing).
irregular_verb(understand, 'understood', understood, understanding).
irregular_verb(find, 'found', found, finding).
irregular_verb(leave, 'left', left, leaving).
irregular_verb(feel, 'felt', felt, feeling).
irregular_verb(put, 'put', put, putting).
irregular_verb(sit, 'sat', sat, sitting).
irregular_verb(stand, 'stood', stood, standing).
irregular_verb(sleep, 'slept', slept, sleeping).
irregular_verb(wake, 'woke', woken, waking).
irregular_verb(forget, 'forgot', forgotten, forgetting).
irregular_verb(speak, 'spoke', spoken, speaking).
irregular_verb(teach, 'taught', taught, teaching).
irregular_verb(hear, 'heard', heard, hearing).
irregular_verb(hold, 'held', held, holding).
irregular_verb(want, 'wanted', wanted, wanting).
irregular_verb(fall, 'fell', fallen, falling).
irregular_verb(walk, 'walked', walked, walking).

% =============================================================================
% ZAMAN EKLERİ: tense_suffix(Suffix, Tense).
% =============================================================================
tense_suffix(iyor, present_continuous).
tense_suffix(ıyor, present_continuous).
tense_suffix(uyor, present_continuous).
tense_suffix(üyor, present_continuous).
tense_suffix(di, past_simple).
tense_suffix(dı, past_simple).
tense_suffix(du, past_simple).
tense_suffix(dü, past_simple).
tense_suffix(ti, past_simple).
tense_suffix(tı, past_simple).
tense_suffix(tu, past_simple).
tense_suffix(tü, past_simple).
tense_suffix(ecek, future).
tense_suffix(acak, future).
tense_suffix(eceg, future).
tense_suffix(acag, future).
tense_suffix(er, aorist).
tense_suffix(ar, aorist).
tense_suffix(ir, aorist).
tense_suffix(ır, aorist).
tense_suffix(ur, aorist).
tense_suffix(ür, aorist).
tense_suffix(miş, past_reported).
tense_suffix(muş, past_reported).
tense_suffix(mış, past_reported).
tense_suffix(müş, past_reported).
tense_suffix(meli, necessity).
tense_suffix(malı, necessity).
tense_suffix(ebil, ability).
tense_suffix(abil, ability).
tense_suffix(yor, present_continuous).
tense_suffix(r, aorist).

% =============================================================================
% ŞAHIS EKLERİ: person_suffix(Suffix, Person, Plurality, Tense).
% =============================================================================
person_suffix(um, 1, singular, present_continuous).
person_suffix(sun, 2, singular, present_continuous).
person_suffix('', 3, singular, present_continuous).
person_suffix(uz, 1, plural, present_continuous).
person_suffix(sunuz, 2, plural, present_continuous).
person_suffix(lar, 3, plural, present_continuous).
person_suffix(ler, 3, plural, present_continuous).
person_suffix(m, 1, singular, past_simple).
person_suffix(n, 2, singular, past_simple).
person_suffix('', 3, singular, past_simple).
person_suffix(k, 1, plural, past_simple).
person_suffix(niz, 2, plural, past_simple).
person_suffix(lar, 3, plural, past_simple).
person_suffix(ler, 3, plural, past_simple).
person_suffix(im, 1, singular, future).
person_suffix(sin, 2, singular, future).
person_suffix('', 3, singular, future).
person_suffix(iz, 1, plural, future).
person_suffix(siniz, 2, plural, future).
person_suffix(lar, 3, plural, future).
person_suffix(im, 1, singular, aorist).
person_suffix(ım, 1, singular, aorist).
person_suffix(um, 1, singular, aorist).
person_suffix(üm, 1, singular, aorist).
person_suffix(sin, 2, singular, aorist).
person_suffix(sın, 2, singular, aorist).
person_suffix(sun, 2, singular, aorist).
person_suffix(sün, 2, singular, aorist).
person_suffix('', 3, singular, aorist).
person_suffix(iz, 1, plural, aorist).
person_suffix(ız, 1, plural, aorist).
person_suffix(uz, 1, plural, aorist).
person_suffix(üz, 1, plural, aorist).
person_suffix(siniz, 2, plural, aorist).
person_suffix(sınız, 2, plural, aorist).
person_suffix(sunuz, 2, plural, aorist).
person_suffix(sünüz, 2, plural, aorist).
person_suffix(lar, 3, plural, aorist).
person_suffix(ler, 3, plural, aorist).
person_suffix(yim, 1, singular, necessity).
person_suffix(sin, 2, singular, necessity).
person_suffix('', 3, singular, necessity).
person_suffix(yiz, 1, plural, necessity).
person_suffix(siniz, 2, plural, necessity).

% =============================================================================
% TÜRKÇE DÜZENSİZ KÖKLER: turkish_irregular_root(Alternate, Canonical).
% =============================================================================
turkish_irregular_root("y", ye).
turkish_irregular_root("yi", ye).
turkish_irregular_root("yiy", ye).
turkish_irregular_root("d", de).
turkish_irregular_root("di", de).
turkish_irregular_root("diy", de).
turkish_irregular_root("gid", git).
turkish_irregular_root("ed", et).
turkish_irregular_root("tad", tat).
turkish_irregular_root("okuy", oku).
turkish_irregular_root("başlıy", başla).
turkish_irregular_root("anlıy", anla).
turkish_irregular_root("oynuy", oyna).

% =============================================================================
% YARDIMCI FİİLLER: auxiliary_verb(Tense, Person, Plurality, Negation, Auxiliary).
% =============================================================================
auxiliary_verb(present_continuous, 1, singular, false, am).
auxiliary_verb(present_continuous, 2, singular, false, are).
auxiliary_verb(present_continuous, 3, singular, false, is).
auxiliary_verb(present_continuous, 1, plural, false, are).
auxiliary_verb(present_continuous, 2, plural, false, are).
auxiliary_verb(present_continuous, 3, plural, false, are).
auxiliary_verb(present_continuous, 1, singular, true, 'am not').
auxiliary_verb(present_continuous, 2, singular, true, 'are not').
auxiliary_verb(present_continuous, 3, singular, true, 'is not').
auxiliary_verb(present_continuous, 1, plural, true, 'are not').
auxiliary_verb(present_continuous, 2, plural, true, 'are not').
auxiliary_verb(present_continuous, 3, plural, true, 'are not').
auxiliary_verb(future, _, _, false, will).
auxiliary_verb(future, _, _, true, 'will not').
auxiliary_verb(past_simple, _, _, true, 'did not').
auxiliary_verb(aorist, 1, singular, true, 'do not').
auxiliary_verb(aorist, 2, singular, true, 'do not').
auxiliary_verb(aorist, 3, singular, true, 'does not').
auxiliary_verb(aorist, 1, plural, true, 'do not').
auxiliary_verb(aorist, 2, plural, true, 'do not').
auxiliary_verb(aorist, 3, plural, true, 'do not').
auxiliary_verb(past_reported, 1, singular, false, have).
auxiliary_verb(past_reported, 2, singular, false, have).
auxiliary_verb(past_reported, 3, singular, false, has).
auxiliary_verb(past_reported, 1, plural, false, have).
auxiliary_verb(past_reported, 3, singular, true, 'has not').
auxiliary_verb(past_reported, 1, singular, true, 'have not').
auxiliary_verb(necessity, _, _, false, should).
auxiliary_verb(necessity, _, _, true, 'should not').
auxiliary_verb(ability, _, _, false, can).
auxiliary_verb(ability, _, _, true, cannot).

% =============================================================================
% FONOLOJİ KURALLARI: phonology_rule(Language, RuleName, RuleType, Context, Priority).
% =============================================================================
phonology_rule(turkish, buyuk_unlu_uyumu_back, vowel_harmony, suffix_attachment, 100).
phonology_rule(turkish, buyuk_unlu_uyumu_front, vowel_harmony, suffix_attachment, 100).
phonology_rule(turkish, unlu_daralmasi_a, vowel_narrowing, before_yor, 95).
phonology_rule(turkish, unlu_daralmasi_e, vowel_narrowing, before_yor, 95).
phonology_rule(turkish, kucuk_unlu_uyumu_rounded, vowel_harmony, suffix_attachment, 90).
phonology_rule(turkish, kucuk_unlu_uyumu_unrounded, vowel_harmony, suffix_attachment, 90).
phonology_rule(english, ie_to_ying, vowel_change, suffix_ing, 90).
phonology_rule(turkish, unsuz_benzesmesi_t, consonant_assimilation, suffix_attachment, 85).
phonology_rule(english, silent_e_drop_ing, vowel_drop, suffix_ing, 85).
phonology_rule(english, silent_e_drop_ed, vowel_drop, suffix_ed, 85).
phonology_rule(english, y_to_ied, vowel_change, suffix_ed, 85).
phonology_rule(english, y_to_ies, vowel_change, third_person, 85).
phonology_rule(turkish, unsuz_yumusamasi_p, consonant_softening, before_vowel, 80).
phonology_rule(turkish, unsuz_yumusamasi_c, consonant_softening, before_vowel, 80).
phonology_rule(turkish, unsuz_yumusamasi_t, consonant_softening, before_vowel, 80).
phonology_rule(turkish, unsuz_yumusamasi_k, consonant_softening, before_vowel, 80).
phonology_rule(english, cvc_doubling_ing, consonant_doubling, suffix_ing, 80).
phonology_rule(english, cvc_doubling_ed, consonant_doubling, suffix_ed, 80).
phonology_rule(english, es_after_sibilant, suffix_selection, third_person, 80).
phonology_rule(turkish, unlu_dusmesi, vowel_drop, suffix_attachment, 75).
phonology_rule(english, ed_id_pronunciation, pronunciation, past_participle, 75).
phonology_rule(english, ed_t_pronunciation, pronunciation, past_participle, 75).
phonology_rule(english, ed_d_pronunciation, pronunciation, past_participle, 75).
phonology_rule(turkish, kaynastirma_y, buffer_consonant, vowel_vowel, 70).
phonology_rule(turkish, kaynastirma_n, buffer_consonant, possessive, 70).
phonology_rule(turkish, kaynastirma_s, buffer_consonant, possessive, 70).
phonology_rule(english, s_default, suffix_selection, third_person, 70).

% =============================================================================
% FONOLOJİ KURAL DETAYLARI: phonology_condition(RuleName, Key, Value).
%                           phonology_action(RuleName, Key, Value).
% =============================================================================
phonology_condition(buyuk_unlu_uyumu_back, last_vowel, ['a', 'ı', 'o', 'u']).
phonology_action(buyuk_unlu_uyumu_back, select_suffix_vowel_e, 'a').
phonology_action(buyuk_unlu_uyumu_back, select_suffix_vowel_i, 'ı').
phonology_condition(buyuk_unlu_uyumu_front, last_vowel, ['e', 'i', 'ö', 'ü']).
phonology_action(buyuk_unlu_uyumu_front, select_suffix_vowel_a, 'e').
phonology_action(buyuk_unlu_uyumu_front, select_suffix_vowel_ı, 'i').
phonology_condition(unlu_daralmasi_a, ends_with, 'a').
phonology_condition(unlu_daralmasi_a, following_suffix, 'yor').
phonology_action(unlu_daralmasi_a, replace_from, 'a').
phonology_action(unlu_daralmasi_a, replace_to, 'ı').
phonology_condition(unlu_daralmasi_e, ends_with, 'e').
phonology_condition(unlu_daralmasi_e, following_suffix, 'yor').
phonology_action(unlu_daralmasi_e, replace_from, 'e').
phonology_action(unlu_daralmasi_e, replace_to, 'i').
phonology_condition(kucuk_unlu_uyumu_rounded, last_vowel, ['o', 'u', 'ö', 'ü']).
phonology_action(kucuk_unlu_uyumu_rounded, select_suffix_vowel_ı, 'u').
phonology_action(kucuk_unlu_uyumu_rounded, select_suffix_vowel_i, 'ü').
phonology_condition(kucuk_unlu_uyumu_unrounded, last_vowel, ['a', 'e', 'ı', 'i']).
phonology_action(kucuk_unlu_uyumu_unrounded, select_suffix_vowel_u, 'ı').
phonology_action(kucuk_unlu_uyumu_unrounded, select_suffix_vowel_ü, 'i').
phonology_condition(ie_to_ying, ends_with, 'ie').
phonology_action(ie_to_ying, replace_from, 'ie').
phonology_action(ie_to_ying, replace_to, 'y').
phonology_condition(unsuz_benzesmesi_t, final_consonant, ['p', 'ç', 't', 'k', 'f', 'h', 's', 'ş']).
phonology_action(unsuz_benzesmesi_t, select_suffix_consonant_d, 't').
phonology_action(unsuz_benzesmesi_t, select_suffix_consonant_c, 'ç').
phonology_condition(silent_e_drop_ing, ends_with, 'e').
phonology_condition(silent_e_drop_ing, preceded_by, 'consonant').
phonology_action(silent_e_drop_ing, drop_final, 'e').
phonology_condition(silent_e_drop_ed, ends_with, 'e').
phonology_action(silent_e_drop_ed, drop_final, 'e').
phonology_action(silent_e_drop_ed, suffix, 'd').
phonology_condition(y_to_ied, ends_with, 'y').
phonology_condition(y_to_ied, preceded_by, 'consonant').
phonology_action(y_to_ied, replace_from, 'y').
phonology_action(y_to_ied, replace_to, 'i').
phonology_condition(y_to_ies, ends_with, 'y').
phonology_condition(y_to_ies, preceded_by, 'consonant').
phonology_action(y_to_ies, replace_from, 'y').
phonology_action(y_to_ies, replace_to, 'ie').
phonology_action(y_to_ies, add, 's').
phonology_condition(unsuz_yumusamasi_p, final_consonant, 'p').
phonology_condition(unsuz_yumusamasi_p, following, 'vowel').
phonology_action(unsuz_yumusamasi_p, replace_from, 'p').
phonology_action(unsuz_yumusamasi_p, replace_to, 'b').
phonology_condition(unsuz_yumusamasi_c, final_consonant, 'ç').
phonology_condition(unsuz_yumusamasi_c, following, 'vowel').
phonology_action(unsuz_yumusamasi_c, replace_from, 'ç').
phonology_action(unsuz_yumusamasi_c, replace_to, 'c').
phonology_condition(unsuz_yumusamasi_t, final_consonant, 't').
phonology_condition(unsuz_yumusamasi_t, following, 'vowel').
phonology_action(unsuz_yumusamasi_t, replace_from, 't').
phonology_action(unsuz_yumusamasi_t, replace_to, 'd').
phonology_condition(unsuz_yumusamasi_k, final_consonant, 'k').
phonology_condition(unsuz_yumusamasi_k, following, 'vowel').
phonology_action(unsuz_yumusamasi_k, replace_from, 'k').
phonology_action(unsuz_yumusamasi_k, replace_to, 'ğ').
phonology_condition(cvc_doubling_ing, pattern, 'CVC').
phonology_condition(cvc_doubling_ing, final_consonant, ['b', 'd', 'g', 'l', 'm', 'n', 'p', 'r', 't']).
phonology_condition(cvc_doubling_ing, stressed_final, true).
phonology_condition(cvc_doubling_ing, not_ending, ['w', 'x', 'y']).
phonology_action(cvc_doubling_ing, double_final_consonant, true).
phonology_condition(cvc_doubling_ed, pattern, 'CVC').
phonology_condition(cvc_doubling_ed, final_consonant, ['b', 'd', 'g', 'm', 'n', 'p', 't']).
phonology_condition(cvc_doubling_ed, stressed_final, true).
phonology_action(cvc_doubling_ed, double_final_consonant, true).
phonology_condition(es_after_sibilant, ends_with, ['s', 'ss', 'sh', 'ch', 'x', 'z']).
phonology_action(es_after_sibilant, add_suffix, 'es').
phonology_condition(unlu_dusmesi, syllable_pattern, 'CVC').
phonology_condition(unlu_dusmesi, second_vowel_unstable, true).
phonology_action(unlu_dusmesi, drop_vowel, 'second').
phonology_condition(ed_id_pronunciation, ends_with, ['t', 'd']).
phonology_action(ed_id_pronunciation, pronunciation, '/ɪd/').
phonology_condition(ed_t_pronunciation, ends_with_voiceless, ['p', 'k', 'f', 's', 'ʃ', 'tʃ']).
phonology_action(ed_t_pronunciation, pronunciation, '/t/').
phonology_condition(ed_d_pronunciation, ends_with_voiced, true).
phonology_action(ed_d_pronunciation, pronunciation, '/d/').
phonology_condition(kaynastirma_y, ends_with, 'vowel').
phonology_condition(kaynastirma_y, suffix_starts, 'vowel').
phonology_action(kaynastirma_y, insert, 'y').
phonology_condition(kaynastirma_n, ends_with, 'vowel').
phonology_condition(kaynastirma_n, suffix_type, 'possessive_3rd').
phonology_action(kaynastirma_n, insert, 'n').
phonology_condition(kaynastirma_s, ends_with, 'vowel').
phonology_condition(kaynastirma_s, suffix_type, 'possessive').
phonology_action(kaynastirma_s, insert, 's').
phonology_condition(s_default, default, true).
phonology_action(s_default, add_suffix, 's').

% =============================================================================
% GENİŞ ZAMAN İSTİSNA FİİLLER: aorist_irregular(Root, Suffix, Example, English).
% Normalde tek heceli fiiller -ar/-er alır, ama bu 13 fiil -ır/-ir/-ur/-ür alır
% =============================================================================
aorist_irregular(al, ır, alır, take).
aorist_irregular(bil, ir, bilir, know).
aorist_irregular(bul, ur, bulur, find).
aorist_irregular(dur, ur, durur, stop/stand).
aorist_irregular(gel, ir, gelir, come).
aorist_irregular(gör, ür, görür, see).
aorist_irregular(kal, ır, kalır, stay).
aorist_irregular(ol, ur, olur, be/become).
aorist_irregular(öl, ür, ölür, die).
aorist_irregular(san, ır, sanır, think/assume).
aorist_irregular(var, ır, varır, arrive).
aorist_irregular(ver, ir, verir, give).
aorist_irregular(vur, ur, vurur, hit).

% =============================================================================
% ÜNLÜ UYUMU İSTİSNALARI: vowel_harmony_exception(Word, Correct, Wrong, Origin).
% Arapça, Farsça, Fransızca kökenli kelimeler
% =============================================================================
vowel_harmony_exception(saat, saatler, saatlar, arabic).
vowel_harmony_exception(hayal, hayaller, hayallar, arabic).
vowel_harmony_exception(dikkat, dikkatler, dikkatlar, arabic).
vowel_harmony_exception(hareket, hareketler, hareketlar, arabic).
vowel_harmony_exception(rol, roller, rollar, french).
vowel_harmony_exception(gol, goller, gollar, english).
vowel_harmony_exception(alkol, alkoller, alkollar, arabic).
vowel_harmony_exception(kontrol, kontroller, kontrollar, french).
vowel_harmony_exception(petrol, petroller, petrollar, french).
vowel_harmony_exception(protokol, protokoller, protokollar, french).
vowel_harmony_exception(kalp, kalbi, kalbı, arabic).
vowel_harmony_exception(harf, harfi, harfı, arabic).

% =============================================================================
% ÜNSÜZ YUMUŞAMASI İSTİSNALARI: consonant_no_mutation(Word, WithSuffix, Rule).
% Tek heceli ve yabancı kelimeler yumuşama yapmaz
% =============================================================================
consonant_no_mutation(top, topu, monosyllable).
consonant_no_mutation(et, eti, monosyllable).
consonant_no_mutation(at, atı, monosyllable).
consonant_no_mutation(ip, ipi, monosyllable).
consonant_no_mutation(üç, üçü, monosyllable).
consonant_no_mutation(saç, saçı, monosyllable).
consonant_no_mutation(süt, sütü, monosyllable).
consonant_no_mutation(ok, oku, monosyllable).
consonant_no_mutation(hukuk, hukuku, loanword).
consonant_no_mutation(sanat, sanatı, loanword).
consonant_no_mutation(sepet, sepeti, loanword).
consonant_no_mutation(cumhuriyet, cumhuriyeti, loanword).
consonant_no_mutation(millet, milleti, loanword).
consonant_no_mutation(devlet, devleti, loanword).
consonant_no_mutation(merak, merakı, loanword).
consonant_no_mutation(bisiklet, bisikleti, loanword).
consonant_no_mutation('Ahmet', "Ahmet'i", proper_noun).
consonant_no_mutation('Mehmet', "Mehmet'i", proper_noun).

% =============================================================================
% ÜNLÜ DÜŞMESİ: vowel_drop(Base, Stem, Result, DroppedVowel).
% İkinci hecedeki dar ünlü düşer: burun → burnu
% =============================================================================
vowel_drop(burun, burn, burnu, 'u').
vowel_drop(ağız, ağz, ağzı, 'ı').
vowel_drop(alın, aln, alnı, 'ı').
vowel_drop(beyin, beyn, beyni, 'i').
vowel_drop(boyun, boyn, boynu, 'u').
vowel_drop(karın, karn, karnı, 'ı').
vowel_drop(göğüs, göğs, göğsü, 'ü').
vowel_drop(oğul, oğl, oğlu, 'u').
vowel_drop(şehir, şehr, şehri, 'i').
vowel_drop(nehir, nehr, nehri, 'i').
vowel_drop(ömür, ömr, ömrü, 'ü').
vowel_drop(akıl, akl, aklı, 'ı').
vowel_drop(fikir, fikr, fikri, 'i').
vowel_drop(isim, ism, ismi, 'i').
vowel_drop(kayın, kayn, kaynı, 'ı').
vowel_drop(zehir, zehr, zehri, 'i').
vowel_drop(çevir, çevr, çevri, 'i').
vowel_drop(devir, devr, devri, 'i').
vowel_drop(ayır, ayr, ayrıl, 'ı').
vowel_drop(çevir, çevr, çevril, 'i').
vowel_drop(kavur, kavr, kavrul, 'u').
vowel_drop(savur, savr, savrul, 'u').

% =============================================================================
% İSİM ÇEKİM EKLERİ: case_suffix(Case, Suffixes, EnglishPrep, HarmonyType).
% Yönelme (to), Bulunma (in/on/at), Ayrılma (from), Belirtme (the), Tamlayan (of)
% =============================================================================
case_suffix(dative, ['e', 'a', 'ye', 'ya'], to, back_front).
case_suffix(locative, ['de', 'da', 'te', 'ta'], 'in/on/at', back_front_voiced).
case_suffix(ablative, ['den', 'dan', 'ten', 'tan'], from, back_front_voiced).
case_suffix(accusative, ['i', 'ı', 'u', 'ü', 'yi', 'yı', 'yu', 'yü'], the, fourfold).
case_suffix(genitive, ['in', 'ın', 'un', 'ün', 'nin', 'nın', 'nun', 'nün'], of, fourfold).
case_suffix(nominative, [''], '', none).

% =============================================================================
% İYELİK EKLERİ: possessive_suffix(Person, Plurality, Suffixes, English).
% my, your, his/her/its, our, their
% =============================================================================
possessive_suffix(1, singular, ['im', 'ım', 'um', 'üm', 'm'], my).
possessive_suffix(2, singular, ['in', 'ın', 'un', 'ün', 'n'], your).
possessive_suffix(3, singular, ['i', 'ı', 'u', 'ü', 'si', 'sı', 'su', 'sü'], 'his/her/its').
possessive_suffix(1, plural, ['imiz', 'ımız', 'umuz', 'ümüz', 'miz', 'mız', 'muz', 'müz'], our).
possessive_suffix(2, plural, ['iniz', 'ınız', 'unuz', 'ünüz', 'niz', 'nız', 'nuz', 'nüz'], 'your (pl.)').
possessive_suffix(3, plural, ['leri', 'ları'], their).

% =============================================================================
% OLUMSUZLUK EKLERİ: negation_suffix(Type, Pattern, EnglishAux).
% -me/-ma, -mez/-maz, değil, yok
% =============================================================================
negation_suffix(verb_general, ['me', 'ma'], not).
negation_suffix(aorist_negative, ['mez', 'maz'], 'does not / do not').
negation_suffix(future_negative, ['meyecek', 'mayacak', 'miyecek', 'mıyacak', 'muyacak', 'müyecek'], 'will not').
negation_suffix(copula_negative, 'değil', 'is not / am not / are not').
negation_suffix(existential_negative, 'yok', '').

% =============================================================================
% SORU EKLERİ: question_particle(Suffixes, HarmonyType).
% -mı/-mi/-mu/-mü
% =============================================================================
question_particle(['mı', 'mi', 'mu', 'mü'], fourfold, _, _).
question_particle(['mıyım', 'miyim', 'muyum', 'müyüm'], fourfold, 1, singular).
question_particle(['mısın', 'misin', 'musun', 'müsün'], fourfold, 2, singular).

% =============================================================================
% EDATLAR: postposition(Turkish, English, Type, CaseRequired).
% ile (with), için (for), kadar (until), gibi (like)
% =============================================================================
postposition('ile', 'with/by', attached, none).
postposition_suffixes('ile', ['la', 'le', 'yla', 'yle']).
postposition('için', for, separate, nominative).
postposition('kadar', 'until/as much as/up to', separate, dative).
postposition('gibi', 'like/as', separate, nominative).
postposition('göre', 'according to', separate, dative).
postposition('doğru', towards, separate, dative).
postposition('karşı', 'against/opposite', separate, dative).
postposition('sonra', after, separate, ablative).
postposition('önce', before, separate, ablative).
postposition('beri', since, separate, ablative).
postposition('rağmen', 'despite/although', separate, dative).

% =============================================================================
% BAĞLAÇLAR: conjunction(Turkish, English, Type).
% ve (and), ama (but), çünkü (because)
% =============================================================================
conjunction(ve, and, coordinating).
conjunction(ile, 'and/with', coordinating).
conjunction(ama, but, coordinating).
conjunction(fakat, 'but/however', coordinating).
conjunction(ancak, 'however/only', coordinating).
conjunction(veya, or, coordinating).
conjunction('ya da', or, coordinating).
conjunction(çünkü, because, subordinating).
conjunction(zira, 'because/for', subordinating).
conjunction(eğer, if, subordinating).
conjunction(şayet, if, subordinating).
conjunction(ise, 'if/as for', subordinating).
conjunction(ki, 'that/so that', subordinating).
conjunction('hem...hem', 'both...and', correlative).
conjunction('ne...ne', 'neither...nor', correlative).
conjunction('ya...ya', 'either...or', correlative).

% =============================================================================
% EK-FİİL EKLERİ: copula_suffix(Person, Plurality, Tense, Suffixes, English).
% İsim cümlelerinde 'to be' karşılığı: öğrenciyim → I am a student
% =============================================================================
copula_suffix(1, singular, present, ['im', 'ım', 'um', 'üm', 'yim', 'yım', 'yum', 'yüm'], am).
copula_suffix(2, singular, present, ['sin', 'sın', 'sun', 'sün'], are).
copula_suffix(3, singular, present, ['dir', 'dır', 'dur', 'dür', 'tir', 'tır', 'tur', 'tür', ''], is).
copula_suffix(1, plural, present, ['iz', 'ız', 'uz', 'üz', 'yiz', 'yız', 'yuz', 'yüz'], are).
copula_suffix(2, plural, present, ['siniz', 'sınız', 'sunuz', 'sünüz'], are).
copula_suffix(3, plural, present, ['dirler', 'dırlar', 'durlar', 'dürler', 'tirler', 'tırlar', 'turlar', 'türler', 'ler', 'lar'], are).
copula_suffix(1, singular, past, ['dim', 'dım', 'dum', 'düm', 'tim', 'tım', 'tum', 'tüm', 'ydim', 'ydım', 'ydum', 'ydüm'], was).
copula_suffix(3, singular, past, ['di', 'dı', 'du', 'dü', 'ti', 'tı', 'tu', 'tü', 'ydi', 'ydı', 'ydu', 'ydü'], was).

% =============================================================================
% ARTICLE KURALLARI: article_rule(Condition, Article).
% Türkçe belirtme eki → İngilizce 'the'; belirtmesiz → 'a/an'
% =============================================================================
article_rule(accusative_suffix, the).
article_rule(no_accusative_suffix, 'a/an').
article_rule(possessive_construction, 'the/possessive').
article_rule(vowel_initial, an).
article_rule(generic_noun, 'no article/the').

% =============================================================================
% KAYNASTIRMA İSTİSNALARI: buffer_exception(Word, BufferConsonant, Cases).
% su → suyun (n yerine y), ne → neyin
% =============================================================================
buffer_exception(su, 'y', ['genitive', 'possessive']).
buffer_exception(ne, 'y', ['genitive']).
buffer_exception(bu, 'n', ['oblique_cases']).
buffer_exception(şu, 'n', ['oblique_cases']).
buffer_exception(o, 'n', ['oblique_cases']).

% =============================================================================
% ÇOĞUL EKLERİ: plural_suffix(Suffixes, HarmonyType).
% -ler (ince ünlü), -lar (kalın ünlü)
% =============================================================================
plural_suffix(['ler', 'lar'], back_front).
plural_harmony(back_vowels, ['a', 'ı', 'o', 'u'], lar).
plural_harmony(front_vowels, ['e', 'i', 'ö', 'ü'], ler).

% =============================================================================
% İSİM KÖKLERİ: noun_root(Turkish, English, EnglishPlural, Category, VowelType).
% ev → house, kitap → book, okul → school
% =============================================================================
noun_root(ev, house, houses, place, front).
noun_root(oda, room, rooms, place, back).
noun_root(okul, school, schools, place, back).
noun_root(hastane, hospital, hospitals, place, front).
noun_root(park, park, parks, place, back).
noun_root(şehir, city, cities, place, front).
noun_root(köy, village, villages, place, front).
noun_root(market, market, markets, place, front).
noun_root(bahçe, garden, gardens, place, front).
noun_root(mutfak, kitchen, kitchens, place, back).
noun_root(kitap, book, books, object, back).
noun_root(kalem, pen, pens, object, front).
noun_root(masa, table, tables, object, back).
noun_root(sandalye, chair, chairs, object, front).
noun_root(araba, car, cars, object, back).
noun_root(telefon, phone, phones, object, back).
noun_root(bilgisayar, computer, computers, object, back).
noun_root(kapı, door, doors, object, back).
noun_root(pencere, window, windows, object, front).
noun_root(anahtar, key, keys, object, back).
noun_root(çocuk, child, children, person, back).
noun_root(adam, man, men, person, back).
noun_root(kadın, woman, women, person, back).
noun_root(öğrenci, student, students, person, front).
noun_root(öğretmen, teacher, teachers, person, front).
noun_root(doktor, doctor, doctors, person, back).
noun_root(arkadaş, friend, friends, person, back).
noun_root(anne, mother, mothers, person, front).
noun_root(baba, father, fathers, person, back).
noun_root(kardeş, sibling, siblings, person, front).
noun_root(kedi, cat, cats, animal, front).
noun_root(köpek, dog, dogs, animal, front).
noun_root(kuş, bird, birds, animal, back).
noun_root(balık, fish, fish, animal, back).
noun_root(at, horse, horses, animal, back).
noun_root(su, water, waters, food, back).
noun_root(ekmek, bread, breads, food, front).
noun_root(elma, apple, apples, food, back).
noun_root(yemek, food, foods, food, front).
noun_root(kahve, coffee, coffees, food, front).
noun_root(iş, work, works, abstract, front).
noun_root(para, money, money, abstract, back).
noun_root(zaman, time, times, abstract, back).
noun_root(gün, day, days, abstract, front).
noun_root(yıl, year, years, abstract, back).
noun_root(ay, month, months, abstract, back).
noun_root(hafta, week, weeks, abstract, back).
noun_root(saat, hour, hours, abstract, back).
noun_root(el, hand, hands, body, front).
noun_root(ayak, foot, feet, body, back).
noun_root(göz, eye, eyes, body, front).
noun_root(baş, head, heads, body, back).
noun_root(kalp, heart, hearts, body, back).
noun_root(yer, ground, grounds, place, front).
noun_root(yol, road, roads, place, back).
noun_root(sokak, street, streets, place, back).
noun_root(deniz, sea, seas, place, front).
noun_root(orman, forest, forests, place, back).
noun_root(dağ, mountain, mountains, place, back).

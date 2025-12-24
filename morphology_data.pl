:- encoding(utf8).
% OTOMATİK OLUŞTURULAN VERİ DOSYASI

noun(ben, i).
noun(sen, you).
noun(o, he/she).
noun(biz, we).
noun(siz, you).
noun(onlar, they).
noun(okul, school).
noun(ev, home).
noun(araba, car).
noun(masa, table).
noun(kitap, book).
noun(kalem, pencil).
noun(bilgisayar, computer).
noun(telefon, phone).
noun(kedi, cat).
noun(köpek, dog).
noun(su, water).
noun(yemek, food).
noun(bahce, garden).
noun(park, park).
noun(kapı, door).
noun(pencere, window).

% 22 isim eklendi.

verb_root(gel, come, irregular).
irregular_verb(come, came, come, coming).
verb_root(git, go, irregular).
irregular_verb(go, went, gone, going).
verb_root(yap, do, irregular).
irregular_verb(do, did, done, doing).
verb_root(ye, eat, irregular).
irregular_verb(eat, ate, eaten, eating).
verb_root(ic, drink, irregular).
irregular_verb(drink, drank, drunk, drinking).
verb_root(al, take, irregular).
irregular_verb(take, took, taken, taking).
verb_root(ver, give, irregular).
irregular_verb(give, gave, given, giving).
verb_root(gor, see, irregular).
irregular_verb(see, saw, seen, seeing).
verb_root(yaz, write, irregular).
irregular_verb(write, wrote, written, writing).
verb_root(oku, read, irregular).
irregular_verb(read, read, read, reading).
verb_root(uyu, sleep, irregular).
irregular_verb(sleep, slept, slept, sleeping).
verb_root(kos, run, irregular).
irregular_verb(run, ran, run, running).
verb_root(yuz, swim, irregular).
irregular_verb(swim, swam, swum, swimming).
verb_root(sev, love, regular).
verb_root(oyna, play, regular).
verb_root(bak, look, regular).
verb_root(calis, work, regular).
verb_root(yuru, walk, regular).
verb_root(konus, talk, regular).
verb_root(dinle, listen, regular).
verb_root(iste, want, regular).
verb_root(kullan, use, regular).
verb_root(ara, call, regular).

% 23 fiil eklendi.

tense_suffix("iyor", present_continuous).
tense_suffix("uyor", present_continuous).
tense_suffix("yor", present_continuous).
tense_suffix("di", past_simple).
tense_suffix("du", past_simple).
tense_suffix("ti", past_simple).
tense_suffix("tu", past_simple).
tense_suffix("ecek", future).
tense_suffix("acak", future).
tense_suffix("eceg", future).
tense_suffix("acag", future).
tense_suffix("er", aorist).
tense_suffix("ar", aorist).
tense_suffix("ir", aorist).
tense_suffix("ur", aorist).
tense_suffix("mis", past_reported).
tense_suffix("mus", past_reported).
tense_suffix("meli", necessity).
tense_suffix("mali", necessity).
tense_suffix("ebil", ability).
tense_suffix("abil", ability).

% --- Şahıs ve Yardımcı Fiiller ---
person_suffix("um", 1, singular, _).
person_suffix("sun", 2, singular, _).
person_suffix("uz", 1, plural, _).
person_suffix("sunuz", 2, plural, _).
person_suffix("lar", 3, plural, _).
person_suffix("m", 1, singular, past_simple).
person_suffix("n", 2, singular, past_simple).
person_suffix("k", 1, plural, past_simple).
auxiliary_verb(present_continuous, 1, singular, false, am).
auxiliary_verb(present_continuous, 3, singular, false, is).
auxiliary_verb(present_continuous, _, _, false, are).
auxiliary_verb(future, _, _, _, will).
auxiliary_verb(past_simple, _, _, true, 'did not').

% --- Türkçe Düzensiz Kökler ---
turkish_irregular_root("gid", git).
turkish_irregular_root("ed", et).
turkish_irregular_root("y", ye).
turkish_irregular_root("diy", de).

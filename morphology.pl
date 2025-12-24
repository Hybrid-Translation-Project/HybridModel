% =============================================================================
    % TÜRKÇE-İNGİLİZCE MORFOLOJİ MODÜLÜ
    % =============================================================================
    %
    % Türkçe fiil çekimlerini analiz eder ve İngilizce'ye dönüştürür.
    %
    % VERİ KAYNAĞI: MongoDB (morphology_data.pl dosyası üzerinden)
    % Veriyi güncellemek için: python morphology_api.py --generate
    %
    % Örnek:
    %   ?- translate_verb(geliyorum, English, Details).
    %   English = "I am coming",
    %   Details = [tense:present_continuous, person:1, plurality:singular]
    %
    % =============================================================================
    :- encoding(utf8).
    :- module(morphology, [
        translate_verb/3,
        translate_noun/3,
        translate_gerund/3,       % Zarf-fiil çevirisi (koşarken → while running)
        translate_question/2,     % Soru cümlesi çevirisi (geldi mi → Did he/she come?)
        translate_word/2,
        translate_sentence/2,
        analyze_turkish/2,
        analyze_noun/2,
        analyze_gerund/2,         % Zarf-fiil analizi
        conjugate_english/6,
        test_morphology/0,
        reload_morphology_data/0
    ]).

    % =============================================================================
    % MONGODB VERİLERİNİ YÜKLE
    % =============================================================================
    % morphology_data.pl dosyası MongoDB'den otomatik oluşturulur.
    % python morphology_api.py --generate komutu ile güncellenir.

    :- consult(morphology_data).

    % Veriyi yeniden yüklemek için (MongoDB güncellendiğinde)
    reload_morphology_data :-
        abolish(verb_root/3),
        abolish(irregular_verb/4),
        abolish(tense_suffix/2),
        abolish(person_suffix/4),
        abolish(turkish_irregular_root/2),
        abolish(auxiliary_verb/5),
        abolish(phonology_rule/5),
        abolish(phonology_condition/3),
        abolish(phonology_action/3),
        consult(morphology_data),
        writeln('[OK] Morfoloji verileri yeniden yüklendi.').

    % =============================================================================
    % TÜRKÇE İSİM MORFOLOJİK ANALİZİ
    % =============================================================================
    % İsim çekim eklerini (hal ekleri, iyelik ekleri, çoğul ekleri) analiz eder.
    %
    % Örnekler:
    %   evde → at house/home (locative)
    %   eve → to house/home (dative)
    %   evden → from house/home (ablative)
    %   evim → my house (possessive 1st singular)
    %   evler → houses (plural)
    %   evdeki → the one at house (locative + relative)
    % =============================================================================

    % analyze_noun(+Word, -Analysis)
    % Analysis = [root:Root, english:English, case:Case, plural:Plural, possessive:Poss]

    analyze_noun(Word, Analysis) :-
        atom_string(Word, WordStr),
        string_lower(WordStr, LowerStr),
        
        % Çoğul kontrolü
        check_plural(LowerStr, SingularStr, IsPlural),
        
        % İyelik kontrolü - kök bulunabilirse iyelik var
        try_possessive_analysis(SingularStr, _AfterPossStr, PossInfo, _RootStr, CaseInfo, TrRoot, EnRoot, EnPlural, Category),
        
        Analysis = [
            root:TrRoot,
            english:EnRoot,
            english_plural:EnPlural,
            case:CaseInfo,
            plural:IsPlural,
            possessive:PossInfo,
            category:Category
        ].

    % İyelik analizi dene - önce hal eki (iyeliksiz), sonra iyelik ekiyle
    % Uzun ek eşleşmelerine öncelik ver

    % KURAL 1: Kombine ekler - Önce hal eki, sonra iyelik eki (evimize = ev + imiz + e)
    try_possessive_analysis(SingularStr, AfterPossStr, PossInfo, RootStr, CaseInfo, TrRoot, EnRoot, EnPlural, Category) :-
        % Önce hal ekini çıkar
        check_case_suffix(SingularStr, AfterCaseStr, CaseInfo),
        CaseInfo \= nominative,
        % Sonra iyelik ekini çıkar
        check_possessive(AfterCaseStr, RootStr, PossInfo),
        PossInfo \= none,
        AfterPossStr = RootStr,  % İyelikten sonra kalan kısım kök
        % Kökü bul
        find_noun_root(RootStr, TrRoot, EnRoot, EnPlural, Category),
        Category \= unknown.

    % KURAL 2: Sadece hal eki (evde, eve, evden)
    try_possessive_analysis(SingularStr, SingularStr, none, RootStr, CaseInfo, TrRoot, EnRoot, EnPlural, Category) :-
        % İyelik eki yok, sadece hal eki
        check_case_suffix(SingularStr, RootStr, CaseInfo),
        CaseInfo \= nominative,
        find_noun_root(RootStr, TrRoot, EnRoot, EnPlural, Category),
        Category \= unknown.

    % KURAL 3: Sadece iyelik eki (evim, kedimiz, evin "your house")
    try_possessive_analysis(SingularStr, AfterPossStr, PossInfo, RootStr, nominative, TrRoot, EnRoot, EnPlural, Category) :-
        % Sadece iyelik ekiyle dene (hal eki yok = nominative)
        check_possessive(SingularStr, AfterPossStr, PossInfo),
        PossInfo \= none,
        % Kalan kısım doğrudan kök olmalı
        find_noun_root(AfterPossStr, TrRoot, EnRoot, EnPlural, Category),
        atom_string(TrRoot, RootStr),
        Category \= unknown.

    % KURAL 4: Sadece kök (ev, kedi)
    try_possessive_analysis(SingularStr, SingularStr, none, RootStr, nominative, TrRoot, EnRoot, EnPlural, Category) :-
        find_noun_root(SingularStr, TrRoot, EnRoot, EnPlural, Category),
        atom_string(TrRoot, RootStr),
        Category \= unknown.

    % KURAL 5: Hiçbir şey bulunamadı - olduğu gibi döndür
    try_possessive_analysis(SingularStr, SingularStr, none, SingularStr, nominative, SingularAtom, SingularAtom, SingularAtom, unknown) :-
        atom_string(SingularAtom, SingularStr).

    % Çoğul eki kontrolü
    check_plural(WordStr, SingularStr, true) :-
        (   sub_string(WordStr, _, 3, 0, "ler")
        ;   sub_string(WordStr, _, 3, 0, "lar")
        ),
        string_length(WordStr, Len),
        BaseLen is Len - 3,
        BaseLen > 0,
        sub_string(WordStr, 0, BaseLen, 3, SingularStr),
        !.

    check_plural(WordStr, WordStr, false).

    % İyelik eki kontrolü - cut'suz versiyon (backtracking için)
    % 1. çoğul ünsüz ile biten kökler: -imiz, -ımız, -umuz, -ümüz (4 karakter)
    check_possessive(WordStr, RootStr, poss(1, plural)) :-
        string_length(WordStr, Len),
        Len > 4,
        (   sub_string(WordStr, _, 4, 0, "imiz")
        ;   sub_string(WordStr, _, 4, 0, "ımız")
        ;   sub_string(WordStr, _, 4, 0, "umuz")
        ;   sub_string(WordStr, _, 4, 0, "ümüz")
        ),
        BaseLen is Len - 4,
        sub_string(WordStr, 0, BaseLen, 4, RootStr).

    % 1. çoğul ünlü ile biten kökler: -miz, -mız, -muz, -müz (3 karakter)
    check_possessive(WordStr, RootStr, poss(1, plural)) :-
        string_length(WordStr, Len),
        Len > 3,
        (   sub_string(WordStr, _, 3, 0, "miz")
        ;   sub_string(WordStr, _, 3, 0, "mız")
        ;   sub_string(WordStr, _, 3, 0, "muz")
        ;   sub_string(WordStr, _, 3, 0, "müz")
        ),
        BaseLen is Len - 3,
        sub_string(WordStr, 0, BaseLen, 3, RootStr).

    % 2. çoğul: -iniz, -ınız, -unuz, -ünüz (4 karakter)
    check_possessive(WordStr, RootStr, poss(2, plural)) :-
        string_length(WordStr, Len),
        Len > 4,
        (   sub_string(WordStr, _, 4, 0, "iniz")
        ;   sub_string(WordStr, _, 4, 0, "ınız")
        ;   sub_string(WordStr, _, 4, 0, "unuz")
        ;   sub_string(WordStr, _, 4, 0, "ünüz")
        ),
        BaseLen is Len - 4,
        sub_string(WordStr, 0, BaseLen, 4, RootStr).

    % 2. çoğul ünlü ile biten kökler: -niz, -nız, -nuz, -nüz (3 karakter)
    check_possessive(WordStr, RootStr, poss(2, plural)) :-
        string_length(WordStr, Len),
        Len > 3,
        (   sub_string(WordStr, _, 3, 0, "niz")
        ;   sub_string(WordStr, _, 3, 0, "nız")
        ;   sub_string(WordStr, _, 3, 0, "nuz")
        ;   sub_string(WordStr, _, 3, 0, "nüz")
        ),
        BaseLen is Len - 3,
        sub_string(WordStr, 0, BaseLen, 3, RootStr).

    % 3. çoğul: -leri, -ları (4 karakter)
    check_possessive(WordStr, RootStr, poss(3, plural)) :-
        string_length(WordStr, Len),
        Len > 4,
        (   sub_string(WordStr, _, 4, 0, "leri")
        ;   sub_string(WordStr, _, 4, 0, "ları")
        ),
        BaseLen is Len - 4,
        sub_string(WordStr, 0, BaseLen, 4, RootStr).

    % 1. tekil: -im, -ım, -um, -üm (2 karakter)
    check_possessive(WordStr, RootStr, poss(1, singular)) :-
        string_length(WordStr, Len),
        Len > 2,
        (   sub_string(WordStr, _, 2, 0, "im")
        ;   sub_string(WordStr, _, 2, 0, "ım")
        ;   sub_string(WordStr, _, 2, 0, "um")
        ;   sub_string(WordStr, _, 2, 0, "üm")
        ),
        BaseLen is Len - 2,
        sub_string(WordStr, 0, BaseLen, 2, RootStr).

    % 1. tekil ünlü ile biten kökler: -m (1 karakter)
    check_possessive(WordStr, RootStr, poss(1, singular)) :-
        string_length(WordStr, Len),
        Len > 1,
        sub_string(WordStr, _, 1, 0, "m"),
        BaseLen is Len - 1,
        sub_string(WordStr, 0, BaseLen, 1, RootStr).

    % 2. tekil: -in, -ın, -un, -ün (2 karakter)
    check_possessive(WordStr, RootStr, poss(2, singular)) :-
        string_length(WordStr, Len),
        Len > 2,
        (   sub_string(WordStr, _, 2, 0, "in")
        ;   sub_string(WordStr, _, 2, 0, "ın")
        ;   sub_string(WordStr, _, 2, 0, "un")
        ;   sub_string(WordStr, _, 2, 0, "ün")
        ),
        BaseLen is Len - 2,
        sub_string(WordStr, 0, BaseLen, 2, RootStr).

    % 2. tekil ünlü ile biten kökler: -n (1 karakter)
    check_possessive(WordStr, RootStr, poss(2, singular)) :-
        string_length(WordStr, Len),
        Len > 1,
        sub_string(WordStr, _, 1, 0, "n"),
        BaseLen is Len - 1,
        sub_string(WordStr, 0, BaseLen, 1, RootStr).

    % 3. tekil: -si, -sı, -su, -sü (2 karakter)
    check_possessive(WordStr, RootStr, poss(3, singular)) :-
        string_length(WordStr, Len),
        Len > 2,
        (   sub_string(WordStr, _, 2, 0, "si")
        ;   sub_string(WordStr, _, 2, 0, "sı")
        ;   sub_string(WordStr, _, 2, 0, "su")
        ;   sub_string(WordStr, _, 2, 0, "sü")
        ),
        BaseLen is Len - 2,
        sub_string(WordStr, 0, BaseLen, 2, RootStr).

    % 3. tekil: -i, -ı, -u, -ü (1 karakter)
    check_possessive(WordStr, RootStr, poss(3, singular)) :-
        string_length(WordStr, Len),
        Len > 1,
        (   sub_string(WordStr, _, 1, 0, "i")
        ;   sub_string(WordStr, _, 1, 0, "ı")
        ;   sub_string(WordStr, _, 1, 0, "u")
        ;   sub_string(WordStr, _, 1, 0, "ü")
        ),
        BaseLen is Len - 1,
        sub_string(WordStr, 0, BaseLen, 1, RootStr).

    % İyelik eki yok
    check_possessive(WordStr, WordStr, none).

    % Hal eki kontrolü - cut'suz versiyon (backtracking için)
    check_case_suffix(WordStr, RootStr, locative) :-
        string_length(WordStr, Len),
        Len > 2,
        (   sub_string(WordStr, _, 2, 0, "de")
        ;   sub_string(WordStr, _, 2, 0, "da")
        ;   sub_string(WordStr, _, 2, 0, "te")
        ;   sub_string(WordStr, _, 2, 0, "ta")
        ),
        BaseLen is Len - 2,
        sub_string(WordStr, 0, BaseLen, 2, RootStr).

    check_case_suffix(WordStr, RootStr, ablative) :-
        string_length(WordStr, Len),
        Len > 3,
        (   sub_string(WordStr, _, 3, 0, "den")
        ;   sub_string(WordStr, _, 3, 0, "dan")
        ;   sub_string(WordStr, _, 3, 0, "ten")
        ;   sub_string(WordStr, _, 3, 0, "tan")
        ),
        BaseLen is Len - 3,
        sub_string(WordStr, 0, BaseLen, 3, RootStr).

    check_case_suffix(WordStr, RootStr, dative) :-
        string_length(WordStr, Len),
        Len > 2,
        (   sub_string(WordStr, _, 2, 0, "ye")
        ;   sub_string(WordStr, _, 2, 0, "ya")
        ),
        BaseLen is Len - 2,
        sub_string(WordStr, 0, BaseLen, 2, RootStr).

    check_case_suffix(WordStr, RootStr, dative) :-
        string_length(WordStr, Len),
        Len > 1,
        (   sub_string(WordStr, _, 1, 0, "e")
        ;   sub_string(WordStr, _, 1, 0, "a")
        ),
        BaseLen is Len - 1,
        sub_string(WordStr, 0, BaseLen, 1, RootStr).

    check_case_suffix(WordStr, RootStr, accusative) :-
        string_length(WordStr, Len),
        Len > 2,
        (   sub_string(WordStr, _, 2, 0, "yi")
        ;   sub_string(WordStr, _, 2, 0, "yı")
        ;   sub_string(WordStr, _, 2, 0, "yu")
        ;   sub_string(WordStr, _, 2, 0, "yü")
        ),
        BaseLen is Len - 2,
        sub_string(WordStr, 0, BaseLen, 2, RootStr).

    check_case_suffix(WordStr, RootStr, accusative) :-
        string_length(WordStr, Len),
        Len > 1,
        (   sub_string(WordStr, _, 1, 0, "i")
        ;   sub_string(WordStr, _, 1, 0, "ı")
        ;   sub_string(WordStr, _, 1, 0, "u")
        ;   sub_string(WordStr, _, 1, 0, "ü")
        ),
        BaseLen is Len - 1,
        sub_string(WordStr, 0, BaseLen, 1, RootStr).

    check_case_suffix(WordStr, RootStr, genitive) :-
        string_length(WordStr, Len),
        Len > 3,
        (   sub_string(WordStr, _, 3, 0, "nin")
        ;   sub_string(WordStr, _, 3, 0, "nın")
        ;   sub_string(WordStr, _, 3, 0, "nun")
        ;   sub_string(WordStr, _, 3, 0, "nün")
        ),
        BaseLen is Len - 3,
        sub_string(WordStr, 0, BaseLen, 3, RootStr).

    check_case_suffix(WordStr, RootStr, genitive) :-
        string_length(WordStr, Len),
        Len > 2,
        (   sub_string(WordStr, _, 2, 0, "in")
        ;   sub_string(WordStr, _, 2, 0, "ın")
        ;   sub_string(WordStr, _, 2, 0, "un")
        ;   sub_string(WordStr, _, 2, 0, "ün")
        ),
        BaseLen is Len - 2,
        sub_string(WordStr, 0, BaseLen, 2, RootStr).

    % Nominative - ek yok (en sonda olmalı)
    check_case_suffix(WordStr, WordStr, nominative).

    % İsim kökü bulma
    find_noun_root(RootStr, TrRoot, EnRoot, EnPlural, Category) :-
        noun_root(TrRoot, EnRoot, EnPlural, Category, _),
        atom_string(TrRoot, TrRootStr),
        RootStr = TrRootStr,
        !.

    find_noun_root(RootStr, TrRoot, EnRoot, EnPlural, Category) :-
        % Ünsüz yumuşaması kontrolü: kitabı → kitap (b → p)
        string_length(RootStr, Len),
        Len > 0,
        LastIdx is Len - 1,
        sub_string(RootStr, LastIdx, 1, 0, LastChar),
        unsoften_consonant(LastChar, HardChar),
        sub_string(RootStr, 0, LastIdx, 1, RootBase),
        string_concat(RootBase, HardChar, HardRootStr),
        noun_root(TrRoot, EnRoot, EnPlural, Category, _),
        atom_string(TrRoot, TrRootStr),
        HardRootStr = TrRootStr,
        !.

    find_noun_root(RootStr, RootAtom, RootAtom, RootAtom, unknown) :-
        % Bilinmeyen kök - olduğu gibi döndür
        atom_string(RootAtom, RootStr).

    % Ünsüz sertleştirme (yumuşamanın tersi)
    unsoften_consonant("b", "p").
    unsoften_consonant("c", "ç").
    unsoften_consonant("d", "t").
    unsoften_consonant("ğ", "k").
    unsoften_consonant("g", "k").

    % =============================================================================
    % TÜRKÇE İSİM ÇEVİRİSİ
    % =============================================================================

    % translate_noun(+TurkishNoun, -EnglishTranslation, -Details)
    translate_noun(TurkishNoun, EnglishTranslation, Details) :-
        analyze_noun(TurkishNoun, Analysis),
        
        % Analiz sonuçlarını çıkar
        member(root:_TrRoot, Analysis),
        member(english:EnRoot, Analysis),
        member(english_plural:EnPlural, Analysis),
        member(case:Case, Analysis),
        member(plural:IsPlural, Analysis),
        member(possessive:PossInfo, Analysis),
        
        % İngilizce çeviri oluştur
        build_noun_translation(EnRoot, EnPlural, Case, IsPlural, PossInfo, EnglishTranslation),
        
        Details = Analysis.

    % İngilizce isim çevirisi oluşturma
    build_noun_translation(EnRoot, EnPlural, Case, IsPlural, PossInfo, Translation) :-
        % Temel isim (tekil/çoğul)
        (IsPlural = true -> BaseNoun = EnPlural ; BaseNoun = EnRoot),
        
        % İyelik öneki
        (   PossInfo = poss(Person, Plurality)
        ->  get_possessive_pronoun(Person, Plurality, PossPron),
            atom_concat(PossPron, ' ', PossPart)
        ;   PossPart = ''
        ),
        
        % Hal eki (preposition)
        get_case_preposition(Case, Prep),
        
        % Birleştir
        (   Prep = ''
        ->  atom_concat(PossPart, BaseNoun, Translation)
        ;   atom_concat(Prep, ' ', PrepSpace),
            atom_concat(PrepSpace, PossPart, Temp1),
            atom_concat(Temp1, BaseNoun, Translation)
        ).

    % İyelik zamirleri
    get_possessive_pronoun(1, singular, my).
    get_possessive_pronoun(2, singular, your).
    get_possessive_pronoun(3, singular, 'his/her').
    get_possessive_pronoun(1, plural, our).
    get_possessive_pronoun(2, plural, your).
    get_possessive_pronoun(3, plural, their).

    % Hal eki → İngilizce preposition
    get_case_preposition(nominative, '').
    get_case_preposition(accusative, the).       % Belirtme hali → the
    get_case_preposition(dative, to).            % Yönelme hali → to
    get_case_preposition(locative, at).          % Bulunma hali → at/in/on
    get_case_preposition(ablative, from).        % Ayrılma hali → from
    get_case_preposition(genitive, 'of').        % Tamlayan hali → of

    % =============================================================================
    % ZARF-FİİL (GERUND/ADVERBIAL) ANALİZİ
    % =============================================================================
    % Türkçe zarf-fiil eklerini analiz eder ve İngilizce'ye dönüştürür.
    %
    % Desteklenen ekler:
    %   -arken/-erken/-ırken/-irken/-urken/-ürken: koşarken → while running
    %   -arak/-erek: koşarak → by running
    %   -ınca/-ince/-unca/-ünce: gelince → when coming
    %   -madan/-meden: gelmeden → without coming
    %   -dığında/-diğinde/-duğunda/-düğünde: geldiğinde → when he/she came
    %   -ken (tek başına): yürürken → while walking
    % =============================================================================

    % analyze_gerund(+Word, -Analysis)
    % Analysis = [root:Root, english_root:EnRoot, gerund_type:Type, translation:Trans]
    analyze_gerund(Word, Analysis) :-
        atom_string(Word, WordStr),
        string_lower(WordStr, LowerStr),
        check_gerund_suffix(LowerStr, RootStr, GerundType),
        atom_string(RootAtom, RootStr),
        find_verb_root_safe(RootAtom, TrRoot, EnRoot),
        get_gerund_translation(EnRoot, GerundType, Translation),
        Analysis = [
            root:TrRoot,
            english_root:EnRoot,
            gerund_type:GerundType,
            translation:Translation
        ].

    % Fiil kökü bulma (güvenli versiyon - başarısız olursa olduğu gibi döndür)
    find_verb_root_safe(RootAtom, TrRoot, EnRoot) :-
        % Önce türkçe düzensiz kökleri dene
        atom_string(RootAtom, RootStr),
        turkish_irregular_root(RootStr, TrRoot),
        verb_root(TrRoot, EnRoot, _),
        !.

    find_verb_root_safe(RootAtom, TrRoot, EnRoot) :-
        verb_root(RootAtom, EnRoot, _),
        TrRoot = RootAtom,
        !.

    % Ünlü ile biten kökler için: "ok" bulunamadıysa "oku" dene
    find_verb_root_safe(RootAtom, TrRoot, EnRoot) :-
        atom_string(RootAtom, RootStr),
        % Farklı ünlü ekleri dene
        member(Vowel, ["u", "ü", "ı", "i", "a", "e"]),
        string_concat(RootStr, Vowel, ExtendedStr),
        atom_string(ExtendedAtom, ExtendedStr),
        verb_root(ExtendedAtom, EnRoot, _),
        TrRoot = ExtendedAtom,
        !.

    find_verb_root_safe(RootAtom, RootAtom, RootAtom).

    % Zarf-fiil eklerini kontrol et ve kökü çıkar
    % KURAL 1: -arken/-erken/-ırken/-irken/-urken/-ürken (while doing)
    check_gerund_suffix(WordStr, RootStr, while) :-
        string_length(WordStr, Len),
        Len > 5,
        (   sub_string(WordStr, _, 5, 0, "arken")
        ;   sub_string(WordStr, _, 5, 0, "erken")
        ;   sub_string(WordStr, _, 5, 0, "ırken")
        ;   sub_string(WordStr, _, 5, 0, "irken")
        ;   sub_string(WordStr, _, 5, 0, "urken")
        ;   sub_string(WordStr, _, 5, 0, "ürken")
        ),
        BaseLen is Len - 5,
        sub_string(WordStr, 0, BaseLen, 5, RootStr),
        !.

    % KURAL 2: -yorken (present continuous + while)
    check_gerund_suffix(WordStr, RootStr, while) :-
        string_length(WordStr, Len),
        Len > 6,
        sub_string(WordStr, _, 6, 0, "yorken"),
        BaseLen is Len - 6,
        sub_string(WordStr, 0, BaseLen, 6, TempRootStr),
        % Bağlayıcı ünlüyü de çıkar (okuyor → oku)
        (   string_length(TempRootStr, TempLen),
            TempLen > 0,
            LastIdx is TempLen - 1,
            sub_string(TempRootStr, LastIdx, 1, 0, LastChar),
            member(LastChar, ["i", "ı", "u", "ü"])
        ->  sub_string(TempRootStr, 0, LastIdx, 1, RootStr)
        ;   RootStr = TempRootStr
        ),
        !.

    % KURAL 3: -ken (yürürken gibi, geniş zaman + ken)
    check_gerund_suffix(WordStr, RootStr, while) :-
        string_length(WordStr, Len),
        Len > 3,
        sub_string(WordStr, _, 3, 0, "ken"),
        \+ sub_string(WordStr, _, 5, 0, "arken"),
        \+ sub_string(WordStr, _, 5, 0, "erken"),
        \+ sub_string(WordStr, _, 6, 0, "yorken"),
        BaseLen is Len - 3,
        sub_string(WordStr, 0, BaseLen, 3, BeforeKen),
        % Geniş zaman ekini çıkar (koşar → koş, gelir → gel)
        remove_aorist_suffix(BeforeKen, RootStr),
        !.

    % KURAL 4: -arak/-erek/-yarak/-yerek (by doing)
    check_gerund_suffix(WordStr, RootStr, by) :-
        string_length(WordStr, Len),
        Len > 5,
        % -yarak / -yerek (bağlayıcı ünsüz ile)
        (   sub_string(WordStr, _, 5, 0, "yarak")
        ;   sub_string(WordStr, _, 5, 0, "yerek")
        ),
        BaseLen is Len - 5,
        sub_string(WordStr, 0, BaseLen, 5, RootStr),
        !.

    check_gerund_suffix(WordStr, RootStr, by) :-
        string_length(WordStr, Len),
        Len > 4,
        (   sub_string(WordStr, _, 4, 0, "arak")
        ;   sub_string(WordStr, _, 4, 0, "erek")
        ),
        BaseLen is Len - 4,
        sub_string(WordStr, 0, BaseLen, 4, RootStr),
        !.

    % KURAL 5: -ınca/-ince/-unca/-ünce (when doing)
    check_gerund_suffix(WordStr, RootStr, when) :-
        string_length(WordStr, Len),
        Len > 4,
        (   sub_string(WordStr, _, 4, 0, "ınca")
        ;   sub_string(WordStr, _, 4, 0, "ince")
        ;   sub_string(WordStr, _, 4, 0, "unca")
        ;   sub_string(WordStr, _, 4, 0, "ünce")
        ),
        BaseLen is Len - 4,
        sub_string(WordStr, 0, BaseLen, 4, RootStr),
        !.

    % KURAL 6: -madan/-meden (without doing)
    check_gerund_suffix(WordStr, RootStr, without) :-
        string_length(WordStr, Len),
        Len > 5,
        (   sub_string(WordStr, _, 5, 0, "madan")
        ;   sub_string(WordStr, _, 5, 0, "meden")
        ),
        BaseLen is Len - 5,
        sub_string(WordStr, 0, BaseLen, 5, RootStr),
        !.

    % Geniş zaman ekini çıkar
    remove_aorist_suffix(WordStr, RootStr) :-
        string_length(WordStr, Len),
        Len > 2,
        (   sub_string(WordStr, _, 2, 0, "ar")
        ;   sub_string(WordStr, _, 2, 0, "er")
        ;   sub_string(WordStr, _, 2, 0, "ır")
        ;   sub_string(WordStr, _, 2, 0, "ir")
        ;   sub_string(WordStr, _, 2, 0, "ur")
        ;   sub_string(WordStr, _, 2, 0, "ür")
        ),
        BaseLen is Len - 2,
        sub_string(WordStr, 0, BaseLen, 2, RootStr),
        !.

    remove_aorist_suffix(WordStr, RootStr) :-
        string_length(WordStr, Len),
        Len > 1,
        (   sub_string(WordStr, _, 1, 0, "r")
        ),
        BaseLen is Len - 1,
        sub_string(WordStr, 0, BaseLen, 1, RootStr),
        !.

    remove_aorist_suffix(WordStr, WordStr).

    % Zarf-fiil tipine göre İngilizce çeviri oluştur
    get_gerund_translation(EnRoot, while, Translation) :-
        get_present_participle(EnRoot, Participle),
        format(atom(Translation), "while ~w", [Participle]).

    get_gerund_translation(EnRoot, by, Translation) :-
        get_present_participle(EnRoot, Participle),
        format(atom(Translation), "by ~w", [Participle]).

    get_gerund_translation(EnRoot, when, Translation) :-
        get_present_participle(EnRoot, Participle),
        format(atom(Translation), "when ~w", [Participle]).

    get_gerund_translation(EnRoot, without, Translation) :-
        get_present_participle(EnRoot, Participle),
        format(atom(Translation), "without ~w", [Participle]).

    % translate_gerund(+TurkishWord, -EnglishTranslation, -Details)
    translate_gerund(TurkishWord, EnglishTranslation, Details) :-
        analyze_gerund(TurkishWord, Analysis),
        member(translation:EnglishTranslation, Analysis),
        Details = Analysis.

    % =============================================================================
    % GENEL KELİME ÇEVİRİSİ (FİİL VEYA İSİM VEYA ZARF-FİİL)
    % =============================================================================

    % translate_word(+TurkishWord, -EnglishTranslation)
    translate_word(TurkishWord, EnglishTranslation) :-
        % Önce zarf-fiil olarak dene (-ken, -arak, vs.)
        (   translate_gerund(TurkishWord, EnglishTranslation, _)
        ->  true
        % Sonra fiil olarak dene
        ;   translate_verb(TurkishWord, EnglishTranslation, _)
        ->  true
        % Sonra isim olarak dene
        ;   translate_noun(TurkishWord, EnglishTranslation, _)
        ->  true
        % Hiçbiri değilse olduğu gibi döndür
        ;   EnglishTranslation = TurkishWord
        ).

    % =============================================================================
    % İNGİLİZCE ÖZNE ZAMİRLERİ (Sabit - MongoDB'ye taşınabilir)
    % =============================================================================

    % subject_pronoun(Person, Plurality, Pronoun).
    subject_pronoun(1, singular, 'I').
    subject_pronoun(2, singular, you).
    subject_pronoun(3, singular, 'he/she').
    subject_pronoun(1, plural, we).
    subject_pronoun(2, plural, you).
    subject_pronoun(3, plural, they).

    % =============================================================================
    % TÜRKÇE MORFOLOJİK ANALİZ
    % =============================================================================

    % analyze_turkish(+Word, -Analysis)
    % Analysis = [root:Root, tense:Tense, person:Person, plurality:Plurality, negation:Neg]

    analyze_turkish(Word, Analysis) :-
        atom_string(Word, WordStr),
        string_lower(WordStr, LowerStr),
        atom_string(LowerWord, LowerStr),
        
        % Olumsuzluk kontrolü
        check_negation(LowerWord, CleanWord, Negation),
        
        % Zaman ve kök analizi
        find_tense_and_root(CleanWord, Root, Tense, Remainder),
        
        % Şahıs analizi
        find_person(Remainder, Tense, Person, Plurality),
        
        Analysis = [
            root:Root,
            tense:Tense,
            person:Person,
            plurality:Plurality,
            negation:Negation
        ].

    % Olumsuzluk kontrolü
    check_negation(Word, CleanWord, true) :-
        atom_string(Word, WordStr),
        % -miyor, -mıyor pattern + şahıs ekleri
        (   sub_string(WordStr, Before, _, After, "miyor")
        ;   sub_string(WordStr, Before, _, After, "muyor")
        ),
        Before > 0,
        sub_string(WordStr, 0, Before, _, RootPart),
        sub_string(WordStr, _, After, 0, PersonPart),
        % 'm' harfini kaldır ve 'iyor' + şahıs ekleri
        string_concat(RootPart, "iyor", TempStr),
        string_concat(TempStr, PersonPart, NewWordStr),
        atom_string(CleanWord, NewWordStr),
        !.

    check_negation(Word, CleanWord, true) :-
        atom_string(Word, WordStr),
        % -medi, -madı pattern
        (   sub_string(WordStr, Before, 4, After, "medi")
        ;   sub_string(WordStr, Before, 4, After, "madı")
        ;   sub_string(WordStr, Before, 4, After, "madi")
        ),
        Before > 0,
        sub_string(WordStr, 0, Before, _, RootPart),
        sub_string(WordStr, _, After, 0, PersonPart),
        string_concat(RootPart, "di", TempStr),
        string_concat(TempStr, PersonPart, NewWordStr),
        atom_string(CleanWord, NewWordStr),
        !.

    check_negation(Word, CleanWord, true) :-
        atom_string(Word, WordStr),
        % -meyecek, -mayacak pattern
        (   sub_string(WordStr, Before, 7, After, "meyecek")
        ;   sub_string(WordStr, Before, 7, After, "mayacak")
        ),
        Before > 0,
        sub_string(WordStr, 0, Before, _, RootPart),
        sub_string(WordStr, _, After, 0, PersonPart),
        (   sub_string(WordStr, _, _, _, "meyecek") 
        ->  string_concat(RootPart, "ecek", TempStr)
        ;   string_concat(RootPart, "acak", TempStr)
        ),
        string_concat(TempStr, PersonPart, NewWordStr),
        atom_string(CleanWord, NewWordStr),
        !.

    check_negation(Word, CleanWord, true) :-
        atom_string(Word, WordStr),
        % -mez, -maz pattern (geniş zaman olumsuz)
        (   sub_string(WordStr, Before, 3, After, "mez")
        ;   sub_string(WordStr, Before, 3, After, "maz")
        ),
        Before > 0,
        sub_string(WordStr, 0, Before, _, RootPart),
        sub_string(WordStr, _, After, 0, PersonPart),
        (   sub_string(WordStr, _, _, _, "mez")
        ->  string_concat(RootPart, "er", TempStr)
        ;   string_concat(RootPart, "ar", TempStr)
        ),
        string_concat(TempStr, PersonPart, NewWordStr),
        atom_string(CleanWord, NewWordStr),
        !.

    check_negation(Word, Word, false).

    % Zaman ve kök bulma
    find_tense_and_root(Word, Root, Tense, Remainder) :-
        atom_string(Word, WordStr),
        tense_suffix(TenseSuffix, Tense),
        atom_string(TenseSuffix, TenseSuffixStr),
        string_length(TenseSuffixStr, TenseLen),
        TenseLen > 0,
        sub_string(WordStr, Before, TenseLen, After, TenseSuffixStr),
        Before > 0,
        sub_string(WordStr, 0, Before, _, RootStr),
        sub_string(WordStr, _, After, 0, RemainderStr),
        % Kökü doğrula
        find_matching_root(RootStr, Root),
        atom_string(Remainder, RemainderStr).
        % Cut kaldırıldı - alternatif çözümler için backtrack

    % Ünlü ile biten kökler için: oku + yor = okuy + or → "yor" suffix ile dene
    find_tense_and_root(Word, Root, Tense, Remainder) :-
        atom_string(Word, WordStr),
        % yor pattern'ı ara ama kökte bağlayıcı ünlü olabilir
        sub_string(WordStr, Before, 3, After, "yor"),
        Before > 0,
        sub_string(WordStr, 0, Before, _, RootWithVowelStr),
        sub_string(WordStr, _, After, 0, RemainderStr),
        % Son karakteri kontrol et (bağlayıcı ünlü mü?)
        string_length(RootWithVowelStr, RootLen),
        RootLen > 0,
        PrevLen is RootLen - 1,
        sub_string(RootWithVowelStr, PrevLen, 1, 0, LastChar),
        member(LastChar, ["i", "u", "ı", "ü"]),
        % Bağlayıcı ünlüyü çıkar
        sub_string(RootWithVowelStr, 0, PrevLen, _, TrueRootStr),
        find_matching_root(TrueRootStr, Root),
        Tense = present_continuous,
        atom_string(Remainder, RemainderStr),
        !.

    % Kök eşleştirme
    find_matching_root(RootStr, Root) :-
        % Önce Türkçe düzensiz fiil alternatifleri kontrol et
        turkish_irregular_root(RootStr, Root),
        !.

    % --- BURASI EKLENDI (Ünlü Daralması Kurtarma) ---
    find_matching_root(RootStr, Root) :-
        % Ünlü daralması: dinl -> dinle, başl -> başla
        member(Vowel, ["e", "a"]),
        string_concat(RootStr, Vowel, RecoveredStr),
        atom_string(RecoveredAtom, RecoveredStr),
        verb_root(RecoveredAtom, _, _),
        Root = RecoveredAtom,
        !.
    % ------------------------------------------------

    find_matching_root(RootStr, Root) :-
        verb_root(Root, _, _),
        atom_string(Root, RootAtomStr),
        (   RootStr = RootAtomStr
        ;   % Ünlü uyumu - son birkaç karakter eşleşebilir
            string_length(RootAtomStr, RootLen),
            string_length(RootStr, InputLen),
            InputLen >= RootLen,
            Diff is InputLen - RootLen,
            Diff =< 2,
            sub_string(RootStr, Diff, RootLen, 0, RootAtomStr)
        ),
        !.

    find_matching_root(RootStr, Root) :-
        atom_string(Root, RootStr).

    % NOT: turkish_irregular_root/2 artık morphology_data.pl'den geliyor

    % Şahıs bulma
    find_person(Remainder, Tense, Person, Plurality) :-
        person_suffix(Suffix, Person, Plurality, Tense),
        atom_string(Suffix, SuffixStr),
        atom_string(Remainder, RemainderStr),
        (   SuffixStr = ""
        ->  RemainderStr = ""
        ;   sub_string(RemainderStr, _, _, 0, SuffixStr)
        ),
        !.

    find_person(_, _, 3, singular).  % Default: 3. tekil şahıs

    % =============================================================================
    % İNGİLİZCE FİİL ÇEKİMİ
    % =============================================================================

    % conjugate_english(+Verb, +Tense, +Person, +Plurality, +Negation, -Conjugated)
    conjugate_english(Verb, Tense, Person, Plurality, Negation, Result) :-
        get_verb_form(Verb, Tense, Person, Plurality, Negation, VerbForm),
        subject_pronoun(Person, Plurality, Subject),
        build_sentence(Subject, Tense, Person, Plurality, Negation, VerbForm, Result).

    % Fiil formunu al
    get_verb_form(Verb, present_continuous, _, _, _, VerbForm) :-
        get_present_participle(Verb, VerbForm).

    get_verb_form(Verb, past_simple, Person, _, false, VerbForm) :-
        get_past_simple(Verb, Person, VerbForm).

    get_verb_form(Verb, past_simple, _, _, true, Verb).  % did not + base form

    get_verb_form(Verb, future, _, _, _, Verb).  % will + base form

    get_verb_form(Verb, aorist, Person, Plurality, false, VerbForm) :-
        get_present_simple(Verb, Person, Plurality, VerbForm).

    get_verb_form(Verb, aorist, _, _, true, Verb).  % do/does not + base form

    get_verb_form(Verb, past_reported, _, _, _, VerbForm) :-
        get_past_participle(Verb, VerbForm).

    get_verb_form(Verb, necessity, _, _, _, Verb).  % should + base form

    get_verb_form(Verb, ability, _, _, _, Verb).  % can + base form

    % Past Continuous: was/were + V-ing (Present Participle kullanılır)
    get_verb_form(Verb, past_continuous, _, _, _, VerbForm) :-
        get_present_participle(Verb, VerbForm).

    % Present Participle (V-ing)
    get_present_participle(Verb, Participle) :-
        irregular_verb(Verb, _, _, Participle),
        !.

% =============================================================================
    % PRESENT PARTICIPLE (V-ing) KURALI
    % =============================================================================
    
    get_present_participle(Verb, Participle) :-
        irregular_verb(Verb, _, _, Participle),
        !.

    get_present_participle(Verb, Participle) :-
        atom_string(Verb, VerbStr),
        (   
            % 1. -e ile bitenler (ee hariç): make -> making, write -> writing
            string_concat(Base, "e", VerbStr),
            \+ string_concat(_, "ee", VerbStr)
        ->  string_concat(Base, "ing", PartStr)
        
        ;   % 2. -ie ile bitenler: lie -> lying, die -> dying
            string_concat(Base, "ie", VerbStr)
        ->  string_concat(Base, "ying", PartStr)
        
        ;   % 3.Çift ünlü + ünsüz (wait -> waiting, eat -> eating)
            % İkizleme YAPMA!
            string_length(VerbStr, Len), Len >= 3,
            sub_string(VerbStr, _, 3, 0, LastThree), % Son 3 harfi al
            string_chars(LastThree, [V1, V2, C]),    % Harflere böl
            member(V1String, ["a","e","i","o","u"]), atom_string(V1, V1String), % İlk harf ünlü
            member(V2String, ["a","e","i","o","u"]), atom_string(V2, V2String), % İkinci harf ünlü
            is_consonant(C)                          % Üçüncü harf ünsüz
        ->  string_concat(VerbStr, "ing", PartStr)

        ;   % 4. "LISTEN" FIX: Sonu 'en', 'el' ile biten çok hecelilerde ikizleme olmaz
            % (listen -> listening, open -> opening, happen -> happening)
            % Burası "listenning" hatasını çözen yer.
            (   sub_string(VerbStr, _, 2, 0, "en")
            ;   sub_string(VerbStr, _, 2, 0, "on") % iron -> ironing
            ;   sub_string(VerbStr, _, 2, 0, "er") % offer -> offering (istisnalar hariç)
            )
        ->  string_concat(VerbStr, "ing", PartStr)

        ;   % 5. CVC Kuralı (Sessiz-Sesli-Sessiz) -> İkizle (run -> running, sit -> sitting)
            string_length(VerbStr, Len2), Len2 >= 2,
            string_concat(Init, LastChar, VerbStr),
            is_consonant(LastChar),
            \+ member(LastChar, ["w", "x", "y"]), % w, x, y ile bitenler ikizlenmez (snowing)
            string_length(Init, InitLen), InitLen > 0,
            string_concat(_, SecondLast, Init),
            string_length(SecondLast, 1),
            is_vowel(SecondLast)
        ->  string_concat(VerbStr, LastChar, Doubled),
            string_concat(Doubled, "ing", PartStr)
            
        ;   % 6. Varsayılan durum (play -> playing, go -> going, see -> seeing)
            string_concat(VerbStr, "ing", PartStr)
        ),
        atom_string(Participle, PartStr).

    % Past Simple
    get_past_simple(Verb, _, Past) :-
        irregular_verb(Verb, Past, _, _),
        !.

    get_past_simple(Verb, _, Past) :-
        atom_string(Verb, VerbStr),
        (   % -e ile biten: love -> loved
            string_concat(_, "e", VerbStr)
        ->  string_concat(VerbStr, "d", PastStr)
        ;   % -y ile biten (ünsüz+y): carry -> carried
            string_concat(Base, "y", VerbStr),
            string_length(Base, BaseLen),
            BaseLen > 0,
            string_concat(_, LastOfBase, Base),
            string_length(LastOfBase, 1),
            \+ is_vowel(LastOfBase)
        ->  string_concat(Base, "ied", PastStr)
        ;   string_concat(VerbStr, "ed", PastStr)
        ),
        atom_string(Past, PastStr).

    % Past Participle
    get_past_participle(Verb, Participle) :-
        irregular_verb(Verb, _, Participle, _),
        !.

    get_past_participle(Verb, Participle) :-
        get_past_simple(Verb, 3, Participle).

    % Present Simple (3rd person singular)
    get_present_simple(Verb, 3, singular, Conjugated) :-
        !,
        atom_string(Verb, VerbStr),
        (   Verb = have
        ->  Conjugated = has
        ;   Verb = be
        ->  Conjugated = is
        ;   Verb = do
        ->  Conjugated = does
        ;   % -s, -sh, -ch, -x, -z, -o ile biten: +es
            (   string_concat(_, "s", VerbStr)
            ;   string_concat(_, "sh", VerbStr)
            ;   string_concat(_, "ch", VerbStr)
            ;   string_concat(_, "x", VerbStr)
            ;   string_concat(_, "z", VerbStr)
            ;   string_concat(_, "o", VerbStr)
            )
        ->  string_concat(VerbStr, "es", ConjStr),
            atom_string(Conjugated, ConjStr)
        ;   % ünsüz + y: carry -> carries
            string_concat(Base, "y", VerbStr),
            string_length(Base, BaseLen),
            BaseLen > 0,
            string_concat(_, LastOfBase, Base),
            string_length(LastOfBase, 1),
            \+ is_vowel(LastOfBase)
        ->  string_concat(Base, "ies", ConjStr),
            atom_string(Conjugated, ConjStr)
        ;   string_concat(VerbStr, "s", ConjStr),
            atom_string(Conjugated, ConjStr)
        ).

    get_present_simple(Verb, _, _, Verb).

    % Yardımcı predicateler
    is_vowel("a"). is_vowel("e"). is_vowel("i"). is_vowel("o"). is_vowel("u").
    is_vowel("ı"). is_vowel("ö"). is_vowel("ü").

    is_consonant(Char) :-
        string_length(Char, 1),
        char_type(Char, alpha),  % Sadece harfse
        \+ is_vowel(Char).

    % =============================================================================
    % FONOLOJİ MOTORU (SES BİLGİSİ KURALLARI)
    % =============================================================================

    % Türkçe ünlü sınıflandırması
    turkish_back_vowel("a"). turkish_back_vowel("ı"). 
    turkish_back_vowel("o"). turkish_back_vowel("u").

    turkish_front_vowel("e"). turkish_front_vowel("i").
    turkish_front_vowel("ö"). turkish_front_vowel("ü").

    turkish_rounded_vowel("o"). turkish_rounded_vowel("u").
    turkish_rounded_vowel("ö"). turkish_rounded_vowel("ü").

    turkish_unrounded_vowel("a"). turkish_unrounded_vowel("e").
    turkish_unrounded_vowel("ı"). turkish_unrounded_vowel("i").

    % Sert ünsüzler (ses benzeşmesi için)
    turkish_hard_consonant("p"). turkish_hard_consonant("ç").
    turkish_hard_consonant("t"). turkish_hard_consonant("k").
    turkish_hard_consonant("f"). turkish_hard_consonant("h").
    turkish_hard_consonant("s"). turkish_hard_consonant("ş").

    % Son ünlüyü bul
    get_last_vowel(Word, Vowel) :-
        atom_string(Word, WordStr),
        string_chars(WordStr, Chars),
        reverse(Chars, RevChars),
        member(Char, RevChars),
        atom_string(CharAtom, [Char]),
        (is_vowel([Char]) ; is_vowel(CharAtom)),
        Vowel = [Char],
        !.

    % Son ünsüzü bul
    get_last_consonant(Word, Consonant) :-
        atom_string(Word, WordStr),
        string_length(WordStr, Len),
        Len > 0,
        LastIdx is Len - 1,
        sub_string(WordStr, LastIdx, 1, 0, Consonant),
        is_consonant(Consonant).

    % --- BÜYÜK ÜNLÜ UYUMU ---
    % Kalın ünlülerden sonra kalın, ince ünlülerden sonra ince ünlü gelir

    apply_vowel_harmony(Root, SuffixTemplate, HarmonizedSuffix) :-
        get_last_vowel(Root, LastVowel),
        (   turkish_back_vowel(LastVowel)
        ->  harmonize_to_back(SuffixTemplate, HarmonizedSuffix)
        ;   harmonize_to_front(SuffixTemplate, HarmonizedSuffix)
        ).

    harmonize_to_back(Suffix, Harmonized) :-
        atom_string(Suffix, SuffixStr),
        string_replace(SuffixStr, "e", "a", Temp1),
        string_replace(Temp1, "i", "ı", Harmonized).

    harmonize_to_front(Suffix, Harmonized) :-
        atom_string(Suffix, SuffixStr),
        string_replace(SuffixStr, "a", "e", Temp1),
        string_replace(Temp1, "ı", "i", Harmonized).

    % String replace helper
    string_replace(String, From, To, Result) :-
        split_string(String, From, "", Parts),
        atomics_to_string(Parts, To, Result).

    % --- ÜNSÜZ YUMUŞAMASI ---
    % p→b, ç→c, t→d, k→ğ (ünlü ile başlayan eklerden önce)

    apply_consonant_softening(Root, SoftenedRoot) :-
        atom_string(Root, RootStr),
        string_length(RootStr, Len),
        Len > 0,
        LastIdx is Len - 1,
        sub_string(RootStr, LastIdx, 1, 0, LastChar),
        soften_consonant(LastChar, SoftenedChar),
        sub_string(RootStr, 0, LastIdx, 1, RootBase),
        string_concat(RootBase, SoftenedChar, SoftenedRootStr),
        atom_string(SoftenedRoot, SoftenedRootStr).

    apply_consonant_softening(Root, Root) :-
        \+ needs_softening(Root).

    needs_softening(Root) :-
        atom_string(Root, RootStr),
        string_length(RootStr, Len),
        Len > 0,
        LastIdx is Len - 1,
        sub_string(RootStr, LastIdx, 1, 0, LastChar),
        member(LastChar, ["p", "ç", "t", "k"]).

    soften_consonant("p", "b").
    soften_consonant("ç", "c").
    soften_consonant("t", "d").
    soften_consonant("k", "ğ").

    % --- ÜNSÜZ BENZEŞMESİ (SERTLEŞMESİ) ---
    % Sert ünsüzlerden sonra ek ünsüzü sertleşir: -di → -ti

    apply_consonant_assimilation(Root, SuffixTemplate, AssimilatedSuffix) :-
        get_last_consonant(Root, LastConsonant),
        (   turkish_hard_consonant(LastConsonant)
        ->  harden_suffix(SuffixTemplate, AssimilatedSuffix)
        ;   AssimilatedSuffix = SuffixTemplate
        ).

    harden_suffix(Suffix, Hardened) :-
        atom_string(Suffix, SuffixStr),
        string_replace(SuffixStr, "d", "t", Temp1),
        string_replace(Temp1, "c", "ç", Hardened).

    % --- ÜNLÜ DARALMASI ---
    % a/e → ı/i -yor önünde (başla + yor → başlıyor)

    apply_vowel_narrowing(Root, before_yor, NarrowedRoot) :-
        atom_string(Root, RootStr),
        string_length(RootStr, Len),
        Len > 0,
        LastIdx is Len - 1,
        sub_string(RootStr, LastIdx, 1, 0, LastChar),
        narrow_vowel(LastChar, NarrowedChar),
        sub_string(RootStr, 0, LastIdx, 1, RootBase),
        string_concat(RootBase, NarrowedChar, NarrowedRootStr),
        atom_string(NarrowedRoot, NarrowedRootStr).

    apply_vowel_narrowing(Root, _, Root) :-
        \+ needs_narrowing(Root).

    needs_narrowing(Root) :-
        atom_string(Root, RootStr),
        string_length(RootStr, Len),
        Len > 0,
        LastIdx is Len - 1,
        sub_string(RootStr, LastIdx, 1, 0, LastChar),
        member(LastChar, ["a", "e"]).

    narrow_vowel("a", "ı").
    narrow_vowel("e", "i").

    % --- KAYNASTIRMA ÜNSÜZLERİ ---
    % İki ünlü arasına y, n, s eklenir

    apply_buffer_consonant(Root, SuffixStart, BufferedRoot) :-
        atom_string(Root, RootStr),
        string_length(RootStr, Len),
        Len > 0,
        LastIdx is Len - 1,
        sub_string(RootStr, LastIdx, 1, 0, LastChar),
        is_vowel(LastChar),
        is_vowel(SuffixStart),
        string_concat(RootStr, "y", BufferedRootStr),
        atom_string(BufferedRoot, BufferedRootStr).

    apply_buffer_consonant(Root, _, Root).

    % --- İNGİLİZCE FONOLOJİ KURALLARI ---

    % CVC pattern kontrolü (ünsüz-ünlü-ünsüz)
    is_cvc_pattern(Word) :-
        atom_string(Word, WordStr),
        string_length(WordStr, Len),
        Len >= 3,
        Idx1 is Len - 3,
        Idx2 is Len - 2,
        Idx3 is Len - 1,
        sub_string(WordStr, Idx1, 1, _, Char1),
        sub_string(WordStr, Idx2, 1, _, Char2),
        sub_string(WordStr, Idx3, 1, _, Char3),
        is_consonant(Char1),
        is_vowel(Char2),
        is_consonant(Char3),
        \+ member(Char3, ["w", "x", "y"]).

    % İngilizce son ünsüz ikilemesi
    apply_english_doubling(Word, Context, Doubled) :-
        member(Context, [suffix_ing, suffix_ed]),
        is_cvc_pattern(Word),
        atom_string(Word, WordStr),
        string_length(WordStr, Len),
        LastIdx is Len - 1,
        sub_string(WordStr, LastIdx, 1, 0, LastChar),
        string_concat(WordStr, LastChar, DoubledStr),
        atom_string(Doubled, DoubledStr).

    apply_english_doubling(Word, _, Word) :-
        \+ is_cvc_pattern(Word).

    % İngilizce sessiz-e düşmesi
    apply_silent_e_drop(Word, Trimmed) :-
        atom_string(Word, WordStr),
        string_length(WordStr, Len),
        Len > 1,
        LastIdx is Len - 1,
        sub_string(WordStr, LastIdx, 1, 0, "e"),
        PrevIdx is Len - 2,
        sub_string(WordStr, PrevIdx, 1, 0, PrevChar),
        is_consonant(PrevChar),
        sub_string(WordStr, 0, LastIdx, 1, TrimmedStr),
        atom_string(Trimmed, TrimmedStr).

    apply_silent_e_drop(Word, Word) :-
        atom_string(Word, WordStr),
        string_length(WordStr, Len),
        (   Len =< 1
        ;   LastIdx is Len - 1,
            sub_string(WordStr, LastIdx, 1, 0, LastChar),
            LastChar \= "e"
        ).

    % İngilizce -ie → -ying dönüşümü
    apply_ie_to_y(Word, Transformed) :-
        atom_string(Word, WordStr),
        sub_string(WordStr, _, 2, 0, "ie"),
        string_length(WordStr, Len),
        BaseLen is Len - 2,
        sub_string(WordStr, 0, BaseLen, 2, Base),
        string_concat(Base, "y", TransformedStr),
        atom_string(Transformed, TransformedStr).

    apply_ie_to_y(Word, Word) :-
        atom_string(Word, WordStr),
        \+ sub_string(WordStr, _, 2, 0, "ie").

    % İngilizce y → i dönüşümü (ünsüz + y)
    apply_y_to_i(Word, Transformed) :-
        atom_string(Word, WordStr),
        string_length(WordStr, Len),
        Len >= 2,
        LastIdx is Len - 1,
        sub_string(WordStr, LastIdx, 1, 0, "y"),
        PrevIdx is Len - 2,
        sub_string(WordStr, PrevIdx, 1, 0, PrevChar),
        is_consonant(PrevChar),
        sub_string(WordStr, 0, LastIdx, 1, Base),
        string_concat(Base, "i", TransformedStr),
        atom_string(Transformed, TransformedStr).

    apply_y_to_i(Word, Word) :-
        atom_string(Word, WordStr),
        string_length(WordStr, Len),
        (   Len < 2
        ;   LastIdx is Len - 1,
            sub_string(WordStr, LastIdx, 1, 0, LastChar),
            LastChar \= "y"
        ;   LastIdx is Len - 1,
            sub_string(WordStr, LastIdx, 1, 0, "y"),
            PrevIdx is Len - 2,
            sub_string(WordStr, PrevIdx, 1, 0, PrevChar),
            is_vowel(PrevChar)
        ).

    % Cümle oluşturma
    build_sentence(Subject, Tense, Person, Plurality, Negation, VerbForm, Result) :-
        (   auxiliary_verb(Tense, Person, Plurality, Negation, Aux)
        ->  format(atom(Result), "~w ~w ~w", [Subject, Aux, VerbForm])
        ;   format(atom(Result), "~w ~w", [Subject, VerbForm])
        ).

    % =============================================================================
    % ANA ÇEVİRİ PREDİKATI
    % =============================================================================

    % translate_verb(+TurkishVerb, -EnglishTranslation, -Details)
    translate_verb(TurkishVerb, EnglishTranslation, Details) :-
        analyze_turkish(TurkishVerb, Analysis),
        
        % Analiz sonuçlarını çıkar
        member(root:TrRoot, Analysis),
        member(tense:Tense, Analysis),
        member(person:Person, Analysis),
        member(plurality:Plurality, Analysis),
        member(negation:Negation, Analysis),
        
        % Türkçe kökü İngilizce'ye çevir
        verb_root(TrRoot, EnRoot, _),
        
        % İngilizce çekim yap
        conjugate_english(EnRoot, Tense, Person, Plurality, Negation, EnglishTranslation),
        
        Details = [
            turkish_root:TrRoot,
            english_root:EnRoot,
            tense:Tense,
            person:Person,
            plurality:Plurality,
            negation:Negation
        ].

    % =============================================================================
    % CÜMLE ÇEVİRİSİ
    % =============================================================================

    % translate_sentence(+TurkishSentence, -EnglishSentence)
    translate_sentence(TurkishSentence, EnglishSentence) :-
        atom_string(TurkishSentence, SentenceStr),
        split_string(SentenceStr, " ", "", WordStrs),
        maplist(atom_string, Words, WordStrs),
        translate_words(Words, TranslatedWords),
        atomic_list_concat(TranslatedWords, ' ', EnglishSentence).

    translate_words([], []).
    translate_words([Word|Rest], [Translation|TransRest]) :-
        translate_word(Word, Translation),
        translate_words(Rest, TransRest).

    % =============================================================================
    % SORU CÜMLESİ ÇEVİRİSİ
    % =============================================================================

    % translate_question(+TurkishQuestion, -EnglishQuestion)
    % Örnek: "geldi mi" → "Did he/she come?"
    translate_question(TurkishQuestion, EnglishQuestion) :-
        atom_string(TurkishQuestion, QuestionStr),
        split_string(QuestionStr, " ", "", WordStrs),
        maplist(atom_string, Words, WordStrs),
        
        % Soru eki kontrolü
        (   append(VerbWords, [QuestionParticle], Words),
            is_question_particle(QuestionParticle)
        ->  % Soru cümlesi
            (   VerbWords = [Verb]
            ->  translate_verb(Verb, _VerbTranslation, Details),
                member(tense:Tense, Details),
                member(person:Person, Details),
                member(plurality:Plurality, Details),
                member(english_root:EnRoot, Details),
                build_question(EnRoot, Tense, Person, Plurality, EnglishQuestion)
            ;   translate_sentence(TurkishQuestion, EnglishQuestion)
            )
        ;   % Normal cümle
            translate_sentence(TurkishQuestion, EnglishQuestion)
        ).

    % Soru eki kontrolü
    is_question_particle(Word) :-
        atom_string(Word, WordStr),
        member(WordStr, ["mı", "mi", "mu", "mü"]).

    % Soru cümlesi oluşturma
    build_question(Verb, past_simple, Person, Plurality, Question) :-
        subject_pronoun(Person, Plurality, Subject),
        format(atom(Question), "Did ~w ~w?", [Subject, Verb]).

    build_question(Verb, present_continuous, Person, Plurality, Question) :-
        subject_pronoun(Person, Plurality, Subject),
        auxiliary_verb(present_continuous, Person, Plurality, false, Aux),
        get_present_participle(Verb, VerbForm),
        format(atom(Question), "~w ~w ~w?", [Aux, Subject, VerbForm]).

    build_question(Verb, future, Person, Plurality, Question) :-
        subject_pronoun(Person, Plurality, Subject),
        format(atom(Question), "Will ~w ~w?", [Subject, Verb]).

    build_question(Verb, aorist, Person, Plurality, Question) :-
        subject_pronoun(Person, Plurality, Subject),
        (Person = 3, Plurality = singular -> Aux = 'Does' ; Aux = 'Do'),
        format(atom(Question), "~w ~w ~w?", [Aux, Subject, Verb]),
        !.

    % Fallback - unknown tense için Do/Does kullan
    build_question(Verb, unknown, Person, Plurality, Question) :-
        subject_pronoun(Person, Plurality, Subject),
        (Person = 3, Plurality = singular -> Aux = 'Does' ; Aux = 'Do'),
        format(atom(Question), "~w ~w ~w?", [Aux, Subject, Verb]),
        !.

    % =============================================================================
    % TEST PREDİKATLARI
    % =============================================================================

    test_morphology :-
        writeln('================================================================='),
        writeln('              TÜRKÇE-İNGİLİZCE MORFOLOJİ TESTİ'),
        writeln('================================================================='),
        nl,
        
        % Present Continuous testleri
        writeln('--- Şimdiki Zaman (Present Continuous) ---'),
        test_verb(geliyorum),
        test_verb(gidiyorsun),
        test_verb(yiyor),
        test_verb(yapiyoruz),
        test_verb(okuyorlar),
        nl,
        
        % Past Simple testleri
        writeln('--- Geçmiş Zaman (Past Simple) ---'),
        test_verb(geldim),
        test_verb(gittin),
        test_verb(yedi),
        test_verb(yaptik),
        test_verb(okudular),
        nl,
        
        % Future testleri
        writeln('--- Gelecek Zaman (Future) ---'),
        test_verb(gelecegim),
        test_verb(gideceksin),
        test_verb(yapacak),
        nl,
        
        % Aorist testleri
        writeln('--- Geniş Zaman (Aorist/Present Simple) ---'),
        test_verb(gelirim),
        test_verb(gidersin),
        test_verb(yapar),
        nl,
        
        % Olumsuz testler
        writeln('--- Olumsuz Formlar ---'),
        test_verb(gelmiyorum),
        test_verb(gitmedim),
        test_verb(yapmayacak),
        test_verb(gelmez),
        nl,
        
        % Necessity testleri
        writeln('--- Gereklilik (Necessity) ---'),
        test_verb(gelmeliyim),
        test_verb(gitmelisin),
        nl,
        
        writeln('================================================================='),
        writeln('                      TEST TAMAMLANDI'),
        writeln('=================================================================').

    test_verb(Verb) :-
        (   translate_verb(Verb, Translation, Details)
        ->  member(turkish_root:TrRoot, Details),
            member(english_root:EnRoot, Details),
            member(tense:Tense, Details),
            member(negation:Neg, Details),
            format('  ~w~n', [Verb]),
            format('      -> ~w~n', [Translation]),
            format('      Kök: ~w -> ~w | Zaman: ~w', [TrRoot, EnRoot, Tense]),
            (Neg = true -> write(' [OLUMSUZ]') ; true),
            nl
        ;   format('  ~w -> [Analiz edilemedi]~n', [Verb])
        ).

    % Pratik sorgular için
    :- writeln('Morfoloji modülü yüklendi.').
    :- writeln('Kullanım: translate_verb(geliyorum, X, D).').
    :- writeln('Test için: test_morphology.').
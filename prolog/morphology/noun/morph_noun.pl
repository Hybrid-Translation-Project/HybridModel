:- module(morph_noun, [
    analyze_noun/2,
    translate_noun/3
]).

:- encoding(utf8).

:- use_module('../utils/morph_utils', [
    unsoften_consonant/2
]).

:- use_module('../data/morphology_data', [
    noun_root/5
]).

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

    % KURAL: Hal ve iyelik ekleri atıldıktan sonra, geriye 'evler' gibi çoğul kalmışsa
    % Onu da temizleyip köke (ev) ulaş.
    find_noun_root(RootStr, TrRoot, EnRoot, EnPlural, Category) :-
        string_length(RootStr, Len), Len > 3,
        (sub_string(RootStr, _, 3, 0, "ler"); sub_string(RootStr, _, 3, 0, "lar")),
        BaseLen is Len - 3,
        sub_string(RootStr, 0, BaseLen, 3, RealRootStr),
        % Şimdi gerçek kökü (ev) arıyoruz
        morphology_data:noun_root(TrRoot, EnRoot, EnPlural, Category, _),
        atom_string(TrRoot, TrRootStr),
        RealRootStr = TrRootStr,
        !.
    
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
        
        unsoften_consonant(LastChar, HardChar),  % <-- user: ÖNEKİ SİLİNDİ, modül importu ile çalışacak
        
        sub_string(RootStr, 0, LastIdx, 1, RootBase),
        string_concat(RootBase, HardChar, HardRootStr),
        
        noun_root(TrRoot, EnRoot, EnPlural, Category, _),  % <-- morphology_data: ÖNEKİ SİLİNDİ
        
        atom_string(TrRoot, TrRootStr),
        HardRootStr = TrRootStr,
        !.

    find_noun_root(RootStr, RootAtom, RootAtom, RootAtom, unknown) :-
        % Bilinmeyen kök - olduğu gibi döndür
        atom_string(RootAtom, RootStr).



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
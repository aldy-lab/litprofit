# -*- coding: utf-8 -*-
"""
Every user-facing string, in the three languages the company sells in.

Only strings live here — the markup stays in build.py, so a layout change is
made once rather than three times.

The Lithuanian and Russian are the company's own wording wherever their old
site had an equivalent: the equipment vocabulary, the service names and the
"Konsultuojame / Organizuojame / Užtikriname" triad are theirs, not a
translation of my English. Copy that is new on this site was written directly
in each language rather than translated word for word.

⚠️ The privacy policy is a legal text translated for convenience. Have it
reviewed by whoever signs it off before launch.
"""

# Russian is off. The translations below are left in place rather than
# deleted: nothing outside LANGS reads them, so they cost nothing at build
# time, and putting the language back is a one-word change rather than a
# retranslation. Every page, the switcher, hreflang and the sitemap all
# follow this tuple.
LANGS = ("en", "lt")

# <html lang>, og:locale, and the label in the switcher
LOCALE = {"en": ("en", "en_GB"), "lt": ("lt", "lt_LT"), "ru": ("ru", "ru_RU")}
LABEL = {"en": "EN", "lt": "LT", "ru": "RU"}
LANG_NAME = {"en": "English", "lt": "Lietuvių", "ru": "Русский"}

# Page paths are shared across languages, prefixed with /lt or /ru. Keeping one
# set of slugs means one sitemap shape and one place to add a page; hreflang
# tells search engines which is which.
NAV = {
    "en": [("About", "/about/"), ("Services", "/services/"),
           ("Completed works", "/completed-works/"), ("Partners", "/partners/"),
           ("Certificates", "/certificates/"), ("Contacts", "/contacts/"),
           ("Careers", "/careers/")],
    "lt": [("Apie mus", "/about/"), ("Paslaugos", "/services/"),
           ("Atlikti darbai", "/completed-works/"), ("Partneriai", "/partners/"),
           ("Sertifikatai", "/certificates/"), ("Kontaktai", "/contacts/"),
           ("Karjera", "/careers/")],
    "ru": [("О нас", "/about/"), ("Услуги", "/services/"),
           ("Выполненные работы", "/completed-works/"),
           ("Партнёры", "/partners/"),
           ("Сертификаты", "/certificates/"),
           ("Контакты", "/contacts/"),
           ("Вакансии", "/careers/")],
}

S = {}

# ============================================================
# ENGLISH
# ============================================================
S["en"] = dict(
    tagline="Ship Repair and Maintenance All Over the World",
    skip="Skip to content", menu="Menu", book="Book a call",
    home="Home", sheets="Sheets", prev="Previous", next="Next",
    f_address="Address", f_contacts="Contacts", f_details="Company details",
    f_site="Site", f_privacy="Privacy policy", f_made="Made by",
    f_calc="Calculator",
    company_no="Company No.", vat="VAT code", lang_label="Language",

    # semi-hermetic reciprocating compressor plate, on the refrigeration page
    prj_eyebrow="Selected work", prj_h2="Jobs, one at a time",
    prj_lead="Each one as it was done: the vessel, the plant, the scope and how long she was alongside.",
    prj_vessel="Vessel", prj_owner="Owner", prj_year="Year", prj_port="Port",
    prj_days="Alongside", prj_days_unit="days", prj_scope="Discipline",
    prj_work="What was done", prj_plant="Plant", prj_all="All completed works",
    prj_where="Where on the vessel",
    prj_tb="Job record", prj_tb2="As carried out",
    cap_chart_eyebrow="What it delivers", cap_chart_h2="Capacity against evaporating temperature",
    cap_chart_lead="A six-cylinder on R404A, at three condensing temperatures. Published "
                   "figures, plotted \u2014 the curve a refrigeration engineer reads before "
                   "deciding whether a machine will hold a hold.",
    cap_chart_x="Evaporating temperature", cap_chart_y="Cooling capacity",
    cap_chart_tb="Six-cylinder // R404A", cap_chart_tb2="EN12900 // 20 \u00b0C suction gas",
    # the live 3D of the same machine, above the elevation
    # the twin-screw cutaway on the about page. Site languages are en and lt
    # only -- Russian lives in the calculator, which carries its own strings.
    # the packaged unit on the refrigeration page
    unit_eyebrow="As it arrives", unit_h2="The whole unit, on its frame",
    unit_lead="A compressor is not what comes aboard \u2014 a skid is: separator, "
              "block, coupling, motor and the pipework tying them together, all on "
              "one frame that has to come out through a hatch. Drag it round.",
    unit_panel="Control panel", unit_frame="Base frame",
    unit_tb="Screw package, oil-flooded", unit_tb2="Arrangement // not to scale",
    unit_alt="A packaged screw compressor unit on its base frame: horizontal oil "
             "separator, compressor block, coupling guard, electric motor, a control "
             "panel and the suction, discharge and oil pipework between them.",
    scr_eyebrow="On the bench", scr_h2="A twin-screw compressor, opened up",
    scr_lead="Four lobes driving six, in a figure-of-eight bore \u2014 the size that "
             "comes off a reefer and onto our bench most often. The casing is drawn "
             "as glass because the casing is the least interesting part of it. "
             "Drag it round.",
    scr_male="Male rotor, 4 lobes", scr_female="Female rotor, 6 flutes",
    scr_suction="Suction, cold", scr_discharge="Discharge, hot",
    scr_casing="Casing", scr_slide="Slide valve", scr_bearing="Rotor bearings",
    scr_tb="Twin-screw, oil-flooded", scr_tb2="Arrangement // not a rotor profile",
    scr_alt="A twin-screw compressor with the casing drawn transparent: two meshing "
            "helical rotors, their bearings at both ends, and the slide valve that "
            "controls capacity running beneath them.",
    cmp_eyebrow="The machine", cmp_h2="The compressor, in the round",
    # "the elevation below" was true while this sat above the side elevation on
    # the refrigeration page. It is on the home page now and the elevation is
    # not below it, so the sentence had to stop saying so.
    cmp_lead="The size we overhaul most: four cylinders, 55 mm bore, 34 mm stroke. "
             "Built from the published envelope and shaded live in the browser \u2014 "
             "drag it round.",
    cmp_hint="Drag to turn",
    cmp_tb="Semi-hermetic reciprocating", cmp_tb2="Built to the published envelope",
    cmp_alt="A semi-hermetic four-cylinder reciprocating compressor seen in three "
            "quarters: ribbed motor housing, crankcase, two banks of cylinders in a V, "
            "and the suction and discharge connections.",
    rec_eyebrow="On the bench", rec_h2="A semi-hermetic four-cylinder, in section",
    rec_lead="The size we overhaul most: four cylinders, 55 mm bore, 34 mm stroke, "
             "28.11 m\u00b3/h at 1450 rpm. Drawn to the connection schedule a "
             "fitter actually works to.",
    rec_tb="Semi-hermetic reciprocating", rec_tb2="Side elevation // not to scale",
    rec_c1="Discharge line", rec_c2="Suction line", rec_c3="High pressure",
    rec_c4="Low pressure", rec_c5="Oil fill plug", rec_c6="Oil drain",
    rec_c7="Oil return, separator", rec_c8="Oil heater",
    rec_motor="Motor", rec_crank="Crankcase", rec_head="Cylinder heads",
    rec_terminal="Terminal box",
    hero_eyebrow="Klaipeda, Lithuania", hero_since="since",
    # vessel general arrangement -- the four spaces the company works in.
    # vsl_, not ga_: ga_ is the compressor package drawing further down.
    vsl_eyebrow="Where the work is", vsl_h2="A ship, deck to keel",
    vsl_lead="A fishing vessel from the side. Every discipline on this page is "
             "a space you can point at.",
    vsl_hold="Fish hold // RSW", vsl_er="Ship equipment|and engine repair",
    vsl_pipe="Hull and piping", vsl_store="Stores",
    vsl_wl="Waterline", vsl_tb="Typical fishing vessel",
    vsl_tb2="Arrangement // not to scale",
    # The street keeps its Lithuanian form in every language: that is what the
    # register holds and what the post office reads. Only the country and city
    # take the reader's language.
    addr_street="Svajonės g. 30", addr_city="LT-94101 Klaipėda", addr_country="Lithuania",
    # The frost easter egg, annotated on the drawing the way a note is.
    lamp_hint="Lamp", lamp_hint_a11y="Light the drawing under the cursor. Double-clicking the hero does the same.",
    lamp_hint_off="Put the lamp away.",
    frost_hint="Frost", frost_hint_a11y="Frost the page over. You can also just type FROST.",
    frost_hint_off="Thaw the page.",
    hero_h1="Ship repair and maintenance all over the world",
    hero_lead='%(legal)s overhauls marine engines, refrigeration plant and piping '
              'systems for fishing fleets, shipowners and shore installations.',
    step1="We consult", step2="We organise", step3="We ensure",
    hero_services="Our services",
    role_bitzer="Authorised marine service partner",
    role_danfoss="Marine refrigeration partner",
    trust_cert="Certified",

    rep_eyebrow="Representation", rep_h2="We represent BITZER and DANFOSS",
    rep_lead="Two of the biggest names in refrigeration and marine controls appoint "
             "us directly. That is not a reseller arrangement — it is factory backing "
             "on the parts, the pricing and the warranty.",
    rep_bitzer="One of the largest independent manufacturers of refrigeration "
               "compressors in the world. As an authorised partner we supply and "
               "service BITZER equipment directly, rather than through an "
               "intermediary — which shortens both the parts chain and the warranty "
               "conversation.",
    rep_danfoss="We represent the Danfoss marine line: controls, valves and "
                "components for refrigeration and engine room systems, specified and "
                "supplied for vessels rather than adapted from shore equipment.",

    pres_title="Company presentation",
    pres_note="Everything on this site, in one document to forward.",
    fact_years="Years in refrigeration", fact_service="Service response",
    fact_certs="Class certificates", fact_insured="Liability insured",

    svc_eyebrow="Services", svc_h2="Four disciplines, one contractor",
    svc_lead="Most jobs need more than one of these at once. Handling them under a "
             "single contract is what removes the coordination problem from the "
             "shipowner's desk.",
    read_more="Read more",

    how_eyebrow="How we work", how_h2="Consult, organise, ensure",
    how_lead="Three steps, in that order — it is how the company has described "
             "itself for years, and it holds up.",
    how1="Advice shaped by experience, where the technology is going, and what you "
         "actually need and can spend. Every customer gets proper time.",
    how2="We arrange and carry out every stage of the repair and service work, "
         "because your time is worth more than the coordination.",
    how3="We control the work as it runs and keep your representatives informed of "
         "progress — no surprises at handover.",

    ga_eyebrow="General arrangement", ga_h2="The machine we take apart most",
    ga_lead="A skid-mounted marine screw compressor package, in side elevation. "
            "Take a balloon to see what we do to that part.",

    cap_eyebrow="Capability", cap_h2="A decade of refrigeration, on ships and ashore",
    cap_lead="Compressor overhauls, class-approved design documentation, plant "
             "installation and commissioning — on fishing vessels and shore "
             "installations alike.",
    clients_eyebrow="Clients", clients_h2="Who we work with",
    rail_prev="Previous clients", rail_next="More clients",

    cta_h2="24/7 service",
    cta_p="We are ready to provide prompt and competent assistance — tell us the "
          "vessel, the equipment and the port, and we will come back with a plan.",
    cta_enquiry="Send an enquiry", cta_call="Call",

    # Booking and the dial code. The booking copy says what pressing the
    # button does BEFORE it does it, which is the whole point of loading the
    # widget on request: until then nothing has been sent anywhere.
    # What the form says back. These lived in main.js as English literals, so
    # a Lithuanian visitor filled in a Lithuanian form and was answered in
    # English -- and once the CV note was translated the reply came out half
    # and half, which is how it was noticed at all.
    form_msg_required="Please complete the required fields.",
    form_msg_sending="Sending\u2026",
    form_msg_ok="Thank you \u2014 we will come back to you shortly.",
    form_msg_fail="Something went wrong. Please email %(email)s directly.",
    form_msg_mail="Your mail client is opening with everything ready to send.",
    form_dial="Country code",
    book_eyebrow="Book a call",
    book_h2="Fifteen minutes with an engineer",
    book_load="Load the booking calendar",
    book_newtab="Open the calendar in a new tab instead",
    book_lead="Pick a slot and we will call you. If it is urgent, the phone "
              "number above is answered around the clock.",
    book_note="The calendar is hosted by Calendly. Nothing is requested from "
              "them until you press this button \u2014 press it and your "
              "browser will connect to Calendly and their terms apply.",
    form_name="Name", form_company="Company", form_phone="Phone",
    form_email="Email", form_message="Message", form_optional="(optional)",
    form_send="Send enquiry",
    form_placeholder="Vessel or plant, the equipment, the port, and when you need "
                     "it done.",
    form_consent='I agree that %(legal)s may use these details to respond to my '
                 'enquiry, as described in the %(privacy)s.',
    form_privacy_link="privacy policy",
)

# ============================================================
# LIETUVIŲ
# ============================================================
S["lt"] = dict(
    tagline="Laivų remontas ir aptarnavimas visame pasaulyje",
    skip="Pereiti prie turinio", menu="Meniu", book="Susitarti dėl pokalbio",
    home="Pradžia", sheets="Puslapiai", prev="Ankstesnis", next="Kitas",
    f_address="Adresas", f_contacts="Kontaktai", f_details="Rekvizitai",
    f_site="Svetainė", f_privacy="Privatumo politika", f_made="Sukūrė",
    f_calc="Skaičiuoklė",
    company_no="Įmonės kodas", vat="PVM mokėtojo kodas", lang_label="Kalba",

    prj_eyebrow="Atrinkti darbai", prj_h2="Darbai po vieną",
    prj_lead="Kiekvienas taip, kaip buvo atliktas: laivas, įranga, apimtis ir kiek stovėta prie kranto.",
    prj_vessel="Laivas", prj_owner="Savininkas", prj_year="Metai", prj_port="Uostas",
    prj_days="Prie kranto", prj_days_unit="d.", prj_scope="Sritis",
    prj_work="Kas atlikta", prj_plant="Įranga", prj_all="Visi atlikti darbai",
    prj_where="Kurioje laivo dalyje",
    prj_tb="Darbo įrašas", prj_tb2="Kaip atlikta",
    cap_chart_eyebrow="Ką jis duoda", cap_chart_h2="Galia priklausomai nuo garavimo temperatūros",
    cap_chart_lead="Šešiacilindris su R404A, esant trims kondensavimo temperatūroms. "
                   "Paskelbti duomenys grafike \u2014 kreivė, kurią šaldymo inžinierius "
                   "žiūri prieš spręsdamas, ar mašina išlaikys triumą.",
    cap_chart_x="Garavimo temperatūra", cap_chart_y="Šaldymo galia",
    cap_chart_tb="Šešiacilindris // R404A", cap_chart_tb2="EN12900 // 20 \u00b0C siurbimo dujos",
    unit_eyebrow="Kaip atkeliauja", unit_h2="Visas agregatas ant rėmo",
    unit_lead="Į laivą patenka ne kompresorius, o agregatas: separatorius, blokas, "
              "mova, variklis ir juos jungiantys vamzdynai \u2014 viskas ant vieno "
              "rėmo, kurį reikia iškelti pro liuką. Pasukite jį.",
    unit_panel="Valdymo skydas", unit_frame="Rėmas",
    unit_tb="Sraigtinis agregatas, alyva užlietas", unit_tb2="Išdėstymas // ne masteliu",
    unit_alt="Sraigtinio kompresoriaus agregatas ant rėmo: horizontalus alyvos "
             "separatorius, kompresoriaus blokas, movos gaubtas, elektros variklis, "
             "valdymo skydas ir tarp jų einantys vamzdynai.",
    scr_eyebrow="Ant stalo", scr_h2="Sraigtinis kompresorius \u2014 iš vidaus",
    scr_lead="Keturios iškyšos suka šešias, aštuoniukės formos ertmėje \u2014 tokio "
             "dydžio mašinos dažniausiai atkeliauja nuo šaldymo laivo ant mūsų stalo. "
             "Korpusas nupieštas kaip stiklas, nes korpusas čia \u2014 mažiausiai "
             "įdomi dalis. Pasukite jį.",
    scr_male="Varantysis rotorius, 4 iškyšos", scr_female="Varomasis rotorius, 6 grioveliai",
    scr_suction="Siurbimas, šaltas", scr_discharge="Slėgis, karštas",
    scr_casing="Korpusas", scr_slide="Slankioji sklendė", scr_bearing="Rotorių guoliai",
    scr_tb="Sraigtinis, alyva užlietas", scr_tb2="Išdėstymas // ne rotoriaus profilis",
    scr_alt="Sraigtinis kompresorius permatomu korpusu: du susikabinę sraigtiniai "
            "rotoriai, jų guoliai abiejuose galuose ir po jais einanti našumą "
            "reguliuojanti slankioji sklendė.",
    cmp_eyebrow="Mašina", cmp_h2="Kompresorius \u2014 erdvėje",
    cmp_lead="Dažniausiai remontuojamas dydis: keturi cilindrai, 55 mm skersmuo, "
             "34 mm eiga. Sudėtas pagal skelbiamus gabaritus ir šešėliuojamas "
             "naršyklėje \u2014 pasukite jį.",
    cmp_hint="Vilkite, kad pasuktumėte",
    cmp_tb="Pusiau hermetiškas stūmoklinis", cmp_tb2="Pagal skelbiamus gabaritus",
    cmp_alt="Pusiau hermetiškas keturių cilindrų stūmoklinis kompresorius trijų "
            "ketvirčių rakurse: briaunotas variklio korpusas, karteris, du cilindrų "
            "blokai V raide, siurbimo ir slėgio jungtys.",
    rec_eyebrow="Ant stalo", rec_h2="Pusiau hermetiškas keturcilindris, pjūvyje",
    rec_lead="Dydis, kurį remontuojame dažniausiai: keturi cilindrai, 55 mm skersmuo, "
             "34 mm eiga, 28,11 m\u00b3/h esant 1450 aps./min. Nubraižyta pagal "
             "prijungimų schemą, su kuria dirba montuotojas.",
    rec_tb="Pusiau hermetiškas stūmoklinis", rec_tb2="Vaizdas iš šono // ne mastelyje",
    rec_c1="Slėginė linija", rec_c2="Siurbimo linija", rec_c3="Aukštas slėgis",
    rec_c4="Žemas slėgis", rec_c5="Alyvos pildymo kamštis", rec_c6="Alyvos išleidimas",
    rec_c7="Alyvos grąžinimas iš separatoriaus", rec_c8="Alyvos šildytuvas",
    rec_motor="Variklis", rec_crank="Karteris", rec_head="Cilindrų galvutės",
    rec_terminal="Gnybtų dėžutė",
    hero_eyebrow="Klaipėda, Lietuva", hero_since="nuo",
    vsl_eyebrow="Kur vyksta darbai", vsl_h2="Laivas nuo denio iki kilio",
    vsl_lead="Žvejybos laivas iš šono. Kiekviena šio puslapio sritis — konkreti "
             "laivo erdvė.",
    vsl_hold="Žuvies triumas // RSW", vsl_er="Laivų įrangos ir|variklių remontas",
    vsl_pipe="Korpusas ir vamzdynai", vsl_store="Sandėliai",
    vsl_wl="Vaterlinija", vsl_tb="Tipinis žvejybos laivas",
    vsl_tb2="Išdėstymas // ne mastelyje",
    addr_street="Svajonės g. 30", addr_city="LT-94101 Klaipėda", addr_country="Lietuva",
    lamp_hint="Lempa", lamp_hint_a11y="Apšviesti brėžinį po žymekliu. Tą patį daro dvigubas spustelėjimas.",
    lamp_hint_off="Padėti lempą.",
    frost_hint="Šerkšnas", frost_hint_a11y="Apšerkšnyti puslapį. Taip pat galite tiesiog įvesti FROST.",
    frost_hint_off="Atitirpdyti puslapį.",
    hero_h1="Laivų remontas ir aptarnavimas visame pasaulyje",
    hero_lead='%(legal)s remontuoja laivų variklius, šaldymo įrangą ir '
              'vamzdynų sistemas žvejybos laivynams, laivų savininkams ir kranto '
              'įrenginiams.',
    step1="Konsultuojame", step2="Organizuojame", step3="Užtikriname",
    hero_services="Mūsų paslaugos",
    role_bitzer="Autorizuoti jūrinio serviso partneriai",
    role_danfoss="Jūrinio šaldymo partneriai",
    trust_cert="Sertifikuota",

    rep_eyebrow="Atstovavimas", rep_h2="Atstovaujame BITZER ir DANFOSS",
    rep_lead="Dvi didžiausios šaldymo ir jūrinių valdymo sistemų rinkos "
             "įmonės paskyrė mus tiesiogiai. Tai nėra perpardavimo sutartis — tai "
             "gamyklos garantija dalims, kainoms ir įrangai.",
    rep_bitzer="Viena didžiausių nepriklausomų šaldymo kompresorių "
               "gamintojų pasaulyje. Būdami autorizuoti partneriai, BITZER įrangą "
               "tiekiame ir aptarnaujame tiesiogiai, be tarpininkų — tai sutrumpina "
               "ir dalių tiekimo grandinę, ir garantinius klausimus.",
    rep_danfoss="Atstovaujame Danfoss jūrinei linijai: valdymo įtaisai, vožtuvai "
                "ir komponentai šaldymo bei mašinų skyriaus sistemoms, parinkti ir "
                "tiekiami laivams, o ne pritaikyti iš kranto įrangos.",

    pres_title="Įmonės pristatymas",
    pres_note="Viskas, kas yra šioje svetainėje, viename dokumente.",
    fact_years="Metai šaldymo rinkoje", fact_service="Serviso atsakas",
    # "Klasifikacijos sertifikatai" is the one label in either language that
    # will not sit on a single line of the hero rule. "Klasės sertifikatai"
    # says the same thing about the same two class societies.
    fact_certs="Klasės sertifikatai", fact_insured="Civilinė atsakomybė",

    svc_eyebrow="Paslaugos", svc_h2="Keturios sritys, vienas rangovas",
    svc_lead="Daugumai darbų reikia ne vienos iš jų vienu metu. Kai viską "
             "atlieka vienas rangovas pagal vieną sutartį, derinimo rūpesčių "
             "laivo savininkui nebelieka.",
    read_more="Skaityti toliau",

    how_eyebrow="Kaip dirbame", how_h2="Konsultuojame, organizuojame, užtikriname",
    how_lead="Trys žingsniai, būtent tokia tvarka — taip įmonė save apibūdina "
             "jau daugelį metų.",
    how1="Konsultuodami vadovaujamės patirtimi, ateities tendencijomis, Jūsų "
         "norais bei galimybėmis. Išskirtinį dėmesį ir laiką skiriame kiekvienam "
         "užsakovui.",
    how2="Vertindami Jūsų brangų laiką, organizuojame visus remonto darbų ir "
         "aptarnavimo etapus bei juos įgyvendiname.",
    how3="Užtikriname darbų proceso kontrolę ir užsakovo atstovų informavimą "
         "apie darbų eigą — jokių staigmenų perduodant darbus.",

    ga_eyebrow="Bendrasis brėžinys", ga_h2="Mašina, kurią ardome dažniausiai",
    ga_lead="Ant rėmo sumontuotas jūrinis sraigtinis kompresorinis agregatas, "
            "šoninis vaizdas. Pasirinkite poziciją ir pamatysite, ką su ja darome.",

    cap_eyebrow="Kompetencija", cap_h2="Dešimtmetis šaldymo darbų laivuose ir krante",
    cap_lead="Kompresorių kapitalinis remontas, klasifikacinių bendrovių patvirtinti "
             "projektiniai dokumentai, įrangos montavimas ir paleidimas — tiek "
             "žvejybiniuose laivuose, tiek kranto įrenginiuose.",
    clients_eyebrow="Klientai", clients_h2="Su kuo dirbame",
    rail_prev="Ankstesni klientai", rail_next="Daugiau klientų",

    cta_h2="24/7 servisas",
    cta_p="Visada pasirengę suteikti operatyvią ir kompetentingą pagalbą — "
          "nurodykite laivą, įrangą ir uostą, o mes pateiksime planą.",
    cta_enquiry="Siųsti užklausą", cta_call="Skambinti",

    form_msg_required="Užpildykite privalomus laukus.",
    form_msg_sending="Siunčiama\u2026",
    form_msg_ok="Ačiū \u2014 netrukus su jumis susisieksime.",
    form_msg_fail="Kažkas nepavyko. Parašykite tiesiai adresu %(email)s.",
    form_msg_mail="Atsidaro jūsų pašto programa su paruoštu laišku.",
    form_dial="Šalies kodas",
    book_eyebrow="Rezervuoti pokalbį",
    book_h2="Penkiolika minučių su inžinieriumi",
    book_load="Įkelti rezervacijos kalendorių",
    book_newtab="Atidaryti kalendorių naujame lange",
    book_lead="Pasirinkite laiką ir mes paskambinsime. Jei skubu \u2014 "
              "aukščiau nurodytu numeriu atsiliepiame visą parą.",
    book_note="Kalendorių talpina „Calendly“. Kol nepaspausite šio mygtuko, "
              "jiems nesiunčiama jokia užklausa \u2014 paspaudus naršyklė "
              "prisijungs prie „Calendly“ ir galios jų sąlygos.",
    form_name="Vardas", form_company="Įmonė", form_phone="Telefonas",
    form_email="El. paštas", form_message="Žinutė", form_optional="(nebūtina)",
    form_send="Siųsti užklausą",
    form_placeholder="Laivas ar įrenginys, įranga, uostas ir kada reikia atlikti "
                     "darbus.",
    form_consent='Sutinku, kad %(legal)s naudotų šiuos duomenis atsakydama į mano '
                 'užklausą, kaip nurodyta %(privacy)s.',
    form_privacy_link="privatumo politikoje",
)

# ============================================================
# РУССКИЙ
# ============================================================
S["ru"] = dict(
    tagline="Ремонт и обслуживание судов в любой точке земного шара",
    skip="Перейти к содержанию", menu="Меню", book="Заказать звонок",
    home="Главная", sheets="Страницы", prev="Назад", next="Далее",
    f_address="Адрес", f_contacts="Контакты", f_details="Реквизиты",
    f_site="Сайт", f_privacy="Политика конфиденциальности", f_made="Сайт сделан",
    f_calc="Калькулятор",
    company_no="Код предприятия", vat="Код плательщика НДС", lang_label="Язык",

    hero_eyebrow="Клайпеда, Литва", hero_since="с",
    vsl_eyebrow="Где идёт работа", vsl_h2="Судно от палубы до киля",
    vsl_lead="Рыболовное судно сбоку. Каждое направление на этой странице — "
             "конкретное помещение.",
    vsl_hold="Рыбный трюм // RSW", vsl_er="Ремонт оборудования|и двигателей",
    vsl_pipe="Корпус и трубопроводы", vsl_store="Кладовые",
    vsl_wl="Ватерлиния", vsl_tb="Типовое рыболовное судно",
    vsl_tb2="Схема // вне масштаба",
    addr_street="Svajonės g. 30", addr_city="LT-94101 Клайпеда", addr_country="Литва",
    lamp_hint="Фонарь", lamp_hint_a11y="Подсветить чертёж под курсором. Двойной щелчок делает то же самое.",
    lamp_hint_off="Убрать фонарь.",
    frost_hint="Иней", frost_hint_a11y="Покрыть страницу инеем. Можно и просто ввести FROST.",
    frost_hint_off="Растопить иней.",
    hero_h1="Ремонт и обслуживание судов в любой точке земного шара",
    hero_lead='%(legal)s ремонтирует судовые двигатели, холодильное '
              'оборудование и трубопроводные системы для рыболовных флотов, '
              'судовладельцев и береговых установок.',
    step1="Консультируем", step2="Организовываем", step3="Обеспечиваем",
    hero_services="Наши услуги",
    role_bitzer="Авторизованный партнёр по морскому сервису",
    role_danfoss="Партнёр по морскому холодоснабжению",
    trust_cert="Сертифицировано",

    rep_eyebrow="Представительство", rep_h2="Мы представляем BITZER и DANFOSS",
    rep_lead="Две крупнейшие компании в области холодильной техники и "
             "морской автоматики назначили нас напрямую. Это не дилерское "
             "соглашение — это заводская поддержка по запчастям, ценам и гарантии.",
    rep_bitzer="Один из крупнейших независимых производителей холодильных "
               "компрессоров в мире. Как авторизованный партнёр мы поставляем и "
               "обслуживаем оборудование BITZER напрямую, без посредников — это "
               "сокращает и цепочку поставки запчастей, и решение гарантийных вопросов.",
    rep_danfoss="Мы представляем морскую линию Danfoss: средства автоматики, "
                "клапаны и компоненты для холодильных систем и систем машинного "
                "отделения, подобранные именно для судов, а не адаптированные с берега.",

    fact_years="Лет в холодильной технике", fact_service="Сервисный отклик",
    fact_certs="Классификационные сертификаты", fact_insured="Гражданская ответственность",

    svc_eyebrow="Услуги", svc_h2="Четыре направления, один подрядчик",
    svc_lead="Большинству работ требуется сразу несколько из них. Когда всё "
             "выполняется по одному договору, вопрос координации снимается с судовладельца.",
    read_more="Читать далее",

    how_eyebrow="Как мы работаем", how_h2="Консультируем, организовываем, обеспечиваем",
    how_lead="Три шага, именно в таком порядке — так компания описывает "
             "себя уже много лет.",
    how1="Консультируя, мы опираемся на опыт, тенденции рынка, Ваши "
         "пожелания и возможности. Каждому заказчику уделяем особое внимание.",
    how2="Ценя Ваше время, мы организуем и выполняем все этапы ремонтных "
         "и сервисных работ.",
    how3="Мы контролируем ход работ и информируем представителей заказчика "
         "о прогрессе — без сюрпризов при сдаче.",

    ga_eyebrow="Общий чертёж", ga_h2="Машина, которую мы разбираем чаще всего",
    ga_lead="Судовой винтовой компрессорный агрегат на раме, вид сбоку. "
            "Выберите позицию, чтобы увидеть, что мы с ней делаем.",

    cap_eyebrow="Компетенции", cap_h2="Десятилетие холодильных работ на судах и на берегу",
    cap_lead="Капитальный ремонт компрессоров, проектная документация, "
             "согласованная с классификационными обществами, монтаж и пусконаладка — "
             "как на рыболовных судах, так и на береговых установках.",
    clients_eyebrow="Клиенты", clients_h2="С кем мы работаем",
    rail_prev="Предыдущие клиенты", rail_next="Ещё клиенты",

    cta_h2="Сервис 24/7",
    cta_p="Мы всегда готовы оказать оперативную и компетентную помощь — "
          "сообщите судно, оборудование и порт, а мы предложим план.",
    cta_enquiry="Отправить запрос", cta_call="Позвонить",

    form_msg_required="Заполните обязательные поля.",
    form_msg_sending="Отправляется\u2026",
    form_msg_ok="Спасибо \u2014 мы скоро свяжемся с вами.",
    form_msg_fail="Что-то пошло не так. Напишите напрямую на %(email)s.",
    form_msg_mail="Открывается ваша почтовая программа с готовым письмом.",
    form_dial="Код страны",
    book_eyebrow="Записаться на звонок",
    book_h2="Пятнадцать минут с инженером",
    book_load="Загрузить календарь записи",
    book_newtab="Открыть календарь в новой вкладке",
    book_lead="Выберите время, и мы позвоним. Если срочно \u2014 по номеру "
              "выше отвечаем круглосуточно.",
    book_note="Календарь размещён на Calendly. Пока вы не нажмёте эту кнопку, "
              "им не отправляется ни одного запроса \u2014 после нажатия "
              "браузер соединится с Calendly и начнут действовать их условия.",
    form_name="Имя", form_company="Компания", form_phone="Телефон",
    form_email="Эл. почта", form_message="Сообщение", form_optional="(необязательно)",
    form_send="Отправить запрос",
    form_placeholder="Судно или установка, оборудование, порт и сроки.",
    form_consent='Я соглашаюсь, что %(legal)s может использовать эти данные для '
                 'ответа на мой запрос, как описано в %(privacy)s.',
    form_privacy_link="политике конфиденциальности",
)


# ============================================================
# SERVICES
# The equipment and manufacturer lists are identical in all three languages —
# they are proper nouns — so they are defined once and shared. Only the prose
# differs. The Lithuanian and Russian are the company's own service copy.
# ============================================================
COMPRESSORS = ["SABROE", "BITZER", "HOWDEN", "KUHLAUTOMAT",
               "STAL", "HALLSCREW", "GRASSO", "MYCOM"]
COUNTRIES = {
    "en": ["Denmark", "Germany", "Scotland", "Germany", "Sweden", "England",
           "Netherlands", "Japan"],
    "lt": ["Danija", "Vokietija", "Škotija", "Vokietija", "Švedija", "Anglija",
           "Olandija", "Japonija"],
    "ru": ["Дания", "Германия", "Шотландия", "Германия", "Швеция", "Англия",
           "Голландия", "Япония"],
}
SYSTEMS = ["GRASSO / KUHLAUTOMAT", "HOWDEN", "MYCOM", "SABROE", "STAL",
           "AERZEN", "YORK DYKIN", "HITACHI"]
ENGINES = ["MAN", "Wartsila", "Yanmar", "Hyundai Himsen", "MAK",
           "Caterpillar", "Deutz", "Daihatsu"]
PART_ENGINES = ["MAN", "VOLVO PENTA", "Wartsila", "STX", "Yanmar", "MTU",
                "Hyundai Himsen", "CUMMINS", "MAK", "SULZER", "Caterpillar",
                "DETROIT DIESEL", "Deutz", "ROLLS ROYCE", "Daihatsu", "SCANIA",
                "WICHMANN", "GUASCOR"]
PART_COMPRESSORS = ["STALL", "Sabroe", "Bitzer", "Howden", "Mycom", "J&amp;E Hall"]
TURBO = ["ABB", "KBB", "MET", "NAPIER", "MAN"]
PUMPS = ["HERMETIC", "WITT"]

SVC = {}

SVC["en"] = {
    "refrigeration-systems": dict(
        title="Refrigeration systems and equipment",
        short="Design, modernisation, compressor overhaul, installation and "
              "commissioning of marine and industrial refrigeration.",
        lead="The company's original discipline, and still the deepest — more than "
             "a decade of refrigeration work on fishing vessels and shore plant.",
        meta="Marine and industrial refrigeration: compressor overhaul, system "
             "modernisation, class-approved design documentation, installation and "
             "commissioning. SABROE, BITZER, HOWDEN, KUHLAUTOMAT, STAL, GRASSO, MYCOM.",
        h_works="What we carry out", h_compressors="Compressors we service",
        h_systems="Systems we modernise",
        works=["Diagnostics and repair of refrigeration compressors, at all levels of complexity.",
               "Diagnostics and repair of commercial and marine refrigeration equipment.",
               "Consultancy on selecting, installing and maintaining refrigeration equipment.",
               "Development of automatic control systems for compressors and refrigeration plant.",
               "Design documents and working drawings for ship refrigeration equipment, prepared "
               "to classification society requirements — including getting them approved.",
               "Installation of refrigeration equipment and refrigerant piping.",
               "Start-up, adjustment and handover to the client."],
        note="We take both one-off jobs and regular contracted service work. All "
             "equipment and spare parts we manufacture and supply comply with quality "
             "and international standards.",
        sys_note="Modernisation and repair of refrigeration systems for fishing "
                 "vessels and shore installations:"),
    "ship-engine-repair": dict(
        title="Ship equipment and engine repair",
        short="Overhaul of 2-stroke and 4-stroke diesel engines, engine room "
              "machinery and deck equipment.",
        lead="Keeping a vessel's machinery inside its operating envelope — main "
             "engines, auxiliaries, and the deck equipment the crew depends on.",
        meta="Overhaul and repair of 4-stroke and 2-stroke marine diesel engines, "
             "engine room machinery and deck equipment. MAN, Wartsila, Yanmar, "
             "Hyundai Himsen, MAK, Caterpillar, Deutz, Daihatsu.",
        h_engines="Diesel engine overhaul", h_machinery="Engine room machinery",
        h_deck="Deck equipment", h_how="How we work",
        engines="We overhaul and repair <strong>4-stroke and 2-stroke diesel "
                "engines</strong> of most types and models. Work runs from diagnostics "
                "through to the upgrades that restore efficiency and extend service "
                "life, on main and auxiliary engines alike.",
        engines_note="Engines we work on regularly:",
        machinery="Beyond the engines themselves, we maintain and repair the rest of "
                  "the machinery space — reduction gears, shafting and the auxiliary "
                  "equipment that surrounds the main plant.",
        deck="Deck equipment is maintained on a regular cycle so that it works when "
             "it is needed: deck systems, ladders and steps, life-saving appliances "
             "and associated gear. Where equipment has been damaged, we repair it "
             "back to full working condition.",
        how="We use quality tooling and vetted sources of spare parts, and every "
            "repair is carried out to meet the applicable safety standards. All work "
            "and equipment carries our warranty."),
    "hull-and-piping": dict(
        title="Hull and piping works",
        short="Steel and stainless steel pipe systems for shipbuilding, ship repair "
              "and industry, including surface coating.",
        lead="Pipe systems and steel structures, from the drawing through to a "
             "coated, finished product delivered wherever it is needed.",
        meta="Manufacture of steel and stainless steel pipe systems for shipbuilding, "
             "ship repair and industry. Hull and steel structure repair, galvanising "
             "and paint work, delivered worldwide.",
        h_pipes="Pipe systems", h_scope="The full scope",
        pipes="We manufacture <strong>all types of steel and stainless steel pipe "
              "systems</strong> used in shipbuilding, ship repair and other "
              "industries, and we carry out major repairs to hulls and other steel "
              "structures.",
        pipes2="Surface coating is done in house — galvanising and paint work — so "
               "the product leaves finished rather than needing another supplier.",
        scope="Our team of qualified specialists can take a project end to end: the "
              "design work, ordering and delivering the materials, and carrying out "
              "the work itself to schedule and to standard.",
        scope2="At the customer's request, finished products are shipped to any "
               "country in the world."),
    "spare-parts": dict(
        title="Supply of spare parts",
        short="Sourcing and delivery of spare parts and consumables for marine "
              "engines and refrigeration compressors.",
        lead="Selecting, ordering and delivering the parts a repair needs — with "
             "stock held in Klaipeda so the common ones do not wait on a supplier.",
        meta="Supply of spare parts for marine engines and refrigeration compressors "
             "— MAN, Wartsila, Caterpillar, SULZER, Sabroe, Bitzer, Howden, Mycom, "
             "Danfoss valves. Warehouse in Klaipeda.",
        h_source="What we source", h_delivery="Delivery time",
        intro="On request we will select, order and deliver spare parts and special "
              "equipment.",
        h_c="Compressors and their parts", h_e="2-stroke and 4-stroke engine parts",
        h_p="Refrigerant pumps and their parts", h_t="Turbogenerator parts",
        h_o="Also supplied",
        other=["Parts for heat exchangers.",
               "Valves and their parts — Danfoss, AWP and others.",
               "Assembly and supply of complete refrigeration units."],
        delivery="We work to keep delivery times short, and we hold a "
                 "<strong>warehouse in Klaipeda</strong> for that reason — it is what "
                 "lets us offer a better combination of price and delivery date than "
                 "sourcing every part from scratch."),
}

SVC["lt"] = {
    "refrigeration-systems": dict(
        title="Šaldymo sistemos ir įranga",
        short="Techninės dokumentacijos projektavimas ir įforminimas, šaldymo įrangos "
              "modernizavimas, visų tipų kompresorių remontas, šaldymo agregatų "
              "montavimas bei tiekimas.",
        lead="Pirminė įmonės specializacija ir iki šiol giliausia — daugiau nei "
             "dešimtmetis šaldymo darbų žvejybiniuose laivuose ir kranto įrenginiuose.",
        meta="Laivų ir pramoninė šaldymo įranga: kompresorių remontas, sistemų "
             "modernizavimas, klasifikacinių bendrovių patvirtinti projektiniai "
             "dokumentai, montavimas ir paleidimas. SABROE, BITZER, HOWDEN, "
             "KUHLAUTOMAT, STAL, GRASSO, MYCOM.",
        h_works="Kompanija LITPROFIT atlieka šiuos darbus",
        h_compressors="Aptarnaujami kompresoriai", h_systems="Modernizuojamos sistemos",
        works=["įvairaus sudėtingumo šaldymo įrenginių kompresorių diagnostika ir remontas;",
               "komercinių ir laivų šaldymo įrenginių diagnostika bei remontas;",
               "konsultacijos šaldymo įrangos parinkimo bei jos montavimo ir techninio "
               "aptarnavimo klausimais;",
               "kompresorių ir šaldymo įrangos automatinio valdymo sistemų parengimas;",
               "laivų šaldymo įrangos projektinių dokumentų ir darbinių brėžinių pagal "
               "klasifikacinių bendrovių reikalavimus parengimas, įskaitant suderinimą;",
               "šaldymo įrangos bei šaltnešio vamzdynų montavimo darbai;",
               "šaldymo įrenginių paleidimo bei derinimo darbai ir pridavimas užsakovui."],
        note="Atliekami kaip vienkartiniai, taip ir nuolatiniai (pagal sutartį) serviso "
             "darbai. Visa mūsų įmonės gaminama bei tiekiama įranga ir atsarginės dalys "
             "atitinka kokybės bei tarptautinių standartų reikalavimus.",
        sys_note="Žvejybinių laivų ir kranto įrenginių šaldymo sistemų modernizavimas "
                 "ir remontas:"),
    "ship-engine-repair": dict(
        title="Laivų įrangos ir variklių remontas",
        short="2-takčių ir 4-takčių dyzelinių variklių, mašinų skyriaus mechanizmų "
              "ir denio įrangos remontas.",
        lead="Kad laivo mechanizmai veiktų optimaliai ir saugiai — pagrindiniai ir "
             "pagalbiniai varikliai bei denio įranga, kuria pasitiki įgula.",
        meta="4-takčių ir 2-takčių laivų dyzelinių variklių, mašinų skyriaus mechanizmų "
             "ir denio įrangos remontas. MAN, Wartsila, Yanmar, Hyundai Himsen, MAK, "
             "Caterpillar, Deutz, Daihatsu.",
        h_engines="Variklių remontas", h_machinery="Mašinų skyriaus mechanizmai",
        h_deck="Denio įranga", h_how="Kaip dirbame",
        engines="Remontuojame įvairių tipų ir modelių <strong>4-takčius ir 2-takčius "
                "dyzelinius variklius</strong>. Atliekame išsamią diagnostiką ir "
                "atnaujinimus, kad užtikrintume variklio efektyvumą ir ilgaamžiškumą — "
                "tiek pagrindinių, tiek pagalbinių variklių.",
        engines_note="Varikliai, su kuriais dirbame nuolat:",
        machinery="Specializuojamės ne tik laivų variklių, bet ir kitų mašinų skyriaus "
                  "mechanizmų aptarnavime — reduktorių, velenų ir kitų mechanizmų "
                  "priežiūroje bei remonte.",
        deck="Denio įranga yra esminė laivo dalis, todėl siūlome reguliarią priežiūrą, "
             "kad užtikrintume jos tinkamą veikimą: denio sistemų, laiptelių, gelbėjimo "
             "priemonių ir kitos denio įrangos aptarnavimą. Jei įranga patyrė pažeidimų, "
             "atliekame remonto darbus.",
        how="Naudojame tik kokybiškus įrankius ir patikimus atsarginių dalių šaltinius. "
            "Visi remonto darbai atliekami laikantis aukščiausių saugos standartų. "
            "Visiems darbams ir įrangai suteikiama garantija."),
    "hull-and-piping": dict(
        title="Laivų korpusų ir vamzdynų darbai",
        short="Pagrindiniai laivų korpusų ir kitų plieno konstrukcijų remonto darbai, "
              "laivų bei pramoninių vamzdynų montavimas.",
        lead="Vamzdynų sistemos ir plieno konstrukcijos — nuo brėžinio iki padengto, "
             "baigto gaminio, pristatyto ten, kur reikia.",
        meta="Visų tipų plieninių ir nerūdijančio plieno vamzdžių sistemų gamyba laivų "
             "statybai, laivų remontui ir pramonei. Korpusų remontas, cinkavimas ir "
             "dažymas, siuntimas į visas pasaulio šalis.",
        h_pipes="Vamzdynų sistemos", h_scope="Visa apimtis",
        pipes="Gaminame <strong>visų tipų plieninių, taip pat ir nerūdijančio plieno "
              "vamzdžių sistemas</strong>, naudojamas laivų statybos, laivų remonto ir "
              "kitose pramonės srityse, bei atliekame pagrindinius laivų korpusų ir kitų "
              "plieno konstrukcijų remonto darbus.",
        pipes2="Paviršiaus padengimo darbus — cinkavimą bei dažymą — atliekame patys, "
               "todėl gaminys išvyksta baigtas, be papildomo tiekėjo.",
        scope="Profesionali kvalifikuotų specialistų komanda pasirengusi pilnai "
              "įgyvendinti projektą: atlikti projektavimo darbus, užsakyti ir pristatyti "
              "reikiamas medžiagas, laiku ir kokybiškai atlikti numatytus darbus.",
        scope2="Pagamintus gaminius, Užsakovo pageidavimu, siunčiame į visas pasaulio šalis."),
    "spare-parts": dict(
        title="Atsarginių dalių tiekimas",
        short="Atsarginių dalių ir eksploatacinių medžiagų tiekimas laivų variklių ir "
              "šaldymo kompresorių remonto darbams, šaldymo agregatų surinkimas bei tiekimas.",
        lead="Parenkame, užsakome ir pristatome remontui reikalingas dalis — sandėlis "
             "Klaipėdoje reiškia, kad dažniausiai naudojamų dalių laukti nereikia.",
        meta="Atsarginių dalių tiekimas laivų varikliams ir šaldymo kompresoriams — MAN, "
             "Wartsila, Caterpillar, SULZER, Sabroe, Bitzer, Howden, Mycom, Danfoss "
             "vožtuvai. Sandėlis Klaipėdoje.",
        h_source="Ką tiekiame", h_delivery="Pristatymo terminai",
        intro="Jūsų pageidavimu parinksime, užsakysime bei pristatysime reikiamas "
              "atsargines dalis bei specialią įrangą.",
        h_c="Kompresoriai ir jų dalys", h_e="2-takčių ir 4-takčių variklių dalys",
        h_p="Šaltnešio siurbliai ir jų dalys", h_t="Turbogeneratorių dalys",
        h_o="Taip pat tiekiame",
        other=["šilumokaičių dalys;",
               "vožtuvai (Danfoss, AWP ir kt.) ir jų dalys;",
               "šaldymo agregatų surinkimas bei tiekimas."],
        delivery="Siekiame maksimaliai sumažinti atsarginių dalių bei įrangos tiekimo "
                 "terminus, todėl turime <strong>sandėlį Klaipėdoje</strong>, kas leidžia "
                 "pasiūlyti Užsakovui patį palankiausią kainos bei pristatymo laiko variantą."),
}

SVC["ru"] = {
    "refrigeration-systems": dict(
        title="Холодильные системы и оборудование",
        short="Проектирование и оформление технической документации, модернизация "
              "холодильного оборудования, ремонт компрессоров всех типов, монтаж и "
              "поставка холодильных агрегатов.",
        lead="Первоначальная специализация компании и до сих пор самая глубокая — "
             "более десяти лет холодильных работ на рыболовных судах и береговых установках.",
        meta="Судовое и промышленное холодильное оборудование: ремонт компрессоров, "
             "модернизация систем, проектная документация по требованиям "
             "классификационных обществ, монтаж и пусконаладка. SABROE, BITZER, HOWDEN, "
             "KUHLAUTOMAT, STAL, GRASSO, MYCOM.",
        h_works="Компания LITPROFIT выполняет следующие работы",
        h_compressors="Обслуживаемые компрессоры", h_systems="Модернизируемые системы",
        works=["диагностика и ремонт компрессоров холодильных установок любой сложности;",
               "диагностика и ремонт коммерческих и судовых холодильных установок;",
               "консультирование по вопросам подбора холодильного оборудования, его "
               "монтажа и технического обслуживания;",
               "разработка систем автоматического управления компрессорным и холодильным "
               "оборудованием;",
               "разработка проектной документации судовых холодильных установок и рабочих "
               "чертежей в соответствии с требованиями классификационных обществ с "
               "последующим согласованием;",
               "монтажные работы по установке холодильного оборудования и трубопроводов "
               "хладагента;",
               "пусконаладочные работы по запуску холодильной установки и сдача в "
               "эксплуатацию заказчику."],
        note="Сервисные работы выполняются как на разовой, так и на постоянной договорной "
             "основе. Всё оборудование и запасные части, производимые и поставляемые нашей "
             "компанией, имеют высокий уровень качества и отвечают требованиям мировых "
             "стандартов.",
        sys_note="Модернизация и ремонт холодильных систем рыболовных судов и береговых "
                 "установок:"),
    "ship-engine-repair": dict(
        title="Ремонт судового оборудования и двигателей",
        short="Ремонт 2-х тактных и 4-х тактных дизельных двигателей, механизмов "
              "машинного отделения и палубного оборудования.",
        lead="Чтобы механизмы судна работали оптимально и безопасно — главные и "
             "вспомогательные двигатели и палубное оборудование, на которое полагается экипаж.",
        meta="Ремонт 4-х тактных и 2-х тактных судовых дизельных двигателей, механизмов "
             "машинного отделения и палубного оборудования. MAN, Wartsila, Yanmar, Hyundai "
             "Himsen, MAK, Caterpillar, Deutz, Daihatsu.",
        h_engines="Ремонт двигателей", h_machinery="Механизмы машинного отделения",
        h_deck="Палубное оборудование", h_how="Как мы работаем",
        engines="Ремонтируем <strong>4-х тактные и 2-х тактные дизельные двигатели</strong> "
                "разных типов и моделей. Выполняем тщательную диагностику и процедуры по "
                "обновлению для обеспечения эффективности и долговечности двигателя — как "
                "главных, так и вспомогательных.",
        engines_note="Двигатели, с которыми мы работаем постоянно:",
        machinery="Мы специализируемся в обслуживании не только судовых двигателей, но и "
                  "других механизмов машинного отделения — редукторов, валов и прочих "
                  "механизмов.",
        deck="Палубное оборудование — основная часть судна, поэтому мы предлагаем "
             "регулярное обслуживание: палубных систем, трапов, спасательных средств и "
             "другого палубного оборудования. При повреждениях выполняем необходимый ремонт.",
        how="Мы используем только качественный инструмент и проверенные источники запасных "
            "частей, а каждый ремонт выполняется в соответствии с действующими стандартами "
            "безопасности. На все работы и оборудование предоставляется гарантия."),
    "hull-and-piping": dict(
        title="Судокорпусные и трубопроводные работы",
        short="Основные работы по ремонту судокорпусных и других стальных конструкций, "
              "монтаж судовых и промышленных трубопроводов.",
        lead="Трубопроводные системы и стальные конструкции — от чертежа до покрытого, "
             "готового изделия, доставленного туда, где оно нужно.",
        meta="Изготовление стальных трубопроводных систем всех типов, в том числе из "
             "нержавеющей стали, для судостроения, судоремонта и промышленности. Оцинковка "
             "и покраска, отправка во все страны мира.",
        h_pipes="Трубопроводные системы", h_scope="Полный объём",
        pipes="Изготавливаем <strong>стальные трубопроводные системы всех типов, а также из "
              "нержавеющей стали</strong>, используемые в судостроении, судоремонте и других "
              "промышленных отраслях, и выполняем основные работы по ремонту судокорпусных и "
              "других стальных конструкций.",
        pipes2="Работы по оцинковке и покраске поверхностей выполняем сами, поэтому изделие "
               "уходит готовым, без привлечения ещё одного поставщика.",
        scope="Профессиональная команда квалифицированных специалистов готова полностью "
              "осуществить проект: выполнить проектировочные работы, заказать и доставить "
              "необходимые материалы, вовремя и качественно выполнить предусмотренные работы.",
        scope2="Изготовленные изделия, по желанию Заказчика, отправляем во все страны мира."),
    "spare-parts": dict(
        title="Поставка запасных частей",
        short="Поставка запасных частей и эксплуатационных материалов для ремонта судовых "
              "двигателей и холодильных компрессоров, сборка и поставка холодильных агрегатов.",
        lead="Подбираем, заказываем и доставляем детали, нужные для ремонта — склад в "
             "Клайпеде означает, что самые ходовые позиции не приходится ждать.",
        meta="Поставка запасных частей для судовых двигателей и холодильных компрессоров — "
             "MAN, Wartsila, Caterpillar, SULZER, Sabroe, Bitzer, Howden, Mycom, клапаны "
             "Danfoss. Склад в Клайпеде.",
        h_source="Что мы поставляем", h_delivery="Сроки поставки",
        intro="По вашему желанию подберём, закажем и доставим необходимые запасные части и "
              "специальное оборудование.",
        h_c="Компрессоры и их части", h_e="Запчасти для 2-х и 4-х тактных двигателей",
        h_p="Холодильные насосы и их части", h_t="Запчасти для турбогенераторов",
        h_o="Также поставляем",
        other=["запчасти для теплообменников;",
               "клапаны (Danfoss, AWP и др.) и их части;",
               "сборка и поставка холодильных агрегатов."],
        delivery="Стараемся максимально сократить сроки поставки запасных частей и "
                 "оборудования, поэтому имеем <strong>склад в Клайпеде</strong>, что позволяет "
                 "предложить Заказчику самый благоприятный вариант цены и срока доставки."),
}

# display order — refrigeration leads, and the numbering follows this list
ORDER = ["refrigeration-systems", "ship-engine-repair", "hull-and-piping", "spare-parts"]

# image per service, shared across languages
IMG = {
    # the first two are our own workshop; the other two are still stock and
    # look it -- replace them as soon as there are photographs of an engine
    # job and a pipe weld
    "refrigeration-systems": ("workshop-overhaul.webp", 1320, 877),
    "ship-engine-repair": ("svc-engine-repair.webp", 600, 410),
    "hull-and-piping": ("svc-hull-piping.webp", 800, 533),
    "spare-parts": ("workshop-valves.webp", 1313, 444),
}
ALT = {
    "en": {"refrigeration-systems": "A screw compressor stripped for overhaul, "
           "rotor set and bearings laid out on the bench",
           "ship-engine-repair": "Marine diesel engine in a ship's engine room",
           "hull-and-piping": "Welder joining a steel pipe bend",
           "spare-parts": "Stop, solenoid and regulating valves held in stock"},
    "lt": {"refrigeration-systems": "Sraigtinis kompresorius, išardytas kapitaliniam "
           "remontui: rotoriai ir guoliai ant stalo",
           "ship-engine-repair": "Laivo dyzelinis variklis mašinų skyriuje",
           "hull-and-piping": "Suvirintojas jungia plieninę vamzdžio alkūnę",
           "spare-parts": "Sandėlyje laikomi uždaromieji, elektromagnetiniai ir "
           "reguliuojamieji vožtuvai"},
    "ru": {"refrigeration-systems": "Винтовой компрессор, разобранный для капитального "
           "ремонта: роторы и подшипники на верстаке",
           "ship-engine-repair": "Судовой дизельный двигатель в машинном отделении",
           "hull-and-piping": "Сварщик соединяет стальной отвод трубы",
           "spare-parts": "Запорные, электромагнитные и регулирующие клапаны на складе"},
}


# ============================================================
# COMPLETED PROJECTS
# ============================================================
# Empty on purpose, and the site is correct while it stays empty: no cards, no
# pages, no sitemap entries, no link to a section that does not exist. Add one
# entry and it grows a card on Completed works, its own page with the drawing
# and photographs, a sitemap line and its own structured data -- the same
# arrangement as the booking URL, where a blank value removes the element
# rather than shipping a dead one.
#
# Nothing here may be invented. Every field is a claim about work a real
# company did for a real owner, and a portfolio is the one part of a site where
# a plausible guess is indistinguishable from a lie.
#
# One entry looks like this:
#
#     dict(slug="rsw-refit-2024",
#          vessel="MV Example",            # or "" if the owner will not be named
#          owner="Example Fishing Ltd",    # or ""
#          year="2024",
#          port="Klaipeda",                # where the work was done
#          days=18,                        # alongside, or "" if not recorded
#          scope="refrigeration-systems",  # must match a services slug
#          title="RSW plant overhaul",
#          lead="One sentence a superintendent would recognise.",
#          work=["What was actually done.", "One line per item."],
#          plant=["SABROE SMC 116", "R404A"],   # equipment involved
#          photos=["workshop-overhaul", "workshop-rotors"]),  # names in assets/photos
#
PROJECTS = []


# ============================================================
# INTERIOR PAGES
# ============================================================
P = {}

P["en"] = dict(
    about_eyebrow="About us", about_h1="A Klaipeda ship repair company, working worldwide",
    about_lead="%(legal)s was established in %(founded)s. More than a decade in the "
               "refrigeration equipment market, a long list of completed projects, and "
               "business partners who have stayed.",
    about_meta="%(legal)s was established in %(founded)s in Klaipeda, Lithuania. Marine "
               "refrigeration and engine repair specialists, RINA and PRS certified.",
    a_spec="What we specialise in",
    a_spec_list=["Design and selection of industrial refrigeration equipment.",
                 "Modernisation and repair of refrigeration systems for fishing boats and "
                 "shore installations.",
                 "Installation and supply of refrigeration equipment.",
                 "Overhaul of main and auxiliary engines.",
                 "Positioning of ships in the port of Klaipeda, Lithuania, for repair works."],
    a_people="The people",
    # Not new copy: the three words a_people_1 already uses about the team,
    # promoted to a heading so the section has one. Worth the client's eye
    # in LT before launch.
    a_people_h="Reliable, qualified, time-tested",
    a_people_1="We have a team of reliable, qualified and time-tested professionals, and "
               "we provide a <strong>warranty on all works and equipment</strong>.",
    a_people_2="We are committed to continuous improvement and pay close attention to "
               "developments in the market. We take each customer's wishes into account, "
               "and aim to offer the solution that is most sensible on cost, on time, and "
               "on the equipment supplied.",
    a_cert="Certification and cover",
    a_cert_1="%(legal)s holds the <strong>RINA</strong> certificate, and is certified by "
             "the <strong>Polish Register of Shipping (PRS)</strong>.",
    a_cert_2="The company's civil liability is insured with <strong>Compensa Vienna "
             "Insurance Group, ADB</strong> for <strong>EUR 250,000</strong>, under "
             "insurance policy no. 230 0008143 / 2020.",
    a_details="Company details",

    svc_h1="What we repair, supply and install",
    svc_page_lead="Marine engines, refrigeration plant, pipe systems and the spare parts "
                  "that keep all three running.",
    svc_meta="Marine engine repair, refrigeration systems, hull and piping works and spare "
             "parts supply — from a single contractor in Klaipeda, Lithuania.",

    cw_eyebrow="Completed works", cw_h1="Where the work has been done",
    # Photographs of the client's own workshop. The captions describe what is
    # visible in the frame and nothing beyond it -- a caption that claims a
    # process is a claim about the company, and those come from the client.
    shots_eyebrow="In the workshop", shots_h2="What an overhaul looks like",
    shots_lead="Klaipeda, on the bench. Machines come in whole, leave the same way, "
               "and everything in between is measured.",
    shot_rotors="The rotor set beside its casing bore. Clearances are measured "
                "against the maker\u2019s limits before anything goes back together.",
    shot_bench="Compressor housing, rotors and bearing pedestals on the bench.",
    cw_lead="Two strands run through everything the company has delivered since "
            "%(founded)s: engines, and refrigeration.",
    cw_meta="Engine overhauls and refrigeration projects delivered by %(legal)s for "
            "fishing fleets, shipowners and shore installations.",
    # Two one-word section labels, the two strands the page is about. Worth
    # the client's eye in LT before launch, like a_people_h.
    cw_engines_e="Engines",
    cw_refrig_e="Refrigeration",
    cw_engines="Ship equipment and engine repair",
    cw_engines_p="Overhauls of main and auxiliary engines carried out on fishing vessels "
                 "and commercial ships, covering both 4-stroke and 2-stroke plant, "
                 "alongside the engine room and deck equipment that surrounds them.",
    cw_refrig="Refrigeration equipment",
    cw_refrig_p="The company's longest-running line of work: modernisation and repair of "
                "refrigeration systems on fishing boats and shore installations, compressor "
                "overhauls, class-approved design documentation, installation of plant and "
                "refrigerant piping, and commissioning through to handover.",
    cw_who="Who the work was for",

    p_eyebrow="Partners", p_h1="Manufacturers we represent, clients we work for",
    p_lead="Two authorised representations, and a client list built up over more than a "
           "decade.",
    p_meta="Authorised BITZER partner and DANFOSS marine line representative. Clients "
           "include Sealord, Limarko Group, Ocean Whale Company and Baltreids.",
    p_rep_h2="Manufacturers we represent",
    p_rep_lead="Two direct appointments — factory backing on parts, pricing and warranty.",
    p_clients_h2="Companies we have worked for",
    p_clients_lead="Fishing groups, shipowners and shipyards across the Baltic and beyond.",

    c_no="No.", c_issued="Issued", c_valid="Valid until",
    c_shot_alt="First page of the %(name)s certificate",
    # Straight off the PRS certificate, which is the definitive statement of
    # what the company is approved to repair. It was not on the site at all.
    c_scope_h="What the PRS approval covers",
    c_scope_lead="Certificate TM/1703/842502/25 approves UAB \u201eLitprofit\u201c to carry "
                 "out repairs of:",
    c_scope=["Main and auxiliary engines \u2014 two-stroke and four-stroke",
             "Deck machinery and mechanisms",
             "Fuel equipment of main and auxiliary engines, compressors and pumps",
             "Turbochargers",
             "Reduction gears",
             "Alignment of diesel engines",
             "Refrigeration equipment and systems"],
    c_scope_extra="It also approves the <strong>design</strong> of refrigeration "
                  "equipment and systems \u2014 not only their repair.",
    c_eyebrow="Certificates", c_h1="Certification and cover",
    c_lead="Class approvals, and the liability insurance behind the work.",
    c_meta="RINA and PRS certification, and EUR 250,000 civil liability insurance with "
           "Compensa Vienna Insurance Group.",
    c_what="What these cover",
    c_what_p="<strong>RINA</strong> is an Italian classification society; "
             "<strong>PRS</strong> is the Polish Register of Shipping. Certification by a "
             "class society is what lets a shipowner accept our work and documentation "
             "without commissioning a separate inspection to verify it.",
    c_ins="Insurance", c_war="Warranty",
    c_war_p="We provide a warranty on all works and equipment. All equipment and spare "
            "parts manufactured and supplied by the company comply with quality and "
            "international standards.",
    c_open="Open", c_rina_note="Italian classification society",
    c_prs_note="Polish Register of Shipping",

    k_eyebrow="Contacts", k_h1="Talk to us",
    k_lead="Enquiries reach people who can answer technical questions, not a call centre.",
    k_meta="%(street)s, %(city)s, %(country)s. Phone %(phone)s, email %(email)s. 24/7 service.",
    k_service="Service", k_service_p="24/7 — we are ready to always provide prompt and "
                                     "competent assistance.",
    k_form_h2="Send an enquiry",
    k_form_lead="The fastest route to a useful answer is the vessel or plant, the "
                "equipment, the port and your timescale.",

    pr_eyebrow="Legal", pr_h1="Privacy policy",
    pr_lead="How %(legal)s handles personal data collected through this website.",
    pr_updated="Last updated",
    pr_h=["Who we are", "What we collect", "Third parties that receive data",
          "Legal basis", "How long we keep it", "Your rights", "Changes"],
    pr_who="%(legal)s is the controller of personal data collected through this website.",
    pr_collect="This website has no user accounts, no analytics and sets no cookies of its "
               "own. Data reaches us through the enquiry form, through direct contact by "
               "email or phone, and through the hosting provider's server logs.",
    pr_third="<strong>GitHub, Inc.</strong> &mdash; website hosting and request logs. "
             "<strong>Calendly LLC</strong> &mdash; appointment booking, but only if you use it: "
             "the booking window is loaded from Calendly at the moment you click "
             "&ldquo;Book a call&rdquo;, not when the page opens. Until then no request reaches "
             "Calendly and it learns nothing about your visit. If you do open it, Calendly "
             "receives your IP address and whatever you enter to book, under its own privacy "
             "policy. Apart from that this site loads no third-party scripts, fonts, analytics "
             "or embeds, and the typeface is served from our own domain.",
    pr_basis="<strong>Consent</strong> (GDPR Art. 6(1)(a)) for the enquiry form, which you "
             "may withdraw at any time, and <strong>legitimate interest</strong> "
             "(Art. 6(1)(f)) for responding to enquiries and keeping the site secure.",
    pr_keep="Enquiries are kept as long as needed for the enquiry or the resulting project, "
            "and for any statutory retention period that applies.",
    pr_rights="Under the GDPR you may request access, correction, erasure, restriction, "
              "portability, and you may object to processing based on legitimate interest. "
              "Write to %(email)s and we will respond within one month. Complaints may be "
              "lodged with the Lithuanian State Data Protection Inspectorate.",
    pr_changes="If this policy changes, the revised version will be published on this page "
               "with a new date at the top.",
    nf_h1="Page not found",
    nf_lead="The page you asked for is not here. It may have moved when the site was rebuilt.",
    nf_home="Go to the homepage", nf_contact="Contact us",
)

P["lt"] = dict(
    about_eyebrow="Apie mus", about_h1="Klaipėdos laivų remonto įmonė, dirbanti visame pasaulyje",
    about_lead="%(legal)s įkurta %(founded)s metais. Daugiau nei dešimtmetis šaldymo įrangos "
               "rinkoje, ilgas įgyvendintų projektų sąrašas ir išlikę verslo partneriai.",
    about_meta="%(legal)s įkurta %(founded)s metais Klaipėdoje. Laivų šaldymo įrangos ir "
               "variklių remonto specialistai, RINA ir PRS sertifikuoti.",
    a_spec="Mūsų specializacija",
    a_spec_list=["pramoninės šaldymo įrangos projektavimas ir parinkimas;",
                 "žvejybinių laivų ir kranto įrenginių šaldymo sistemų modernizavimas ir remontas;",
                 "šaldymo įrangos montavimas ir tiekimas;",
                 "pagrindinių bei pagalbinių variklių kapitalinis remontas;",
                 "laivų pastatymas Klaipėdos uoste remonto darbams atlikti."],
    a_people="Komanda",
    a_people_h="Patikimi, kvalifikuoti, laiko patikrinti",
    a_people_1="Mūsų įmonėje dirba patikimų, kvalifikuotų ir laiko patikrintų specialistų "
               "komanda. <strong>Visiems darbams ir įrangai suteikiama garantija</strong>.",
    a_people_2="Nuolat tobulėjame, domimės rinkos naujovėmis, įdėmiai išklausome klientų "
               "pageidavimų bei pasiūlymų, todėl užsakovui siekiame pasiūlyti patį "
               "optimaliausią darbų kainos bei laiko sąnaudų variantą.",
    a_cert="Sertifikatai ir draudimas",
    a_cert_1="Įmonei %(legal)s suteiktas kompanijos <strong>RINA</strong> sertifikatas, taip "
             "pat ji sertifikuota <strong>Lenkijos laivų registro (PRS)</strong>.",
    a_cert_2="Įmonės civilinė atsakomybė apdrausta kompanijoje <strong>ADB „Compensa Vienna "
             "Insurance Group“</strong> <strong>250 000,00 EUR</strong> sumai. Draudimo "
             "polisas Nr. 230 0008143 / 2020.",
    a_details="Rekvizitai",

    svc_h1="Ką remontuojame, tiekiame ir montuojame",
    svc_page_lead="Laivų varikliai, šaldymo įranga, vamzdynų sistemos ir atsarginės dalys, "
                  "reikalingos visiems trims.",
    svc_meta="Laivų variklių remontas, šaldymo sistemos, korpusų ir vamzdynų darbai bei "
             "atsarginių dalių tiekimas — iš vieno rangovo Klaipėdoje.",

    cw_eyebrow="Atlikti darbai", cw_h1="Kur darbai buvo atlikti",
    shots_eyebrow="Dirbtuvėse", shots_h2="Kaip atrodo kapitalinis remontas",
    shots_lead="Klaipėda, ant stalo. Mašinos atkeliauja surinktos, tokios ir išvyksta, "
               "o viskas, kas tarp to \u2014 išmatuota.",
    shot_rotors="Rotoriai šalia korpuso angos. Tarpai matuojami pagal gamintojo "
                "leistinas ribas prieš surenkant atgal.",
    shot_bench="Kompresoriaus korpusas, rotoriai ir guolių atramos ant stalo.",
    cw_lead="Dvi kryptys eina per viską, ką įmonė nuveikė nuo %(founded)s metų: varikliai "
            "ir šaldymas.",
    cw_meta="Variklių kapitalinis remontas ir šaldymo projektai, kuriuos %(legal)s atliko "
            "žvejybos laivynams, laivų savininkams ir kranto įrenginiams.",
    cw_engines_e="Varikliai",
    cw_refrig_e="Šaldymas",
    cw_engines="Laivų įrangos ir variklių remontas",
    cw_engines_p="Pagrindinių ir pagalbinių variklių kapitalinis remontas žvejybiniuose ir "
                 "komerciniuose laivuose, tiek 4-takčių, tiek 2-takčių, kartu su mašinų "
                 "skyriaus mechanizmais ir denio įranga.",
    cw_refrig="Šaldymo įranga",
    cw_refrig_p="Ilgiausiai vykdoma įmonės veiklos kryptis: žvejybinių laivų ir kranto "
                "įrenginių šaldymo sistemų modernizavimas ir remontas, kompresorių "
                "kapitalinis remontas, klasifikacinių bendrovių patvirtinti projektiniai "
                "dokumentai, įrangos ir šaltnešio vamzdynų montavimas, paleidimas ir "
                "pridavimas užsakovui.",
    cw_who="Kam darbai buvo atlikti",

    p_eyebrow="Partneriai", p_h1="Gamintojai, kuriems atstovaujame, ir klientai, kuriems dirbame",
    p_lead="Du autorizuoti atstovavimai ir klientų sąrašas, sukauptas per daugiau nei dešimtmetį.",
    p_meta="Autorizuoti BITZER partneriai ir DANFOSS jūrinės linijos atstovai. Tarp klientų — "
           "Sealord, Limarko Group, Ocean Whale Company ir Baltreids.",
    p_rep_h2="Gamintojai, kuriems atstovaujame",
    p_rep_lead="Du tiesioginiai paskyrimai — gamyklos garantija dalims, kainoms ir įrangai.",
    p_clients_h2="Įmonės, kurioms dirbome",
    p_clients_lead="Žvejybos grupės, laivų savininkai ir laivų statyklos Baltijos regione ir toliau.",

    c_no="Nr.", c_issued="Išduota", c_valid="Galioja iki",
    c_shot_alt="%(name)s sertifikato pirmasis puslapis",
    c_scope_h="Ką apima PRS pripažinimas",
    c_scope_lead="Sertifikatas TM/1703/842502/25 suteikia UAB \u201eLitprofit\u201c teisę "
                 "remontuoti:",
    c_scope=["Pagrindinius ir pagalbinius variklius \u2014 dviejų ir keturių taktų",
             "Denio mechanizmus ir įrenginius",
             "Pagrindinių ir pagalbinių variklių, kompresorių ir siurblių kuro įrangą",
             "Turbokompresorius",
             "Reduktorius",
             "Dyzelinių variklių centravimą",
             "Šaldymo įrangą ir sistemas"],
    c_scope_extra="Jis taip pat suteikia teisę <strong>projektuoti</strong> šaldymo "
                  "įrangą ir sistemas \u2014 ne tik jas remontuoti.",
    c_eyebrow="Sertifikatai", c_h1="Sertifikatai ir draudimas",
    c_lead="Klasifikacinių bendrovių patvirtinimai ir civilinės atsakomybės draudimas.",
    c_meta="RINA ir PRS sertifikatai bei 250 000 EUR civilinės atsakomybės draudimas "
           "kompanijoje Compensa Vienna Insurance Group.",
    c_what="Ką jie apima",
    c_what_p="<strong>RINA</strong> — Italijos klasifikacinė bendrovė, "
             "<strong>PRS</strong> — Lenkijos laivų registras. Klasifikacinės bendrovės "
             "sertifikatas leidžia laivo savininkui priimti mūsų darbus ir dokumentus be "
             "atskiro patikrinimo.",
    c_ins="Draudimas", c_war="Garantija",
    c_war_p="Visiems darbams ir įrangai suteikiame garantiją. Visa mūsų įmonės gaminama bei "
            "tiekiama įranga ir atsarginės dalys atitinka kokybės bei tarptautinių standartų "
            "reikalavimus.",
    c_open="Atidaryti", c_rina_note="Italijos klasifikacinė bendrovė",
    c_prs_note="Lenkijos laivų registras",

    k_eyebrow="Kontaktai", k_h1="Susisiekite su mumis",
    k_lead="Užklausas gauna žmonės, galintys atsakyti į techninius klausimus, o ne skambučių centras.",
    k_meta="%(street)s, %(city)s, %(country)s. Tel. %(phone)s, el. paštas %(email)s. Servisas 24/7.",
    k_service="Servisas", k_service_p="24/7 — visada pasirengę suteikti operatyvią ir "
                                      "kompetentingą pagalbą.",
    k_form_h2="Siųsti užklausą",
    k_form_lead="Greičiausias kelias iki naudingo atsakymo — nurodyti laivą ar įrenginį, "
                "įrangą, uostą ir terminus.",

    pr_eyebrow="Teisinė informacija", pr_h1="Privatumo politika",
    pr_lead="Kaip %(legal)s tvarko per šią svetainę surinktus asmens duomenis.",
    pr_updated="Atnaujinta",
    pr_h=["Kas mes esame", "Kokius duomenis renkame", "Tretieji asmenys",
          "Teisinis pagrindas", "Kiek laiko saugome", "Jūsų teisės", "Pakeitimai"],
    pr_who="%(legal)s yra per šią svetainę surenkamų asmens duomenų valdytoja.",
    pr_collect="Ši svetainė neturi naudotojų paskyrų, nenaudoja analitikos ir nenustato savo "
               "slapukų. Duomenis gauname per užklausos formą, tiesiogiai susisiekus el. paštu "
               "ar telefonu, taip pat iš prieglobos paslaugų teikėjo serverio žurnalų.",
    pr_third="<strong>GitHub, Inc.</strong> &mdash; svetainės prieglobą ir užklausų žurnalai. "
             "<strong>Calendly LLC</strong> &mdash; susitikimų registracija, bet tik jeigu ja "
             "pasinaudojate: registracijos langas iš Calendly įkeliamas tik tada, kai paspaudžiate "
             "&bdquo;Susitarti dėl pokalbio&ldquo;, o ne atidarius puslapį. Iki tol į Calendly "
             "neišsiunčiama jokia užklausa ir apie Jūsų apsilankymą jai nieko nežinoma. Jei "
             "langą atidarote, Calendly gauna Jūsų IP adresą ir registracijai įvestus duomenis "
             "pagal savo privatumo politiką. Daugiau jokių trečiųjų šalių skriptų, šriftų, "
             "analitikos ar įskiepių svetainė neįkelia, o šriftas pateikiamas iš mūsų domeno.",
    pr_basis="<strong>Sutikimas</strong> (BDAR 6 str. 1 d. a p.) dėl užklausos formos, kurį "
             "galite bet kada atšaukti, ir <strong>teisėtas interesas</strong> "
             "(6 str. 1 d. f p.) atsakant į užklausas bei užtikrinant svetainės saugumą.",
    pr_keep="Užklausos saugomos tiek, kiek reikia užklausai ar iš jos kilusiam projektui, taip "
            "pat taikomą teisės aktų nustatytą laikotarpį.",
    pr_rights="Pagal BDAR turite teisę susipažinti su duomenimis, juos ištaisyti, ištrinti, "
              "apriboti tvarkymą, perkelti duomenis ir nesutikti su tvarkymu teisėto intereso "
              "pagrindu. Rašykite %(email)s — atsakysime per vieną mėnesį. Skundą galite pateikti "
              "Valstybinei duomenų apsaugos inspekcijai.",
    pr_changes="Pasikeitus šiai politikai, atnaujinta versija bus paskelbta šiame puslapyje "
               "nurodant naują datą.",
    nf_h1="Puslapis nerastas",
    nf_lead="Ieškomo puslapio čia nėra. Jis galėjo pasikeisti atnaujinant svetainę.",
    nf_home="Į pradžios puslapį", nf_contact="Susisiekti",
)

P["ru"] = dict(
    about_eyebrow="О нас", about_h1="Клайпедская судоремонтная компания, работающая по всему миру",
    about_lead="%(legal)s основана в %(founded)s году. Более десяти лет на рынке холодильного "
               "оборудования, длинный список реализованных проектов и оставшиеся с нами деловые партнёры.",
    about_meta="%(legal)s основана в %(founded)s году в Клайпеде, Литва. Специалисты по судовому "
               "холодильному оборудованию и ремонту двигателей, сертифицированы RINA и PRS.",
    a_spec="Наша специализация",
    a_spec_list=["проектирование и подбор промышленного холодильного оборудования;",
                 "модернизация и ремонт холодильных систем рыболовных судов и береговых установок;",
                 "монтаж и поставка холодильного оборудования;",
                 "капитальный ремонт главных и вспомогательных двигателей;",
                 "постановка судов в порту Клайпеды для выполнения ремонтных работ."],
    a_people="Команда",
    a_people_h="Надёжные, квалифицированные, проверенные временем",
    a_people_1="В нашей компании работает команда надёжных, квалифицированных и проверенных "
               "временем специалистов. <strong>На все работы и оборудование предоставляется "
               "гарантия</strong>.",
    a_people_2="Мы постоянно совершенствуемся, интересуемся новинками рынка, внимательно "
               "выслушиваем пожелания и предложения клиентов, поэтому стремимся предложить "
               "заказчику оптимальный вариант по цене, срокам и поставляемому оборудованию.",
    a_cert="Сертификаты и страхование",
    a_cert_1="Компании %(legal)s выдан сертификат <strong>RINA</strong>, а также она "
             "сертифицирована <strong>Польским регистром судоходства (PRS)</strong>.",
    a_cert_2="Гражданская ответственность компании застрахована в <strong>ADB «Compensa Vienna "
             "Insurance Group»</strong> на сумму <strong>250 000,00 EUR</strong>. Страховой полис "
             "№ 230 0008143 / 2020.",
    a_details="Реквизиты",

    svc_h1="Что мы ремонтируем, поставляем и монтируем",
    svc_page_lead="Судовые двигатели, холодильное оборудование, трубопроводные системы и "
                  "запасные части, необходимые для всех трёх направлений.",
    svc_meta="Ремонт судовых двигателей, холодильные системы, судокорпусные и трубопроводные "
             "работы, поставка запасных частей — от одного подрядчика в Клайпеде.",

    cw_eyebrow="Выполненные работы", cw_h1="Где выполнялись работы",
    shots_eyebrow="В мастерской", shots_h2="Как выглядит капитальный ремонт",
    shots_lead="Клайпеда, на верстаке. Машины приходят собранными, такими и уходят, "
               "а всё, что между \u2014 измерено.",
    shot_rotors="Роторы рядом с расточкой корпуса. Зазоры измеряются по допускам "
                "изготовителя, прежде чем что-либо собирать обратно.",
    shot_bench="Корпус компрессора, роторы и опоры подшипников на верстаке.",
    cw_lead="Две линии проходят через всё, что компания сделала с %(founded)s года: двигатели "
            "и холод.",
    cw_meta="Капитальный ремонт двигателей и холодильные проекты, выполненные %(legal)s для "
            "рыболовных флотов, судовладельцев и береговых установок.",
    cw_engines_e="Двигатели",
    cw_refrig_e="Холод",
    cw_engines="Ремонт судового оборудования и двигателей",
    cw_engines_p="Капитальный ремонт главных и вспомогательных двигателей на рыболовных и "
                 "коммерческих судах, как 4-х тактных, так и 2-х тактных, вместе с механизмами "
                 "машинного отделения и палубным оборудованием.",
    cw_refrig="Холодильное оборудование",
    cw_refrig_p="Самое длительное направление работы компании: модернизация и ремонт холодильных систем "
                "на рыболовных судах и береговых установках, капитальный ремонт компрессоров, "
                "проектная документация, согласованная с классификационными обществами, монтаж "
                "оборудования и трубопроводов хладагента, пусконаладка и сдача заказчику.",
    cw_who="Для кого выполнялись работы",

    p_eyebrow="Партнёры", p_h1="Производители, которых мы представляем, и клиенты, для которых работаем",
    p_lead="Два авторизованных представительства и список клиентов, накопленный более чем за десять лет.",
    p_meta="Авторизованный партнёр BITZER и представитель морской линии DANFOSS. Среди клиентов — "
           "Sealord, Limarko Group, Ocean Whale Company и Baltreids.",
    p_rep_h2="Производители, которых мы представляем",
    p_rep_lead="Два прямых назначения — заводская поддержка по запчастям, ценам и гарантии.",
    p_clients_h2="Компании, для которых мы работали",
    p_clients_lead="Рыболовные группы, судовладельцы и верфи Балтики и не только.",

    c_no="№", c_issued="Выдан", c_valid="Действует до",
    c_shot_alt="Первая страница сертификата %(name)s",
    c_scope_h="Что охватывает признание PRS",
    c_scope_lead="Сертификат TM/1703/842502/25 даёт UAB \u201eLitprofit\u201c право "
                 "выполнять ремонт:",
    c_scope=["Главных и вспомогательных двигателей \u2014 двух- и четырёхтактных",
             "Палубных механизмов и устройств",
             "Топливной аппаратуры главных и вспомогательных двигателей, компрессоров и насосов",
             "Турбокомпрессоров",
             "Редукторов",
             "Центровки дизельных двигателей",
             "Холодильного оборудования и систем"],
    c_scope_extra="Он также даёт право на <strong>проектирование</strong> холодильного "
                  "оборудования и систем \u2014 не только на их ремонт.",
    c_eyebrow="Сертификаты", c_h1="Сертификаты и страхование",
    c_lead="Одобрения классификационных обществ и страхование гражданской ответственности.",
    c_meta="Сертификаты RINA и PRS и страхование гражданской ответственности на 250 000 EUR "
           "в Compensa Vienna Insurance Group.",
    c_what="Что они охватывают",
    c_what_p="<strong>RINA</strong> — итальянское классификационное общество, "
             "<strong>PRS</strong> — Польский регистр судоходства. Сертификат классификационного "
             "общества позволяет судовладельцу принять наши работы и документацию без отдельной "
             "проверки.",
    c_ins="Страхование", c_war="Гарантия",
    c_war_p="На все работы и оборудование предоставляется гарантия. Всё оборудование и запасные "
            "части, производимые и поставляемые компанией, отвечают требованиям качества и "
            "международных стандартов.",
    c_open="Открыть", c_rina_note="Итальянское классификационное общество",
    c_prs_note="Польский регистр судоходства",

    k_eyebrow="Контакты", k_h1="Свяжитесь с нами",
    k_lead="Запросы попадают к людям, способным ответить на технические вопросы, а не в колл-центр.",
    k_meta="%(street)s, %(city)s, %(country)s. Тел. %(phone)s, эл. почта %(email)s. Сервис 24/7.",
    k_service="Сервис", k_service_p="24/7 — мы всегда готовы оказать оперативную и компетентную помощь.",
    k_form_h2="Отправить запрос",
    k_form_lead="Быстрее всего получить полезный ответ, указав судно или установку, оборудование, "
                "порт и сроки.",

    pr_eyebrow="Правовая информация", pr_h1="Политика конфиденциальности",
    pr_lead="Как %(legal)s обрабатывает персональные данные, собранные через этот сайт.",
    pr_updated="Обновлено",
    pr_h=["Кто мы", "Какие данные мы собираем", "Третьи лица",
          "Правовое основание", "Сколько мы храним данные", "Ваши права", "Изменения"],
    pr_who="%(legal)s является контролёром персональных данных, собираемых через этот сайт.",
    pr_collect="На этом сайте нет учётных записей, не используется аналитика и не устанавливаются "
               "собственные файлы cookie. Данные поступают к нам через форму запроса, при прямом "
               "обращении по электронной почте или телефону, а также из журналов сервера хостинг-провайдера.",
    pr_third="<strong>GitHub, Inc.</strong> &mdash; хостинг сайта и журналы запросов. "
             "<strong>Calendly LLC</strong> &mdash; запись на встречу, но только если вы ею "
             "воспользуетесь: окно записи загружается из Calendly в момент нажатия "
             "&laquo;Заказать звонок&raquo;, а не при открытии страницы. До этого в Calendly не "
             "уходит ни одного запроса и о вашем посещении ей ничего не известно. Если вы "
             "откроете окно, Calendly получит ваш IP-адрес и данные, введённые для записи, "
             "согласно своей политике конфиденциальности. Кроме этого сайт не загружает никаких "
             "сторонних скриптов, шрифтов, аналитики или встраиваемых элементов, а шрифт "
             "отдаётся с нашего домена.",
    pr_basis="<strong>Согласие</strong> (GDPR ст. 6(1)(a)) для формы запроса, которое вы можете "
             "отозвать в любой момент, и <strong>законный интерес</strong> (ст. 6(1)(f)) для ответа "
             "на запросы и обеспечения безопасности сайта.",
    pr_keep="Запросы хранятся столько, сколько необходимо для запроса или возникшего из него проекта, "
            "а также в течение установленного законом срока хранения.",
    pr_rights="Согласно GDPR вы вправе запросить доступ, исправление, удаление, ограничение обработки, "
              "переносимость данных и возразить против обработки на основании законного интереса. "
              "Пишите на %(email)s — мы ответим в течение одного месяца. Жалобу можно подать в "
              "Государственную инспекцию по защите данных Литвы.",
    pr_changes="При изменении настоящей политики обновлённая версия будет опубликована на этой "
               "странице с указанием новой даты.",
    nf_h1="Страница не найдена",
    nf_lead="Запрошенной страницы здесь нет. Возможно, она изменилась при обновлении сайта.",
    nf_home="На главную", nf_contact="Связаться с нами",
)


# ============================================================
# GENERAL ARRANGEMENT — the drawing's callouts
# ============================================================
PARTS_ORDER = ["motor", "coupling", "screw", "separator", "lines"]
PARTS_LABEL = {          # short label inside the drawing box
    "en": dict(motor="Motor", coupling="Coupling", screw="Compressor",
               separator="Separator", lines="Piping"),
    "lt": dict(motor="Variklis", coupling="Mova", screw="Kompresorius",
               separator="Separatorius", lines="Vamzdynai"),
    "ru": dict(motor="Двигатель", coupling="Муфта", screw="Компрессор",
               separator="Сепаратор", lines="Трубопроводы"),
}
PARTS = {
    "en": dict(
        motor=("Electric motor", "Drives the compressor through the coupling. Bearings, "
               "insulation resistance and alignment are checked before anything is reassembled."),
        coupling=("Coupling", "Where misalignment turns into vibration and a wrecked bearing. "
                  "Set cold, then checked again once the package has run up to temperature."),
        screw=("Screw compressor", "Rotors, slide valve, shaft seal and bearings. This is the "
               "overhaul itself &mdash; SABROE, BITZER, HOWDEN, KUHLAUTOMAT, STAL, GRASSO, MYCOM."),
        separator=("Oil separator", "Takes the oil back out of the discharge gas and returns it. "
                   "Carry-over here shows up much later as poor heat transfer in the condenser."),
        lines=("Suction &amp; discharge", "Refrigerant piping to class requirements, then "
               "pressure testing and commissioning before the plant is handed over.")),
    "lt": dict(
        motor=("Elektros variklis", "Suka kompresorių per movą. Prieš surenkant tikrinami "
               "guoliai, izoliacijos varža ir centravimas."),
        coupling=("Mova", "Čia necentruotumas virsta vibracija ir sugadintu guoliu. Nustatoma "
                  "šaltoje būsenoje ir patikrinama vėl, agregatui įšilus."),
        screw=("Sraigtinis kompresorius", "Rotoriai, sklendė, veleno riebokšlis ir guoliai. Tai "
               "ir yra pats kapitalinis remontas &mdash; SABROE, BITZER, HOWDEN, KUHLAUTOMAT, "
               "STAL, GRASSO, MYCOM."),
        separator=("Alyvos separatorius", "Išskiria alyvą iš išmetamų dujų ir grąžina ją atgal. "
                   "Alyvos pernešimas čia vėliau pasireiškia prastu šilumos perdavimu kondensatoriuje."),
        lines=("Siurbimo ir slėgio vamzdynai", "Šaltnešio vamzdynai pagal klasifikacinių bendrovių "
               "reikalavimus, po to slėgio bandymai ir paleidimas prieš perduodant įrenginį.")),
    "ru": dict(
        motor=("Электродвигатель", "Приводит компрессор через муфту. Перед сборкой проверяются "
               "подшипники, сопротивление изоляции и центровка."),
        coupling=("Муфта", "Здесь несоосность превращается в вибрацию и разрушенный подшипник. "
                  "Выставляется на холодную и проверяется снова, когда агрегат прогрелся."),
        screw=("Винтовой компрессор", "Роторы, золотник, торцевое уплотнение и подшипники. Это и "
               "есть сам капитальный ремонт &mdash; SABROE, BITZER, HOWDEN, KUHLAUTOMAT, STAL, "
               "GRASSO, MYCOM."),
        separator=("Маслоотделитель", "Отделяет масло от нагнетаемого газа и возвращает его. Унос "
                   "масла здесь позже проявляется как плохой теплообмен в конденсаторе."),
        lines=("Всасывание и нагнетание", "Трубопроводы хладагента по требованиям "
               "классификационных обществ, затем опрессовка и пусконаладка перед сдачей.")),
}
TB = {   # drawing title block
    "en": ("Screw compressor package", "Side elevation"),
    "lt": ("Sraigtinis kompresorinis agregatas", "Šoninis vaizdas"),
    "ru": ("Винтовой компрессорный агрегат", "Вид сбоку"),
}


# ============================================================
# CAREERS
# ============================================================
CAR = {
 "en": dict(
   nav="Careers", h1="Work at LITPROFIT",
   lead="Marine refrigeration and engine work, out of Klaipeda and on vessels "
        "wherever they happen to be.",
   meta="Careers at %(legal)s — marine refrigeration engineers, ship mechanics, "
        "pipe fitters and welders. Klaipeda, Lithuania.",
   open_h2="Open positions",
   none_h="No open positions right now",
   none_p="We still read every open application, and we come back when a job "
          "matches. Use the form below.",
   disc_h2="What we recruit for",
   disc_p="Even when nothing is advertised, we keep qualified people on file. "
          "These are the trades our work is built from:",
   disc=["Refrigeration engineers — compressors, automatic control systems, "
         "commissioning",
         "Marine mechanics — 4-stroke and 2-stroke diesel overhaul",
         "Pipe fitters and welders — steel and stainless steel systems",
         "Electrical and automation technicians",
         "Service coordinators and project supervisors"],
   matters_h2="What matters to us",
   matters=["Documented qualifications for your trade.",
            "Readiness to travel — vessels are not always in Klaipeda.",
            "A serious approach to safety in machinery spaces and confined areas.",
            "Working English; Lithuanian or Russian are useful additions."],
   apply_h2="Send an application",
   # Rewritten when the CV field went in: the old copy said uploads were not
   # accepted through this page, which the drop zone directly under it now
   # contradicts. Where the file actually goes depends on whether a form
   # endpoint is configured, and the form itself says so at the moment it
   # matters rather than in advance.
   apply_p="Tell us your trade, your experience and when you could start, and "
           "attach a CV if you have one to hand.",
   # The apply flow. f_cv_attach is the honest half of it: a browser cannot
   # put a file into a mail client, so when no form endpoint is configured the
   # applicant is told to attach it, and the filename goes into the message so
   # nothing is lost quietly.
   apply_cta="Apply for this role",
   f_cv="CV",
   f_cv_hint="PDF, Word or plain text, up to 10 MB.",
   f_cv_drop="Drop a file here, or choose one",
   f_cv_choose="Choose a file",
   f_cv_clear="Remove",
   f_cv_big="That file is over 10 MB. Please send a smaller one, or a link to it.",
   f_cv_type="Please attach a PDF, a Word document or plain text.",
   f_cv_attach="Attach your CV to the email that opens \u2014 a browser cannot "
               "attach it for you.",
   f_role_other="Another role, or a speculative application",
   f_role="Trade or position", f_exp="Experience and availability",
   f_exp_ph="Your trade, years of experience, certifications, and when you could start.",
   sample="Example",
   f_send="Send application", f_open="Open application",
   consent='I agree that %(legal)s may keep these details on file to consider me '
           'for current and future positions, as described in the %(privacy)s.'),
 "lt": dict(
   nav="Karjera", h1="Darbas LITPROFIT",
   lead="Laivų šaldymo ir variklių darbai Klaipėdoje ir laivuose, kad ir kur jie būtų.",
   meta="Karjera %(legal)s — šaldymo inžinieriai, laivų mechanikai, vamzdynų "
        "montuotojai ir suvirintojai. Klaipėda, Lietuva.",
   open_h2="Laisvos darbo vietos",
   none_h="Šiuo metu laisvų darbo vietų nėra",
   none_p="Vis dėlto perskaitome kiekvieną atvirą kandidatūrą ir susisiekiame, kai "
          "atsiranda tinkamas darbas. Užpildykite formą žemiau.",
   disc_h2="Ko ieškome",
   disc_p="Net kai skelbimų nėra, kvalifikuotus specialistus registruojame. Štai "
          "sritys, iš kurių sudarytas mūsų darbas:",
   disc=["Šaldymo inžinieriai — kompresoriai, automatinio valdymo sistemos, paleidimas",
         "Laivų mechanikai — 4-takčių ir 2-takčių dyzelinių variklių remontas",
         "Vamzdynų montuotojai ir suvirintojai — plieno ir nerūdijančio plieno sistemos",
         "Elektros ir automatikos technikai",
         "Serviso koordinatoriai ir projektų vadovai"],
   matters_h2="Kas mums svarbu",
   matters=["Dokumentais patvirtinta kvalifikacija.",
            "Pasirengimas keliauti — laivai ne visada Klaipėdoje.",
            "Rimtas požiūris į saugą mašinų skyriuose ir uždarose erdvėse.",
            "Anglų kalba; lietuvių ar rusų — privalumas."],
   apply_h2="Siųsti kandidatūrą",
   apply_p="Nurodykite specialybę, patirtį ir kada galėtumėte pradėti, ir prisekite "
           "gyvenimo aprašymą, jei jį turite po ranka.",
   apply_cta="Kandidatuoti į šią poziciją",
   f_cv="Gyvenimo aprašymas",
   f_cv_hint="PDF, Word arba tekstas, iki 10 MB.",
   f_cv_drop="Nutempkite failą čia arba pasirinkite",
   f_cv_choose="Pasirinkti failą",
   f_cv_clear="Pašalinti",
   f_cv_big="Failas didesnis nei 10 MB. Atsiųskite mažesnį arba nuorodą į jį.",
   f_cv_type="Prisekite PDF, Word dokumentą arba tekstinį failą.",
   f_cv_attach="Prisekite gyvenimo aprašymą prie atsidariusio laiško \u2014 "
               "naršyklė to padaryti už jus negali.",
   f_role_other="Kita pozicija arba atvira kandidatūra",
   f_role="Specialybė ar pareigos", f_exp="Patirtis ir galimybės",
   f_exp_ph="Specialybė, patirtis metais, sertifikatai ir kada galėtumėte pradėti.",
   sample="Pavyzdys",
   f_send="Siųsti kandidatūrą", f_open="Atvira kandidatūra",
   consent='Sutinku, kad %(legal)s saugotų šiuos duomenis vertindama mane esamoms ir '
           'būsimoms pozicijoms, kaip nurodyta %(privacy)s.'),
 "ru": dict(
   nav="Вакансии", h1="Работа в LITPROFIT",
   lead="Судовые холодильные и двигательные работы в Клайпеде и на судах, где бы "
        "они ни находились.",
   meta="Вакансии в %(legal)s — инженеры-холодильщики, судовые механики, "
        "трубопроводчики и сварщики. Клайпеда, Литва.",
   open_h2="Открытые вакансии",
   none_h="Сейчас открытых вакансий нет",
   none_p="Мы всё равно читаем каждую открытую заявку и связываемся, когда появляется "
          "подходящая работа. Заполните форму ниже.",
   disc_h2="Кого мы ищем",
   disc_p="Даже когда вакансий нет, мы вносим квалифицированных специалистов в базу. "
          "Вот направления, из которых состоит наша работа:",
   disc=["Инженеры-холодильщики — компрессоры, системы автоматики, пусконаладка",
         "Судовые механики — ремонт 4-х и 2-х тактных дизельных двигателей",
         "Трубопроводчики и сварщики — системы из стали и нержавеющей стали",
         "Электрики и специалисты по автоматике",
         "Координаторы сервиса и руководители проектов"],
   matters_h2="Что для нас важно",
   matters=["Документально подтверждённая квалификация.",
            "Готовность к командировкам — судно не всегда в Клайпеде.",
            "Серьёзное отношение к безопасности в машинных отделениях и замкнутых пространствах.",
            "Рабочий английский; литовский или русский — преимущество."],
   apply_h2="Отправить заявку",
   apply_p="Укажите специальность, опыт и когда могли бы приступить, и приложите "
           "резюме, если оно под рукой.",
   apply_cta="Откликнуться на вакансию",
   f_cv="Резюме",
   f_cv_hint="PDF, Word или текст, до 10 МБ.",
   f_cv_drop="Перетащите файл сюда или выберите",
   f_cv_choose="Выбрать файл",
   f_cv_clear="Убрать",
   f_cv_big="Файл больше 10 МБ. Пришлите меньше или ссылку на него.",
   f_cv_type="Приложите PDF, документ Word или текстовый файл.",
   f_cv_attach="Приложите резюме к открывшемуся письму \u2014 браузер не может "
               "сделать это за вас.",
   f_role_other="Другая позиция или открытая заявка",
   f_role="Специальность или должность", f_exp="Опыт и возможности",
   f_exp_ph="Специальность, стаж, сертификаты и когда могли бы приступить.",
   sample="Пример",
   f_send="Отправить заявку", f_open="Открытая заявка",
   consent='Я соглашаюсь, что %(legal)s может хранить эти данные для рассмотрения моей '
           'кандидатуры на текущие и будущие позиции, как описано в %(privacy)s.'),
}

# title block on the hero vessel drawing
# Kept short on purpose: 31 monospace characters do not fit the 190px cell,
# which is exactly how the general arrangement's title block broke.
VESSEL_TB = {"en": "SHIP REFRIGERATION PLANT",
             "lt": "LAIVO ŠALDYMO ĮRANGA",
             "ru": "СУДОВАЯ ХОЛОДИЛЬНАЯ УСТАНОВКА"}

# the three refrigerated spaces on the hero P&ID
ROOMS = {"en": ["CHILLER", "FREEZER", "PRE-STORAGE"],
         "lt": ["ŠALDYTUVAS", "ŠALDIKLIS", "PARUOŠIMO PATALPA"],
         "ru": ["ОХЛАЖДЕНИЕ", "МОРОЗИЛЬНАЯ", "ПРЕДВАРИТЕЛЬНАЯ"]}

# Sector lines under a client's logo. Only filled where the company's own site
# states it — six of the nine are deliberately absent until the client confirms.
SECTORS = {
 "en": {"seafood": "Seafood group", "frozenfish": "Frozen fish supplier",
        "engineering": "Engineering partner"},
 "lt": {"seafood": "Žuvininkystės grupė", "frozenfish": "Šaldytos žuvies tiekėjas",
        "engineering": "Inžinerijos partneris"},
 "ru": {"seafood": "Рыбопромысловая группа", "frozenfish": "Поставщик мороженой рыбы",
        "engineering": "Инженерный партнёр"},
}

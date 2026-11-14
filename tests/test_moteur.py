"""Le moteur, sans Windows : lecture des sorties winget, des raccourcis,
des pages d'éditeurs et du service NVIDIA ; ménage dans un dossier jetable."""
import json
import os
import struct
import time

import pytest

from martinet import (historique, menage, orchestre, raccourcis, reglages, sources, versions,
                      winget)
from martinet.i18n import definir_langue

definir_langue("fr")


# ------------------------------------------------------------ versions
def test_comparaison_de_versions():
    assert versions.plus_recente("7.1.3", "7.0.2.4721")
    assert not versions.plus_recente("3.2", "3.2.0.9001")      # numéro de compilation en plus
    assert versions.plus_recente("v2.6.14", "2.6.13")
    assert versions.plus_recente("2026.07.16", "2025.10.18")
    assert not versions.plus_recente("", "1.0") and not versions.plus_recente("1.0", "inconnu")
    assert versions.la_plus_haute(["3.2", "3.10", "3.9"]) == "3.10"


def test_version_nvidia():
    assert versions.nvidia_lisible("32.0.15.7680") == "576.80"
    assert versions.nvidia_lisible("32.0.16.2114") == "621.14"
    assert versions.nvidia_lisible("31.0.15.5222") == "552.22"
    assert versions.nvidia_lisible("6.1") is None


# ------------------------------------------------------------ winget (tableau texte)
UPGRADE_EN = ("\r   - \r   \\ \r   | \r"
              "Name                       Id                Version  Available Source\n"
              "-----------------------------------------------------------------------\n"
              "Mozilla Firefox (x64 fr)   Mozilla.Firefox   144.0.1  145.0     winget\n"
              "7-Zip 24.08 (x64)          7zip.7zip         24.08    25.01     winget\n"
              "Éditeur accentué           Edit.Accent       1.0      1.1       winget\n"
              "3 upgrades available.\n\n"
              "The following packages have an upgrade available, but require explicit targeting:\n"
              "Name   Id        Version Available Source\n"
              "------------------------------------------\n"
              "Discord Discord.Discord 1.0 1.1 winget\n")

LISTE_FR = ("Nom                        ID                                  Version    Disponible Source\n"
            "-------------------------------------------------------------------------------------------\n"
            "Mozilla Firefox (x64 fr)   Mozilla.Firefox                     144.0.1    145.0      winget\n"
            "PHD2                       ARP\\Machine\\X86\\PHD2                 2.6.13\n"
            "Un jeu                     ARP\\Machine\\X64\\Steam App 3768760    Unknown\n"
            "Notepad++ (64-bit x64)     Notepad++.Notepad++                 8.8.6                 winget\n"
            "Xbox                       MSIX\\Microsoft.XboxApp_48.104.4001  48.104.4001\n")


def test_tableau_upgrade_anglais():
    p = winget._texte_vers_paquets(UPGRADE_EN, avec_dispo=True)
    assert [x.id for x in p] == ["Mozilla.Firefox", "7zip.7zip", "Edit.Accent"]   # 2e tableau ignoré
    assert p[0].disponible == "145.0" and p[0].source == "winget" and p[0].a_mettre_a_jour


def test_tableau_liste_francais():
    p = {x.id: x for x in winget._texte_vers_paquets("\ufeff" + LISTE_FR, avec_dispo=False)}
    assert p["Mozilla.Firefox"].suivi and p["Mozilla.Firefox"].a_mettre_a_jour
    assert not p["ARP\\Machine\\X86\\PHD2"].suivi
    assert p["ARP\\Machine\\X64\\Steam App 3768760"].installee == "Unknown"     # espace dans l'identifiant
    assert p["Notepad++.Notepad++"].suivi and not p["Notepad++.Notepad++"].a_mettre_a_jour


def test_bruit_ecarte_des_logiciels_hors_winget():
    assert orchestre._est_bruit(winget.Paquet("MSIX\\Microsoft.XboxApp_1", "Xbox", "1"))
    assert not orchestre._est_bruit(winget.Paquet("ARP\\Machine\\X86\\PHD2", "PHD2", "2.6.13"))


# ------------------------------------------------------------ raccourcis (.lnk)
def fabriquer_lnk(local="", env="", reseau="", relatif="", darwin=False) -> bytes:
    """Petit écrivain MS-SHLLINK, juste ce qu'il faut pour les essais."""
    drapeaux = 0x80                                     # IsUnicode
    corps = b""
    if local or reseau:
        drapeaux |= 0x2
        if local:
            base = local.encode("cp1252") + b"\0"
            entete = 0x1C
            vol = b"\x10\0\0\0" + b"\3\0\0\0" + b"\0" * 8      # VolumeID minimal (16 octets)
            off_vol = entete
            off_base = off_vol + len(vol)
            off_suff = off_base + len(base)
            contenu = vol + base + b"\0"
            li = struct.pack("<7I", entete + len(contenu), entete, 0x1, off_vol, off_base, 0, off_suff) + contenu
        else:
            nom = reseau.encode("cp1252") + b"\0"
            cnrl = struct.pack("<5I", 0x14 + len(nom), 0x2, 0x14, 0, 0) + nom
            entete = 0x1C
            off_cnrl = entete
            off_suff = off_cnrl + len(cnrl)
            contenu = cnrl + b"dossier\\fichier.exe\0"
            li = struct.pack("<7I", entete + len(contenu), entete, 0x2, 0, 0, off_cnrl, off_suff) + contenu
        corps += li
    if relatif:
        drapeaux |= 0x8
        corps += struct.pack("<H", len(relatif)) + relatif.encode("utf-16-le")
    extra = b""
    if env:
        drapeaux |= 0x200
        ansi = env.encode("cp1252").ljust(260, b"\0")
        uni = env.encode("utf-16-le").ljust(520, b"\0")
        extra = struct.pack("<II", 0x314, 0xA0000001) + ansi + uni
    if darwin:
        drapeaux |= 0x1000
    entete = struct.pack("<I", 0x4C) + b"\x01\x14\x02\0\0\0\0\0\xc0\0\0\0\0\0\0\x46" + struct.pack("<I", drapeaux)
    entete = entete.ljust(0x4C, b"\0")
    return entete + corps + extra + b"\0\0\0\0"


def test_lnk_chemin_local():
    assert raccourcis.lire_lnk(fabriquer_lnk(local=r"C:\Programmes\Outil\outil.exe")).chemin == \
        r"C:\Programmes\Outil\outil.exe"


def test_lnk_variable_d_environnement(monkeypatch):
    monkeypatch.setenv("MONDOSSIER", "/opt/essai")
    c = raccourcis.lire_lnk(fabriquer_lnk(local=r"C:\ancien.exe", env="$MONDOSSIER/outil.exe"))
    assert c.chemin == "/opt/essai/outil.exe"                # le bloc d'environnement prime


def test_lnk_reseau_et_speciaux():
    assert raccourcis.lire_lnk(fabriquer_lnk(reseau=r"\\SERVEUR\partage")).chemin == \
        r"\\SERVEUR\partage\dossier\fichier.exe"
    assert raccourcis.lire_lnk(fabriquer_lnk(local=r"C:\x.exe", darwin=True)).special
    assert raccourcis.lire_lnk(fabriquer_lnk()).special
    with pytest.raises(ValueError):
        raccourcis.lire_lnk(b"pas un raccourci")


def test_verdict_prudent(tmp_path):
    present = tmp_path / "la.exe"
    present.write_text("")
    assert raccourcis.verdict(str(present)) == "ok"
    assert raccourcis.verdict(str(tmp_path / "parti.exe")) == "mort"
    assert raccourcis.verdict(r"\\NAS\partage\film.mkv") == "non_verifie"     # jamais de réveil réseau
    assert raccourcis.verdict("https://exemple.org") == "non_verifie"


# ------------------------------------------------------------ sources
def test_version_dans_une_page():
    texte = sources.texte_de_page(
        "<h2>Version 3.2</h2><a>Download</a> <h3>Version 3.2 HF1 RC2</h3> <p>Version 3.3 NIGHTLY #69</p>"
        "<script>var v='Version 9.9';</script>")
    assert sources.version_dans_page(texte, r"Version (\d+(?:\.\d+)+)",
                                     r"^\s*(HF\d+\s*)?(RC|NIGHTLY|BETA)") == "3.2"
    assert sources.version_dans_page(texte, r"Version (\d+(?:\.\d+)+)") == "3.3"


def test_catalogue_par_defaut_valide():
    import re
    for s in sources.charger():
        re.compile(s.motif)
        assert s.type in sources.TYPES
        if s.type == "page":
            assert s.url.startswith("https://") and re.compile(s.regex).groups == 1
        elif s.type == "github":
            assert re.fullmatch(r"[\w.-]+/[\w.-]+", s.depot)
    noms = {"PHD2", "ASCOM Platform 7", "N.I.N.A. - Nighttime Imaging 'N' Astronomy", "ASTAP, Astrometric STAcking Program"}
    for nom in noms:
        assert any(s.correspond(nom) for s in sources.charger()), nom


def test_github_ecarte_les_preversions(monkeypatch):
    rels = [{"tag_name": "v2.6.14dev1", "prerelease": False, "assets": []},
            {"tag_name": "v2.6.14rc", "prerelease": True, "assets": []},
            {"tag_name": "v2.6.14", "prerelease": False, "html_url": "https://github.com/x/y/releases/v2.6.14",
             "assets": [{"name": "outil-2.6.14-setup.exe", "browser_download_url": "https://github.com/x/y/a.exe"}]}]
    monkeypatch.setattr(sources.systeme, "telecharger_json", lambda url, timeout=20: rels)
    assert sources.derniere_github("x/y", "dev|rc", r"setup\.exe$") == \
        ("2.6.14", "https://github.com/x/y/releases/v2.6.14", "https://github.com/x/y/a.exe")


def test_reponse_nvidia():
    rep = {"DriverAttributes": {"Version": "621.14", "ReleaseDateTime": "2026-11-04T00:00:00+0000",
                                "Name": "GeForce Game Ready Driver",
                                "DownloadURLAdmin": "https://us.download.nvidia.com/Windows/621.14/x.exe",
                                "DetailsURL": "https://www.nvidia.com/en-us/drivers/details/1/"}}
    infos = sources.lire_reponse_nvidia(rep)
    assert infos["version"] == "621.14" and infos["date"] == "2026-11-04"
    assert infos["fichier"].startswith("https://us.download.nvidia.com/")
    with pytest.raises(LookupError):
        sources.lire_reponse_nvidia({"DriverAttributes": {}})
    studio = {"DriverAttributes": dict(rep["DriverAttributes"], Name="NVIDIA Studio Driver", IsCRD=1)}
    with pytest.raises(LookupError):                     # mode jeu seulement
        sources.lire_reponse_nvidia(studio)
    assert "2786_10DE" in sources.url_nvidia("2786")


def test_sources_personnelles(donnees):
    tout = sources.charger()
    perso = sources.Source(id="phd2", nom="PHD2 (ma version)", motif="^PHD2", type="page",
                           url="https://exemple.org", regex=r"v(\d+\.\d+)", perso=True)
    autre = sources.Source(id=sources.nouvel_id("Mon Outil", {s.id for s in tout}), nom="Mon Outil",
                           motif="^Mon Outil", type="github", depot="moi/outil", perso=True)
    sources.enregistrer_perso(tout + [perso, autre])
    relu = {s.id: s for s in sources.charger()}
    assert relu["phd2"].nom == "PHD2 (ma version)" and relu["phd2"].perso     # remplace le catalogue
    assert relu["mon-outil"].depot == "moi/outil"
    assert json.loads((donnees / "sources.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------ orchestre (mode démonstration)
def test_hors_winget_et_ignores():
    r = reglages.Reglages(ignores_hors_winget=["Outil maison de traitement"])
    inv = winget.inventaire()
    res, sans = orchestre.hors_winget(inv, r)
    assert {x.source for x in res} >= {"phd2", "nina", "ascom", "astap"}
    assert [p.nom for p in sans] == ["Pilote de caméra du fabricant"]


def test_verifier_puis_tout_mettre_a_jour():
    r = reglages.Reglages(ignores_winget=["Git.Git"])
    b = orchestre.verifier_tout(r)
    assert not b.erreurs
    assert "Git.Git" not in [p.id for p in orchestre.a_mettre_a_jour(b, r)]
    resume = orchestre.tout_mettre_a_jour(r, bilan=b, admin=True)
    assert resume[0] == "Programmes : 5 sur 5 mis à jour."
    assert "Pilote graphique 621.14 installé." in resume and "3 raccourci(s) mis de côté." in resume
    assert not any(l.startswith("À faire à la main : NVIDIA") for l in resume)
    resume = orchestre.tout_mettre_a_jour(r, bilan=b, admin=True, pilote=False, ranger_raccourcis=False)
    assert any(l.startswith("À faire à la main : NVIDIA") for l in resume)


# ------------------------------------------------------------ ménage
def test_menage_respecte_l_age(tmp_path, monkeypatch):
    monkeypatch.setattr(menage.demo, "actif", lambda: False)
    monkeypatch.setenv("TEMP", str(tmp_path))
    vieux, recent = tmp_path / "vieux.tmp", tmp_path / "sous" / "recent.tmp"
    recent.parent.mkdir()
    vieux.write_bytes(b"x" * 1000)
    recent.write_bytes(b"y" * 10)
    ancien = time.time() - 10 * 86400
    os.utime(vieux, (ancien, ancien))
    assert menage.mesurer("temp_utilisateur") == (1000, 1)
    assert menage.nettoyer("temp_utilisateur") == 1000
    assert not vieux.exists() and recent.exists() and tmp_path.exists()


def test_tailles_lisibles():
    assert menage.taille_lisible(None) == "?"
    assert menage.taille_lisible(512) == "512 o"
    assert menage.taille_lisible(3 * 1024 ** 3) == "3,0 Go"


# ------------------------------------------------------------ réglages, historique
def test_reglages_et_historique():
    r = reglages.charger()
    r.ignores_winget = ["A.B"]
    reglages.enregistrer(r)
    assert reglages.charger().ignores_winget == ["A.B"]
    historique.ajouter("auto", ["ligne"], "résumé")
    assert historique.lire()[0]["resume"] == "résumé"


def test_rapprochements_d_un_vrai_poste():
    """Noms relevés sur un vrai poste : pas de faux rapprochement."""
    cat = sources.charger()

    def source(nom):
        return next((s.id for s in cat if s.correspond(nom)), None)
    assert source("PHD2") == "phd2" and source("PHD2 Log Viewer version 0.6.4") is None
    assert source("ASTAP") == "astap" and source("ASTAP D80 star database. v2022-03-17") is None
    assert source("ASTAP, Astrometric STAcking Program") == "astap"
    assert source("GraXpert") == "graxpert"
    assert source("Google Chrome") == "chrome" and source("NVIDIA Pilote graphique 621.01") == "nvidia-app"
    assert source("Adobe Photoshop 2026") == "adobe"


def test_version_inconnue_lue_dans_le_nom():
    s = next(s for s in sources.charger() if s.id == "astap")
    assert sources.version_installee("Cartes du Ciel V4.3", "Unknown") == "4.3"
    assert sources.version_installee("ASTAP", "Unknown") == ""
    r = sources.verifier(s, "ASTAP", "Unknown")
    assert r.etat == "inconnu" and r.installee == "?"
    chrome = next(s for s in sources.charger() if s.id == "chrome")
    assert sources.verifier(chrome, "Google Chrome", "157.0").etat == "seul"


def test_bruit_d_un_vrai_poste():
    bruit = [("ARP\\Machine\\X64\\Steam App 223750", "Un simulateur"),
             ("ARP\\Machine\\X64\\F9D2", "Package de pilotes Windows - Garmin (grmnusb)"),
             ("ARP\\Machine\\X64\\{ad8a}", "Microsoft Visual C++ 2005 Redistributable (x64)")]
    for ident, nom in bruit:
        assert orchestre._est_bruit(winget.Paquet(ident, nom, "1")), nom
    assert not orchestre._est_bruit(winget.Paquet("ARP\\Machine\\X86\\PixInsight 1.9.6", "PixInsight", "1.9.6"))


def test_import_de_sources(tmp_path):
    f = tmp_path / "sources.json"
    f.write_text(json.dumps([{"id": "outil", "nom": "Outil", "motif": "^Outil$", "type": "github",
                              "depot": "editeur/outil", "fichier": "Setup\\.exe$"}]), encoding="utf-8")
    assert sources.importer(f) == 1
    assert any(s.id == "outil" and s.perso for s in sources.charger())
    f.write_text(json.dumps([{"id": "x", "nom": "X", "motif": "(", "type": "github"}]), encoding="utf-8")
    with pytest.raises(Exception):
        sources.importer(f)


def test_ligne_crlf_conservee():
    from martinet import systeme
    assert systeme.nettoyer_ligne("###JSON###\r") == "###JSON###"
    assert systeme.nettoyer_ligne("10%\r50%\r100%\r") == "100%"


def test_clixml_lisible():
    from martinet import systeme
    brut = ('#< CLIXML\n<Objs Version="1.1.0.1" xmlns="x"><S S="Error">Acc&#232;s refus&#233;_x000D__x000A_</S>'
            '<S S="Error">HRESULT 0x800106ba_x000D__x000A_</S></Objs>')
    assert systeme.clixml_lisible(brut) == "Accès refusé HRESULT 0x800106ba"


def test_echec_windows_update_n_arrete_pas_la_suite(monkeypatch):
    from martinet import orchestre, windows_update
    from martinet.reglages import Reglages

    def casse(*a, **k):
        raise RuntimeError("code 0")
    monkeypatch.setattr(windows_update, "installer", casse)
    b = orchestre.verifier_tout(Reglages())
    resume = orchestre.tout_mettre_a_jour(Reglages(), bilan=b, admin=True, programmes=False)
    texte = "\n".join(resume)
    assert "Windows Update" in texte and "code 0" in texte
    assert any("Ménage" in l or "Clean" in l or "libéré" in l for l in resume), resume


class _JournalEssai(list):
    def __init__(self):
        super().__init__()
        self.avances = []

    def __call__(self, t):
        self.append(t)

    def progres(self, f, libelle=""):
        self.avances.append((f, libelle))


def test_progression_monte_jusqu_au_bout():
    from martinet import orchestre
    from martinet.reglages import Reglages
    j = _JournalEssai()
    b = orchestre.verifier_tout(Reglages(), j)
    fr = [f for f, _ in j.avances]
    assert fr == sorted(fr) and fr[-1] == 1.0 and len(fr) > 5
    assert any(l for _, l in j.avances)
    j2 = _JournalEssai()
    orchestre.tout_mettre_a_jour(Reglages(), j2, bilan=b, admin=True)
    fr = [f for f, _ in j2.avances]
    assert fr == sorted(fr) and fr[-1] == 1.0


def test_menage_nouveaux_elements_demo():
    from martinet import menage
    for e in menage.ELEMENTS:
        t, _n = menage.mesurer(e.cle)
        assert t is None or t >= 0


def test_menage_miniatures_filtre(tmp_path, monkeypatch):
    from martinet import menage
    monkeypatch.delenv("MARTINET_DEMO", raising=False)
    monkeypatch.setattr(menage.demo, "actif", lambda: False)
    ex = tmp_path / "Microsoft" / "Windows" / "Explorer"
    ex.mkdir(parents=True)
    (ex / "thumbcache_256.db").write_bytes(b"x" * 10)
    (ex / "autre.dat").write_bytes(b"y" * 5)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert menage.mesurer("miniatures") == (10, 1)
    menage.nettoyer("miniatures")
    assert not (ex / "thumbcache_256.db").exists() and (ex / "autre.dat").exists()


PAGE_AMD = ('<a href="https://drivers.amd.com/drivers/amd-software-adrenalin-edition-26.11.1-win11-b.exe">opt</a>'
            '<a href="https://drivers.amd.com/drivers/whql-amd-software-adrenalin-edition-26.10.1-win11-b.exe">rec</a>'
            '<a href="https://drivers.amd.com/drivers/installer/26.20/beta/amd-software-adrenalin-edition-26.11.1-'
            'minimalsetup-261111_web.exe">auto</a>')


def test_amd_recommande_jamais_optionnel():
    from martinet import sources
    r = sources.lire_page_amd(PAGE_AMD)
    assert r["version"] == "26.10.1" and r["fichier"].endswith("whql-amd-software-adrenalin-edition-26.10.1-win11-b.exe")
    assert not r["historique"]
    v = sources.lire_page_amd('"https://drivers.amd.com/drivers/whql-amd-software-adrenalin-edition-26.5.2-win11-may-vega-polaris.exe"')
    assert v["version"] == "26.5.2" and v["historique"]


def test_amd_page_produit():
    from martinet import sources
    assert sources.url_amd("AMD Radeon RX 9070 XT").endswith(
        "graphics/radeon-rx/radeon-rx-9000-series/amd-radeon-rx-9070-xt.html")
    assert sources.url_amd("AMD Radeon RX 7900 XTX").endswith("radeon-rx-7000-series/amd-radeon-rx-7900-xtx.html")
    assert sources.url_amd("AMD Radeon(TM) Graphics", "AMD Ryzen 7 5700G with Radeon Graphics").endswith(
        "processors/ryzen/ryzen-5000-series/amd-ryzen-7-5700g.html")
    assert sources.url_amd("AMD Radeon(TM) Graphics", "AMD Ryzen 7 7800X3D 8-Core Processor").endswith(
        "ryzen-7000-series/amd-ryzen-7-7800x3d.html")
    assert sources.url_amd("Microsoft Basic Display Adapter", "Intel Core i5-6600K") == ""


def test_amd_comparaison(monkeypatch):
    from martinet import sources
    from martinet.materiel import Carte
    monkeypatch.setattr(sources.demo, "actif", lambda: False)
    monkeypatch.setattr(sources.systeme, "telecharger_texte", lambda url, timeout=20: PAGE_AMD)
    c = Carte("AMD Radeon RX 9070 XT", "amd", "7550", "32.0.21030.1000", version_logiciel="26.5.1")
    r = sources.verifier_carte(c)
    assert r.etat == "maj" and r.derniere == "26.10.1" and r.installee == "26.5.1"
    c.version_logiciel = "26.10.1"
    assert sources.verifier_carte(c).etat == "a_jour"
    c.version_logiciel = ""
    r = sources.verifier_carte(c)
    assert r.etat == "inconnu" and r.derniere == "26.10.1" and r.fichier


def test_passage_interrompu_entre_dans_historique(tmp_path, monkeypatch):
    from martinet import historique, systeme
    monkeypatch.setattr(systeme, "dossier_donnees", lambda: tmp_path)
    historique.demarrer_passe("manuel")
    historique.ecrire_passe("winget upgrade Exemple.Paquet")
    historique.ecrire_passe("Installation de Exemple 2.0…")
    assert historique.recuperer_passe_interrompue("Passage interrompu")
    e = historique.lire()[0]
    assert e["mode"] == "manuel" and "Installation de Exemple 2.0" in e["resume"]
    assert not (tmp_path / "passage_en_cours.log").exists()
    assert not historique.recuperer_passe_interrompue("x")      # une seule fois


def test_passage_termine_ne_laisse_rien(tmp_path, monkeypatch):
    from martinet import historique, systeme
    monkeypatch.setattr(systeme, "dossier_donnees", lambda: tmp_path)
    historique.demarrer_passe("auto")
    historique.ecrire_passe("ligne")
    historique.finir_passe()
    assert not historique.recuperer_passe_interrompue("x")
    assert historique.lire() == []


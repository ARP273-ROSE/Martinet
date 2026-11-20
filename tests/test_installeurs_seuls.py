"""Logiciels hors winget que Martinet installe lui-même (ASIStudio) : lien direct,
signature Authenticode exigée, report si le logiciel est ouvert."""
from martinet import observatoire, orchestre, sources, systeme
from martinet.i18n import definir_langue
from martinet.reglages import Reglages

definir_langue("fr")

SUJET_ZWO = ('CN="SUZHOU ZWO CO., LTD.", O="SUZHOU ZWO CO., LTD.", L=Suzhou, S=Jiangsu, C=CN, '
             'SERIALNUMBER=91320500, OID.2.5.4.15=Private Organization')


def _catalogue():
    return {s.id: s for s in sources.charger()}


def test_seul_asistudio_est_automatique():
    cat = _catalogue()
    assert sources.automatique(cat["asistudio"])
    # pilotes de caméra et ASCOM : lien direct pour le bouton « Installer », jamais seuls
    assert cat["zwo-ascom"].installeur and not sources.automatique(cat["zwo-ascom"])
    assert cat["zwo-camera"].installeur and not sources.automatique(cat["zwo-camera"])


def test_page_donne_le_lien_direct(monkeypatch):
    src = _catalogue()["asistudio"]
    monkeypatch.setattr(systeme, "telecharger_texte",
                        lambda url, **k: "<p>Windows X64 Version: V1.23.0.0</p>")
    version, _page, lien = sources.derniere(src)
    assert version == "1.23.0.0" and lien.startswith("https://dl.zwoastro.com/")


def test_nom_de_fichier_pour_un_lien_de_redirection():
    r = sources.Resultat("ASIStudio", "1.22.0.0", derniere="1.23.0.0", source="asistudio",
                         fichier="https://dl.zwoastro.com/software?app=ASIStudio&platform=windows64")
    assert sources.nom_installeur(r) == "asistudio-1.23.0.0.exe"
    r.fichier = "https://exemple.org/dl/Outil_Setup.exe?jeton=1"
    assert sources.nom_installeur(r) == "Outil_Setup.exe"


def test_signataire_attendu(monkeypatch):
    motif = _catalogue()["asistudio"].signataire
    monkeypatch.setattr(sources, "signature", lambda c: ("Valid", SUJET_ZWO))
    assert sources.signature_attendue("x.exe", motif) == ""
    monkeypatch.setattr(sources, "signature", lambda c: ("Valid", 'CN="Quelqu\'un d\'autre"'))
    assert "inattendu" in sources.signature_attendue("x.exe", motif)
    monkeypatch.setattr(sources, "signature", lambda c: ("NotSigned", ""))
    assert "NotSigned" in sources.signature_attendue("x.exe", motif)


def _bilan():
    r = sources.Resultat("ASIStudio", "1.22.0.0", derniere="1.23.0.0", etat="maj", source="asistudio",
                         fichier=_catalogue()["asistudio"].installeur)
    return orchestre.Bilan(hors=[r]), r


def _passage(monkeypatch, ouverts=frozenset(), signature=("Valid", SUJET_ZWO), admin=True):
    lances = []
    monkeypatch.setattr(orchestre, "systeme_demo", lambda: False)
    monkeypatch.setattr(systeme, "linux", lambda: False)
    monkeypatch.setattr(systeme, "attendre_reseau", lambda *a, **k: True)
    monkeypatch.setattr(systeme, "telecharger_fichier", lambda url, dest, *a, **k: dest)
    monkeypatch.setattr(systeme, "executer_flux", lambda cmd, *a, **k: (lances.append(cmd), (0, ""))[1])
    monkeypatch.setattr(sources, "signature", lambda c: signature)
    monkeypatch.setattr(observatoire, "processus_en_cours", lambda: set(ouverts))
    b, _r = _bilan()
    resume = orchestre.tout_mettre_a_jour(Reglages(), bilan=b, admin=admin, windows=False, nettoyer=False,
                                          pilote=False, ranger_raccourcis=False)
    return resume, lances


def test_passage_installe_asistudio_sans_fenetre(monkeypatch):
    resume, lances = _passage(monkeypatch)
    assert len(lances) == 1 and lances[0][1:] == ["/S"]
    assert "ASIStudio 1.23.0.0 installé." in resume
    assert not any(l.startswith("À faire à la main : ASIStudio") for l in resume)


def test_signature_refusee_rien_ne_se_lance(monkeypatch):
    resume, lances = _passage(monkeypatch, signature=("HashMismatch", SUJET_ZWO))
    assert lances == []
    assert any("ASIStudio non installé" in l and "HashMismatch" in l for l in resume)
    assert any(l.startswith("À faire à la main : ASIStudio") for l in resume)


def test_reporte_si_asicap_est_ouvert(monkeypatch):
    resume, lances = _passage(monkeypatch, ouverts={"asicap", "explorer"})
    assert lances == [] and "ASIStudio reporté : asicap ouvert." in resume


def test_sans_droits_admin_signale_seulement(monkeypatch):
    resume, lances = _passage(monkeypatch, admin=False)
    assert lances == [] and any("ASIStudio" in l and "administrateur" in l for l in resume)

"""Garde d'observatoire : pas de passage automatique pendant une acquisition ni la nuit,
pas de pilote Windows Update automatique sur un poste astro."""
import datetime as dt

from martinet import observatoire
from martinet.reglages import Reglages
from martinet.windows_update import MiseAJour


def _maj(pilote, facultatif=False):
    return MiseAJour(id=f"{pilote}{facultatif}", titre="x", pilote=pilote, facultatif=facultatif, taille=0)


def test_plage_qui_passe_minuit():
    p = "17:00-09:00"
    assert observatoire.dans_plage(dt.time(23, 30), p)
    assert observatoire.dans_plage(dt.time(3, 0), p)
    assert observatoire.dans_plage(dt.time(17, 0), p)
    assert not observatoire.dans_plage(dt.time(9, 0), p)
    assert not observatoire.dans_plage(dt.time(12, 0), p)


def test_plage_de_jour_vide_ou_invalide():
    assert observatoire.dans_plage(dt.time(10, 0), "09:00-11:00")
    assert not observatoire.dans_plage(dt.time(12, 0), "09:00-11:00")
    assert not observatoire.dans_plage(dt.time(3, 0), "")
    assert not observatoire.dans_plage(dt.time(3, 0), "nuit")


def test_reporte_pendant_acquisition_et_la_nuit():
    r = Reglages(garde_observatoire="oui")
    midi = dt.datetime(2026, 11, 22, 12, 0)
    nuit = dt.datetime(2026, 11, 22, 2, 0)
    assert observatoire.raison_de_reporter(r, midi, processus={"explorer"}) is None
    assert observatoire.raison_de_reporter(r, midi, processus={"nina", "explorer"}) == "acquisition:nina"
    assert observatoire.raison_de_reporter(r, nuit, processus=set()) == "nuit:17:00-09:00"


def test_garde_coupee_ne_reporte_jamais():
    r = Reglages(garde_observatoire="non")
    assert observatoire.raison_de_reporter(r, dt.datetime(2026, 11, 22, 2, 0), processus={"phd2"}) is None


def test_auto_hors_poste_astro_ne_garde_pas():
    # en démonstration (et sous Linux) il n'y a pas de poste d'observatoire
    assert not observatoire.active(Reglages())


def test_pilotes_retenus_sur_poste_astro():
    liste = [_maj(False), _maj(True), _maj(True, True), _maj(False, True)]
    r = Reglages(garde_observatoire="oui", facultatives=True)
    voulues = observatoire.windows_voulues(liste, r)
    assert all(not m.pilote for m in voulues) and len(voulues) == 2
    assert len(observatoire.pilotes_retenus(liste, r)) == 2
    r.facultatives = False
    assert observatoire.windows_voulues(liste, r) == [liste[0]]


def test_sans_garde_comportement_inchange():
    liste = [_maj(False), _maj(True), _maj(True, True)]
    r = Reglages(garde_observatoire="non", facultatives=True)
    assert observatoire.windows_voulues(liste, r) == liste
    assert observatoire.pilotes_retenus(liste, r) == []
    r.facultatives = False
    assert observatoire.windows_voulues(liste, r) == liste[:2]


def test_auto_reporte_sans_rien_lancer(monkeypatch):
    from martinet import auto, historique, orchestre
    notes = []
    monkeypatch.setattr(auto.mod_reglages, "charger", lambda: Reglages(garde_observatoire="oui"))
    monkeypatch.setattr(observatoire, "processus_en_cours", lambda: {"nina"})
    monkeypatch.setattr(historique, "ajouter", lambda mode, lignes, resume, date="": notes.append(resume))

    def interdit(*a, **k):
        raise AssertionError("aucune mise à jour pendant une acquisition")
    monkeypatch.setattr(orchestre, "tout_mettre_a_jour", interdit)
    assert auto.executer(notifier=False) == 0
    assert notes and "nina" in notes[0]

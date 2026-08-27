# Testplan – PF2 Cross-Model-Gegencheck v0.1

Vor Merge lokal ausführen:

```powershell
python -m unittest tests.synthetic.test_sem_pf2_cross_model_countercheck_v0_1
python -m unittest discover -s tests
```

Erwartung: beide Läufe GREEN. Kein Modellkontakt.

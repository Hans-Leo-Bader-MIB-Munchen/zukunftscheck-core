# ZS-DEV-KI-B-SEM-V22-PERSISTENT-AUTHORIZATION-CONSUMPTION-PREP-2026-001

## Zweck

Dieser Block schliesst modellfrei die in V21 noch offene Persistenzluecke zwischen einer nur im Speicher konsumierten Einmal-Autorisierung und einem spaeter robusten Live-Runner. Er definiert eine persistente Single-Use-Claim-Grenze, die vor jedem spaeteren Modellkontakt ausgefuehrt werden muss.

## Verbindliche Ausgangsbindung

V22 baut auf der in V21 gesicherten 16-Fall-Autorisierungsstruktur auf. Unveraendert gebunden bleiben insbesondere Ministral, die candidate Prompt-/Schema-Hashes, voller 67/67-Kontext, `max_tokens=1024`, `stream=false`, Timeout 1800 Sekunden, Retry 0, Output-Repair false, synthetic-only, loopback-only und single-run-only.

## Persistente Consumption-Grenze

`claim_authorization_once()` akzeptiert nur ein exakt gueltiges V21-Autorisierungsobjekt. Der Zielpfad wird mit exklusiver Dateierzeugung (`O_CREAT | O_EXCL`) beansprucht. Dadurch kann fuer denselben State-Pfad nur ein Prozess gewinnen; ein bereits existierender Claim beendet jeden weiteren Versuch fail-closed.

Der persistierte Zustand wird vor einem spaeteren Modellkontakt als `CONSUMED_PRE_MODEL_CONTACT` geschrieben, mit `authorization_consumed=true` und allen Autorisierungsfeldern wieder auf false. Die Datei wird vor Rueckgabe mit `fsync` dauerhaft geschrieben. Erst danach wird auch das uebergebene In-Memory-Objekt geschlossen.

Ein Schreibfehler nach erfolgreicher exklusiver Dateierzeugung darf den Claim nicht still freigeben: Der existierende Zielpfad blockiert einen erneuten Versuch fail-closed. Ein spaeterer produktionsnaher Runner darf daher einen unlesbaren oder unvollstaendigen Claim niemals als neue Freigabe interpretieren.

## Abgrenzung

V22 erzeugt beim normalen Report keine Authorization- oder Consumption-Datei, besitzt keinen Default-State-Pfad und keinen Transport-, HTTP-, localhost-, Preflight- oder Modellgenerationspfad. Die persistente Schreibfunktion wird nur explizit mit einem Pfad und einem bereits exakt autorisierten Objekt aufgerufen; die Tests verwenden ausschliesslich temporaere lokale Dateien und In-Memory-Daten.

`persistent_consumption_binding_ready=true` bedeutet daher nicht `READY_TO_EXECUTE`. Es gibt weiterhin keine aktuelle Modellkontaktfreigabe, keinen Modelllauf und keine Modellqualifikation. `READY_TO_EXECUTE=false` und `MODEL_QUALIFIED=false` bleiben verbindlich.

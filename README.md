# OdoPlan für Home Assistant

[OdoPlan](https://www.odoplan.ch) rechnet dein Kilometerkontingent für Leasing oder Versicherung auf jeden Tag herunter. Diese Integration holt die Zahlen deiner Autos als Sensoren nach Home Assistant und trägt den Kilometerstand auf Wunsch automatisch ein.

*English below.*

## Was du bekommst

Pro Auto ein Gerät mit diesen Sensoren:

| Sensor | Bedeutung |
|---|---|
| Polster | Kilometer vor (positiv) oder hinter (negativ) dem Plan |
| Status | Im Plan, leicht darüber oder darüber |
| Woche noch frei / Monat noch frei | Was du bis Sonntag bzw. Monatsende noch fahren kannst |
| Nächster Monat | Monatsbudget für den nächsten Monat |
| Kilometerstand, Letzter Eintrag | Der zuletzt eingetragene Stand und sein Datum |
| Gefahren seit Vertragsbeginn, Erlaubt bis heute | Die beiden Linien des Diagramms |
| Tempo, Normaler Tag | km pro Tag zuletzt und ohne Ferien und lange Fahrten |
| Vertrag noch frei, Prognose Vertragsende, Vertragsende | nur mit Vertragsdauer |
| Prognose Vertragsjahr | Wo du am Ende des Vertragsjahrs landest |
| Mehrkilometer, Mehrkilometer-Kosten | Was am Ende zu viel wäre und was es kostet (Kosten nur mit Preis pro Mehrkilometer) |
| Nächster Vertrag | Vorgeschlagenes Kontingent pro Jahr |
| Elektrisch gefahren | nur Plug-in-Hybrid |
| Verbrauch, Energie pro 100 km | aus Tank- und Ladevorgängen |

Dazu die Aktion **OdoPlan: Kilometerstand eintragen** (`odoplan.add_reading`). Home Assistant fragt OdoPlan alle 15 Minuten nach den Zahlen.

## Installation

1. In HACS oben rechts ⋮ → *Benutzerdefinierte Repositories*, diese Adresse eintragen, Typ *Integration*.
2. **OdoPlan** in HACS suchen, herunterladen, Home Assistant neu starten.
3. *Einstellungen → Geräte & Dienste → Integration hinzufügen → OdoPlan*.
4. Den Schlüssel eintragen. Du erzeugst ihn in OdoPlan bei einem Auto unter **Automatisierung**; er gilt für alle deine Autos.

Ohne HACS: den Ordner `custom_components/odoplan` in den Ordner `custom_components` deiner Home-Assistant-Konfiguration kopieren und neu starten.

## Kilometerstand jeden Abend eintragen

Kennt Home Assistant den Kilometerstand deines Autos, etwa über die Integration des Herstellers:

```yaml
automation:
  - alias: "OdoPlan: Kilometerstand eintragen"
    triggers:
      - trigger: time
        at: "22:00:00"
    actions:
      - action: odoplan.add_reading
        data:
          device_id: DEINE_GERÄTE_ID   # im Aktions-Editor das Auto auswählen
          km: "{{ states('sensor.dein_auto_mileage') }}"
```

Ein Eintrag pro Tag; kommt am selben Tag ein neuer Wert, wird er korrigiert. Wie in der App muss der Stand zu den anderen passen. Wer bisher den `rest_command` aus OdoPlan nutzt, kann ihn durch diese Aktion ersetzen.

## Beispiel für ein Dashboard

```yaml
type: vertical-stack
cards:
  - type: gauge
    entity: sensor.familienauto_polster
    min: -1000
    max: 1000
    severity:
      green: 0
      yellow: -300
      red: -1000
  - type: entities
    entities:
      - sensor.familienauto_status
      - sensor.familienauto_monat_noch_frei
      - sensor.familienauto_prognose_vertragsende
      - sensor.familienauto_mehrkilometer_kosten
  - type: history-graph
    hours_to_show: 720
    entities:
      - sensor.familienauto_polster
```

Die Namen der Sensoren hängen vom Namen deines Autos und der Sprache von Home Assistant ab.

## Datenschutz

Die Integration spricht nur mit der Adresse, die du beim Einrichten angibst (in der Regel `https://www.odoplan.ch`), und schickt nur deinen Schlüssel und die Kilometerstände, die du einträgst. Wie OdoPlan mit deinen Daten umgeht, steht in der [Datenschutzerklärung](https://www.odoplan.ch/datenschutz).

---

## English

This integration brings the numbers of your cars in [OdoPlan](https://www.odoplan.ch) – buffer, what is left this week and month, forecast at contract end, extra kilometre cost, suggestion for the next contract and more – into Home Assistant as sensors, one device per car, and adds the action `odoplan.add_reading` to enter the odometer. Install it as a custom repository in HACS, then add **OdoPlan** under *Settings → Devices & services* with the key from a car's **Automation** page in OdoPlan. The entities are translated into English, German, French and Italian.

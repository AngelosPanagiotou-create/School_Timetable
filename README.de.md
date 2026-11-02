[Ελληνικά](README.md) · [English](README.en.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md)

# Ωρολόγιο (Stundenplan)

**Eine Windows-App, die den Wochenstundenplan der Lehrkräfte einer Schule erstellt.**

Du gibst Lehrkräfte, Klassen und Zuweisungen ein. Die App füllt die ganze Woche selbst. Danach passt du per Ziehen an, was du willst, und druckst den Plan als PDF. Ohne Konto, ohne Abo, und die Daten bleiben auf deinem Computer.

## Funktionen

- **Automatisches Füllen** mit Google OR-Tools. Die ganze Woche wird auf einmal gelöst: alle Stunden werden gesetzt, mit möglichst wenigen Springstunden.
- **Schulregeln:**
  - lückenlose Stunden für Schüler,
  - Sperrzeiten der Lehrkräfte,
  - Springstunden und Höchststunden pro Tag je Lehrkraft,
  - Doppelstunden,
  - Öffnungszeiten der Schule (z. B. freitags nur bis zur 6. Stunde).
- **Gleichzeitige Kurse:** Gruppen mit eigenem Namen, z. B. parallel unterrichtete Fremdsprachen.
- **Zonen:** Stunden der Woche nur für bestimmte Kurse, z. B. Profil- oder Wahlkurse des Abschlussjahrgangs. In einer Zone liegt keine andere Stunde desselben Jahrgangs.
- **Änderungen von Hand:** ziehen, Stunden tauschen, sperren. Das Feld „Probleme“ zeigt, was nicht eingehalten wird.
- **Druck** nach Lehrkraft und nach Klasse, mit Archiv aller Ausdrucke.
- **Mehrere Schulen**, jede mit eigenen Lehrkräften und eigenem Plan.
- **Mehrere Pläne in einem Lauf:** es findet 2–4 verschiedene, gleich gute Pläne, und du behältst den, der dir gefällt.
- **Automatisches Speichern** und Sicherungen, mit Wiederherstellung der letzten oder vorletzten Speicherung.
- **Fünf Sprachen:** Ελληνικά, English, Français, Deutsch, Español. Auswahl beim ersten Start, änderbar in den Einstellungen.

## Installation

1. Klicke auf **Code → Download ZIP** und entpacke die Dateien in einen Ordner.
2. Doppelklicke auf **`Start.cmd`**.

Die App braucht **Python**. Fehlt es, fragt `Start.cmd` nach und installiert es. Beim ersten Mal werden auch die benötigten Bibliotheken geladen, das braucht Internet und einige Minuten. Danach gibt es ein Symbol auf dem Desktop.

**Voraussetzungen:** Windows 10 oder 11.

## So funktioniert es

1. Lege deine Schule an: Name und Öffnungszeiten (Klick auf die Stunden der Woche).
2. Lege die Klassen an, gib an, welche Kurse gleichzeitig stattfinden, und eventuelle Zonen. Dann die Lehrkräfte und ihre Zuweisungen.
3. Klicke auf **Automatisch füllen**, korrigiere nach Bedarf und drucke.

Ausführliche Anleitung: [`ANLEITUNG.txt`](ANLEITUNG.txt).

> Die Programmdateien behalten ihre griechischen Namen (`Ωρολόγιο.pyw`, `Ωρολόγιο.html` …), ebenso der Datenordner `Dokumente\Ωρολόγιο`. Das ist normal.

## Lizenz

[MIT](LICENSE): frei nutzen, ändern und weitergeben.

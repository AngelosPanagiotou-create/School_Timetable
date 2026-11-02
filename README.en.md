[Ελληνικά](README.md) · [English](README.en.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md)

# Ωρολόγιο (Timetable)

**A Windows app that builds a school’s weekly teacher timetable.**

You enter the teachers, the classes and the assignments. The app fills in the whole week by itself. Then you adjust whatever you like by dragging, and print the timetable to PDF. No account, no subscription, and your data stays on your computer.

## Features

- **Auto-fill** with Google OR-Tools. It solves the whole week at once, places every period and leaves as few teacher gaps as possible.
- **School rules:**
  - consecutive periods for students,
  - teacher unavailability,
  - gaps and maximum periods per day for each teacher,
  - double periods,
  - school opening hours (e.g. Friday only until period 6).
- **Lessons at the same time:** groups with your own name, e.g. foreign languages taught in parallel.
- **Zones:** periods of the week reserved for certain lessons only, e.g. the track/option lessons of the final year. No other lesson of the same year is placed inside a zone.
- **Manual changes:** drag, swap periods, lock. The “Problems” panel shows what is not respected.
- **Printing** by teacher and by class, with an archive of every print.
- **Several schools**, each with its own teachers and timetable.
- **Autosave** and backups.
- **Five languages:** Ελληνικά, English, Français, Deutsch, Español. You choose at first start and can change it in Settings.

## Installation

1. Click **Code → Download ZIP** and unzip the files into a folder.
2. Double-click **`Start.cmd`**.

The app needs **Python**. If it is missing, `Start.cmd` asks you and installs it. The first time, the required libraries are also downloaded, so it needs internet and a few minutes. A desktop icon is then created.

**Requirements:** Windows 10 or 11.

## How it works

1. Add your school: name and opening hours (click the periods of the week).
2. Create the classes, declare which lessons take place at the same time and any zones. Then the teachers and their assignments.
3. Click **Auto-fill**, make any corrections you want and print.

Detailed instructions are in [`INSTRUCTIONS.txt`](INSTRUCTIONS.txt).

> The program files keep their Greek names (`Ωρολόγιο.pyw`, `Ωρολόγιο.html` …) and so does the data folder `Documents\Ωρολόγιο`. That is normal.

## License

[MIT](LICENSE): free to use, change and share.

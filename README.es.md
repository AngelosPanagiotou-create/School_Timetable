[Ελληνικά](README.md) · [English](README.en.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md)

# Ωρολόγιο (Horario)

**Una aplicación para Windows que crea el horario semanal del profesorado de un centro.**

Introduces los docentes, los grupos y las asignaciones. La aplicación rellena sola toda la semana. Después ajustas lo que quieras arrastrando e imprimes el horario en PDF. Sin cuenta, sin suscripción, y los datos se quedan en tu ordenador.

## Características

- **Rellenado automático** con Google OR-Tools. Resuelve toda la semana a la vez: coloca todas las horas con los menos huecos posibles para el profesorado.
- **Reglas del centro:**
  - horas seguidas para los alumnos,
  - indisponibilidad del profesorado,
  - huecos y máximo de horas por día para cada docente,
  - horas dobles,
  - horario del centro (p. ej. viernes solo hasta la 6.ª hora).
- **Clases simultáneas:** grupos con el nombre que elijas, p. ej. idiomas impartidos en paralelo.
- **Zonas:** horas de la semana reservadas a ciertas materias, p. ej. los itinerarios u optativas del último curso. Dentro de una zona no se coloca ninguna otra clase del mismo curso.
- **Cambios a mano:** arrastrar, intercambiar horas, bloquear. El panel «Problemas» muestra lo que no se cumple.
- **Impresión** por docente y por grupo, con archivo de todas las impresiones.
- **Varios centros**, cada uno con sus docentes y su horario.
- **Varios horarios en una ejecución:** encuentra 2–4 horarios distintos e igual de buenos y te quedas con el que prefieras.
- **Guardado automático** y copias de seguridad, con recuperación del último o penúltimo guardado.
- **Cinco idiomas:** Ελληνικά, English, Français, Deutsch, Español. Se elige en el primer inicio y se cambia en Ajustes.

## Instalación

1. Pulsa **Code → Download ZIP** y descomprime los archivos en una carpeta.
2. Haz doble clic en **`Start.cmd`**.

La aplicación necesita **Python**. Si no está, `Start.cmd` te lo pregunta y lo instala. La primera vez también se descargan las bibliotecas necesarias, así que hace falta internet y unos minutos. Después se crea un icono en el escritorio.

**Requisitos:** Windows 10 u 11.

## Cómo se usa

1. Añade tu centro: nombre y horario (clic en las horas de la semana).
2. Crea los grupos, indica qué clases van a la misma hora y las zonas, si las hay. Después los docentes y sus asignaciones.
3. Pulsa **Rellenado automático**, corrige lo que quieras e imprime.

Instrucciones detalladas: [`INSTRUCCIONES.txt`](INSTRUCCIONES.txt).

> Los archivos del programa conservan sus nombres en griego (`Ωρολόγιο.pyw`, `Ωρολόγιο.html` …), igual que la carpeta de datos `Documentos\Ωρολόγιο`. Es normal.

## Licencia

[MIT](LICENSE): uso, modificación y distribución libres.

# -*- coding: utf-8 -*-
"""Ωρολόγιο — επίλυση με Google OR-Tools (CP-SAT).
Ίδιοι κανόνες με την ενσωματωμένη μηχανή (engine.js)."""
import time

# βάρη «προσπαθειών» (μεγαλύτερο = πιο σημαντικό)
W_GAP = 60     # κάθε κενό εκπαιδευτικού χωρίς δηλωμένα κενά
W_FAIR = 30    # ισομοιρασμός κενών: το 2ο, 3ο… κενό στον ίδιο κοστίζει όλο και περισσότερο
W_BAL = 10     # ισοκατανομή ωρών εκπαιδευτικού: 1 ώρα πάνω/κάτω από τον στόχο
W_BAL2 = 200   # … 2+ ώρες πάνω/κάτω (π.χ. εξάωρο και δίωρο)
W_PREF, W_SOFT = 8, 40
W_STUDENT_BAL = 300   # ισοκατανομή ωρών μαθητών: προσπάθεια, πάνω από τα κενά


def split_units(n, split):
    if split == 'double1' and n >= 2:
        return [2] + [1] * (n - 2)
    if split == 'doubles':
        return [2] * (n // 2) + ([1] if n % 2 else [])
    return [1] * n


def blocks_of(a):
    n = int(a.get('hours') or 0)
    b = a.get('blocks')
    if isinstance(b, list) and b:
        b = sorted((max(1, min(3, int(x or 1))) for x in b), reverse=True)
        if sum(b) == n:
            return b
        out, t = [], 0
        for x in b:
            if t + x <= n:
                out.append(x)
                t += x
        return out + [1] * (n - t)
    return split_units(n, a.get('split') or 'single')


def remaining_blocks(blocks, fixed_n):
    n = sum(blocks) - fixed_n
    out, t = [], 0
    for x in blocks:
        if t + x <= n:
            out.append(x)
            t += x
    return out + [1] * max(0, n - t)


def is_mixed(c):
    return bool(c) and c.get('kind') in ('mixed', 'group') and bool(c.get('members'))


def base_classes(data, cid, seen=None):
    """Κανονικά τμήματα στα οποία καταλήγει ένα (μικτό) τμήμα, αναδρομικά."""
    seen = seen if seen is not None else set()
    if cid in seen:
        return []
    seen.add(cid)
    c = next((x for x in data['classes'] if x['id'] == cid), None)
    if not c:
        return []
    if not is_mixed(c):
        return [cid]
    out = []
    for m in c.get('members') or []:
        for b in base_classes(data, m, seen):
            if b not in out:
                out.append(b)
    return out


merge_of = {}
ZINFO = {}


def closed_set(data):
    return set((data.get('settings') or {}).get('closed') or [])


def sync_sets(data):
    """Ομάδες ταυτόχρονων + ζώνες (ίδια λογική με engine.js):
    ίδια ομάδα ταυτόχρονων → την ίδια ώρα· ίδια ζώνη → εναλλακτικές μόνο μέσα στη ζώνη·
    μικτό που χρεώνεται σε ≥2 μικτά της ίδιας ομάδας/ζώνης → κοινό τους τμήμα."""
    global merge_of, ZINFO
    cby = {c['id']: c for c in data['classes']}

    def is_dep(c):
        return any(is_mixed(cby.get(mb)) for mb in c.get('members') or [])
    sets, tag, set_of, merges, zone_of, max_hour_of = [], {}, {}, [], {}, {}
    merge_of = {}
    for g in data.get('syncGroups') or []:
        ids = [i for i in g.get('classIds') or [] if i in cby]
        for i in ids:
            if int(g.get('maxHour') or 0) > 0:
                max_hour_of[i] = int(g.get('maxHour'))
        if len(ids) < 2:
            continue
        ids.sort(key=lambda i: cby[i].get('name', ''))
        si = len(sets)
        sets.append(ids)
        merges.append([])
        for i in ids:
            set_of[i] = si
            if is_mixed(cby[i]):
                tag[i] = 'S:' + g['id']
    zones = list((data.get('settings') or {}).get('zones') or [])
    for z in zones:
        own = []
        for i in z.get('classIds') or []:
            if i not in cby:
                continue
            zone_of[i] = z
            if is_mixed(cby[i]) and i not in tag and not is_dep(cby[i]):
                tag[i] = 'Z:' + z['id']
                own.append(i)
        if len(own) >= 2:   # τα μαθήματα της ζώνης γίνονται ταυτόχρονα
            own.sort(key=lambda i: cby[i].get('name', ''))
            si = len(sets)
            sets.append(own)
            merges.append([])
            for i in own:
                set_of[i] = si
    for c in data['classes']:
        if not is_mixed(c) or not is_dep(c) or c['id'] in set_of:
            continue
        ms = [m for m in c.get('members') or [] if m in cby]
        t0 = tag.get(ms[0]) if ms else None
        if len(ms) >= 2 and t0 and all(tag.get(m) == t0 for m in ms):
            tag[c['id']] = t0
            merge_of[c['id']] = list(ms)
            si = set_of.get(ms[0])
            if si is not None and all(set_of.get(m) == si for m in ms):
                merges[si].append(c['id'])
                set_of[c['id']] = si
            if c['id'] not in zone_of and ms[0] in zone_of:
                zone_of[c['id']] = zone_of[ms[0]]
            continue
        tag.setdefault(c['id'], 'D:' + c['id'])
    zone_bases = {}
    for z in zones:
        o = set()
        for i in z.get('classIds') or []:
            if i in cby:
                o.update(base_classes(data, i))
        zone_bases[z['id']] = o
    ZINFO = {'zone_of': zone_of, 'max_hour_of': max_hour_of, 'zones': zones, 'zone_bases': zone_bases, 'closed': closed_set(data)}
    return sets, tag, merges


def slot_allowed(data, cid, d, h):
    """Κλειστή ώρα, ζώνη, «μόνο έως Νη ώρα», αποκλειστικότητα ζωνών (ίδια τάξη έξω από τη ζώνη)."""
    k = f'{d}-{h}'
    if k in ZINFO['closed']:
        return False
    mh = ZINFO['max_hour_of'].get(cid)
    if mh and h + 1 > mh:
        return False
    z = ZINFO['zone_of'].get(cid)
    if z:
        sl = z.get('slots') or []
        return not sl or k in sl
    bs = None
    for zz in ZINFO['zones']:
        if k not in (zz.get('slots') or []):
            continue
        bs = bs if bs is not None else set(base_classes(data, cid))
        if bs & ZINFO['zone_bases'][zz['id']]:
            return False
    return True


def label_of(data, a):
    names = {c['id']: c.get('name', '') for c in data['classes']}
    return '+'.join(names[i] for i in a.get('classIds', []) if i in names)


def build(data):
    D, H = int(data['settings']['days']), int(data['settings']['hours'])
    teachers = data['teachers']
    tidx = {t['id']: i for i, t in enumerate(teachers)}
    cby = {c['id']: c for c in data['classes']}
    sets, stag, smerges = sync_sets(data)
    def touches(class_ids):
        res = {}
        for cid in class_ids:
            c = cby.get(cid)
            if not c:
                continue
            members = [m for m in (c.get('members') or []) if m in cby]
            mixed = is_mixed(c) and bool(members)
            bases = base_classes(data, c['id']) if mixed else [c['id']]
            tag = stag.get(c['id'], '') if mixed else ''
            for b in bases:
                t = {'base': b, 'tag': tag, 'group': c['id'] if mixed else ''}
                prev = res.get(b)
                if prev is None or (prev['tag'] and not t['tag']):
                    res[b] = t
        return list(res.values())

    asg = []
    for a in data['assignments']:
        if a.get('teacherId') not in tidx:
            continue
        cls = [i for i in a.get('classIds', []) if i in cby]
        hours = int(a.get('hours') or 0)
        if not cls or hours <= 0:
            continue
        t = teachers[tidx[a['teacherId']]]
        av, sl = t.get('avail') or {}, a.get('slots') or {}
        allowed, pref, must = [], [], []
        for d in range(D):
            for h in range(H):
                k = f'{d}-{h}'
                fr, to = int(a.get('fromHour') or 0), int(a.get('toHour') or 0)
                in_range = (fr <= 0 or h + 1 >= fr) and (to <= 0 or h + 1 <= to)
                in_range = in_range and slot_allowed(data, cls[0], d, h)
                allowed.append(av.get(k) != 'no' and sl.get(k) != 'never' and in_range)
                pref.append(av.get(k) == 'pref')
                if sl.get(k) == 'must':
                    must.append(d * H + h)
        asg.append(dict(id=a['id'], ai=len(asg), t=tidx[a['teacherId']], hours=hours, split=a.get('split') or 'single', blocks=blocks_of(a),
                        sec=cls[0] if len(cls) == 1 else None,
                        maxPerDay=max(1, int(a.get('maxPerDay') or 1)), noConsecutive=bool(a.get('noConsecutive')),
                        allowed=allowed, pref=pref, must=must, touches=touches(cls), label=label_of(data, a)))
    # υποομάδες μαθητών (ίδια λογική με engine.js)
    tags_by_base, dep_tag = {}, set()
    for c in data['classes']:
        tag = stag.get(c['id'], '')
        if not is_mixed(c) or not tag or c['id'] in merge_of:
            continue
        if any(is_mixed(cby.get(mb)) for mb in c.get('members') or []):
            dep_tag.add(tag)
        for mb in base_classes(data, c['id']):
            tags_by_base.setdefault(mb, {}).setdefault(tag, []).append(c['id'])
    bases = []
    for a in asg:
        for tc in a['touches']:
            if tc['base'] not in bases:
                bases.append(tc['base'])
    sps, sps_by_base = [], {}
    for b in bases:
        tags = tags_by_base.get(b, {})
        keys = [tg for tg in sorted(tags) if tg not in dep_tag]
        deps = [tg for tg in sorted(tags) if tg in dep_tag]
        combos = [{}]
        for tg in keys:
            combos = [dict(cb, **{tg: g}) for cb in combos for g in tags[tg]]
        for cb in combos:   # εξαρτημένα («Κόντρα» σε μικτό): τα παίρνουν όσοι επέλεξαν τον γονέα
            for tg in deps:
                chosen = set(cb.values())
                hit = next((x for x in tags[tg] if set(cby[x].get('members') or []) & chosen), None)
                if hit:
                    cb[tg] = hit
        keys = [tg for tg in sorted(tags) if tg in keys or tg in deps]
        sps_by_base[b] = []
        for cb in combos:
            gn = [cby[cb[tg]].get('name', '') for tg in keys if cb.get(tg) in cby]
            sps.append({'i': len(sps), 'base': b, 'choice': cb, 'N': 0,
                        'name': cby[b].get('name', '') + (' · ' + ' · '.join(gn) if gn else '')})
            sps_by_base[b].append(len(sps) - 1)
    for a in asg:
        st = set()
        for tc in a['touches']:
            for pi in sps_by_base.get(tc['base'], []):
                ch = sps[pi]['choice']
                if tc['tag']:
                    mo = merge_of.get(tc['group'])
                    if (ch.get(tc['tag']) not in mo) if mo else (ch.get(tc['tag']) != tc['group']):
                        continue
                st.add(pi)
        a['sp'] = sorted(st)
        for pi in a['sp']:
            sps[pi]['N'] += a['hours']
    open_days = max(1, sum(1 for d in range(D) if any(f'{d}-{h}' not in ZINFO['closed'] for h in range(H))))
    for sp in sps:
        sp['lo'], sp['hi'] = sp['N'] // open_days, -(-sp['N'] // open_days)
    def hrs(i):
        return sum(a['hours'] for a in asg if a['sec'] == i)
    syncs = []
    for si, ids in enumerate(sets):
        mg = smerges[si]
        cover = [[x for x in mg if i in (cby[x].get('members') or [])] for i in ids]
        syncs.append({'secs': ids, 'merges': mg, 'cover': cover, 'name': ' / '.join(cby[i].get('name', '') for i in ids),
                      'hours': [hrs(i) + sum(hrs(x) for x in cover[k]) for k, i in enumerate(ids)]})
    return D, H, teachers, asg, sps, syncs




DAY_SHORT = ['Δευ', 'Τρί', 'Τετ', 'Πέμ', 'Παρ', 'Σάβ']

# ---- Γλώσσα μηνυμάτων (data['_lang'] από την εφαρμογή) ----
LANG = 'el'
MSG = {
 "NO_SLOT": {
  "el": "καμία επιτρεπτή ώρα (κωλύματα / ζώνες)",
  "en": "no allowed period (unavailability / zones)",
  "fr": "aucune heure autorisée (indisponibilités / zones)",
  "de": "keine erlaubte Stunde (Sperrzeiten / Zonen)",
  "es": "ninguna hora permitida (indisponibilidad / zonas)"
 },
 "SYNC_HOURS": {
  "el": "Τα ταυτόχρονα μικτά τμήματα {0} έχουν διαφορετικές ώρες ({1}).",
  "en": "The simultaneous mixed groups {0} have different periods ({1}).",
  "fr": "Les groupes mixtes simultanés {0} ont des heures différentes ({1}).",
  "de": "Die gleichzeitigen Mischgruppen {0} haben unterschiedliche Stunden ({1}).",
  "es": "Los grupos mixtos simultáneos {0} tienen horas distintas ({1})."
 },
 "LOCK_SYNC": {
  "el": "Οι κλειδωμένες ώρες σπάνε το «ταυτόχρονα» των {0}.",
  "en": "The locked periods break the “simultaneous” rule of {0}.",
  "fr": "Les heures verrouillées cassent la règle « simultanés » de {0}.",
  "de": "Die gesperrten Stunden verletzen „gleichzeitig“ bei {0}.",
  "es": "Las horas bloqueadas rompen la regla «simultáneas» de {0}."
 },
 "LOCK_GAP": {
  "el": "Οι κλειδωμένες ώρες αφήνουν κενό στους μαθητές {0}.",
  "en": "The locked periods leave a gap for students {0}.",
  "fr": "Les heures verrouillées laissent un trou aux élèves {0}.",
  "de": "Die gesperrten Stunden lassen eine Lücke für die Schüler {0}.",
  "es": "Las horas bloqueadas dejan un hueco a los alumnos {0}."
 },
 "STEP1": {
  "el": "Βήμα 1/2: τοποθέτηση όλων των ωρών…",
  "en": "Step 1/2: placing all periods…",
  "fr": "Étape 1/2 : placement de toutes les heures…",
  "de": "Schritt 1/2: alle Stunden setzen…",
  "es": "Paso 1/2: colocando todas las horas…"
 },
 "STEP1B": {
  "el": "Βήμα 1/2: δεν χωρούν όλες — όσο περισσότερες γίνεται…",
  "en": "Step 1/2: not all fit — as many as possible…",
  "fr": "Étape 1/2 : tout ne tient pas — le plus possible…",
  "de": "Schritt 1/2: nicht alle passen — so viele wie möglich…",
  "es": "Paso 1/2: no caben todas — las máximas posibles…"
 },
 "STEP2": {
  "el": "Βήμα 2/2: λιγότερα κενά, καλύτερη κατανομή…",
  "en": "Step 2/2: fewer gaps, better spread…",
  "fr": "Étape 2/2 : moins de trous, meilleure répartition…",
  "de": "Schritt 2/2: weniger Springstunden, bessere Verteilung…",
  "es": "Paso 2/2: menos huecos, mejor reparto…"
 },
 "NO_FIT": {
  "el": "δεν χωράει χωρίς σύγκρουση με τους αυστηρούς κανόνες",
  "en": "does not fit without breaking the strict rules",
  "fr": "ne tient pas sans enfreindre les règles strictes",
  "de": "passt nicht, ohne strenge Regeln zu verletzen",
  "es": "no cabe sin romper las reglas estrictas"
 },
 "UNPLACED": {
  "el": "{0} · {1}: {2} ώρ. χωρίς θέση — {3}",
  "en": "{0} · {1}: {2} per. unplaced — {3}",
  "fr": "{0} · {1} : {2} h non placées — {3}",
  "de": "{0} · {1}: {2} Std. ohne Platz — {3}",
  "es": "{0} · {1}: {2} h sin ubicar — {3}"
 },
 "INFEAS": {
  "el": "Τα δεσμευτικά κενά κάποιου εκπαιδευτικού (ή οι κλειδωμένες ώρες / οι μέγιστες ώρες την ημέρα) δεν γίνεται να τηρηθούν μαζί με τους υπόλοιπους κανόνες. Έλεγξε τα κενά που έχεις ορίσει (π.χ. κάνε τα «Στόχο») ή ξεκλείδωσε ώρες.",
  "en": "A teacher’s binding gaps (or locked periods / maximum periods per day) cannot be met together with the other rules. Check the gaps you set (e.g. make them “Target”) or unlock periods.",
  "fr": "Les trous obligatoires d’un enseignant (ou les heures verrouillées / le maximum d’heures par jour) ne peuvent pas être respectés avec les autres règles. Vérifie les trous définis (ex. mets-les en « Objectif ») ou déverrouille des heures.",
  "de": "Die verbindlichen Springstunden einer Lehrkraft (oder gesperrte Stunden / Höchststunden pro Tag) lassen sich nicht mit den übrigen Regeln vereinbaren. Prüfe die festgelegten Springstunden (z. B. als „Ziel“) oder entsperre Stunden.",
  "es": "Los huecos obligatorios de un docente (o las horas bloqueadas / el máximo de horas por día) no pueden cumplirse junto con las demás reglas. Revisa los huecos definidos (p. ej. ponlos como «Objetivo») o desbloquea horas."
 },
 "TIMEOUT": {
  "el": "Δεν βρέθηκε λύση στον χρόνο που δόθηκε. Δοκίμασε περισσότερο χρόνο.",
  "en": "No solution found in the given time. Try more time.",
  "fr": "Aucune solution trouvée dans le temps imparti. Essaie avec plus de temps.",
  "de": "In der vorgegebenen Zeit keine Lösung gefunden. Versuche es mit mehr Zeit.",
  "es": "No se encontró solución en el tiempo dado. Prueba con más tiempo."
 }
}


def _(key, *args):
    m = MSG[key]
    s = m.get(LANG) or m['el']
    for i, a in enumerate(args):
        s = s.replace('{' + str(i) + '}', str(a))
    return s



def solve(data, seconds=30, keep_placed=False, progress=None, stopper=None):
    global LANG
    LANG = data.get('_lang') or 'el'
    """Όλη η εβδομάδα λύνεται μαζί (όχι μέρα-μέρα).
    Σειρά προτεραιότητας:
      1. αυστηροί κανόνες — δεν παραβιάζονται ποτέ (ποτέ δύο μαθήματα την ίδια ώρα)
      2. να μπουν ΟΛΕΣ οι ώρες — μια ώρα μένει χωρίς θέση μόνο αν είναι αδύνατο αλλιώς
      3. ισοκατανομή ωρών μαθητών ανά ημέρα
      4. λίγα κενά καθηγητών, ομαλή εβδομάδα, «καλύτερα όχι»"""
    from ortools.sat.python import cp_model
    D, H, teachers, asg, sps, syncs = build(data)
    settings = data.get('settings') or {}
    student_rule = settings.get('studentNoGaps', True) is not False
    balance = settings.get('balanceDays', True) is not False
    S = D * H
    by_id = {a['id']: a for a in asg}
    tname = lambda ti: ((teachers[ti].get('surname') or '') + ' ' + (teachers[ti].get('name') or '')).strip()

    # σταθερές ώρες: κλειδωμένες (ή όλες, αν keep_placed) + υποχρεωτικές
    fixed, fcount = [], {}
    for e in data.get('schedule') or []:
        a = by_id.get(e.get('aid'))
        if not a or not (e.get('locked') or keep_placed):
            continue
        if fcount.get(a['id'], 0) >= a['hours']:
            continue
        fixed.append((a, e['d'] * H + e['h'], bool(e.get('locked'))))
        fcount[a['id']] = fcount.get(a['id'], 0) + 1
    for a in asg:
        for s in a['must']:
            if fcount.get(a['id'], 0) >= a['hours']:
                break
            if any(f[0] is a and f[1] == s for f in fixed):
                continue
            fixed.append((a, s, False))
            fcount[a['id']] = fcount.get(a['id'], 0) + 1

    m = cp_model.CpModel()
    occ_terms, occ_const, day_terms, day_const = {}, {}, {}, {}
    units, unplaceable, obj = [], [], []
    for (a, s, _l) in fixed:
        occ_const[(a['ai'], s)] = occ_const.get((a['ai'], s), 0) + 1
    for a in asg:
        mine = sorted(s for (x, s, _l) in fixed if x is a)
        for i, s in enumerate(mine):
            contig = i > 0 and s == mine[i - 1] + 1 and s // H == mine[i - 1] // H
            if not contig:
                day_const[(a['ai'], s // H)] = day_const.get((a['ai'], s // H), 0) + 1
        if a['hours'] - fcount.get(a['id'], 0) <= 0:
            continue
        lens = []
        for ln in remaining_blocks(a['blocks'], fcount.get(a['id'], 0)):
            dom = [d * H + h for d in range(D) for h in range(H - ln + 1) if all(a['allowed'][d * H + h + i] for i in range(ln))]
            lens += [1] * ln if (not dom and ln > 1) else [ln]
        for ln in lens:
            dom = [d * H + h for d in range(D) for h in range(H - ln + 1) if all(a['allowed'][d * H + h + i] for i in range(ln))]
            if not dom:
                unplaceable.append({'aid': a['id'], 'len': ln, 'why': _('NO_SLOT')})
                continue
            xs = {}
            for st in dom:
                v = m.NewBoolVar('')
                xs[st] = v
                for i in range(ln):
                    occ_terms.setdefault((a['ai'], st + i), []).append(v)
                day_terms.setdefault((a['ai'], st // H), []).append(v)
            placed = m.NewBoolVar('')
            m.Add(sum(xs.values()) == placed)   # μπαίνει το πολύ μία φορά — ποτέ «στοίβαγμα»
            units.append((a, ln, xs, placed))

    def occ(ai, s):
        return sum(occ_terms.get((ai, s), [])) + occ_const.get((ai, s), 0)

    def occ_ok(ai, s):
        return (ai, s) in occ_terms or occ_const.get((ai, s), 0) > 0

    # καθηγητής: μία ώρα τη φορά
    by_teacher = {}
    for a in asg:
        by_teacher.setdefault(a['t'], []).append(a)
    for t, lst in by_teacher.items():
        for s in range(S):
            terms = [a for a in lst if occ_ok(a['ai'], s)]
            if len(terms) > 1 or any(occ_const.get((a['ai'], s), 0) > 1 for a in terms):
                m.Add(sum(occ(a['ai'], s) for a in terms) <= 1)

    # τμήματα / ομάδες: ποτέ δύο μαθήματα για τους ίδιους μαθητές
    bases = {}
    for a in asg:
        for tc in a['touches']:
            bases.setdefault(tc['base'], []).append((a, tc))
    for b, lst in bases.items():
        for s in range(S):
            here = [(a, tc) for (a, tc) in lst if occ_ok(a['ai'], s)]
            if len(here) < 2:
                continue
            direct = [occ(a['ai'], s) for (a, tc) in here if not tc['tag']]
            tags = {}
            for (a, tc) in here:
                if tc['tag']:
                    tags.setdefault(tc['tag'], []).append((a, tc))
            busy = []
            for tag, items in tags.items():
                if not direct and len(tags) == 1:
                    busy = []
                    break
                v = m.NewBoolVar('')
                for (a, tc) in items:
                    m.Add(v >= occ(a['ai'], s))
                busy.append(v)
            if direct or len(tags) > 1:
                m.Add(sum(direct) + sum(busy) <= 1)
            for tag, items in tags.items():
                groups = {}
                for (a, tc) in items:
                    groups.setdefault(tc['group'], []).append(a)
                for g, al in groups.items():
                    if len(al) > 1:
                        m.Add(sum(occ(a['ai'], s) for a in al) <= 1)
                for g, al in groups.items():
                    for mb in merge_of.get(g, []):
                        if mb in groups:
                            m.Add(sum(occ(a['ai'], s) for a in al) + sum(occ(a['ai'], s) for a in groups[mb]) <= 1)

    # ανά ανάθεση: φορές την ημέρα, διαδοχικές ημέρες
    for a in asg:
        used = []
        for d in range(D):
            terms = day_terms.get((a['ai'], d), [])
            c = day_const.get((a['ai'], d), 0)
            if terms:
                m.Add(sum(terms) + c <= a['maxPerDay'])
            if a['noConsecutive']:
                if c > 0:
                    used.append(1)
                elif terms:
                    u = m.NewBoolVar('')
                    for v in terms:
                        m.AddImplication(v, u)
                    m.Add(u <= sum(terms))
                    used.append(u)
                else:
                    used.append(0)
        if a['noConsecutive']:
            for d in range(D - 1):
                if not (isinstance(used[d], int) and isinstance(used[d + 1], int)):
                    m.Add(used[d] + used[d + 1] <= 1)

    # ταυτόχρονα μικτά τμήματα: ίδια πληρότητα σε κάθε ώρα
    for sy in syncs:
        if len(set(sy['hours'])) > 1:
            return {'ok': False, 'message': _('SYNC_HOURS', sy['name'], ' / '.join(map(str, sy['hours'])))}
        secs = [[a for a in asg if a['sec'] == cid or a['sec'] in sy['cover'][k]] for k, cid in enumerate(sy['secs'])]
        for s_ in range(S):
            exprs = [sum(occ(a['ai'], s_) for a in lst if occ_ok(a['ai'], s_)) for lst in secs]
            if all(isinstance(e, int) for e in exprs):
                if len(set(exprs)) > 1:
                    return {'ok': False, 'message': _('LOCK_SYNC', sy['name'])}
                continue
            for e in exprs[1:]:
                m.Add(exprs[0] == e)

    # μαθητές: συνεχόμενες ώρες από την 1η (αυστηρό) · ισοκατανομή ανά ημέρα (προσπάθεια)
    if student_rule:
        for sp in sps:
            mine = [a for a in asg if sp['i'] in a['sp']]
            for d in range(D):
                b = []
                for h in range(H):
                    if f'{d}-{h}' in ZINFO['closed']:
                        continue   # κλειστή ώρα σχολείου: δεν μετράει
                    s_ = d * H + h
                    b.append(sum(occ(a['ai'], s_) for a in mine if occ_ok(a['ai'], s_)))
                for h in range(len(b) - 1):
                    if isinstance(b[h], int) and isinstance(b[h + 1], int):
                        if b[h] < b[h + 1]:
                            return {'ok': False, 'message': _('LOCK_GAP', sp['name'])}
                        continue
                    m.Add(b[h] >= b[h + 1])
                if balance:
                    tot = sum(b)
                    if not isinstance(tot, int):
                        lo_x, hi_x = m.NewIntVar(0, H, ''), m.NewIntVar(0, H, '')
                        m.Add(tot + lo_x >= sp['lo'])
                        m.Add(tot - hi_x <= sp['hi'])
                        obj.append(W_STUDENT_BAL * (lo_x + hi_x))

    # ομαλή κατανομή ωρών καθηγητή μέσα στην εβδομάδα
    smooth = settings.get('smoothTeachers', True) is not False
    fair = settings.get('fairGaps', True) is not False
    target, target_lo, work_day = [], [], []
    for ti, t in enumerate(teachers):
        need = sum(a['hours'] for a in asg if a['t'] == ti)
        wd = [any((t.get('avail') or {}).get(f'{d}-{h}') != 'no' and f'{d}-{h}' not in ZINFO['closed'] for h in range(H)) for d in range(D)]
        days = max(1, sum(wd))
        target.append(-(-need // days) if need else 0)   # π.χ. 18 ώρες σε 5 μέρες → 3–4 ώρες τη μέρα
        target_lo.append(need // days if need else 0)
        work_day.append(wd)

    # καθηγητές: ώρες/ημέρα, κενά (οι ώρες με κώλυμα ΔΕΝ είναι κενό), «καλύτερα όχι»
    for ti, t in enumerate(teachers):
        lst = by_teacher.get(ti, [])
        if not lst:
            continue
        av = t.get('avail') or {}
        hard = t.get('gapsMode') != 'soft'
        lim_d = t.get('maxGapsDay')
        lim_w = t.get('maxGapsWeek')
        lim_d = None if lim_d in (None, '') else int(lim_d)
        lim_w = None if lim_w in (None, '') else int(lim_w)
        max_h = t.get('maxHoursDay')
        max_h = int(max_h) if max_h not in (None, '', 0) else None
        week_gaps = []
        for d in range(D):
            w = []
            for h in range(H):
                s = d * H + h
                expr = sum(occ(a['ai'], s) for a in lst if occ_ok(a['ai'], s))
                w.append(expr)
                if av.get(f'{d}-{h}') == 'pref' and not isinstance(expr, int):
                    obj.append(W_PREF * expr)
            if all(isinstance(x, int) for x in w):
                continue
            if smooth and target[ti]:
                # ισοκατανομή: 1 ώρα πάνω/κάτω από τον στόχο κοστίζει λίγο (για να φύγουν κενά),
                # 2+ ώρες (π.χ. εξάωρο και δίωρο) κοστίζουν πολύ
                ex_b, ex_b2 = m.NewIntVar(0, H, ''), m.NewIntVar(0, H, '')
                m.Add(ex_b >= sum(w) - target[ti])
                m.Add(ex_b2 >= sum(w) - target[ti] - 1)
                obj.append(W_BAL * ex_b + W_BAL2 * ex_b2)
                if work_day[ti][d] and target_lo[ti]:
                    lo_b, lo_b2 = m.NewIntVar(0, H, ''), m.NewIntVar(0, H, '')
                    m.Add(lo_b >= target_lo[ti] - sum(w))
                    m.Add(lo_b2 >= target_lo[ti] - 1 - sum(w))
                    obj.append(W_BAL * lo_b + W_BAL2 * lo_b2)
            if max_h is not None:
                m.Add(sum(w) <= max_h)
            f, l = [], [None] * H
            for h in range(H):
                fv = m.NewBoolVar('')
                m.Add(fv >= w[h])
                if h > 0:
                    m.Add(fv >= f[h - 1])
                    m.Add(fv <= w[h] + f[h - 1])
                else:
                    m.Add(fv <= w[h])
                f.append(fv)
            for h in range(H - 1, -1, -1):
                lv = m.NewBoolVar('')
                m.Add(lv >= w[h])
                if h < H - 1:
                    m.Add(lv >= l[h + 1])
                    m.Add(lv <= w[h] + l[h + 1])
                else:
                    m.Add(lv <= w[h])
                l[h] = lv
            day_gaps = []
            for h in range(1, H - 1):
                if av.get(f'{d}-{h}') == 'no' or f'{d}-{h}' in ZINFO['closed']:
                    continue   # ώρα με κώλυμα ή κλειστή ώρα: δεν μετράει ως κενό
                gv = m.NewBoolVar('')
                m.Add(gv >= f[h - 1] + l[h + 1] - 1 - w[h])
                m.Add(gv <= 1 - w[h])
                m.Add(gv <= f[h - 1])
                m.Add(gv <= l[h + 1])
                day_gaps.append(gv)
            week_gaps += day_gaps
            if lim_w is None:
                obj.append(W_GAP * sum(day_gaps))   # χωρίς αριθμό την εβδομάδα: όσο λιγότερα κενά γίνεται
            if lim_d is not None:
                # «έως Ν κενά την ημέρα»: σε καμία μέρα περισσότερα
                if hard:
                    m.Add(sum(day_gaps) <= lim_d)
                else:
                    ex = m.NewIntVar(0, H, '')
                    m.Add(ex >= sum(day_gaps) - lim_d)
                    obj.append(W_SOFT * ex)
        if fair and week_gaps and lim_w is None:   # δίκαιη μοιρασιά κενών (κυρτό κόστος)
            for k in range(1, 9):
                e = m.NewIntVar(0, S, '')
                m.Add(e >= sum(week_gaps) - k)
                obj.append(W_FAIR * e)
        if lim_w is not None and week_gaps:
            # κενά την εβδομάδα: ΑΚΡΙΒΩΣ τόσα (μοιρασμένα στις μέρες με το όριο «έως Ν την ημέρα»)
            if hard:
                m.Add(sum(week_gaps) == lim_w)
            else:
                ex = m.NewIntVar(0, S, '')
                m.Add(ex >= sum(week_gaps) - lim_w)
                m.Add(ex >= lim_w - sum(week_gaps))
                obj.append(W_SOFT * ex)
    soft = [x for x in obj]   # (οι ώρες χωρίς θέση μετριούνται χωριστά, βλ. παρακάτω)
    placed_sum = sum(ln * p for (a, ln, xs, p) in units)
    total_free = sum(ln for (a, ln, xs, p) in units)

    def schedule_from(val):
        sch = [{'aid': a['id'], 'd': s // H, 'h': s % H, 'locked': lk} for (a, s, lk) in fixed]
        for (a, ln, xs, _p) in units:
            st = next((s for s, v in xs.items() if val(v)), None)
            if st is None:
                continue
            for i in range(ln):
                sch.append({'aid': a['id'], 'd': (st + i) // H, 'h': (st + i) % H, 'locked': False})
        return sch

    def missing_from(val):
        return sum(ln for (a, ln, xs, p) in units if not val(p))

    t0 = time.time()
    phase = {'from': 0.0, 'to': 1.0, 'text': ''}

    class CB(cp_model.CpSolverSolutionCallback):
        def __init__(self, with_obj):
            super().__init__()
            self.last = 0
            self.with_obj = with_obj

        def on_solution_callback(self):
            if stopper and stopper():
                self.StopSearch()
                return
            if progress and time.time() - self.last > 0.7:
                self.last = time.time()
                frac = min(1.0, (time.time() - t0) / max(1, seconds))
                progress({'progress': frac, 'text': phase['text'],
                          'best': {'hard': 0, 'soft': int(self.ObjectiveValue()) if self.with_obj else 0, 'missing': missing_from(self.BooleanValue)},
                          'schedule': schedule_from(self.BooleanValue)})

    def run(model, secs, with_obj):
        sv = cp_model.CpSolver()
        sv.parameters.max_time_in_seconds = max(1.0, float(secs))
        sv.parameters.num_workers = 8
        if stopper is not None:
            solve.current = sv
        st = sv.Solve(model, CB(with_obj))
        return st, sv

    def hint_from(model, val):
        model.ClearHints()
        for (a, ln, xs, p) in units:
            for v in xs.values():
                model.AddHint(v, 1 if val(v) else 0)
            model.AddHint(p, 1 if val(p) else 0)

    # αρχική ιδέα (hint) από την ενσωματωμένη μηχανή
    hint = {}
    for e in data.get('hint') or []:
        hint.setdefault(e['aid'], set()).add(e['d'] * H + e['h'])
    if hint:
        for (a, ln, xs, p) in sorted(units, key=lambda u: -u[1]):
            pool = hint.get(a['id'], set())
            pick = next((st for st in xs if all((st + i) in pool for i in range(ln))), None)
            for st, v in xs.items():
                m.AddHint(v, 1 if st == pick else 0)
            m.AddHint(p, 1 if pick is not None else 0)
            if pick is not None:
                for i in range(ln):
                    pool.discard(pick + i)

    # 1ο βήμα: να μπουν ΟΛΕΣ οι ώρες (χωρίς να κοιτάμε κενά κ.λπ.)
    best_val, best_k, status = None, -1, cp_model.UNKNOWN
    p1 = m.Clone()
    p1.Add(placed_sum == total_free)
    phase['text'] = _('STEP1')
    st1, sv1 = run(p1, seconds * 0.4, False)
    if st1 in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        best_k, best_val, status = total_free, {v.Index(): sv1.BooleanValue(v) for (a, ln, xs, p) in units for v in list(xs.values()) + [p]}, st1
    elif not (stopper and stopper()):
        # δεν χωράνε όλες: όσο περισσότερες γίνεται
        p1b = m.Clone()
        p1b.Maximize(placed_sum)
        phase['text'] = _('STEP1B')
        st1b, sv1b = run(p1b, seconds * 0.3, False)
        if st1b in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            best_k = int(sv1b.Value(placed_sum))
            best_val = {v.Index(): sv1b.BooleanValue(v) for (a, ln, xs, p) in units for v in list(xs.values()) + [p]}
            status = st1b
        elif st1b == cp_model.INFEASIBLE:
            status = st1b
    # 2ο βήμα: ίδιες (ή περισσότερες) ώρες, με λιγότερα κενά και καλύτερη κατανομή
    solver = None
    if best_val is not None and not (stopper and stopper()):
        p2 = m.Clone()
        p2.Add(placed_sum >= best_k)
        hint_from(p2, lambda v: best_val[v.Index()])
        if soft:
            p2.Minimize(sum(soft))
        phase['text'] = _('STEP2')
        st2, sv2 = run(p2, max(2.0, seconds - (time.time() - t0)), bool(soft))
        if st2 in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            solver, status = sv2, st2
    if solver is None and best_val is not None:
        class _V:   # λύση του 1ου βήματος
            def __init__(self, vals):
                self.vals = vals

            def BooleanValue(self, v):
                return self.vals[v.Index()]

            def ObjectiveValue(self):
                return 0
        solver = _V(best_val)
    elapsed = time.time() - t0
    if solver is not None:
        for (a, ln, xs, p) in units:
            if not solver.BooleanValue(p):
                unplaceable.append({'aid': a['id'], 'len': ln, 'why': _('NO_FIT')})
        msgs = []
        for u in unplaceable:
            a = by_id[u['aid']]
            msgs.append(_('UNPLACED', tname(a['t']), a['label'], u['len'], u['why']))
        return {'ok': True, 'engine': 'OR-Tools', 'schedule': schedule_from(solver.BooleanValue), 'seconds': elapsed,
                'optimal': status == cp_model.OPTIMAL,
                'summary': {'hard': 0, 'soft': int(solver.ObjectiveValue()) if soft else 0, 'missing': sum(u['len'] for u in unplaceable)},
                'unplaceable': unplaceable, 'messages': msgs}
    if status == cp_model.INFEASIBLE:
        return {'ok': False, 'message': _('INFEAS')}
    return {'ok': False, 'message': _('TIMEOUT')}

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


def sync_sets(data):
    """Μικτά τμήματα που γίνονται ταυτόχρονα (ίδια λογική με engine.js)."""
    cby = {c['id']: c for c in data['classes']}
    par = {c['id']: c['id'] for c in data['classes'] if is_mixed(c)}

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    def uni(a, b):
        if a in par and b in par:
            a, b = find(a), find(b)
            if a != b:
                par[b] = a
    by_tag = {}
    for c in data['classes']:
        if not is_mixed(c):
            continue
        for o in c.get('syncWith') or []:
            uni(c['id'], o)
        k = (c.get('parallel') or '').strip()
        if k:
            if k in by_tag:
                uni(by_tag[k], c['id'])
            else:
                by_tag[k] = c['id']
    # ίδια κατηγορία + κοινό τμήμα χρέωσης → ταυτόχρονα
    def is_dep(c):
        return any(is_mixed(cby.get(mb)) for mb in c.get('members') or [])
    mixed = [c for c in data['classes'] if is_mixed(c) and c.get('category')]
    for i, x in enumerate(mixed):
        for y in mixed[i + 1:]:
            if is_dep(x) != is_dep(y):
                continue  # συγχωνευμένο (π.χ. ΓΘετΥγ) ή Κόντρα: όχι μαζί με τα κανονικά
            if is_dep(x) and is_dep(y) and x['category'] != 'kontra':
                continue  # συγχωνευμένα: το καθένα μόνο του
            if x['category'] == y['category'] and set(base_classes(data, x['id'])) & set(base_classes(data, y['id'])):
                uni(x['id'], y['id'])
    groups = {}
    for cid in par:
        groups.setdefault(find(cid), []).append(cid)
    sets, tag, set_of, merges = [], {}, {}, []
    global merge_of
    merge_of = {}
    for r, ids in groups.items():
        if len(ids) < 2:
            if is_dep(cby[ids[0]]):
                tag[ids[0]] = 'D:' + ids[0]  # μοναχικό εξαρτημένο: δική του ετικέτα
            continue
        for cid in ids:
            tag[cid] = 'S:' + r
            set_of[cid] = len(sets)
        sets.append(ids)
        merges.append([])
    # συγχωνευμένα: μικτό ίδιας κατηγορίας που χρεώνεται σε ≥2 τμήματα του ίδιου σετ (π.χ. ΓΘετΥγ → Γθετ, Γυγ)
    for c in data['classes']:
        if not is_mixed(c) or not is_dep(c) or c['id'] in set_of:
            continue
        ms = c.get('members') or []
        si = set_of.get(ms[0]) if ms else None
        if len(ms) < 2 or si is None:
            continue
        if all(set_of.get(mb) == si and cby[mb].get('category') == c.get('category') for mb in ms):
            merges[si].append(c['id'])
            tag[c['id']] = tag[ms[0]]  # ίδιο «κανάλι» μαθητών με το σετ
            merge_of[c['id']] = list(ms)
    return sets, tag, merges


def label_of(data, a):
    names = {c['id']: c.get('name', '') for c in data['classes']}
    return '+'.join(names[i] for i in a.get('classIds', []) if i in names)


def build(data):
    D, H = int(data['settings']['days']), int(data['settings']['hours'])
    teachers = data['teachers']
    tidx = {t['id']: i for i, t in enumerate(teachers)}
    cby = {c['id']: c for c in data['classes']}
    sets, stag, smerges = sync_sets(data)
    zones = set((data.get('settings') or {}).get('zonesG') or [])
    if (data.get('school') or {}).get('type', 'lyceum') != 'lyceum':
        zones = set()   # ζώνες κατεύθυνσης υπάρχουν μόνο στο Λύκειο
    zone_bases = set()   # τμήματα (Γ1, Γ2…) που έχουν κατεύθυνση Γ΄
    for c in data['classes']:
        if c.get('category') == 'dirG' and is_mixed(c):
            zone_bases.update(base_classes(data, c['id']))

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
                c0 = cby.get(cls[0]) or {}
                if c0.get('category') == 'dirG' and is_mixed(c0) and zones:
                    in_range = in_range and k in zones
                if c0.get('category') == 'dirB' and is_mixed(c0):
                    in_range = in_range and h < 5  # κατεύθυνση Β΄: ποτέ 6η και 7η ώρα
                if zones and k in zones and not (c0.get('category') == 'dirG' and is_mixed(c0)) and zone_bases & set(base_classes(data, cls[0])):
                    in_range = False   # γενική παιδεία / Κόντρα της Γ΄: ποτέ μέσα στη ζώνη
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
    for sp in sps:
        sp['lo'], sp['hi'] = sp['N'] // D, -(-sp['N'] // D)
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


def solve(data, seconds=30, keep_placed=False, progress=None, stopper=None):
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
                unplaceable.append({'aid': a['id'], 'len': ln, 'why': 'καμία επιτρεπτή ώρα (κωλύματα / ζώνες)'})
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
            return {'ok': False, 'message': 'Τα ταυτόχρονα μικτά τμήματα ' + sy['name'] + ' έχουν διαφορετικές ώρες (' + ' / '.join(map(str, sy['hours'])) + ').'}
        secs = [[a for a in asg if a['sec'] == cid or a['sec'] in sy['cover'][k]] for k, cid in enumerate(sy['secs'])]
        for s_ in range(S):
            exprs = [sum(occ(a['ai'], s_) for a in lst if occ_ok(a['ai'], s_)) for lst in secs]
            if all(isinstance(e, int) for e in exprs):
                if len(set(exprs)) > 1:
                    return {'ok': False, 'message': 'Οι κλειδωμένες ώρες σπάνε το «ταυτόχρονα» των ' + sy['name'] + '.'}
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
                    s_ = d * H + h
                    b.append(sum(occ(a['ai'], s_) for a in mine if occ_ok(a['ai'], s_)))
                for h in range(H - 1):
                    if isinstance(b[h], int) and isinstance(b[h + 1], int):
                        if b[h] < b[h + 1]:
                            return {'ok': False, 'message': 'Οι κλειδωμένες ώρες αφήνουν κενό στους μαθητές ' + sp['name'] + '.'}
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
        wd = [any((t.get('avail') or {}).get(f'{d}-{h}') != 'no' for h in range(H)) for d in range(D)]
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
                if av.get(f'{d}-{h}') == 'no':
                    continue   # ώρα με κώλυμα: δεν μετράει ως κενό
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
    phase['text'] = 'Βήμα 1/2: τοποθέτηση όλων των ωρών…'
    st1, sv1 = run(p1, seconds * 0.4, False)
    if st1 in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        best_k, best_val, status = total_free, {v.Index(): sv1.BooleanValue(v) for (a, ln, xs, p) in units for v in list(xs.values()) + [p]}, st1
    elif not (stopper and stopper()):
        # δεν χωράνε όλες: όσο περισσότερες γίνεται
        p1b = m.Clone()
        p1b.Maximize(placed_sum)
        phase['text'] = 'Βήμα 1/2: δεν χωρούν όλες — όσο περισσότερες γίνεται…'
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
        phase['text'] = 'Βήμα 2/2: λιγότερα κενά, καλύτερη κατανομή…'
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
                unplaceable.append({'aid': a['id'], 'len': ln, 'why': 'δεν χωράει χωρίς σύγκρουση με τους αυστηρούς κανόνες'})
        msgs = []
        for u in unplaceable:
            a = by_id[u['aid']]
            msgs.append(tname(a['t']) + ' · ' + a['label'] + ': ' + str(u['len']) + ' ώρ. χωρίς θέση — ' + u['why'])
        return {'ok': True, 'engine': 'OR-Tools', 'schedule': schedule_from(solver.BooleanValue), 'seconds': elapsed,
                'optimal': status == cp_model.OPTIMAL,
                'summary': {'hard': 0, 'soft': int(solver.ObjectiveValue()) if soft else 0, 'missing': sum(u['len'] for u in unplaceable)},
                'unplaceable': unplaceable, 'messages': msgs}
    if status == cp_model.INFEASIBLE:
        return {'ok': False, 'message': 'Τα δεσμευτικά κενά κάποιου εκπαιδευτικού (ή οι κλειδωμένες ώρες / οι μέγιστες ώρες την ημέρα) δεν γίνεται να τηρηθούν μαζί με τους υπόλοιπους κανόνες. Έλεγξε τα κενά που έχεις ορίσει (π.χ. κάνε τα «Στόχο») ή ξεκλείδωσε ώρες.'}
    return {'ok': False, 'message': 'Δεν βρέθηκε λύση στον χρόνο που δόθηκε. Δοκίμασε περισσότερο χρόνο.'}

"""Exact-subgroup dependence check.

Reads the deposited factorial per-paper values and the coverage matrix.
Reports the exact-subgroup paired difference with and without the 7-paper
shared-pattern cluster (B036, B049, B050, B092, B137, B186, B211).
"""
import csv, collections, json
import numpy as np

d = json.load(open('reproducibility/panel_decomposition.json'))
fp = d['factorial_per_paper']
papers = sorted(fp['full_row'])

def ci(vals, B=10000, seed=42):
    vals = np.asarray(vals)
    rng = np.random.default_rng(seed)
    bs = np.array([np.median(rng.choice(vals, len(vals), replace=True)) for _ in range(B)])
    return np.quantile(bs, [.025, .975])

rows = list(csv.DictReader(open('reproducibility/coverage_matrix.csv')))
hdr = [k for k in rows[0] if k not in ('paper', 'row', 'rho')]
by = collections.defaultdict(list)
for x in rows:
    by[x['paper']].append(tuple(int(float(x[k])) for k in hdr))
cnt = collections.Counter()
for k, v in by.items():
    for p in set(v):
        cnt[p] += 1
exact = [k for k, v in by.items() if any(cnt[p] > 1 for p in set(v))]
seven = {'B036', 'B049', 'B050', 'B092', 'B137', 'B186', 'B211'}

for label, grp in [('all exact', exact), ('exclude seven', [p for p in exact if p not in seven])]:
    dd = np.array([fp['full_row'][p] - fp['collapsed_unique'][p] for p in grp])
    print(label, len(dd), 'median', np.median(dd), 'ci', ci(dd))

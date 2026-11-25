import json, os, sys
import numpy as np
sys.path.insert(0, 'code')
import panel_decomposition as pdec
from common import load_curated, fit, common_ratio, unique_mask, seed_for

X, rho, paper = load_curated()
n = len(X)
papers = sorted(set(paper))
uni = unique_mask(X, paper)
uni_idx = np.where(uni)[0]
Xc = X[uni]
paper_c = paper[uni]
config_rows = {}
for j in range(len(Xc)):
    p = paper_c[j]
    same = np.where((paper == p) & np.all(X == Xc[j], axis=1))[0]
    config_rows[j] = same
S_full = fit(X)
S_full_c = fit(Xc)
DRAWS = 100
out = {k: {} for k in ('full_row', 'collapsed_unique')}
for p in papers:
    idx_p = np.where(paper == p)[0]
    n_p = len(idx_p)
    keep_block = paper != p
    block_rows = np.where(keep_block)[0]
    S_block = fit(X[keep_block])
    keep_block_c = paper_c != p
    block_rows_c = np.where(keep_block_c)[0]
    S_block_c = fit(Xc[keep_block_c])
    n_u = int(uni[idx_p].sum())
    donors = np.where(paper != p)[0]
    donors_c = np.where(paper_c != p)[0]
    base = seed_for(str(p))
    ratios = {k: [] for k in out}
    for dr in range(DRAWS):
        rng = np.random.default_rng(base + 7919 * dr)
        drop = rng.choice(donors, size=n_p, replace=False)
        keep_match = np.ones(n, bool)
        keep_match[drop] = False
        match_rows = np.where(keep_match)[0]
        S_match = fit(X[keep_match])
        drop_c = rng.choice(donors_c, size=n_u, replace=False)
        drop_rows = np.concatenate([config_rows[j] for j in drop_c])
        keep_match_c = np.ones(n, bool)
        keep_match_c[drop_rows] = False
        match_rows_c = np.where(keep_match_c)[0]
        S_match_c = fit(X[keep_match_c])
        keep_match_c_c = np.ones(len(Xc), bool)
        keep_match_c_c[drop_c] = False
        match_rows_c_c = np.where(keep_match_c_c)[0]
        S_match_c_c = fit(Xc[keep_match_c_c])
        common_c = keep_block_c & keep_match_c_c
        common_mask = np.zeros(n, bool)
        common_mask[uni_idx[common_c]] = True
        ratios['full_row'].append(common_ratio(S_full, S_block, block_rows, S_match, match_rows, common_mask))
        ratios['collapsed_unique'].append(common_ratio(S_full_c, S_block_c, block_rows_c, S_match_c_c, match_rows_c_c, common_c))
    for k in out:
        out[k][p] = [float(x) for x in ratios[k]]

# point estimates
fr = np.array([np.median(out['full_row'][p]) for p in papers])
cu = np.array([np.median(out['collapsed_unique'][p]) for p in papers])
print('point full median', np.median(fr), 'collapsed', np.median(cu), 'diff', np.median(fr-cu))
# two-level bootstrap
rng = np.random.default_rng(42)
B = 2000
vals = []
for b in range(B):
    idx = rng.integers(0, len(papers), len(papers))
    ds = []
    for i in idx:
        p = papers[i]
        frd = np.array(out['full_row'][p])
        cud = np.array(out['collapsed_unique'][p])
        fi = rng.integers(0, len(frd), len(frd))
        ci = rng.integers(0, len(cud), len(cud))
        ds.append(np.median(frd[fi] - cud[ci]))
    vals.append(np.median(ds))
vals = np.array(vals)
print('two-level delta 95%', np.quantile(vals, [0.025, 0.975]), 'median', np.median(vals))
json.dump({'papers': papers, 'full_row': out['full_row'], 'collapsed_unique': out['collapsed_unique'],
           'two_level': {'median': float(np.median(vals)), 'ci_lo': float(np.quantile(vals,0.025)),
                         'ci_hi': float(np.quantile(vals,0.975)), 'n_boot': B}},
          open('/tmp/two_level_delta.json','w'))

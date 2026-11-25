import csv, numpy as np, collections, statistics, json, sys, time
from numpy.linalg import svd, norm

def load(path='reproducibility/coverage_matrix.csv'):
    rows=list(csv.DictReader(open(path)))
    hdr=[k for k in rows[0] if k not in ('paper','row','rho')]
    papers=np.array([r['paper'] for r in rows])
    X=np.array([[float(r[k]) for k in hdr] for r in rows],dtype=float)
    return X,papers

def pca(X,k):
    Xc=X-X.mean(0,keepdims=True)
    U,s,Vt=svd(Xc,full_matrices=False)
    return U[:,:k]*s[:k]

def align_resid(A,B):
    A0=A-A.mean(0,keepdims=True); B0=B-B.mean(0,keepdims=True)
    na=norm(A0); nb=norm(B0)
    if na==0 or nb==0: return None
    A0=A0/na; B0=B0/nb
    U,s,Vt=svd(B0.T@A0); R=U@Vt
    Ba=(B0@R)*s.sum()
    return norm(A0-Ba,axis=1)

def build_collapsed(X,papers):
    seen=set(); keep=[]
    for i,p in enumerate(papers):
        key=(p,tuple(X[i].astype(int)))
        if key not in seen:
            seen.add(key); keep.append(i)
    keep=np.array(keep)
    return X[keep],papers[keep]

def ratios_for_dims(X,papers,dims=(2,3,4,5),ndraw=100,seed0=42):
    n=len(papers); uniq=sorted(set(papers))
    Xf={k:pca(X,k) for k in dims}
    res={k:{} for k in dims}
    for si,s in enumerate(uniq):
        idx=np.where(papers==s)[0]
        other=np.where(papers!=s)[0]
        keepB=np.setdiff1d(np.arange(n),idx)
        Xb={k:pca(X[keepB],k) for k in dims}
        rng=np.random.default_rng(seed0+si*1009)
        vals={k:{'B':[],'M':[]} for k in dims}
        for d in range(ndraw):
            sel=rng.choice(other,size=len(idx),replace=False)
            keepM=np.setdiff1d(np.arange(n),sel)
            Xm={k:pca(X[keepM],k) for k in dims}
            for k in dims:
                rB=align_resid(Xf[k][keepB],Xb[k]); rM=align_resid(Xf[k][keepM],Xm[k])
                vals[k]['B'].append(np.median(rB)); vals[k]['M'].append(np.median(rM))
        for k in dims:
            B=np.array(vals[k]['B']); M=np.array(vals[k]['M'])
            res[k][s]=float(np.median(B)/np.median(M))
    return res

if __name__=='__main__':
    X,papers=load()
    Xc,pc=build_collapsed(X,papers)
    t=time.time()
    print('full...',flush=True)
    rf=ratios_for_dims(X,papers,dims=(2,3,4,5),ndraw=100)
    print('done',time.time()-t,flush=True)
    print('collapsed...',flush=True)
    rc=ratios_for_dims(Xc,pc,dims=(2,3,4,5),ndraw=100)
    print('done',time.time()-t,flush=True)
    json.dump({'full':rf,'collapsed':rc},open('/tmp/dim_paired.json','w'))
    for k in (2,3,4,5):
        fv=np.array([rf[k][s] for s in rf[k]]); cv=np.array([rc[k][s] for s in rc[k]])
        d=fv-cv
        print(k,'full med',np.median(fv),'coll med',np.median(cv),'paired diff med',np.median(d),
              'frac>0',(d>0).mean(),'q25/q75',np.quantile(d,[.25,.75]))

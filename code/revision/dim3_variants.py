import csv, numpy as np, collections, statistics, json
from numpy.linalg import svd, norm

def load():
    rows=list(csv.DictReader(open('reproducibility/coverage_matrix.csv')))
    hdr=[k for k in rows[0] if k not in ('paper','row','rho')]
    papers=np.array([r['paper'] for r in rows])
    X=np.array([[float(r[k]) for k in hdr] for r in rows],dtype=float)
    return X,papers

def pca(X,k):
    Xc=X-X.mean(0,keepdims=True)
    U,s,Vt=svd(Xc,full_matrices=False)
    return U[:,:k]*s[:k]

def align(A,B,center=True,scale=True,rownorm=False):
    A0=A.copy(); B0=B.copy()
    if center:
        A0=A0-A0.mean(0,keepdims=True); B0=B0-B0.mean(0,keepdims=True)
    if rownorm:
        A0=A0/np.maximum(norm(A0,axis=1,keepdims=True),1e-12)
        B0=B0/np.maximum(norm(B0,axis=1,keepdims=True),1e-12)
    na=norm(A0); nb=norm(B0)
    if na==0 or nb==0: return None
    A0=A0/na; B0=B0/nb
    U,s,Vt=svd(B0.T@A0); R=U@Vt
    Ba=(B0@R)*(s.sum() if scale else 1.0)
    return norm(A0-Ba,axis=1)

def ratio(X,papers,k,seed,center=True,scale=True,rownorm=False,ndraw=100):
    n=len(papers); uniq=sorted(set(papers)); Xf=pca(X,k); out={}
    for si,s in enumerate(uniq):
        idx=np.where(papers==s)[0]; other=np.where(papers!=s)[0]
        keepB=np.setdiff1d(np.arange(n),idx); Xb=pca(X[keepB],k)
        rng=np.random.default_rng(seed+si*1009); B=[];M=[]
        for d in range(ndraw):
            sel=rng.choice(other,size=len(idx),replace=False)
            keepM=np.setdiff1d(np.arange(n),sel); Xm=pca(X[keepM],k)
            B.append(np.median(align(Xf[keepB],Xb,center,scale,rownorm)))
            M.append(np.median(align(Xf[keepM],Xm,center,scale,rownorm)))
        out[s]=float(np.median(B)/np.median(M))
    return np.array(list(out.values()))

X,papers=load()
for name,kw in [('current',{}),('no_scale',{'scale':False}),('no_center',{'center':False}),('rownorm',{'rownorm':True})]:
    for seed in [42,7,123]:
        v=ratio(X,papers,3,seed,**kw)
        print(name,'seed',seed,'median',np.median(v))

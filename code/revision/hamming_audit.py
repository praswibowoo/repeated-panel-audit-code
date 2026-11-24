import csv, numpy as np, collections, statistics, json, time
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

def collapse_hamming(X,papers,t):
    # greedy connected components within paper at Hamming <= t; medoid representative
    keep=[]
    for p in sorted(set(papers)):
        idx=np.where(papers==p)[0]
        n=len(idx)
        if n==1:
            keep.append(idx[0]); continue
        # union-find
        parent=list(range(n))
        def find(a):
            while parent[a]!=a:
                parent[a]=parent[parent[a]]; a=parent[a]
            return a
        def union(a,b):
            ra,rb=find(a),find(b)
            if ra!=rb: parent[rb]=ra
        for i in range(n):
            for j in range(i+1,n):
                if np.sum(X[idx[i]]!=X[idx[j]])<=t:
                    union(i,j)
        groups=collections.defaultdict(list)
        for i in range(n): groups[find(i)].append(i)
        for g in groups.values():
            if len(g)==1: keep.append(idx[g[0]]); continue
            sub=X[idx[g]]
            # medoid
            D=np.sum(sub[:,None,:]!=sub[None,:,:],axis=2)
            m=g[int(np.argmin(D.sum(1)))]
            keep.append(idx[m])
    keep=np.array(sorted(keep))
    return X[keep],papers[keep]

def ratios(X,papers,ndraw=100,seed0=42):
    n=len(papers); uniq=sorted(set(papers))
    Xf=pca(X,2); res={}
    for si,s in enumerate(uniq):
        idx=np.where(papers==s)[0]; other=np.where(papers!=s)[0]
        keepB=np.setdiff1d(np.arange(n),idx)
        Xb=pca(X[keepB],2)
        rng=np.random.default_rng(seed0+si*1009)
        B=[];M=[]
        for d in range(ndraw):
            sel=rng.choice(other,size=len(idx),replace=False)
            keepM=np.setdiff1d(np.arange(n),sel)
            Xm=pca(X[keepM],2)
            B.append(np.median(align_resid(Xf[keepB],Xb)))
            M.append(np.median(align_resid(Xf[keepM],Xm)))
        res[s]=float(np.median(B)/np.median(M))
    return res

if __name__=='__main__':
    X,papers=load()
    out={}
    for t in [0,1,2,3]:
        Xc,pc=collapse_hamming(X,papers,t)
        print('t',t,'configs',len(pc),'papers',len(set(pc)),flush=True)
        r=ratios(Xc,pc,ndraw=100)
        vals=list(r.values())
        out[t]={'n_configs':int(len(pc)),'median':float(np.median(vals)),
                'q25':float(np.quantile(vals,.25)),'q75':float(np.quantile(vals,.75)),
                'per_paper':r}
        print('t',t,'median',np.median(vals),'q25/q75',np.quantile(vals,[.25,.75]),flush=True)
    json.dump(out,open('/tmp/hamming_results.json','w'))

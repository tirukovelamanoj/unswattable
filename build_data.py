import pandas as pd, numpy as np, json, base64

ann = pd.read_csv('flywire_annotations/supplemental_files/Supplemental_file1_neuron_annotations.tsv',
                  sep='\t', low_memory=False,
                  usecols=['root_id','pos_x','pos_y','pos_z','super_class','cell_class','cell_type','side','top_nt'])
con = pd.read_csv('connections_783.csv.gz')
rng = np.random.default_rng(7)

XYZ = ann[['pos_x','pos_y','pos_z']].to_numpy(np.float64)*np.array([4.,4.,40.])
ctr = XYZ.mean(0); scale = np.abs(XYZ-ctr).max()
ann[['nx','ny','nz']] = (XYZ-ctr)/scale
ct = ann.cell_type.fillna('').astype(str)

VIS = ['LC4','LPLC2','LPLC1','LC6']
DNS = ['DNp01','DNp02','DNp03','DNp04','DNp11','DNa02']
vis_ids = set(ann[ann.cell_type.isin(VIS)].root_id)
dn_ids  = set(ann[ann.cell_type.isin(DNS)].root_id)

# escape-path interneurons (same rule as before)
a = con[con.pre_root_id.isin(vis_ids) & ~con.post_root_id.isin(vis_ids|dn_ids)]
b = con[con.post_root_id.isin(dn_ids) & ~con.pre_root_id.isin(vis_ids|dn_ids)]
path = a.groupby('post_root_id').syn_count.sum().to_frame('i').join(
       b.groupby('pre_root_id').syn_count.sum().to_frame('o'), how='inner')
path['s'] = path.min(axis=1)
mid_ids = set(path.sort_values('s',ascending=False).head(900).index)

# ---- mushroom body, one hemisphere so the sim stays cheap
SIDE='right'
kc_all = ann[(ann.cell_class=='Kenyon_Cell')&(ann.side==SIDE)].root_id.to_numpy()
kc_ids = set(rng.choice(kc_all, size=min(900,len(kc_all)), replace=False))
mbon_ids = set(ann[ct.str.match('^MBON')].root_id)
dan_all  = ann[(ann.cell_class=='DAN')&(ann.side==SIDE)].root_id.to_numpy()
dan_ids  = set(rng.choice(dan_all, size=min(150,len(dan_all)), replace=False))

# MBON -> X -> DN relays (the LAL steering route)
ma = con[con.pre_root_id.isin(mbon_ids)]; mb_ = con[con.post_root_id.isin(dn_ids)]
relay = ma.groupby('post_root_id').syn_count.sum().to_frame('i').join(
        mb_.groupby('pre_root_id').syn_count.sum().to_frame('o'), how='inner')
relay['s'] = relay.min(axis=1)
relay_ids = set(relay.sort_values('s',ascending=False).head(70).index)

keep_ids = vis_ids|dn_ids|mid_ids|kc_ids|mbon_ids|dan_ids|relay_ids
keep = ann[ann.root_id.isin(keep_ids)].copy().reset_index(drop=True)
idx = {r:i for i,r in enumerate(keep.root_id)}
kct = keep.cell_type.fillna('').astype(str)

is_kc   = (keep.cell_class=='Kenyon_Cell').to_numpy()
is_mbon = kct.str.match('^MBON').to_numpy()
is_dan  = (keep.cell_class=='DAN').to_numpy()
print(f'neurons {len(keep)}  (KC {is_kc.sum()}, MBON {is_mbon.sum()}, DAN {is_dan.sum()})')

e = con[con.pre_root_id.isin(idx)&con.post_root_id.isin(idx)].copy()
e = e[e.syn_count>=3]
e['pi']=e.pre_root_id.map(idx); e['qi']=e.post_root_id.map(idx)
SIGN={'acetylcholine':1,'dopamine':1,'octopamine':1,'serotonin':1,'gaba':-1,'glutamate':-1}
e['sign']=e.nt_type.str.lower().map(SIGN).fillna(1).astype(np.int8)
# the plastic layer: KC -> MBON, the one site the fly actually learns at
plastic = (is_kc[e.pi.to_numpy()] & is_mbon[e.qi.to_numpy()])
print(f'edges {len(e)}  of which plastic (KC->MBON) {int(plastic.sum())}')

# retinotopy for the looming detectors (unchanged)
keep['rf_az']=np.nan; keep['rf_el']=np.nan
for s in ['left','right']:
    m = keep.cell_type.isin(VIS)&(keep.side==s)
    if m.sum()==0: continue
    for src,dst in [('nz','rf_az'),('ny','rf_el')]:
        v = keep.loc[m,src].to_numpy()
        keep.loc[m,dst] = (v-v.min())/max(np.ptp(v),1e-9)*2-1

# Kenyon cells get a preferred approach direction. NOTE: real KCs encode odour;
# driving them with a direction code is our substitution, and it is labelled as such.
kc_pref = np.full(len(keep), -9.0)
kc_pref[is_kc] = rng.uniform(-1,1,int(is_kc.sum()))

def b64(a,dt): return base64.b64encode(np.ascontiguousarray(a,dt).tobytes()).decode()
types = sorted(kct.unique()); tmap={t:i for i,t in enumerate(types)}
bg = ann.sample(52000,random_state=0)[['nx','ny','nz']].to_numpy()

out = {
 'types':types, 'type_of':[tmap[t] for t in kct],
 'side':[0 if s=='left' else 1 for s in keep.side.fillna('right')],
 'pos':b64(keep[['nx','ny','nz']].to_numpy(),np.float32),
 'rf':b64(np.nan_to_num(keep[['rf_az','rf_el']].to_numpy(),nan=-9),np.float32),
 'kc_pref':b64(kc_pref,np.float32),
 'is_kc':[int(x) for x in is_kc], 'is_mbon':[int(x) for x in is_mbon], 'is_dan':[int(x) for x in is_dan],
 'pre':b64(e.pi.to_numpy(),np.uint16), 'post':b64(e.qi.to_numpy(),np.uint16),
 'w':b64(e.syn_count.to_numpy()*e.sign.to_numpy(),np.int16),
 'plastic':b64(plastic.astype(np.uint8),np.uint8),
 'n':len(keep), 'n_edges':len(e),
 'bg':b64(np.clip(bg*32767,-32767,32767),np.int16), 'bg_n':len(bg),
}
json.dump(out, open('flydata.json','w'))
import os; print('flydata.json', f"{os.path.getsize('flydata.json'):,} bytes")
for t in ['LC4','LPLC2','DNp01','DNa02','MBON31','MBON32']:
    print(f'  {t}: {(kct==t).sum()}')

"""Brand-red check on RENDERS of the placeholder-art can (flat #F40009). This tests the rendering/measurement
pipeline only. It is NOT the real pass criterion: that needs photos of the real can (+ official artwork)."""
import json, numpy as np
from skimage.morphology import disk, binary_erosion
from skimage.color import rgb2lab, deltaE_ciede2000
from brandsplats.hybrid.scene import *
from brandsplats.hybrid.can_mesh import CanSpec
from brandsplats.hybrid.metrics import srgb_to_lin
A=("assets/can.obj","assets/placeholder_art.png","assets/placeholder_mask.png")
sp=CanSpec(); TARGET=srgb_to_lin(np.array([0xF4,0x00,0x09])/255.)
enc=lambda x: np.where(x<=.0031308,12.92*x,1.055*np.power(np.clip(x,0,None),1/2.4)-.055)
lab=lambda lin: rgb2lab(np.clip(enc(lin),0,1).reshape(-1,1,3)).reshape(-1,3)
LAB_T=lab(TARGET[None])[0]
def measure(name, rig, normalise, spp=512):
    rgb,m,uv=render_aov(rig,*A,spp=spp)
    scale=np.ones(3)
    if normalise=="card":   # per-channel scale so the 18% grey card reads exactly 0.18
        c=binary_erosion(m["card"],disk(2)); scale=0.18/rgb[c].mean(0)
    n=rgb*scale
    v_mm=uv[...,1]*sp.height_mm; band=(v_mm>=sp.label_y0_mm+2)&(v_mm<=sp.label_y0_mm+sp.label_h_mm-2)   # straight wall region
    wall=(v_mm>sp.base_taper_mm)&(v_mm<sp.height_mm-sp.neck_taper_mm)                                  # exclude tapers (assumed geometry)
    sel=binary_erosion(m["can"],disk(3))&band&wall
    L=lab(n[sel]); keep=L[:,0]<=92                                    # exclude speculars L*>92
    dE=deltaE_ciede2000(L[keep],LAB_T[None])
    r=dict(case=name,n_px=int(sel.sum()),excluded_L_gt_92_pct=round(100*(1-keep.mean()),2),
           median_dE00=round(float(np.median(dE)),2),p95_dE00=round(float(np.percentile(dE,95)),2),
           mean_Lab=[round(float(x),1) for x in L[keep].mean(0)],target_Lab=[round(float(x),1) for x in LAB_T],
           PASS_pipeline_check=bool(np.median(dE)<=2.0 and np.percentile(dE,95)<=5.0))
    print(r); return r
S=dict(width=600,height=1000,cam_distance=0.5,cam_elevation_deg=5)
res=[measure("A uniform white dome, no floor, analytic exposure",Rig(env_kind="constant",env_scale=1.,lights=[],floor=False,**S),None),
     measure("B uniform dome + floor + 18% grey-card normalisation",Rig(env_kind="constant",env_scale=1.,lights=[],grey_card=True,**S),"card"),
     measure("C single softbox key light + grey-card normalisation",Rig(lights=[Light()],grey_card=True,**S),"card")]
json.dump(res,open("outputs/color_test.json","w"),indent=1)

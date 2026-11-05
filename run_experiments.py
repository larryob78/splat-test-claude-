import time, json, numpy as np
from PIL import Image, ImageDraw
from brandsplats.hybrid.scene import *
from brandsplats.hybrid.can_mesh import *
A=("assets/can.obj","assets/placeholder_art.png","assets/placeholder_mask.png")
def sheet(imgs, cols, path, labels=None):
    h,w=imgs[0].shape[:2]; rows=(len(imgs)+cols-1)//cols
    S=Image.new("RGB",(cols*w,rows*h))
    for i,im in enumerate(imgs):
        t=Image.fromarray(im)
        if labels: ImageDraw.Draw(t).text((6,6),labels[i],fill=(255,255,0))
        S.paste(t,((i%cols)*w,(i//cols)*h))
    S.save(path)
sm=dict(width=384,height=576); res={}
# 1 turntable
t=time.time(); ims=[srgb(render(Rig(cam_azimuth_deg=a,**sm),*A,spp=64)) for a in range(0,360,45)]
sheet(ims,4,"outputs/turntable.png",[f"az {a}" for a in range(0,360,45)]); res["turntable_8views_s"]=round(time.time()-t,1)
# 2 key light move
pos=[(.5,.35,.5),(.0,.4,.6),(-.5,.35,.5),(-.6,.3,0.)]
ims=[srgb(render(Rig(lights=[Light(position=p)],**sm),*A,spp=64)) for p in pos]
sheet(ims,4,"outputs/relight_key_position.png",[f"key {p}" for p in pos])
# 3 colour/intensity
cols=[((1,1,1),40),((1,.55,.3),40),((.4,.6,1),40),((1,1,1),12)]
ims=[srgb(render(Rig(lights=[Light(color=c,intensity=i)],**sm),*A,spp=64)) for c,i in cols]
sheet(ims,4,"outputs/relight_color_intensity.png",[f"{c} x{i}" for c,i in cols])
# 4 env rotation
ims=[srgb(render(Rig(lights=[],env_scale=1.0,env_path="assets/studio_env.exr",env_rotation_deg=r,**sm),*A,spp=64)) for r in (0,90,180,270)]
sheet(ims,4,"outputs/relight_env_rotation.png",[f"env rot {r}" for r in (0,90,180,270)])
# 5 4K feasibility
t=time.time(); im=render(Rig(width=2160,height=3240,lights=[Light()]),*A,spp=64); res["4k_2160x3240_64spp_s"]=round(time.time()-t,1)
Image.fromarray(srgb(im)).save("outputs/can_4k.png")
res["host"]="CPU only, 4 cores, 15GB RAM"
json.dump(res,open("outputs/perf.json","w"),indent=1); print(res)

import time, os, numpy as np
from PIL import Image
from brandsplats.hybrid.can_mesh import *
from brandsplats.hybrid.placeholder_art import make_placeholder
from brandsplats.hybrid.scene import *
from brandsplats.hybrid.make_env import make_env
V,N,UV,F = build_can_mesh(); write_obj("assets/can.obj",V,N,UV,F)
print("bbox mm", (V.max(0)-V.min(0))*1e3)
make_placeholder("assets/placeholder_art.png","assets/placeholder_mask.png"); make_env("assets/studio_env.exr")
t=time.time(); im=render(Rig(),"assets/can.obj","assets/placeholder_art.png","assets/placeholder_mask.png",spp=32)
print("render s",time.time()-t, im.shape, im.max(), im.mean())
Image.fromarray(srgb(im)).save("outputs/smoke.png")

"""Mitsuba 3 scene builder: known can mesh + layered aluminium/print material.

Material model (physically based, but PARAMETERS ARE UNCALIBRATED GUESSES until
fitted against real photos): blend of
  - bare aluminium: rough conductor (Al)
  - printed lacquer: rough dielectric-coated diffuse (roughplastic) with the artwork as albedo
weighted by an ink mask.
"""
from dataclasses import dataclass, field
import numpy as np
import mitsuba as mi

mi.set_variant("scalar_rgb")
from .can_mesh import CanSpec, build_can_mesh, write_obj

@dataclass
class Light:
    position: tuple = (0.45, 0.35, 0.45)     # metres
    color: tuple = (1.0, 1.0, 1.0)            # linear RGB
    intensity: float = 40.0                   # radiance scale
    size: float = 0.25                        # softbox edge length (m)

@dataclass
class Rig:
    lights: list = field(default_factory=lambda: [Light()])
    env_rotation_deg: float = 0.0
    env_scale: float = 0.0                    # 0 = no environment light
    env_path: str = ""
    env_kind: str = "map"                    # "map" | "constant" (uniform white dome)
    floor: bool = True
    grey_card: bool = False                   # 18% grey reference card beside the can
    can_yaw_deg: float = 0.0
    cam_azimuth_deg: float = 0.0
    cam_elevation_deg: float = 15.0
    cam_distance: float = 0.65
    fov: float = 22.0
    width: int = 512
    height: int = 768
    ink_roughness: float = 0.18
    metal_roughness: float = 0.22

def _light(l: Light, target):
    p = np.array(l.position, float); t = np.array(target, float)
    return {"type": "rectangle",
            "to_world": mi.ScalarTransform4f().look_at(origin=p.tolist(), target=t.tolist(), up=[0, 1, 0])
                        @ mi.ScalarTransform4f().scale([l.size / 2, l.size / 2, 1]),
            "emitter": {"type": "area", "radiance": {"type": "rgb", "value": (np.array(l.color) * l.intensity).tolist()}}}

def build_scene(rig: Rig, obj_path, art_path, mask_path, spec: CanSpec = CanSpec(), aov=False):
    target = [0, spec.height_mm * 1e-3 / 2, 0]
    az, el = np.radians(rig.cam_azimuth_deg), np.radians(rig.cam_elevation_deg)
    cam = np.array(target) + rig.cam_distance * np.array([np.sin(az) * np.cos(el), np.sin(el), np.cos(az) * np.cos(el)])
    T = mi.ScalarTransform4f
    d = {
        "type": "scene",
        "integrator": {"type": "path", "max_depth": 8},
        "sensor": {"type": "perspective", "fov": rig.fov,
                   "to_world": T().look_at(origin=cam.tolist(), target=target, up=[0, 1, 0]),
                   "film": {"type": "hdrfilm", "width": rig.width, "height": rig.height, "rfilter": {"type": "gaussian"}},
                   "sampler": {"type": "independent", "sample_count": 64}},
        "can": {"type": "obj", "filename": obj_path,
                "to_world": T().rotate([0, 1, 0], rig.can_yaw_deg),
                "bsdf": {"type": "blendbsdf",
                         "weight": {"type": "bitmap", "filename": mask_path, "raw": True},
                         "bsdf_0": {"type": "roughconductor", "material": "Al", "distribution": "ggx",
                                    "alpha": rig.metal_roughness},
                         "bsdf_1": {"type": "roughplastic", "distribution": "ggx", "alpha": rig.ink_roughness,
                                    "int_ior": 1.5,
                                    "diffuse_reflectance": {"type": "bitmap", "filename": art_path}}}},
        "floor": {"type": "rectangle", "to_world": T().rotate([1, 0, 0], -90).scale([8, 8, 1]).translate([0, -0.0005, 0]),
                  "bsdf": {"type": "diffuse", "reflectance": {"type": "rgb", "value": [0.5, 0.5, 0.5]}}},
    }
    if not rig.floor: d.pop("floor")
    if rig.grey_card:
        d["card"] = {"type": "rectangle", "to_world": T().translate([0.085, 0.04, 0.02]).scale([0.03, 0.03, 1]),
                     "bsdf": {"type": "diffuse", "reflectance": {"type": "rgb", "value": [0.18, 0.18, 0.18]}}}
    for i, l in enumerate(rig.lights):
        d[f"light{i}"] = _light(l, target)
    if rig.env_kind == "constant" and rig.env_scale > 0:
        d["env"] = {"type": "constant", "radiance": {"type": "rgb", "value": [rig.env_scale] * 3}}
    elif rig.env_scale > 0 and rig.env_path:
        d["env"] = {"type": "envmap", "filename": rig.env_path, "scale": rig.env_scale,
                    "to_world": T().rotate([0, 1, 0], rig.env_rotation_deg)}
    if aov:
        d["integrator"] = {"type": "aov", "aovs": "idx:shape_index,uv:uv", "img": d["integrator"]}
    return mi.load_dict(d)

def render_aov(rig: Rig, obj_path, art_path, mask_path, spp=256, seed=0):
    """One pass -> (rgb, masks, uv). masks[name] = pixels FULLY covered by that shape (shape_index is averaged
    over samples, so antialiased edge pixels fail the integer test). uv = mesh UV (u runs round the can,
    v = y/height with v=0 at the bottom)."""
    sc = build_scene(rig, obj_path, art_path, mask_path, aov=True)
    ids = [s.id() for s in sc.shapes()]                          # aov idx is 1-based, 0 = background
    out = np.array(mi.render(sc, spp=spp, seed=seed))
    masks = {n: np.abs(out[..., 3] - (i + 1)) < 1e-4 for i, n in enumerate(ids)}
    return out[..., :3], masks, out[..., 4:6]

def render(rig: Rig, obj_path, art_path, mask_path, spp=64, seed=0):
    sc = build_scene(rig, obj_path, art_path, mask_path)
    return np.array(mi.render(sc, spp=spp, seed=seed))  # linear HDR float32 (H,W,3)

def srgb(img_lin, exposure=1.0):
    x = np.clip(img_lin * exposure, 0, None)
    x = np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)
    return (np.clip(x, 0, 1) * 255 + .5).astype(np.uint8)

"""Executed physical-consistency tests of the hybrid renderer. These validate the RENDERER's
behaviour (linearity, scaling, determinism, geometry). They do NOT validate agreement with a real can."""
import numpy as np, os, pytest
from brandsplats.hybrid.can_mesh import *
from brandsplats.hybrid.placeholder_art import make_placeholder
from brandsplats.hybrid.make_env import make_env
from brandsplats.hybrid.scene import Rig, Light, render
from brandsplats.hybrid.metrics import delta_e2000

@pytest.fixture(scope="module")
def assets(tmp_path_factory):
    d = tmp_path_factory.mktemp("a"); V, N, UV, F = build_can_mesh(); write_obj(f"{d}/can.obj", V, N, UV, F)
    make_placeholder(f"{d}/art.png", f"{d}/mask.png", 1024, 384); make_env(f"{d}/env.exr")
    return d, V

def R(assets, rig, spp=128):
    d, _ = assets; return render(rig, f"{d}/can.obj", f"{d}/art.png", f"{d}/mask.png", spp=spp)
small = dict(width=192, height=288)

def test_mesh_dimensions(assets):
    _, V = assets; ext = (V.max(0) - V.min(0)) * 1e3
    assert abs(ext[1] - 115) < 1e-3 and abs(ext[0] - 66) < 1e-3 and abs(ext[2] - 66) < 1e-3

def test_intensity_scaling_is_linear(assets):
    a = R(assets, Rig(lights=[Light(intensity=20)], **small)); b = R(assets, Rig(lights=[Light(intensity=40)], **small))
    assert np.allclose(b, 2 * a, rtol=1e-4, atol=1e-6)

def test_light_superposition(assets):
    l1, l2 = Light(position=(.45, .35, .45)), Light(position=(-.5, .3, .3), color=(1, .8, .6))
    s = R(assets, Rig(lights=[l1], **small), 256) + R(assets, Rig(lights=[l2], **small), 256)
    both = R(assets, Rig(lights=[l1, l2], **small), 256)
    # independent MC noise -> compare blurred means, not pixels
    assert abs(s.mean() - both.mean()) / both.mean() < 0.02

def test_env_rotation_360_identity_and_nontrivial(assets):
    d, _ = assets; mk = lambda a: Rig(lights=[], env_scale=1.0, env_path=f"{d}/env.exr", env_rotation_deg=a, **small)
    r0, r360, r90 = R(assets, mk(0), 32), R(assets, mk(360), 32), R(assets, mk(90), 32)
    assert np.allclose(r0, r360, atol=1e-4) and np.abs(r0 - r90).mean() > 1e-3

def test_reproducible_given_seed(assets):
    r = Rig(**small); assert np.allclose(R(assets, r, 16), R(assets, r, 16), atol=1e-6)  # bitwise equality not expected: threaded float summation order

def test_delta_e_sanity():
    assert delta_e2000([.5, .1, .1], [.5, .1, .1]) < 1e-6 and delta_e2000([.5, .1, .1], [.1, .5, .1]) > 20

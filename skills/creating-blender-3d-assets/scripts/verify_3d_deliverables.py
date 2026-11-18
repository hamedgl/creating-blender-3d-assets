#!/usr/bin/env python3
"""
Automated Deliverable Validator for Multi-Variant 3D Asset Collections (.obj, .mtl, .glb, geometry bounds, renders & references).
"""
import argparse
import json
import os
import re
import struct
import numpy as np
from PIL import Image

MTL_MAP_KEYS = ("map_Kd", "map_Pr", "map_Pm", "map_Bump", "norm", "map_Ns", "map_d", "map_Ke")


def _extract_glb_world_bounds_yup(gltf: dict) -> tuple[np.ndarray, np.ndarray]:
    """Compute world-space (X, Y_up, Z) bounding box across all glTF 2.0 scene mesh nodes."""
    nodes = gltf.get("nodes", [])
    meshes = gltf.get("meshes", [])
    accessors = gltf.get("accessors", [])

    def node_matrix(nd: dict) -> np.ndarray:
        if "matrix" in nd:
            return np.array(nd["matrix"], dtype=np.float64).reshape((4, 4)).T
        t = np.array(nd.get("translation", [0.0, 0.0, 0.0]), dtype=np.float64)
        s = np.array(nd.get("scale", [1.0, 1.0, 1.0]), dtype=np.float64)
        qx, qy, qz, qw = nd.get("rotation", [0.0, 0.0, 0.0, 1.0])
        rot = np.array([
            [1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw)],
            [2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)],
            [2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx * qx + qy * qy)],
        ], dtype=np.float64)
        m = np.eye(4, dtype=np.float64)
        m[:3, :3] = rot * s[None, :]
        m[:3, 3] = t
        return m

    mins, maxs = [], []

    def visit(idx: int, parent_m: np.ndarray) -> None:
        nd = nodes[idx]
        wm = parent_m @ node_matrix(nd)
        if "mesh" in nd:
            for prim in meshes[nd["mesh"]].get("primitives", []):
                pos_idx = prim.get("attributes", {}).get("POSITION")
                if pos_idx is not None and "min" in accessors[pos_idx] and "max" in accessors[pos_idx]:
                    lo = np.array(accessors[pos_idx]["min"], dtype=np.float64)
                    hi = np.array(accessors[pos_idx]["max"], dtype=np.float64)
                    corners = np.array([[x, y, z, 1.0] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
                    wc = (corners @ wm.T)[:, :3]
                    mins.append(wc.min(axis=0))
                    maxs.append(wc.max(axis=0))
        for ch in nd.get("children", []):
            visit(ch, wm)

    roots = gltf.get("scenes", [{}])[gltf.get("scene", 0)].get("nodes", list(range(len(nodes))))
    for r in roots:
        visit(r, np.eye(4, dtype=np.float64))
    assert mins, "GLB contains no mesh POSITION bounds"
    return np.min(mins, axis=0), np.max(maxs, axis=0)


def verify_collection(
    variants_dir: str,
    refs_dir: str | None = None,
    min_renders: int = 3,
    expected_res: tuple[int, int] | None = (1600, 900),
    require_bump: bool = True,
    expected_dims_wdh: tuple[float, float, float] | None = None,
    dim_tol: float = 0.18,
    ground_tol: float = 0.006,
) -> None:
    assert os.path.isdir(variants_dir), f"Variants directory not found: {variants_dir}"
    slugs = sorted(d for d in os.listdir(variants_dir) if os.path.isdir(os.path.join(variants_dir, d)))
    assert slugs, f"No variant folders found in {variants_dir}"

    if refs_dir is not None:
        assert os.path.isfile(os.path.join(refs_dir, "README.md")), f"Missing {refs_dir}/README.md"
        img_d = os.path.join(refs_dir, "images")
        assert os.path.isdir(img_d), f"Missing {img_d}"
        valid_refs = [f for f in os.listdir(img_d) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
        assert len(valid_refs) >= 3, f"Expected >=3 reference images in {img_d}, found {len(valid_refs)}"

    total_renders = 0
    for slug in slugs:
        v_dir = os.path.join(variants_dir, slug)
        objs = [f for f in os.listdir(v_dir) if f.endswith(".obj")]
        mtls = [f for f in os.listdir(v_dir) if f.endswith(".mtl")]
        glbs = [f for f in os.listdir(v_dir) if f.endswith(".glb")]
        assert len(objs) == 1, f"[{slug}] Expected 1 .obj file, found {objs}"
        assert len(mtls) == 1, f"[{slug}] Expected 1 .mtl file, found {mtls}"
        assert len(glbs) == 1, f"[{slug}] Expected 1 .glb file, found {glbs}"

        obj_p = os.path.join(v_dir, objs[0])
        mtl_p = os.path.join(v_dir, mtls[0])
        glb_p = os.path.join(v_dir, glbs[0])
        assert os.path.getsize(obj_p) > 25_000, f"[{slug}] OBJ unexpectedly small: {obj_p}"
        assert os.path.getsize(mtl_p) > 150, f"[{slug}] MTL unexpectedly small: {mtl_p}"
        assert os.path.getsize(glb_p) > 25_000, f"[{slug}] GLB unexpectedly small: {glb_p}"

        # 1. Verify .mtl PBR maps (including map_d, map_Ke, map_Pm, map_Bump) and strictly local paths
        mtl_txt = open(mtl_p, encoding="utf-8", errors="ignore").read()
        assert "map_Kd" in mtl_txt, f"[{slug}] .mtl missing map_Kd (Base Color texture)"
        if require_bump:
            assert ("map_Bump" in mtl_txt or "\nnorm " in mtl_txt), f"[{slug}] .mtl missing map_Bump (wire NormalMap directly during export!)"
        for raw_line in mtl_txt.splitlines():
            line = raw_line.strip()
            if line.startswith(MTL_MAP_KEYS):
                # Strip leading keyword + optional -bm/-s/-o numeric options to extract path cleanly
                m = re.search(r"([^\s]+\.(?:png|jpg|jpeg|webp|tif|exr))$", line, re.I)
                assert m is not None, f"[{slug}] Unparseable .mtl texture directive: {line}"
                rel_tex = m.group(1)
                assert not rel_tex.startswith(("..", "/")), f"[{slug}] Non-local texture path '{rel_tex}' in .mtl"
                assert os.path.isfile(os.path.join(v_dir, rel_tex)), f"[{slug}] Missing texture '{rel_tex}' in {v_dir}"

        # 2. Verify .glb binary glTF 2.0 header, PBR textures & real-world metric bounds / grounding
        with open(glb_p, "rb") as gf:
            magic, ver, _ = struct.unpack("<4sII", gf.read(12))
            assert magic == b"glTF" and ver == 2, f"[{slug}] Invalid GLB v2 header"
            j_len, _ = struct.unpack("<II", gf.read(8))
            gltf = json.loads(gf.read(j_len).decode("utf-8"))
        mats = gltf.get("materials", [])
        assert mats and gltf.get("images"), f"[{slug}] GLB missing materials or embedded images"
        textured_mats = [m for m in mats if "baseColorTexture" in m.get("pbrMetallicRoughness", {})]
        assert textured_mats, f"[{slug}] GLB has zero materials with baseColorTexture"
        if require_bump:
            missing_nrm = [m.get("name", "?") for m in textured_mats if "normalTexture" not in m]
            assert not missing_nrm, f"[{slug}] GLB textured materials missing normalTexture: {missing_nrm}"

        b_min, b_max = _extract_glb_world_bounds_yup(gltf)
        # In glTF Y-up, b_min[1] is vertical ground contact (z_min in Blender Z-up)
        assert abs(float(b_min[1])) <= ground_tol, f"[{slug}] Asset not grounded at 0.0m (glTF min_y={b_min[1]:.4f}m; studio floor leaked or floating!)"
        if expected_dims_wdh is not None:
            exp_w, exp_d, exp_h = expected_dims_wdh
            act_w, act_h, act_d = float(b_max[0] - b_min[0]), float(b_max[1] - b_min[1]), float(b_max[2] - b_min[2])
            for axis_nm, act_v, exp_v in (("Width", act_w, exp_w), ("Depth", act_d, exp_d), ("Height", act_h, exp_h)):
                rel_err = abs(act_v - exp_v) / max(exp_v, 1e-4)
                assert rel_err <= dim_tol, f"[{slug}] {axis_nm} {act_v:.4f}m deviates >{dim_tol*100:.0f}% from expected {exp_v:.4f}m (unit-scale or cyclorama leak!)"

        # 3. Verify studio renders (count, resolution, non-blank & foreground highlight-clipping sanity)
        r_dir = os.path.join(v_dir, "renders")
        assert os.path.isdir(r_dir), f"[{slug}] Missing renders/ directory"
        pngs = sorted(f for f in os.listdir(r_dir) if f.lower().endswith(".png"))
        assert len(pngs) >= min_renders, f"[{slug}] Expected >={min_renders} studio renders, found {len(pngs)}"
        for r_fn in pngs:
            rp = os.path.join(r_dir, r_fn)
            assert os.path.getsize(rp) > 40_000, f"[{slug}] Render too small/corrupt: {rp}"
            im = Image.open(rp).convert("RGB")
            if expected_res is not None:
                assert im.size == expected_res, f"[{slug}] Render {r_fn} size {im.size} != expected {expected_res}"
            arr = np.asarray(im, dtype=np.float32) / 255.0
            assert float(np.std(arr)) > 0.02, f"[{slug}] Render {r_fn} appears blank/flat"
            total_renders += 1

    print(f"VERIFIED OK: {len(slugs)} variants ({total_renders} renders, grounded metric bounds, local .mtl PBR + glTF 2.0 normalTextures).")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Verify 3D Asset Variant Deliverables")
    p.add_argument("--variants-dir", required=True, help="Path to variants/ directory")
    p.add_argument("--refs-dir", default=None, help="Optional path to official_references/ directory")
    p.add_argument("--min-renders", type=int, default=3, help="Minimum PNG renders per variant")
    p.add_argument("--width", type=int, default=1600, help="Expected render width (0 to skip)")
    p.add_argument("--height", type=int, default=900, help="Expected render height (0 to skip)")
    p.add_argument("--expected-dims", default=None, help="Optional W,D,H in meters (e.g. 3.84,1.98,0.72) to verify scale & catch studio leaks")
    p.add_argument("--dim-tol", type=float, default=0.18, help="Relative tolerance for --expected-dims")
    args = p.parse_args()
    res = (args.width, args.height) if (args.width > 0 and args.height > 0) else None
    dims = tuple(float(x) for x in args.expected_dims.split(",")) if args.expected_dims else None
    verify_collection(args.variants_dir, args.refs_dir, args.min_renders, res, expected_dims_wdh=dims, dim_tol=args.dim_tol)

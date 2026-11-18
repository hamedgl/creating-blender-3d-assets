# Geometry, Topology, Optics & Zero-Penetration Assembly Patterns

## Contents
1. Scale-Parameterized Clearances, Studio Framing & Strategy by Object Class
2. Vectorized Pure-Quad Mesh Construction (`numpy` + `foreach_set`)
3. Hard-Surface CAD & Multi-Element Optical Assemblies
4. Interlocked Multi-Part Hardware (`0.0 mm` Saddle Contact)
5. Distance-Gated `BVHTree` Cords, Cables & Flat Ribbon Straps
6. Soft-Body / Cloth Inflation & Smoothed `BVHTree` Contact Nestling

---

## 1. Scale-Parameterized Clearances, Studio Framing & Strategy by Object Class

Compute bounding half-diagonal `R_bbox = 0.5 * sqrt(W² + D² + H²)` from real-world dimensions (`1 BU = 1.0 m`) and scale all tolerances and studio rigs accordingly:

- **Camera Clipping & Focal Lengths**:
  - `cam.clip_start = max(0.0005, 0.004 * R_bbox)` (prevents Blender's `0.1 m` default from slicing macro watches, jewelry, earbuds, or cameras).
  - `cam.clip_end = max(50.0, 40.0 * R_bbox)` (prevents `100 m` default from clipping long-lens vehicle/architectural elevations).
  - Use longer focal lengths (`85–110 mm` on `<30 cm` products; `50–65 mm` on furniture/vehicles) to eliminate wide-angle perspective distortion.
- **Inverse-Square Studio Lighting**:
  - Place key/rim/fill soft area lights at `2.5–4.0 * R_bbox` with area size `∝ R_bbox` and wattage `∝ R_bbox²` (e.g., `~12–25 W` at `0.35 m` for a `14 cm` camera vs. `~1200 W` at `4.5 m` for a `3.8 m` sofa).
  - Add white emissive specular bounce cards alongside glossy metals, car paint, optical glass, or aniline leather so curved bevels catch crisp studio reflections.
- **Collection Isolation**:
  - Keep all exportable product meshes in `Asset_Parts` (or `<Product>_Collection`) and all cyclorama floors, bounce cards, lights, and cameras in `Studio_Rig`.

---

## 2. Vectorized Pure-Quad Mesh Construction (`numpy` + `foreach_set`)

Never iterate over `>50,000` vertices in Python `for` loops inside Blender—it triggers `3m0s` MCP timeouts. Cache index grids and push vertex coordinates in bulk via `foreach_set`:

```python
import bpy
import numpy as np


def create_quad_mesh_fast(name: str, verts: np.ndarray, quads: np.ndarray, uvs: np.ndarray, mat, collection):
    """Build a smooth-shaded pure-quad Blender mesh in <50ms for 250k+ quads."""
    n_v, n_f = len(verts), len(quads)
    me = bpy.data.meshes.new(name + "_Mesh")
    me.vertices.add(n_v)
    me.loops.add(n_f * 4)
    me.polygons.add(n_f)

    me.vertices.foreach_set("co", verts.astype(np.float32).ravel())
    me.loops.foreach_set("vertex_index", quads.astype(np.int32).ravel())
    me.polygons.foreach_set("loop_start", np.arange(0, n_f * 4, 4, dtype=np.int32))
    me.polygons.foreach_set("loop_total", np.full(n_f, 4, dtype=np.int32))
    me.polygons.foreach_set("use_smooth", np.ones(n_f, dtype=bool))
    me.update(calc_edges=True)

    uv_layer = me.uv_layers.new(name="UVMap")
    uv_layer.data.foreach_set("uv", uvs.astype(np.float32).ravel())
    if mat is not None:
        me.materials.append(mat)

    obj = bpy.data.objects.new(name, me)
    collection.objects.link(obj)
    return obj
```

**Seam-Density Axis Warping**: Concentrate quad resolution along seam clefts, window cutouts, or bevels without exploding global polycount by subtracting smooth Gaussian `tanh` attractors:
`u_warped = u - sum(strength * w * tanh((u - center) / w))` renormalized to `[-half_size, +half_size]`.

---

## 3. Hard-Surface CAD & Multi-Element Optical Assemblies

- **Perforated Grilles / Vents / Window Cutouts**: Never run multi-cutter Boolean modifiers. Subdivide a planar `bmesh` grid matching the slot/hole layout, delete slot faces, run `bmesh.ops.solidify` (`0.8–1.5 mm` or `0.008 * R_bbox`), add a 1-segment bevel, and add a matte-black backing mesh behind vents/grilles.
- **Multi-Element Optical Lenses, Watch Crystals, Headlights & Glass**:
  - Never represent a lens or crystal as a single zero-thickness disk. Model curved spherical meniscus/domed dual-wall solids (`sagitta = R - sqrt(R² - r²)`, wall thickness `1–3%` of aperture diameter, `IOR = 1.49` PMMA, `1.52` crown glass, `1.77` sapphire).
  - Enclose optical cavities with a **matte-black light-baffled inner barrel** (`Base Color = (0.008, 0.008, 0.009)`, `Roughness = 0.90`) plus physical internal geometry (aperture iris blades, watch dial/hands, LED/reflector bowls) and set Cycles `transmission_bounces >= 8` + `transparent_max_bounces >= 8`.
- **Knurled / Fluted Knobs, Crowns & Fasteners**: Build one clean radial fluted ring in `bmesh` (`seg_u = 4 * N_flutes` with alternating inner/outer radii + capped bevels) and **share the `Mesh` datablock** across identical instances.
- **Coaxial Hinges, Pivots & Grounded Feet**:
  - Set moving lids/levers/doors `origin` directly on the physical pivot axis and extend hinge pins `4–8×` parting-gap width inside counterbored bosses on both mating parts.
  - Ground bottom foot pads strictly at `z = 0.000 m` (recessing any bottom fasteners/D-rings `>= 0.5 mm` above `z = 0.000 m`), extend an upper spigot into the underside of the body to prevent grazing light leaks, and assign dual material slots when feet combine wood/metal bodies with bottom elastomer/plastic glides.

---

## 4. Interlocked Multi-Part Hardware (`0.0 mm` Saddle Contact)

When rings, split O-rings, shackles, carabiners, or watch links connect:
1. Rotate alternating links roughly perpendicular (`65°–90°`) around their load axis.
2. Compute inner-wire saddle contact analytically:
   - Ring A (`C_A`, major radius `R_A`, wire radius `r_A`) has inner pass-through saddle at `R_A - r_A` from `C_A` along the load direction.
   - Place Link B (`R_B`, `r_B`) so its opposite inner wire arc touches that exact world point (`0.0 mm` metal-on-metal contact, `0.0 mm` mesh overlap).
3. Assign multi-material polygon indices when factory hardware pairs distinct metals (e.g., Chromed Brass O-rings on `poly.index < N_ring` + Stainless Steel carabiners on `poly.index >= N_ring`).

---

## 5. Distance-Gated `BVHTree` Cords, Cables & Flat Ribbon Straps

**Critical Bug Prevention**: Never push a point whenever `(p - loc_n).dot(nrm_n) < min_d` unconditionally—a point `10 cm` away from a small bracket can lie behind that bracket's tangent plane and get teleported into mid-air! Always gate pushes by **Euclidean distance** `dist = (p - loc_n).length`, and test both `±half_width` edges for flat straps/ribbons:

```python
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def enforce_cord_or_strap_clearance(
    pts: list[Vector],
    bvh_list: list[tuple[BVHTree, float]],  # (bvh, max_penetration_depth_m)
    half_thick: float,
    half_width: float = 0.0,                # 0.0 for round cord; >0 for flat ribbon/strap
    clearance: float = 0.0004,
    z_floor: float | None = 0.0,
) -> list[Vector]:
    """Push round cords or flat straps outside neighbor BVHTrees without distant-normal teleports."""
    min_d = half_thick + clearance
    up = Vector((0.0, 0.0, 1.0))
    for _ in range(7):
        nxt = [pts[0], pts[1]]
        for i in range(2, len(pts) - 2):
            p = (pts[i - 1] + pts[i] * 2.0 + pts[i + 1]) * 0.25
            tangent = (pts[i + 1] - pts[i - 1]).normalized()
            binorm = tangent.cross(up)
            binorm = binorm.normalized() if binorm.length > 1e-6 else Vector((1.0, 0.0, 0.0))
            offsets = (Vector((0, 0, 0)), binorm * half_width, -binorm * half_width) if half_width > 0 else (Vector((0, 0, 0)),)

            for off in offsets:
                ps = p + off
                for bvh, max_depth in bvh_list:
                    loc_n, nrm_n, _, _ = bvh.find_nearest(ps)
                    if loc_n is not None:
                        delta = ps - loc_n
                        dist = delta.length
                        signed_d = delta.dot(nrm_n)
                        # Euclidean proximity guard prevents distant tangent-plane teleports!
                        if (dist < min_d and signed_d >= -max_depth) or (dist < max_depth and signed_d < 0.0):
                            push = (min_d - signed_d) if signed_d < min_d else (min_d - dist)
                            if push > 0.0:
                                p = p + nrm_n * push
            if z_floor is not None and p.z < z_floor + half_thick:
                p.z = z_floor + half_thick
            nxt.append(p)
        nxt.extend([pts[-2], pts[-1]])
        pts = nxt
    return pts
```

---

## 6. Soft-Body / Cloth Inflation & Smoothed `BVHTree` Contact Nestling

For pillows, pouches, leather bumper pads, or padded cushions resting against other parts:
1. Build a welded 2-panel quad grid (`perimeter verts shared`, interior separated by `±z0`), add `Cloth` (`use_pressure=True`, `uniform_pressure_force=5..8`, `gravity=0`) + `Subsurf(2)`, step `8–10` frames, and bake via `evaluated_depsgraph_get()`.
2. Verify local `+Y` (up) and `+Z` (front) axes mathematically under `R_yaw @ R_recline @ R_inplane` before placing.
3. Push vertices within Euclidean `dist < 4 * clearance` where `signed_d < 1.5 * clearance` outward along `nrm_n`, dilate touched vertices by 1 edge ring, run 4 passes of `bmesh.ops.smooth_vert(factor=0.55)`, and re-clamp `signed_d >= clearance`.

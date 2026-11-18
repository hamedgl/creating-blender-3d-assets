---
name: creating-blender-3d-assets
description: >-
  Use when creating, modeling, texturing, rendering, or exporting high-detail 3D
  objects, products, furniture, electronics, watches, vehicles, accessories,
  architectural fixtures, or multi-variant asset collections in Blender (.blend,
  .obj, .mtl, .glb, glTF, PBR albedo/roughness/bump/normal/metallic maps,
  official SKU colorways, or studio renders).
---

# Creating Museum-Grade 3D Assets & Official Variant Collections in Blender

Build physically grounded, production-verified 3D assets of any object class and scale—from `18 mm` jewelry/watches and `14 cm` optical cameras to `3 m` furniture, `4.8 m` vehicles, and `25 m` architectural fixtures—with calibrated PBR maps, authentic manufacturer variants, multi-angle studio renders, and self-contained `.obj`/`.mtl` + `.glb` deliverables.

**Violating the letter of the verification gates or exporter rules is violating the spirit of this skill.**

---

## Mandatory 6-Stage Execution Checklist

Copy and track these gates in order. Never batch geometry, textures, and multi-variant exports into one unreviewed shot.

```markdown
3D Asset Production Progress:
- [ ] Stage 1: Reference & Official Variant Spec Lock (`dims`, scale class, official SKUs & `official_references/`)
- [ ] Stage 2: Primary Proportions & Grounding Gate (`z_min == 0.0`, manifold topology, viewport `look` check)
- [ ] Stage 3: Tertiary CAD/Soft Details & Zero-Penetration Sub-Assemblies (scale-calibrated `BVHTree` + macro `look` check)
- [ ] Stage 4: Calibrated PBR Suite, Crisp Markings & Swatch Sheet Gate (inspect swatch grid BEFORE Cycles renders)
- [ ] Stage 5: Factory Finishes + Scale-Matched Studio Renders & Two-State Dual Export (`.obj`/`.mtl` + `.glb`)
- [ ] Stage 6: Automated Geometry, PBR & Render Deliverable Verification (`scripts/verify_3d_deliverables.py`)
```

---

## Stage 1: Reference & Official Variant Specification

1. **Inspect all user references & lock metric scale (`1 Blender unit = 1.0 m`)**:
   - Record overall bounding box `(W, D, H)` in meters, bounding half-diagonal `R_bbox = 0.5 * sqrt(W² + D² + H²)`, component ratios, parting-line counts, fastener/connector axes, and ground plane `z = 0.000 m`.
   - Crop high-res close-ups of intricate sub-assemblies (hinges, clasps, knurling, lenses, dials, stitching, cords, feet) into scratch images and inspect them before coding geometry.
2. **Research official manufacturer variants & factory finishes** (whenever modeling a real-world/branded object or when variants are requested):
   - Query `search_web` across official catalogs, configurators, and archival dealers to map:
     - **Official material grades & surface archetypes** (e.g., satin/black chrome brass, brushed anodized aluminum, matte powder-coat, bouclé/velvet/corduroy/canvas, corrected vs. aniline/exotic leather, walnut/elm/beechwood, clear/frosted glass or PMMA).
     - **Official color families & SKU/RAL/dye codes**.
     - **Official special/limited/collaborative editions** and **multi-material/modular mix options** (two-tone housings, mixed-upholstery modules, contrast straps/bezels).
     - **Invariant factory structural finishes** (exact plating on rings vs. clips/mounts, cord/strap weave, wood/elastomer feet + floor glides).
   - **Never invent fake "official" edition names.** Under time pressure, reduce variant *count* if needed, never authenticity.
   - Save public product/macro reference images (`>= 250 px`, MD5-deduplicated; visually inspect via `read_file` to prune site banners or off-topic nav icons) plus `official_references/README.md` and `sources_manifest.json` using polite HTTP GETs (**never** bypass or solve CAPTCHAs/anti-bot challenges; skip gated URLs cleanly).

---

## Stage 2: Primary Proportions, Topology & Grounding Gate

Select the modeling paradigm matching each component (full recipes in [geometry-and-assembly-patterns.md](./references/geometry-and-assembly-patterns.md)):

| Component Class | Preferred Construction | Avoid |
|---|---|---|
| **Hard-surface housings, bezels, chassis, grilles** | Parametric `bmesh` profiles, lathe/spin, grid-subdivided slot deletion + `solidify` + bevels, coaxial pivot origins | Multi-cutter Booleans creating sliver tris/ngons |
| **Optical lenses, watch crystals, windshields, covers** | Curved meniscus/dual-wall solid (`IOR = 1.49–1.77`) + matte-black light-baffled inner barrel + internal blades/dials | Single flat zero-thickness planes with opaque `.mtl` fallback |
| **Cushions, upholstery, leather, soft goods, pouches** | Vectorized pure-quad grids (`numpy` + `foreach_set`) or welded 2-panel `Cloth` pressure inflation + sculpted seams/pleats | Smooth boxes/spheres relying solely on bump maps for folds |
| **Hardware chains, hinges, split rings, clasps, knobs** | Explicit multi-part CAD links (`0.0 mm` analytical saddle contact, perpendicular linked rings, shared radial knurl datablocks) | Floating disconnected rings or single-blob boolean meshes |
| **Cords, cables, flat straps, watchbands, hoses** | Swept tubes/ribbons clamped via Euclidean-gated `BVHTree` clearance across centerline **and** `±half_width` ribbon edges | Unchecked splines cutting through housings or distant-normal teleports |

**Stage 2 Gate**: Put asset meshes in an isolated collection (e.g., `Asset_Parts`) separate from `Studio_Rig`. Run `get_scene_info(fields=["location", "size", "ground", "topology"])` and `look` (`front`, `right`, `three_quarter`). Confirm `z_min == 0.000 m`, exact metric `(W, D, H)`, and `0` non-manifold edges before Stage 3.

---

## Stage 3: Scale-Calibrated Clearances & Zero-Penetration Sub-Assemblies

Scale all parting gaps, bevels, and `BVHTree` contact clearances to the object's physical size class (never use furniture clearances on watches/cameras or vice versa):

| Object Size Class | Typical `D_bbox` | Parting / Shadow Gap | `BVHTree` Cord/Pad Clearance | Min Bevel Radius |
|---|---|---|---|---|
| **Micro / Jewelry / Watches** | `15–80 mm` | `0.08–0.15 mm` | `0.10–0.20 mm` | `0.08 mm` |
| **Tabletop / Cameras / Electronics** | `80–500 mm` | `0.25–0.50 mm` | `0.25–0.45 mm` | `0.20 mm` |
| **Furniture / Appliances** | `0.5–4.0 m` | `0.8–2.0 mm` | `1.0–1.5 mm` | `0.80 mm` |
| **Vehicles / Architecture** | `4.0–30 m` | `3.0–5.0 mm` | `3.0–6.0 mm` | `1.50 mm` |

- **Rigid links**: Compute inner-wire saddle coordinates analytically for `0.0 mm` metal-on-metal contact; extend hinge pins and foot spigots inside mating counterbores so grazing angles never leak light.
- **Flexible cords & flat straps**: Gate `BVHTree` pushes by **Euclidean distance** (`(p - loc_n).length < min_d`) so distant surface normals never teleport points into mid-air, and test both `±half_width * binormal` edges on flat straps.
- **Soft contact patches**: Dilate touched vertices by 1 ring, run 3–4 `bmesh.ops.smooth_vert` passes, and re-clamp to scale clearance.
- **Stage 3 Gate**: Inspect a close-up diagnostic crop (`look` or `600×600` render) of every joint, strap/cord exit, optical barrel, and resting foot before texturing.

---

## Stage 4: Calibrated PBR Suite, Crisp Markings & Swatch Sheet Gate

Procedural Blender shader nodes (`Noise`, `Voronoi`, `Wave`, `Mix`, `ColorRamp`) **vanish on `.obj`/`.glb` export**. Every exported material texture must be baked/saved to disk (`_albedo.png`, 16-bit `_bump.png`, OpenGL `_normal.png`, `_roughness.png`, plus `_metallic.png`, `_alpha.png`, `_emission.png` when spatially varying).

Read [pbr-textures-and-official-variants.md](./references/pbr-textures-and-official-variants.md) and use [pbr_texture_pipeline.py](./scripts/pbr_texture_pipeline.py):
1. **AI Base Swatches (`image-generator`)**: Request **flat, orthographic, top-down 1:1 square** swatches (`NO folds, NO curvature, NO directional shadows, NO vignette`) + pixel-aligned height maps for organic/woven/grained surfaces.
2. **Deterministic Vector/Raster Typography, Dials & Badges**: **Never** use diffusion AI or `make_seamless` for engraved numerals, shutter/watch dials, technical scales, keyboard legends, or logos. Rasterize crisp `2048–4096 px` planar/polar masks (`PIL.ImageDraw` / SVG) via `composite_engraved_markings()` in `scripts/pbr_texture_pipeline.py` to emit pixel-registered `_albedo`, recessed/embossed 16-bit `_bump`, `_normal`, `_roughness`, and `_metallic` (`0.0` enamel/ink vs. `1.0` bare metal).
3. **Seamless Tiling by Symmetry**: Toroidal crossfade (`make_seamless`) for stochastic grain/weaves; single-axis mirror (`make_seamless_wave_2x2`) for sinusoidal waves; narrow border feather (`periodic_edge_feather`) for periodic checks/twills.
4. **Physical Millimeter UV Calibration**: Bake metric UVs (`uv = coords / L_uv`) or pre-tile seamless maps so yarn/pebble/knurl/grain pitch matches real-world millimeters without relying on `ShaderNodeMapping`.
5. **Highlight-Safe Variant Recoloring**: Use `recolor_swatch()` (standardized `tanh` z-score) or `recolor_two_tone()` so brightening dark base swatches into chalk-white/silver variants (`<= 0.985`) never clips highlights.
6. **Stage 4 Gate**: Build and inspect (`read_file`) a swatch contact sheet (`build_swatch_contact_sheet`) of all variant maps **before** launching Cycles renders.

---

## Stage 5: Blender MCP Contract, Scale-Matched Studio Rig & Two-State Export

### Critical Blender MCP & Exporter Rules (Low Freedom — Follow Exactly)

1. **Blender MCP `user_prompt` & Dynamic Enum Hygiene**:
   - Pass the user's **exact verbatim prompt** in `user_prompt` on every `execute_blender_code`, `get_scene_info`, and `look` call.
   - Look up default shader nodes by `n.type == "BSDF_PRINCIPLED"`, never localized names; assign explicit `.name` strings to nodes you create.
   - Use `from mathutils import Euler; Euler((rx, ry, rz), "XYZ").to_matrix()` (`Matrix.Euler` does not exist).
   - Wrap render engine/GPU device selection (`OPTIX` -> `CUDA` -> `HIP` -> `METAL` -> `CPU`) and `view_transform` assignment in `try/except` so headless or localized setups never crash.
2. **Scale-Matched Studio Camera & Lighting (`R_bbox` Parameterization)**:
   - Set **`cam.clip_start = max(0.0005, 0.004 * R_bbox)`** and **`cam.clip_end = max(50.0, 40.0 * R_bbox)`** (default `0.1 m` slices macro cameras/watches; default `100 m` clips architectural elevations!).
   - Place soft area lights at `2.5–4.0 * R_bbox` with power scaled `∝ R_bbox²` (plus white specular bounce cards for metals/glass/leather) and `transmission_bounces >= 8` when glass/acrylic is present.
   - Adjust per-variant exposure (`-0.50..-0.65` on chalk-white/bright-silver variants vs. `-0.15` default) so highlights never blow out.
3. **Two-State Material Wiring for `.obj`/`.mtl` AND `.glb`**:
   - Neither `wm.obj_export` nor `export_scene.gltf` traverses `ShaderNodeBump` or math/mix nodes!
   - *State A (Cycles Render)*: Rich Cycles graph (`LayerWeight` sheen/rim, `NormalMap -> BumpNode -> BSDF["Normal"]`, refractive glass `Transmission Weight = 1.0, Alpha = 1.0`).
   - *State B (Export)*: Before exporting, call `img.reload()` on updated images, unhide all `Asset_Parts` meshes (`obj.hide_set(False); obj.hide_viewport = False`), temporarily wire **direct** `TexImage` links to `Base Color`, `Roughness`, `NormalMap -> BSDF["Normal"]` (plus `Metallic`, `Alpha`, `Emission Color` when textured), and set transmissive glass to `Alpha = 0.18–0.25` (`BLEND`) so `.mtl` writes `d 0.20` instead of opaque white plaster `d 1.0`! Restore State A immediately after export.
   - Use `export_image_format="AUTO"` (never `"JPEG"`, which strips alpha and adds `4:2:0` DCT block artifacts to tangent-space normal maps) and `export_tangents=False` on dense (`>200k` face) meshes.
4. **Self-Contained Per-Variant Deliverable Structure**:
   Copy any shared sub-part textures into `<variant_dir>/textures/` before `wm.obj_export(..., path_mode="RELATIVE")`:
   ```text
   variants/<NN_variant_slug>/
   ├── <asset>_<NN_variant_slug>.obj
   ├── <asset>_<NN_variant_slug>.mtl          # Local `textures/...` with map_Kd, map_Pr, map_Bump (+ map_Pm/map_d/map_Ke)
   ├── <asset>_<NN_variant_slug>.glb          # Self-contained binary glTF 2.0 (Y-up, embedded lossless normals)
   ├── textures/                              # Complete local PBR texture set for this variant
   └── renders/
       ├── 01_hero_3quarter.png               # 1600x900+ balanced 3/4 hero studio render
       ├── 02_front_elevation.png             # Clean long-lens elevation
       └── 03_closeup_detail.png              # Macro shot of material relief, markings & hardware
   ```
5. **RPC Timeout Prevention (`< 120s` per call)**: Set `scene.render.use_persistent_data = True` and process `1` variant (or split `mode="render"` and `mode="export"`) per `execute_blender_code` call. Remove `.blend1` backups when saving `.blend`.

---

## Stage 6: Automated Verification & Visual Catalog Handoff

Run [verify_3d_deliverables.py](./scripts/verify_3d_deliverables.py) with expected metric dimensions `(W, D, H)` (Blender Z-up `(X, Y, Z)` maps to glTF Y-up `(X, Z_up=H, D)` automatically inside the validator!) and visually inspect renders via `read_file`:

```bash
python3 <skill_dir>/scripts/verify_3d_deliverables.py \
  --variants-dir ./variants \
  --refs-dir ./official_references \
  --expected-dims W,D,H
```

When presenting a visual catalog artifact in `<appDataDir>/brain/<conversation-id>/`, copy all embedded render/reference images into that artifact directory first and link every `.obj`, `.glb`, and render using clickable `file://` links.

---

## Common Rationalizations & Red Flags — STOP Immediately

| Rationalization / Red Flag | Reality & Required Action |
|---|---|
| *"Keep it fast — I'll invent plausible 'Dark / Nordic Edition' variants instead of searching."* | Fake SKUs fail authenticity. Run `search_web`, verify real manufacturer lines/editions, and populate `official_references/`. |
| *"I wired `ShaderNodeBump` to `BSDF['Normal']`, so bump maps will export."* | Blender's `.obj` and `.glb` exporters ignore `ShaderNodeBump`. Wire `TexImage(Non-Color) -> ShaderNodeNormalMap -> BSDF['Normal']` during export. |
| *"Glass has `Transmission Weight = 1.0`, so `.obj` and `.glb` viewers will show clear glass."* | With `Alpha = 1.0`, `.mtl` writes `d 1.0` (opaque plaster!). Drop export-state glass `Alpha` to `0.18–0.25` (`BLEND`), then restore `1.0` for Cycles. |
| *"I'll ask `image-generator` for the dial numbers / brand logo."* | Diffusion models hallucinate gibberish glyphs. Rasterize dials/scales/logos deterministically (`PIL.ImageDraw` / SVG) via `composite_engraved_markings()`. |
| *"Default camera `clip_start = 0.1 m` and `export_image_format='JPEG'` are fine."* | `0.1 m` slices off `<30 cm` macro products, and JPEG strips alpha + corrupts normal maps. Scale `clip_start` to `0.004 * R_bbox` and use `"AUTO"`. |
| *"I'll push strap/cord points whenever `(p - loc_n).dot(nrm_n) < min_d`."* | Without a Euclidean distance guard `(p - loc_n).length < min_d`, distant normals teleport cords into mid-air. Gate by Euclidean proximity + ribbon width. |

---

## Bundled References & Reusable Scripts (Load On-Demand)

- **Geometry, Scale-Matched Assemblies & Optics Recipes**: [geometry-and-assembly-patterns.md](./references/geometry-and-assembly-patterns.md)
- **Official Variant Research, Markings & Two-State PBR Wiring**: [pbr-textures-and-official-variants.md](./references/pbr-textures-and-official-variants.md)
- **Seamless PBR, Recoloring, Engraved Markings & Swatch Sheet**: [pbr_texture_pipeline.py](./scripts/pbr_texture_pipeline.py)
- **Automated Geometry Bounds, `.obj`/`.mtl`/`.glb` & Render Validator**: [verify_3d_deliverables.py](./scripts/verify_3d_deliverables.py)

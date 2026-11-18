# Official Variant Research, Crisp Markings, AI PBR Swatches & Exporter Wiring

## Contents
1. Official Variant & Reference Archive Protocol (`official_references/`)
2. Prompting `image-generator` for Orthographic PBR Base Swatches
3. Deterministic Engraved Typography, Radial Dials, Scales & Badges
4. Seamless Tiling: Stochastic vs. Wave vs. Periodic Grid
5. Physical Millimeter UV Scale Calibration
6. Highlight-Safe `tanh` Z-Score & Two-Tone Variant Recoloring
7. Material-Class Principled BSDF & Studio Exposure Presets
8. Blender 5.x Full Two-State Shader Wiring (`.obj`/`.mtl` + `.glb` + Glass + Cycles)

---

## 1. Official Variant & Reference Archive Protocol (`official_references/`)

Whenever building a real-world product or multi-variant collection:
1. Query `search_web` for official manufacturer material lines, surface grades, SKU/RAL/Pantone/dye codes, limited/collaborative editions, multi-material modular rules, and standard structural hardware finishes.
2. Populate `official_references/`:
   - `images/`: Polite HTTP GET downloads of public studio/macro photos (`>= 250 px`, MD5-deduplicated). **Visually inspect downloaded images (`read_file`)** and delete off-topic site banners, nav icons, or unrelated products. **Never** solve, click through, or bypass CAPTCHAs/Cloudflare challenges—skip gated URLs cleanly.
   - `README.md`: Table mapping official material grades, compositions, finish codes, special editions, hardware specs, and direct source URLs to modeled variant slugs.
   - `sources_manifest.json`: Resolved source URLs and image metadata.

---

## 2. Prompting `image-generator` for Orthographic PBR Base Swatches

Generate **1 flat orthographic base swatch per organic/woven/grained material archetype** (never perspective/curved/shadowed photos) and derive colorways in Python:

- **Albedo Prompt**:
  > *"Flat, orthographic, top-down 1:1 square diffuse PBR material swatch of [exact material, e.g., pebbled camera vulcanite leatherette / brushed anodized aluminum / heavy 3D looped bouclé / open-pore American walnut / sinusoidal jacquard monogram], evenly flat-lit studio illumination, NO folds, NO curvature, NO directional shadows, NO vignette, edge-to-edge macro texture."*
- **Pixel-Aligned Height/Bump Prompt**:
  > *"Pixel-aligned 1:1 neutral grayscale height/bump map centered near 50% gray matching `<albedo_name>`, where raised [threads/pebbles/ribs/grain] are bright and recessed [crevices/pores/grooves] are dark, flat orthographic top-down."*

If `image-generator` fails transiently on straight ribs/flutes/corduroy wales, modulate an AI micro-fiber/metal swatch with exact analytical `cos` rib profiles in NumPy so ribs remain 100% straight across UV seams.

---

## 3. Deterministic Engraved Typography, Radial Dials, Scales & Badges

**Never** prompt diffusion models for technical numerals, shutter/watch dials, lens focal engravings, keyboard legends, or brand wordmarks—they hallucinate crooked gibberish—and **never** run `make_seamless` over text!

Instead:
1. Render crisp `2048–4096 px` planar or polar masks using `PIL.ImageDraw` / `cairosvg` (supporting multi-color paint fills, e.g., white dial stops + red index).
2. Call `composite_engraved_markings()` in `scripts/pbr_texture_pipeline.py` over a seamless base metal/polymer/wood swatch to emit **pixel-registered**:
   - `_albedo.png` (base finish + crisp multi-color ink/enamel/gold fills),
   - 16-bit `_bump.png` & `_normal.png` (recessed `-depth` engraving troughs or `+depth` raised badges),
   - `_roughness.png` (matte/satin paint fill vs. brushed/polished base),
   - `_metallic.png` (`0.0` dielectric paint/enamel ink vs. `1.0` bare metal—essential so paint-filled metal dials don't render as colored chrome!).

---

## 4. Seamless Tiling: Stochastic vs. Wave vs. Periodic Grid

| Pattern Class | Examples | Seamless Function (`pbr_texture_pipeline.py`) | Why |
|---|---|---|---|
| **Stochastic / Isotropic** | Velvet, bouclé, canvas, leather, powder-coat, stone, wood | `make_seamless(arr)` | Toroidal raised-cosine crossfade eliminates 100% of border cliffs in Sobel normals |
| **Sinusoidal / Directional Wave** | S-Wave monograms, wavy weaves, vertical guilloché | `make_seamless_wave_2x2(arr)` | `0.0 px` X-mirror continuity + Y feather avoids 4-way butterfly kaleidoscopes |
| **Strict Wallpaper Grid** | Asymmetric checks, herringbone, diagonal twill | `periodic_edge_feather(arr, pad=10)` | Preserves directional weave orientation without mirroring |

---

## 5. Physical Millimeter UV Scale Calibration

1. Measure `L_uv` = real-world meters covered by `[0, 1]` UV on each part (e.g., `0.048 m` on a camera body wrap, `0.22 m` on a sofa seat, `0.80 m` on a car door).
2. Count `N_raw` = features across the `1024 px` swatch and compare `L_uv / N_raw` against real-world feature pitch `p_real` (`1.1 mm` camera leatherette pebble, `1.5–3.0 mm` woven yarn, `4.2 mm` jumbo corduroy wale, `32 mm` jacquard wave).
3. Bake scale directly into mesh UVs (`uv = metric_coords / L_uv`) **or** pre-tile (`tile_and_resize(arr, reps=...)`) so `.obj` viewers that ignore `.mtl -s` display true millimeter scale.

---

## 6. Highlight-Safe `tanh` Z-Score & Two-Tone Variant Recoloring

- **Single-Hue Recoloring (`recolor_swatch`)**: Standardizes luminance via inter-percentile z-score `z = (L - P50) / (P92 - P08)` bounded via `tanh` (`<= 0.985`) so lightening dark swatches into Chalk White (`#EBE7E0`) never clips highlights to `1.0` salt-and-pepper white.
- **Two-Tone Jacquards/Prints (`recolor_two_tone`)**: Maps normalized luminance `t ∈ [0, 1]` cleanly between `dark_hex` motif and `light_hex` ground while preserving `(bump - 0.5)` micro-yarn relief.

---

## 7. Material-Class Principled BSDF & Studio Exposure Presets

| Surface Archetype | Roughness Base | Metallic | Sheen Weight | Specular / IOR | Cycles Exposure Note |
|---|---|---|---|---|---|
| **Velvet / Chenille / High-Pile** | `0.74–0.80` | `0.0` | `0.54–0.60` (`LayerWeight` rim) | `Spec = 0.09` | `-0.15` (`-0.58` on chalk white) |
| **Bouclé / Heavy Looped Weave** | `0.78–0.84` | `0.0` | `0.38–0.45` | `Spec = 0.11` | `-0.15` (`-0.55` on white) |
| **Tailored Canvas / Jacquard / Strap** | `0.66–0.74` | `0.0` | `0.24–0.32` (macro noise `<=0.04`) | `Spec = 0.14` | `-0.25..-0.32` on ecru grounds |
| **Full-Grain Leather / Leatherette** | `0.34–0.44` (`+0.20` pores) | `0.0` | **`0.0`** (no cloth sheen!) | `Spec = 0.44` | `-0.15` |
| **Satin Hardwood / Veneer** | `0.26–0.34` | `0.0` | `0.0` | `Spec = 0.38` | `-0.15` |
| **Satin Silver / Brushed Aluminum** | `0.18–0.26` | `1.0` | `0.0` | `Spec = 0.50` | `-0.35` + white bounce cards |
| **Black Chrome / Anodized Metal** | `0.22–0.30` | `1.0` | `0.0` | `Base ~ (0.07, 0.07, 0.075)` | `-0.12` + rim card |
| **Gloss Black Paint / Automotive** | `0.05–0.08` | `0.0` (`Coat = 1.0`) | `0.0` | `Spec = 0.50` | Add overhead softbox strip |
| **Polished Chrome / Brass / Gold** | `0.045–0.065` | `1.0` | `0.0` | Brass `(0.955, 0.92, 0.84)` | Add bounce cards |
| **Optical Glass / Clear PMMA** | `0.01–0.03` | `0.0` | `0.0` | `IOR = 1.49–1.77`, `Trans = 1.0` | `transmission_bounces >= 8` |

---

## 8. Blender 5.x Full Two-State Shader Wiring (`.obj`/`.mtl` + `.glb` + Glass + Cycles)

```python
# 1) STATE A — Cycles Studio Render (Fresnel rim + BumpNode + pure refractive Alpha=1.0 glass)
for gmat in glass_mats:
    next(n for n in gmat.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Alpha"].default_value = 1.0
bpy.ops.render.render(write_still=True)

# 2) STATE B — Direct Exporter Links BEFORE wm.obj_export & export_scene.gltf!
for mat, prefix in textured_mats:
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    nt.links.new(nt.nodes[f"Tex_{prefix}_Albedo"].outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(nt.nodes[f"Tex_{prefix}_Roughness"].outputs["Color"], bsdf.inputs["Roughness"])
    nt.links.new(nt.nodes[f"{prefix}_NormalMap"].outputs["Normal"], bsdf.inputs["Normal"])  # NOT ShaderNodeBump!
    if f"Tex_{prefix}_Metallic" in nt.nodes:
        nt.links.new(nt.nodes[f"Tex_{prefix}_Metallic"].outputs["Color"], bsdf.inputs["Metallic"])
    if f"Tex_{prefix}_Alpha" in nt.nodes:
        nt.links.new(nt.nodes[f"Tex_{prefix}_Alpha"].outputs["Color"], bsdf.inputs["Alpha"])
    if f"Tex_{prefix}_Emission" in nt.nodes and "Emission Color" in bsdf.inputs:
        nt.links.new(nt.nodes[f"Tex_{prefix}_Emission"].outputs["Color"], bsdf.inputs["Emission Color"])

# Prevent `.mtl` `d 1.0` opaque white plaster bug on glass/acrylic!
for gmat in glass_mats:
    next(n for n in gmat.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Alpha"].default_value = 0.20
    if hasattr(gmat, "surface_render_method"):
        gmat.surface_render_method = "BLENDED"

bpy.ops.object.select_all(action="DESELECT")
for obj in bpy.data.collections["Asset_Parts"].objects:
    if obj.type == "MESH":
        obj.hide_set(False)
        obj.hide_viewport = False
        obj.select_set(True)

bpy.ops.wm.obj_export(
    filepath=obj_path,
    check_existing=False,
    export_selected_objects=True,
    apply_modifiers=True,
    apply_transform=True,
    export_uv=True,
    export_normals=True,
    export_materials=True,
    export_pbr_extensions=True,
    path_mode="RELATIVE",
    export_triangulated_mesh=False,
)

bpy.ops.export_scene.gltf(
    filepath=glb_path,
    check_existing=False,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_texcoords=True,
    export_normals=True,
    export_tangents=False,       # Avoids single-threaded MikkTSpace stall on >200k-face meshes
    export_materials="EXPORT",
    export_image_format="AUTO",  # Lossless PNG normals & alpha (never "JPEG"!)
    export_yup=True,
)
```

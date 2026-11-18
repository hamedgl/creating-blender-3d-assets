# creating-blender-3d-assets

An agent skill for creating **museum-grade, physically grounded 3D assets and official multi-variant collections in Blender**—engineered for any object class and scale (`18 mm` watches/jewelry, `14 cm` cameras/electronics, `3 m` furniture, `4.8 m` vehicles, `25 m` architectural fixtures) with calibrated PBR textures, authentic manufacturer SKUs, studio Cycles renders, and self-contained `.obj`/`.mtl` + `.glb` deliverables.

Compatible with **Antigravity**, **Claude Code**, **Gemini CLI**, **Cursor**, **Codex**, **GitHub Copilot**, and any agent supporting the [Agent Skills (`skills.sh`)](https://skills.sh/) standard.

---

## Installation (`npx skills`)

### Quick Install (Interactive)

```bash
npx skills add hamedgl/creating-blender-3d-assets
```

### Global Install (Available Across All Projects)

```bash
npx skills add hamedgl/creating-blender-3d-assets -g
```

### Non-Interactive / Install to Specific Agents

```bash
# Install to all detected agents without prompts
npx skills add hamedgl/creating-blender-3d-assets --all

# Install to specific agents (e.g., antigravity, claude-code, gemini-cli, cursor, codex)
npx skills add hamedgl/creating-blender-3d-assets -g -a antigravity claude-code gemini-cli cursor -y

# Inspect available skills before installing
npx skills add hamedgl/creating-blender-3d-assets --list

# One-shot prompt generation without installing
npx skills use hamedgl/creating-blender-3d-assets@creating-blender-3d-assets
```

### Updating or Removing

```bash
npx skills update creating-blender-3d-assets
npx skills remove creating-blender-3d-assets -g
```

### Manual Clone (Antigravity / `.agents` Workspace Fallback)

```bash
git clone https://github.com/hamedgl/creating-blender-3d-assets.git /tmp/creating-blender-3d-assets
cp -r /tmp/creating-blender-3d-assets/skills/creating-blender-3d-assets ./.agents/skills/
```

---

## What This Skill Enforces

1. **6-Stage Gated 3D Production Pipeline**:
   - **Stage 1 — Reference & Official SKU Lock**: Metric dimensions (`1 BU = 1.0 m`), component ratios, and `search_web` verification of real manufacturer material grades, color palettes, special editions, and invariant structural hardware (`official_references/README.md` + reference image archive).
   - **Stage 2 — Proportions, Pure-Quad Topology & Grounding Gate**: Vectorized `numpy` + `foreach_set` mesh builders, non-Boolean slot grids, curved multi-element meniscus optics, and strict `z_min == 0.000 m` grounding verified via viewport gates.
   - **Stage 3 — Scale-Parameterized Clearances & Zero-Penetration Assemblies**: Bounding-diagonal (`R_bbox`) parting gaps, analytical `0.0 mm` saddle-contact linked hardware, soft-body `Cloth` inflation, and Euclidean-gated `BVHTree` cord/flat-strap surface routing.
   - **Stage 4 — Calibrated PBR Maps & Deterministic Markings**: Orthographic AI base swatches, toroidal vs. wave vs. periodic seamless tiling, highlight-safe `tanh` z-score recoloring (`<= 0.985`, zero whiteout clipping), `composite_engraved_markings()` for crisp polar/planar dials & logos, and mandatory pre-render swatch contact sheets.
   - **Stage 5 — Scale-Matched Studio Rig & Two-State Dual Export**: Auto-scaled `Camera.clip_start` / `clip_end`, inverse-square studio lighting, and **Two-State Principled BSDF Wiring** so both Cycles renders and exported `.obj`/`.mtl` (`map_Kd`, `map_Pr`, `map_Pm`, `map_Bump`, glass `d 0.20`) + `.glb` (`normalTexture`, lossless `"AUTO"` images) retain full PBR fidelity without `3m0s` MCP timeouts.
   - **Stage 6 — Automated Deliverable Validation**: Executable `assert`-based validator checking `.obj`, `.mtl` local relative paths, `.glb` v2 binary headers, world-space metric `POSITION` bounds & grounding, and studio `.png` renders.

---

## Repository Structure

```text
creating-blender-3d-assets/
├── README.md
├── LICENSE
└── skills/
    └── creating-blender-3d-assets/
        ├── SKILL.md                                     # Core 6-stage workflow, exporter rules & red-flag counters
        ├── references/
        │   ├── geometry-and-assembly-patterns.md        # Scale-matched CAD, optics, pure-quads & BVHTree routing
        │   └── pbr-textures-and-official-variants.md    # Official SKU research, markings, PBR math & BSDF presets
        └── scripts/
            ├── pbr_texture_pipeline.py                  # Seamless PBR, tanh recoloring, engraved dials & swatch sheets
            └── verify_3d_deliverables.py                # CLI validator for .obj/.mtl/.glb, metric bounds & renders
```

---

## Bundled CLI Utilities

```bash
# Run built-in PBR math & highlight non-clipping assertions
python3 skills/creating-blender-3d-assets/scripts/pbr_texture_pipeline.py --self-test

# Validate an exported multi-variant 3D collection (.obj + .mtl + .glb + renders + bounds)
python3 skills/creating-blender-3d-assets/scripts/verify_3d_deliverables.py \
  --variants-dir ./variants \
  --refs-dir ./official_references \
  --expected-dims 3.84,1.95,0.71
```

---

## License

MIT

#!/usr/bin/env python3
"""
Reusable PBR Texture Synthesis, Seamless Tiling, Highlight-Safe Recoloring, Engraved Markings & Swatch Sheet Utility.
Works across all 3D object classes: textiles, leathers, woods, brushed/plated metals, dials/scales, polymers, jacquards.
"""
import argparse
import os
import numpy as np
from PIL import Image


def load_rgb(path: str, size: int = 1024) -> np.ndarray:
    im = Image.open(path).convert("RGB")
    if im.size != (size, size):
        im = im.resize((size, size), Image.Resampling.LANCZOS)
    return np.asarray(im, dtype=np.float32) / 255.0


def load_gray(path: str, size: int = 1024) -> np.ndarray:
    im = Image.open(path).convert("L")
    if im.size != (size, size):
        im = im.resize((size, size), Image.Resampling.LANCZOS)
    return np.asarray(im, dtype=np.float32) / 255.0


def make_seamless(arr: np.ndarray) -> np.ndarray:
    """Raised-cosine toroidal blend for stochastic textures (weaves, leather, wood, metal, stone)."""
    h, w = arr.shape[:2]
    u = np.linspace(0.0, 1.0, w, endpoint=False, dtype=np.float32)
    v = np.linspace(0.0, 1.0, h, endpoint=False, dtype=np.float32)
    wx = 0.5 - 0.5 * np.cos(2.0 * np.pi * u)
    wy = 0.5 - 0.5 * np.cos(2.0 * np.pi * v)
    w2 = np.clip((wy[:, None] * wx[None, :] - 0.12) / 0.76, 0.0, 1.0)
    w2 = w2 * w2 * (3.0 - 2.0 * w2)

    s_xy = np.roll(np.roll(arr, h // 2, axis=0), w // 2, axis=1)
    s_x = np.roll(arr, w // 2, axis=1)
    s_y = np.roll(arr, h // 2, axis=0)

    bx, by = wx[None, :], wy[:, None]
    if arr.ndim == 3:
        bx, by, w2 = bx[..., None], by[..., None], w2[..., None]
    base_shift = (1.0 - by) * ((1.0 - bx) * s_xy + bx * s_y) + by * ((1.0 - bx) * s_x + bx * arr)
    return w2 * arr + (1.0 - w2) * base_shift


def periodic_edge_feather(arr: np.ndarray, pad: int = 12) -> np.ndarray:
    """Narrow opposite-edge feather for already-periodic wallpaper/check/herringbone patterns."""
    out = arr.copy()
    t = np.linspace(0.0, 0.5, pad, dtype=np.float32)
    tx = t[None, :, None] if arr.ndim == 3 else t[None, :]
    ty = t[:, None, None] if arr.ndim == 3 else t[:, None]
    out[:, :pad] = (0.5 + tx) * out[:, :pad] + (0.5 - tx) * out[:, -pad:]
    out[:, -pad:] = (0.5 + tx[:, ::-1]) * out[:, -pad:] + (0.5 - tx[:, ::-1]) * out[:, :pad]
    out[:pad, :] = (0.5 + ty) * out[:pad, :] + (0.5 - ty) * out[-pad:, :]
    out[-pad:, :] = (0.5 + ty[::-1, :]) * out[-pad:, :] + (0.5 - ty[::-1, :]) * out[:pad, :]
    return out


def make_seamless_wave_2x2(arr: np.ndarray, out_size: int = 1536, pad_y: int = 10) -> np.ndarray:
    """Mirror X (0px horizontal jump) + feather Y repeat for sinusoidal waves without butterfly diamonds."""
    a = arr.copy()
    ty = np.linspace(0.0, 0.5, pad_y, dtype=np.float32)
    ty = ty[:, None, None] if a.ndim == 3 else ty[:, None]
    a[:pad_y] = (0.5 + ty) * a[:pad_y] + (0.5 - ty) * a[-pad_y:]
    a[-pad_y:] = (0.5 + ty[::-1]) * a[-pad_y:] + (0.5 - ty[::-1]) * a[:pad_y]
    row = np.concatenate([a, a[:, ::-1]], axis=1)
    full = np.concatenate([row, row], axis=0)
    return tile_and_resize(full, reps=1, out_size=out_size)


def tile_and_resize(arr: np.ndarray, reps: int = 1, out_size: int = 1536) -> np.ndarray:
    if reps > 1:
        arr = np.tile(arr, (reps, reps, 1) if arr.ndim == 3 else (reps, reps))
    if arr.shape[0] == out_size and arr.shape[1] == out_size:
        return arr
    if arr.ndim == 3:
        im = Image.fromarray(np.clip(arr * 255.0, 0, 255).astype(np.uint8))
        return np.asarray(im.resize((out_size, out_size), Image.Resampling.LANCZOS), dtype=np.float32) / 255.0
    im = Image.fromarray(np.clip(arr * 65535.0, 0, 65535).astype(np.uint16))
    return np.asarray(im.resize((out_size, out_size), Image.Resampling.BILINEAR), dtype=np.float32) / 65535.0


def hex_to_rgb(hx: str) -> np.ndarray:
    hx = hx.lstrip("#")
    return np.array([int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)], dtype=np.float32) / 255.0


def recolor_swatch(rgb: np.ndarray, target_hex: str, contrast: float = 1.0) -> np.ndarray:
    """Highlight-safe standardized tanh z-score recoloring (strictly <= 0.985; never clips chalk/white)."""
    tgt = hex_to_rgb(target_hex)
    lum = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    p08, p50, p92 = np.percentile(lum, [8.0, 50.0, 92.0])
    z = (lum - p50) / max(p92 - p08, 0.06)
    max_up = max(min(0.32 * contrast, (0.945 / max(float(np.max(tgt)), 0.15)) - 1.0), 0.05)
    mod = np.where(z >= 0.0, 1.0 + max_up * np.tanh(z * 1.15), 1.0 + (0.34 * contrast) * np.tanh(z * 1.15))
    mean_c = np.mean(rgb, axis=(0, 1), keepdims=True) + 1e-6
    chroma = np.clip(rgb / mean_c, 0.92, 1.08)
    chroma /= np.mean(chroma, axis=-1, keepdims=True) + 1e-6
    return np.clip(tgt[None, None, :] * mod[..., None] * (0.82 + 0.18 * chroma), 0.0, 1.0)


def recolor_two_tone(rgb: np.ndarray, bump: np.ndarray, dark_hex: str, light_hex: str) -> np.ndarray:
    """Two-tone jacquard/print recoloring mapping dark motif -> dark_hex and light ground -> light_hex."""
    lum = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    lo, hi = np.percentile(lum, [5.0, 95.0])
    t = np.clip((lum - lo) / max(hi - lo, 1e-4), 0.0, 1.0)[..., None]
    c_dark, c_light = hex_to_rgb(dark_hex), hex_to_rgb(light_hex)
    micro = np.clip((bump - 0.5) * 0.22 + 1.0, 0.86, 1.14)[..., None]
    return np.clip(((1.0 - t) * c_dark + t * c_light) * micro, 0.0, 1.0)


def composite_engraved_markings(
    base_albedo: np.ndarray,
    base_bump: np.ndarray,
    color_masks: list[tuple[np.ndarray, str]],
    engrave_delta: float = -0.35,
    base_metallic: float = 1.0,
    ink_metallic: float = 0.0,
    base_roughness: float = 0.24,
    ink_roughness: float = 0.44,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Composite crisp deterministic vector/raster markings (dials, scales, serials, badges) onto a base material.
    `color_masks`: list of `(mask_float_0_to_1, hex_color)` pairs.
    Returns `(albedo, bump, roughness, metallic)` pixel-registered arrays.
    """
    alb = base_albedo.copy()
    total_mask = np.zeros(base_bump.shape, dtype=np.float32)
    for m, hx in color_masks:
        mc = np.clip(m, 0.0, 1.0)
        c_rgb = hex_to_rgb(hx)
        alb = alb * (1.0 - mc[..., None]) + c_rgb[None, None, :] * mc[..., None]
        total_mask = np.maximum(total_mask, mc)
    bmp = np.clip(base_bump + engrave_delta * total_mask, 0.0, 1.0)
    rgh = np.clip(base_roughness * (1.0 - total_mask) + ink_roughness * total_mask + 0.06 * (0.5 - base_bump), 0.04, 0.98)
    met = np.clip(base_metallic * (1.0 - total_mask) + ink_metallic * total_mask, 0.0, 1.0)
    return np.clip(alb, 0.0, 1.0), bmp, rgh, met


def height_to_normal(height: np.ndarray, strength: float = 2.8) -> np.ndarray:
    """Toroidal 3x3 Sobel height-to-OpenGL-tangent-space normal map (+Y up)."""
    gx = (
        -1.0 * np.roll(np.roll(height, 1, 0), 1, 1)
        - 2.0 * np.roll(height, 1, 1)
        - 1.0 * np.roll(np.roll(height, -1, 0), 1, 1)
        + 1.0 * np.roll(np.roll(height, 1, 0), -1, 1)
        + 2.0 * np.roll(height, -1, 1)
        + 1.0 * np.roll(np.roll(height, -1, 0), -1, 1)
    ) * 0.125
    gy = (
        -1.0 * np.roll(np.roll(height, 1, 0), 1, 1)
        - 2.0 * np.roll(height, 1, 0)
        - 1.0 * np.roll(np.roll(height, 1, 0), -1, 1)
        + 1.0 * np.roll(np.roll(height, -1, 0), 1, 1)
        + 2.0 * np.roll(height, -1, 0)
        + 1.0 * np.roll(np.roll(height, -1, 0), -1, 1)
    ) * 0.125
    nx, ny, nz = -gx * strength, gy * strength, np.ones_like(height)
    inv_len = 1.0 / np.sqrt(nx * nx + ny * ny + nz * nz + 1e-12)
    return np.clip(np.stack([nx * inv_len * 0.5 + 0.5, ny * inv_len * 0.5 + 0.5, nz * inv_len * 0.5 + 0.5], axis=-1), 0.0, 1.0)


def save_pbr_suite(
    out_dir: str,
    prefix: str,
    albedo: np.ndarray,
    bump: np.ndarray,
    nrm_strength: float = 2.8,
    rgh_base: float = 0.75,
    rgh_cavity_span: float = 0.18,
    roughness_map: np.ndarray | None = None,
    metallic_map: np.ndarray | None = None,
) -> None:
    os.makedirs(out_dir, exist_ok=True)
    lo, hi = np.percentile(bump, [1.0, 99.0])
    h_norm = np.clip((bump - lo) / max(hi - lo, 1e-4), 0.0, 1.0)
    nrm = height_to_normal(h_norm, strength=nrm_strength)
    rgh = roughness_map if roughness_map is not None else np.clip(rgh_base + rgh_cavity_span * (0.5 - h_norm), 0.04, 0.98)

    Image.fromarray(np.clip(albedo * 255.0, 0, 255).astype(np.uint8)).save(f"{out_dir}/{prefix}_albedo.png")
    Image.fromarray(np.clip(h_norm * 65535.0, 0, 65535).astype(np.uint16)).save(f"{out_dir}/{prefix}_bump.png")
    Image.fromarray(np.clip(nrm * 255.0, 0, 255).astype(np.uint8)).save(f"{out_dir}/{prefix}_normal.png")
    Image.fromarray(np.clip(rgh * 255.0, 0, 255).astype(np.uint8)).save(f"{out_dir}/{prefix}_roughness.png")
    if metallic_map is not None:
        Image.fromarray(np.clip(metallic_map * 255.0, 0, 255).astype(np.uint8)).save(f"{out_dir}/{prefix}_metallic.png")


def build_swatch_contact_sheet(albedo_paths: list[str], out_path: str, cols: int = 5, tile_px: int = 360) -> str:
    rows = (len(albedo_paths) + cols - 1) // cols
    grid = Image.new("RGB", (cols * tile_px, rows * tile_px))
    for i, p in enumerate(albedo_paths):
        im = Image.open(p).convert("RGB")
        w, h = im.size
        c0, c1 = int(w * 0.2), int(w * 0.8)
        crop = im.crop((c0, c0, c1, c1)).resize((tile_px, tile_px), Image.Resampling.LANCZOS)
        grid.paste(crop, ((i % cols) * tile_px, (i // cols) * tile_px))
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    grid.save(out_path, quality=92)
    return out_path


def _self_test() -> None:
    rng = np.random.default_rng(42)
    dark_swatch = np.clip(0.08 + 0.05 * rng.standard_normal((256, 256, 3)).astype(np.float32), 0.01, 0.35)
    seamless = make_seamless(dark_swatch)
    assert float(np.mean(np.abs(seamless[:, 0] - seamless[:, -1]))) < 0.05
    chalk = recolor_swatch(seamless, "#EBE7E0", contrast=1.0)
    assert float(np.mean(chalk >= 0.995)) == 0.0 and not np.isnan(chalk).any()

    # Engraved dial composite check (dielectric ink met=0.0 vs metal met=1.0)
    mask = np.zeros((256, 256), dtype=np.float32)
    mask[100:120, 80:180] = 1.0
    alb_e, bmp_e, rgh_e, met_e = composite_engraved_markings(seamless, np.full((256, 256), 0.5, dtype=np.float32), [(mask, "#F0EFEA")])
    assert float(met_e[110, 120]) == 0.0 and float(met_e[10, 10]) == 1.0 and float(bmp_e[110, 120]) < 0.25
    nrm = height_to_normal(bmp_e, strength=2.5)
    assert nrm.shape == (256, 256, 3) and 0.45 < float(np.mean(nrm[..., 0])) < 0.55
    print("pbr_texture_pipeline self-test PASSED!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PBR Texture Pipeline & Self-Test")
    parser.add_argument("--self-test", action="store_true", help="Run built-in unit assertions")
    args = parser.parse_args()
    if args.self_test:
        _self_test()

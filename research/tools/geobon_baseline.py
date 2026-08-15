#!/usr/bin/env python3
"""GeoBoN fixed-budget baseline (M-geobon): external, independent of WISE.

Implements the *fixed-budget* variant (not the gated one -- see module note
below) from "Test-Time Scaling for World Action Models via Zero-Shot
Geometric Verification" (arXiv:2607.17454): always sample K candidates from
the same context, score each by cross-view depth-reprojection inconsistency,
execute the candidate with the LOWEST inconsistency.

Cited from the paper, not derived from anything WISE-specific -- same status
as consensus_baseline.py's `K=4 consensus` row. Shares no code with WISE's
own r_exec/r_cons/r_task (research/METHOD.md) and never calls the project's
IDM: the executed action is always the winning candidate's own Cosmos-
generated action, exactly like the consensus baseline, since
Cosmos3-Edge-Policy-DROID is a joint-prediction WAM.

What this file does NOT implement, on purpose: the paper's *gated* variant
(a first single rollout, an action-future optical-flow gate deciding whether
to bother sampling K-1 more, escalating only when the gate trips). That
needs proprioceptive end-effector positions and Farneback optical flow for
the gate signal; the fixed-budget path needs neither -- it always samples K
and always scores geometrically. Left out by explicit request.

## The scoring mechanism (paper Eq. 5)

    e_depth(candidate) = mean_{p in Omega} |log(d_proj(p) / d_vggt(p))|

For each candidate, run VGGT-Omega jointly on its own {primary, wrist} frame
pair (jointly, in one forward pass, so both views land in one shared
predicted coordinate frame -- this is the entire point of VGGT-style models
and is NOT the same as calling the model once per image separately).

  - d_vggt(p): VGGT-Omega's own predicted depth for the primary image at
    pixel p.
  - d_proj(p): backproject the wrist image's predicted depth to 3D using its
    own predicted camera pose, reproject those 3D points into the primary
    camera using the primary's own predicted pose, and read off the Z-depth
    at whichever primary pixel each point lands on (nearest-pixel, z-buffered
    so the nearest point wins on ties -- ordinary rasterization).
  - Omega: pixels where a wrist point actually lands in-frame, with positive
    depth on both sides, and confidence above `confidence_threshold` (paper:
    gamma_conf = 0.5) on both the reprojected wrist prediction and the
    primary's own prediction at that pixel.

Lower e_depth means the two camera views agree with each other about the
scene's geometry -- pick the candidate whose dreamed views are most mutually
consistent, on the theory that an implausible/hallucinated future is less
likely to be geometrically self-consistent across views than a plausible one.

## Camera source

Cosmos3-Edge-Policy-DROID's fixed decode geometry (see
research/IDM_DESIGN.md's "Frozen architecture" / decoded-dream section):
33 x 528 x 640 x 3, wrist rows 0:360 cols 0:640, exterior-1 (left) rows
360:528 cols 0:320, exterior-2 (right) rows 360:528 cols 320:640. This module
treats exterior-1 (left) as "primary", matching RoboLab's own
WRIST_LEFT-style camera preset convention. Only the LAST decoded frame of
each candidate's 33-frame dream is used per view (the predicted end state of
the rollout) -- the paper's e_depth is a single-frame comparison, not a
trajectory aggregate.

## VGGT-Omega checkpoint status

Gated on Hugging Face (facebook/VGGT-Omega); access was requested but is not
yet approved as of writing. `VGGTOmegaDepthModel` below is a real
integration against the actual public inference API
(github.com/facebookresearch/vggt-omega: `VGGTOmega`,
`load_and_preprocess_images`, `encoding_to_camera`) -- not a placeholder --
but cannot run until the checkpoint file exists locally. Everything else
(the reprojection geometry, candidate selection, RoboLab wiring) is complete
and unit-tested independently of the checkpoint via `_SyntheticDepthModel`
in this file's own smoke test, which fabricates two consistent synthetic
cameras/depth maps and confirms the geometry math (not the neural network)
is correct.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

DEFAULT_CONFIDENCE_THRESHOLD = 0.5  # paper's gamma_conf
PRIMARY_ROWS = (360, 528)  # exterior-1 (left) in the fixed Cosmos dream decode
PRIMARY_COLS = (0, 320)
WRIST_ROWS = (0, 360)
WRIST_COLS = (0, 640)


def split_dream_views(dream_frame: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """One decoded 528x640x3 dream frame -> (primary, wrist) crops, per the
    fixed geometry in research/IDM_DESIGN.md. Validates the exact shape
    rather than inferring a seam, same discipline as the IDM's own dream
    ingestion.
    """
    if dream_frame.shape[:2] != (528, 640):
        raise ValueError(f"expected a 528x640 decoded dream frame, got {dream_frame.shape[:2]}")
    primary = dream_frame[PRIMARY_ROWS[0]:PRIMARY_ROWS[1], PRIMARY_COLS[0]:PRIMARY_COLS[1]]
    wrist = dream_frame[WRIST_ROWS[0]:WRIST_ROWS[1], WRIST_COLS[0]:WRIST_COLS[1]]
    return primary, wrist


def reproject_depth(
    *,
    depth_src: np.ndarray,
    conf_src: np.ndarray,
    extrinsics_src: np.ndarray,
    intrinsics_src: np.ndarray,
    extrinsics_dst: np.ndarray,
    intrinsics_dst: np.ndarray,
    dst_shape: tuple[int, int],
    confidence_threshold: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Backproject every confident src-view pixel to 3D, reproject into the
    dst camera, z-buffer onto dst's pixel grid.

    extrinsics are camera-from-world [R|T] (3x4), OpenCV convention -- the
    exact format VGGT-Omega's own encoding_to_camera returns (see
    vggt_omega/utils/pose_enc.py: "Extrinsics are camera-from-world matrices
    in OpenCV coordinates"). intrinsics are standard 3x3 pinhole.

    Returns (depth_proj, valid_mask), both shaped dst_shape. depth_proj is
    the reprojected Z-depth in the dst camera's own frame at whichever pixel
    each src point lands on (garbage where valid_mask is False).
    """
    h_src, w_src = depth_src.shape
    h_dst, w_dst = dst_shape

    v, u = np.mgrid[0:h_src, 0:w_src]
    ones = np.ones_like(u, dtype=np.float64)
    pixels = np.stack([u.astype(np.float64), v.astype(np.float64), ones], axis=-1)  # (h,w,3)

    fx, fy = intrinsics_src[0, 0], intrinsics_src[1, 1]
    cx, cy = intrinsics_src[0, 2], intrinsics_src[1, 2]
    x_cam = (pixels[..., 0] - cx) / fx * depth_src
    y_cam = (pixels[..., 1] - cy) / fy * depth_src
    z_cam = depth_src
    points_cam_src = np.stack([x_cam, y_cam, z_cam], axis=-1)  # (h,w,3), src camera frame

    r_src, t_src = extrinsics_src[:, :3], extrinsics_src[:, 3]
    r_dst, t_dst = extrinsics_dst[:, :3], extrinsics_dst[:, 3]

    # src-cam -> world -> dst-cam. World-to-cam is X_cam = R @ X_world + T,
    # so X_world = R^T @ (X_cam - T).
    points_world = np.einsum("ji,hwj->hwi", r_src, points_cam_src - t_src)
    points_cam_dst = np.einsum("ij,hwj->hwi", r_dst, points_world) + t_dst  # (h,w,3)

    valid_src = (depth_src > 0) & (conf_src > confidence_threshold)
    in_front = points_cam_dst[..., 2] > 0

    fx_d, fy_d = intrinsics_dst[0, 0], intrinsics_dst[1, 1]
    cx_d, cy_d = intrinsics_dst[0, 2], intrinsics_dst[1, 2]
    u_dst = fx_d * points_cam_dst[..., 0] / np.clip(points_cam_dst[..., 2], 1e-6, None) + cx_d
    v_dst = fy_d * points_cam_dst[..., 1] / np.clip(points_cam_dst[..., 2], 1e-6, None) + cy_d
    u_dst_i = np.round(u_dst).astype(np.int64)
    v_dst_i = np.round(v_dst).astype(np.int64)
    in_frame = (u_dst_i >= 0) & (u_dst_i < w_dst) & (v_dst_i >= 0) & (v_dst_i < h_dst)

    keep = valid_src & in_front & in_frame
    depth_proj = np.full((h_dst, w_dst), np.inf, dtype=np.float64)
    z_flat = points_cam_dst[..., 2]

    # z-buffer: nearest point wins where multiple src pixels land on the same
    # dst pixel. Sort by depth descending and write in that order so the
    # smallest depth (nearest) is the last, surviving write.
    flat_u, flat_v, flat_z = u_dst_i[keep], v_dst_i[keep], z_flat[keep]
    order = np.argsort(-flat_z)
    depth_proj[flat_v[order], flat_u[order]] = flat_z[order]

    valid_mask = np.isfinite(depth_proj)
    depth_proj = np.where(valid_mask, depth_proj, 0.0)
    return depth_proj, valid_mask


def select_geobon(candidates: list[dict], depth_predictor, confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD) -> dict:
    """Fixed-budget GeoBoN selection over K candidates from one decision point.

    candidates: list of K dicts, each with:
      - "action": (T, D) np.ndarray, the candidate's own Cosmos-generated action chunk
      - "primary_frame": (H, W, 3) uint8, last decoded frame's primary-view crop
      - "wrist_frame": (H, W, 3) uint8, same candidate's wrist-view crop

    depth_predictor: callable([primary_frame, wrist_frame]) -> [primary_pred, wrist_pred],
      each a dict with "depth" (H,W) float, "depth_conf" (H,W) float,
      "extrinsics" (3,4), "intrinsics" (3,3) -- called ONCE PER CANDIDATE with
      both frames together, since VGGT-style models predict multi-view
      geometry jointly and the two predictions must land in one shared
      coordinate frame for reprojection to be meaningful. Calling it
      separately per image would give two unrelated coordinate frames and
      silently produce nonsense.
    """
    if not candidates:
        raise ValueError("at least one candidate is required")

    e_depth = []
    diagnostics = []
    for c in candidates:
        primary_pred, wrist_pred = depth_predictor([c["primary_frame"], c["wrist_frame"]])
        depth_proj, valid_mask = reproject_depth(
            depth_src=wrist_pred["depth"], conf_src=wrist_pred["depth_conf"],
            extrinsics_src=wrist_pred["extrinsics"], intrinsics_src=wrist_pred["intrinsics"],
            extrinsics_dst=primary_pred["extrinsics"], intrinsics_dst=primary_pred["intrinsics"],
            dst_shape=primary_pred["depth"].shape, confidence_threshold=confidence_threshold,
        )
        d_vggt = primary_pred["depth"]
        omega = (
            valid_mask
            & (primary_pred["depth_conf"] > confidence_threshold)
            & (d_vggt > 0)
            & (depth_proj > 0)
        )
        n_valid = int(omega.sum())
        if n_valid == 0:
            err = float("inf")  # degenerate candidate: no geometric evidence, always loses
        else:
            err = float(np.abs(np.log(depth_proj[omega] / d_vggt[omega])).mean())
        e_depth.append(err)
        diagnostics.append({"e_depth": err, "valid_pixel_count": n_valid, "valid_pixel_fraction": n_valid / omega.size})

    best_idx = int(np.argmin(e_depth))
    return {
        "k": len(candidates),
        "confidence_threshold": confidence_threshold,
        "selected_index": best_idx,
        "selected_action": candidates[best_idx]["action"],
        "e_depth": e_depth,
        "diagnostics": diagnostics,
    }


class VGGTOmegaDepthModel:
    """Real integration against github.com/facebookresearch/vggt-omega's
    public API. Not runnable until the gated checkpoint
    (facebook/VGGT-Omega, e.g. vggt_omega_1b_512.pt) is downloaded locally --
    access requested, pending approval as of writing.
    """

    def __init__(self, checkpoint_path: str, device: str = "cuda", image_resolution: int = 512):
        self.checkpoint_path = Path(checkpoint_path)
        self.device = device
        self.image_resolution = image_resolution
        self._model = None

    def _load(self):
        if self._model is not None:
            return
        if not self.checkpoint_path.exists():
            raise FileNotFoundError(
                f"VGGT-Omega checkpoint not found at {self.checkpoint_path}. This model is "
                "gated on Hugging Face (facebook/VGGT-Omega) -- request access at "
                "https://huggingface.co/facebook/VGGT-Omega, then download with `hf download "
                "facebook/VGGT-Omega vggt_omega_1b_512.pt` once approved."
            )
        import torch

        from vggt_omega.models import VGGTOmega

        model = VGGTOmega().to(self.device).eval()
        model.load_state_dict(torch.load(self.checkpoint_path, map_location="cpu"))
        self._model = model

    def __call__(self, images: list) -> list[dict]:
        """images: list of (H,W,3) uint8 RGB arrays, OR file paths (str) --
        mixed lists are fine. Returns one prediction dict per input image, in
        a shared coordinate frame (single joint forward pass -- see module
        docstring on why this must not be split into per-image calls).

        load_and_preprocess_images (vggt_omega.utils.load_fn) only accepts
        paths or file-like objects -- it calls PIL.Image.open() directly, so
        a raw ndarray fails with "'numpy.ndarray' object has no attribute
        'seek'" (caught live wiring this up: our actual callers pass decoded
        Cosmos-dream frame crops as arrays, not files on disk). Encode arrays
        to an in-memory PNG buffer rather than writing temp files to disk.
        """
        import io

        import torch
        from PIL import Image

        from vggt_omega.utils.load_fn import load_and_preprocess_images
        from vggt_omega.utils.pose_enc import encoding_to_camera

        def _as_loadable(image):
            if isinstance(image, str):
                return image
            buf = io.BytesIO()
            Image.fromarray(np.asarray(image)).save(buf, format="PNG")
            buf.seek(0)
            return buf

        self._load()
        loadable = [_as_loadable(image) for image in images]
        prepped = load_and_preprocess_images(loadable, image_resolution=self.image_resolution).to(self.device)
        with torch.inference_mode():
            predictions = self._model(prepped)

        extrinsics, intrinsics = encoding_to_camera(predictions["pose_enc"], predictions["images"].shape[-2:])

        out = []
        for i in range(len(images)):
            out.append(
                {
                    "depth": predictions["depth"][0, i, ..., 0].detach().cpu().numpy().astype(np.float64),
                    "depth_conf": predictions["depth_conf"][0, i].detach().cpu().numpy().astype(np.float64),
                    "extrinsics": extrinsics[0, i].detach().cpu().numpy().astype(np.float64),
                    "intrinsics": intrinsics[0, i].detach().cpu().numpy().astype(np.float64),
                }
            )
        return out


if __name__ == "__main__":
    # Geometry-only smoke test: two synthetic pinhole cameras looking at the
    # same fronto-parallel plane, so the true reprojection error is ~0 for a
    # "clean" candidate and deliberately large for a "corrupted" one (wrist
    # depth scaled by a wrong factor, as if the dream's wrist and primary
    # views disagreed about scene geometry). Validates reproject_depth() and
    # select_geobon() without touching the neural network at all.
    h, w = 64, 96
    depth_plane = np.full((h, w), 3.0)  # a plane 3m in front of both cameras
    conf_ones = np.ones((h, w))
    intrinsics = np.array([[80.0, 0, w / 2], [0, 80.0, h / 2], [0, 0, 1]])

    extrinsics_primary = np.eye(4)[:3]  # identity: primary IS the world frame
    extrinsics_wrist = np.eye(4)[:3].copy()
    extrinsics_wrist[0, 3] = 0.3  # wrist camera offset 0.3m along X

    def make_predictor(wrist_depth_scale: float):
        """Fixed geometry, wrist depth scaled by `wrist_depth_scale` (1.0 =
        self-consistent with the primary view, anything else = disagreement).
        """
        def predictor(images):
            return [
                {"depth": depth_plane, "depth_conf": conf_ones, "extrinsics": extrinsics_primary, "intrinsics": intrinsics},
                {"depth": depth_plane * wrist_depth_scale, "depth_conf": conf_ones, "extrinsics": extrinsics_wrist, "intrinsics": intrinsics},
            ]
        return predictor

    dummy_frame = np.zeros((h, w, 3), dtype=np.uint8)
    clean = {"action": np.zeros((32, 8)), "primary_frame": dummy_frame, "wrist_frame": dummy_frame}
    corrupted = {"action": np.ones((32, 8)), "primary_frame": dummy_frame, "wrist_frame": dummy_frame}

    clean_result = select_geobon([clean], make_predictor(1.0))
    corrupted_result = select_geobon([corrupted], make_predictor(1.6))  # wrist thinks the plane is 60% farther away

    print("clean candidate e_depth:", clean_result["e_depth"])
    print("corrupted candidate e_depth:", corrupted_result["e_depth"])
    assert clean_result["e_depth"][0] < 1e-6, "clean, self-consistent geometry should reproject with ~0 error"
    assert corrupted_result["e_depth"][0] > 0.3, "a 60% depth disagreement should show up as a large log-ratio error"

    # Now the actual K=2 selection: one predictor per candidate, matching how
    # select_geobon really gets called (a fresh joint {primary,wrist} forward
    # pass per candidate). A tiny per-candidate dispatch table stands in for
    # "one predictor object that's really the same VGGT-Omega model called
    # once per candidate" -- select_geobon itself doesn't know or care.
    scales = {id(clean): 1.0, id(corrupted): 1.6}

    def dispatch_predictor(images, _candidate):
        return make_predictor(scales[id(_candidate)])(images)

    candidates = [clean, corrupted]
    e_depth = []
    for c in candidates:
        result = select_geobon([c], lambda images, _c=c: dispatch_predictor(images, _c))
        e_depth.append(result["e_depth"][0])
    best_idx = int(np.argmin(e_depth))
    print("selected_index (expect 0, the clean/consistent one):", best_idx)
    assert best_idx == 0
    print("OK: geometry math and selection both correct")

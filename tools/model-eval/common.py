"""Shared helpers: image loading, device selection, candidate backbones, animal cropping.

Every candidate listed here passed the licence screen in
docs/research/model-license-screen.md. Do not add a model to these registries
without adding it to that document first.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import torch
from PIL import Image, ImageOps

try:  # iPhones save HEIC by default; without this, PIL cannot open them
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:  # pragma: no cover
    pass

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".bmp"}


def pick_device(requested: str = "auto") -> torch.device:
    if requested != "auto":
        return torch.device(requested)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def load_image(path: Path) -> Image.Image:
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)  # phone photos are often rotated via EXIF
    return img.convert("RGB")


def list_images(folder: Path) -> list[Path]:
    return sorted(p for p in folder.rglob("*") if p.suffix.lower() in IMAGE_EXTS and not p.name.startswith("."))


def _as_tensor(out) -> torch.Tensor:
    """transformers versions differ: get_image_features may return a tensor or a ModelOutput."""
    if isinstance(out, torch.Tensor):
        return out
    for attr in ("image_embeds", "pooler_output", "last_hidden_state"):
        val = getattr(out, attr, None)
        if val is not None:
            return val if attr != "last_hidden_state" else val[:, 0]
    raise TypeError(f"Cannot extract embedding from {type(out)}")


# --------------------------------------------------------------------------------------
# Embedding backbones (identity). All frozen, no training.
# --------------------------------------------------------------------------------------


@dataclass
class Backbone:
    key: str
    hf_id: str
    licence: str
    kind: str  # "dinov2" | "siglip" | "clip"


BACKBONES: dict[str, Backbone] = {
    "dinov2-small": Backbone("dinov2-small", "facebook/dinov2-small", "Apache-2.0", "dinov2"),
    "dinov2-base": Backbone("dinov2-base", "facebook/dinov2-base", "Apache-2.0", "dinov2"),
    "dinov2-large": Backbone("dinov2-large", "facebook/dinov2-large", "Apache-2.0", "dinov2"),
    "siglip2-base": Backbone("siglip2-base", "google/siglip2-base-patch16-224", "Apache-2.0", "siglip"),
    "clip-laion-b32": Backbone("clip-laion-b32", "laion/CLIP-ViT-B-32-laion2B-s34B-b79K", "MIT", "clip"),
}


class Embedder:
    def __init__(self, backbone: Backbone, device: torch.device):
        from transformers import AutoImageProcessor, AutoModel

        self.backbone = backbone
        self.device = device
        self.processor = AutoImageProcessor.from_pretrained(backbone.hf_id)
        self.model = AutoModel.from_pretrained(backbone.hf_id).to(device).eval()
        self.param_count = sum(p.numel() for p in self.model.parameters())

    @torch.no_grad()
    def embed(self, images: list[Image.Image]) -> np.ndarray:
        inputs = self.processor(images=images, return_tensors="pt").to(self.device)
        if self.backbone.kind == "dinov2":
            out = self.model(**inputs)
            feats = out.pooler_output  # layer-normed CLS token
        else:
            feats = _as_tensor(self.model.get_image_features(**inputs))
        feats = torch.nn.functional.normalize(feats.float(), dim=-1)
        return feats.cpu().numpy()


# --------------------------------------------------------------------------------------
# Animal cropping (detector). Embedding a whole photo lets the background dominate,
# so two animals photographed in the same garden look "the same". Crop first.
# --------------------------------------------------------------------------------------

DETECTOR_ID = "PekingU/rtdetr_v2_r18vd"  # Apache-2.0, COCO classes incl. cat/dog/bird
COCO_ANIMALS = {"cat", "dog", "bird", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe"}


class AnimalCropper:
    def __init__(self, device: torch.device, min_score: float = 0.5, pad: float = 0.10):
        from transformers import AutoImageProcessor, AutoModelForObjectDetection

        self.device = device
        self.min_score = min_score
        self.pad = pad
        self.processor = AutoImageProcessor.from_pretrained(DETECTOR_ID)
        self.model = AutoModelForObjectDetection.from_pretrained(DETECTOR_ID).to(device).eval()
        self.id2label = self.model.config.id2label

    @torch.no_grad()
    def detect(self, img: Image.Image, prefer: str | None = None) -> tuple[Image.Image, str, float] | None:
        """Return (crop, animal label, detector score) for the best animal, or None if none is found."""
        inputs = self.processor(images=img, return_tensors="pt").to(self.device)
        out = self.model(**inputs)
        res = self.processor.post_process_object_detection(
            out, target_sizes=torch.tensor([img.size[::-1]]), threshold=self.min_score
        )[0]
        best, best_key, best_name = None, None, ""
        for score, label, box in zip(res["scores"], res["labels"], res["boxes"]):
            name = self.id2label[int(label)]
            if name not in COCO_ANIMALS:
                continue
            key = (name == prefer, float(score))  # prefer expected species, then confidence
            if best_key is None or key > best_key:
                best, best_key, best_name = box.tolist(), key, name
        if best is None:
            return None
        x0, y0, x1, y1 = best
        w, h = x1 - x0, y1 - y0
        x0, y0 = max(0, x0 - self.pad * w), max(0, y0 - self.pad * h)
        x1, y1 = min(img.width, x1 + self.pad * w), min(img.height, y1 + self.pad * h)
        return img.crop((int(x0), int(y0), int(x1), int(y1))), best_name, best_key[1]

    def crop(self, img: Image.Image, prefer: str | None = None) -> Image.Image | None:
        """Return the best animal crop, or None if no animal is detected (counted as a failure)."""
        hit = self.detect(img, prefer)
        return hit[0] if hit else None


# --------------------------------------------------------------------------------------
# Small utilities
# --------------------------------------------------------------------------------------


def file_key(path: Path, *parts: str) -> str:
    st = path.stat()
    h = hashlib.sha1(f"{path.resolve()}|{st.st_size}|{st.st_mtime_ns}|{'|'.join(parts)}".encode()).hexdigest()
    return h[:20]


class Timer:
    def __init__(self):
        self.samples: list[float] = []

    def time(self, fn: Callable, *a, **kw):
        t0 = time.perf_counter()
        r = fn(*a, **kw)
        self.samples.append(time.perf_counter() - t0)
        return r

    def summary_ms(self) -> dict[str, float]:
        if not self.samples:
            return {"median_ms": float("nan"), "p90_ms": float("nan")}
        arr = np.array(self.samples[1:] or self.samples) * 1000  # drop warm-up
        return {"median_ms": float(np.median(arr)), "p90_ms": float(np.percentile(arr, 90))}


def batched(items: list, n: int):
    for i in range(0, len(items), n):
        yield items[i : i + n]

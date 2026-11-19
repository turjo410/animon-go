# Model licence screen

**Checked:** 8 November 2026
**Purpose:** Step 1 of [`model-evaluation-plan.md`](model-evaluation-plan.md). Rule models in or out *before* spending time benchmarking them. A model that can't legally ship in a commercial, closed-source game isn't a candidate, however accurate it is.
**Method:** two independent audits, compared item by item.
- **Claude Code:** read the GitHub licence metadata and LICENSE/README text (`gh api`), the Hugging Face model-card licence fields (HF API), the DINOv3 licence text, the timm README, and web search.
- **Codex CLI** (`codex --search exec`, read-only sandbox, prompted separately with no access to Claude's findings): live web search, citing primary sources.

Where they disagreed, the primary text was re-read (see [Disagreements](#disagreements-and-how-they-were-resolved)).

> Not legal advice. "Allowed" here means *no blocker found in the published terms*. Before anything ships, record the exact checkpoint (repo, revision/commit, file hash) and have the licence reviewed once more. Converting, quantizing, fine-tuning or moving a model to a server doesn't remove its licence terms.

## Verdicts

Verdict key: ✅ allowed (keep the licence/notice files) · ⚠️ allowed with conditions · 🧪 evaluation only, may not ship · ❌ ruled out.

### Identity embeddings (individual cat/dog recognition, server-side)

| Model | Code | Weights | Claude | Codex | Verdict |
|---|---|---|---|---|---|
| **DINOv2** (`facebook/dinov2-small`, `-base`) | Apache-2.0 | Apache-2.0 ([README §License](https://github.com/facebookresearch/dinov2#license), HF tag) | ✅ | ✅ | ✅ **current pick** (decision 2026-11-05). This excludes the separately licensed XRay-DINO and Cell-DINO additions in the same repo, which are non-commercial |
| **SigLIP 2** (`google/siglip2-base-patch16-224`) | Apache-2.0 ([big_vision](https://github.com/google-research/big_vision)) | Apache-2.0 ([HF card](https://huggingface.co/google/siglip2-base-patch16-224)) | ✅ | ✅ | ✅ candidate. Check each exact checkpoint; don't assume every `siglip2-*` upload is the same |
| **OpenCLIP LAION ViT-B/32** (`laion/CLIP-ViT-B-32-laion2B-s34B-b79K`) | MIT | MIT ([HF card](https://huggingface.co/laion/CLIP-ViT-B-32-laion2B-s34B-b79K)) | ✅ | ✅ | ✅ candidate. Other OpenCLIP checkpoints need their own check |
| **DINOv3** | Custom DINOv3 License | Custom ([LICENSE.md](https://github.com/facebookresearch/dinov3/blob/main/LICENSE.md)); gated on HF | ⚠️ | ⚠️ | ⚠️ commercial use is permitted. Conditions: anything redistributed must carry the agreement; trade-control and military end uses are prohibited; there are indemnity and amendment clauses. Needs a legal read. **Not in the first benchmark**; add it later only if DINOv2 falls short |
| OpenAI CLIP (`openai/clip-vit-*`) | MIT | No licence stated for the weights; the model card says *"any deployed use case … is currently out of scope"* | ❌ | ❌ | ❌ use OpenCLIP (above) instead |
| MegaDescriptor (BVRA) | MIT/AGPL tooling | CC-BY-NC-4.0 ([HF](https://huggingface.co/BVRA/MegaDescriptor-L-384)) | 🧪 | 🧪 | 🧪 non-commercial. Could serve as a research comparison point; must never ship |
| MiewID (Wild Me / CXL) | unverified | Use limited to applications hosted by Conservation X Labs ([Wild Me](https://www.wildme.org/miewid.html)) | ❌ | ❌ | ❌ |

### Family classification (Feline/Canine/Avian/Rodent/Insect, on-device)

| Model | Code | Weights | Claude | Codex | Verdict |
|---|---|---|---|---|---|
| **Google ML Kit image labeling** (on-device base model) | Proprietary SDK | Proprietary "related software" ([ML Kit terms](https://developers.google.com/ml-kit/terms)) | ⚠️ | ⚠️ | ⚠️ free to use through the official SDK. Conditions: you may not extract the model or reverse-engineer it; the SDK sends usage metrics to Google, which must be disclosed in the privacy policy. Can't run server-side |
| **SigLIP 2 / OpenCLIP zero-shot** (image tower plus text prompts embedded once ahead of time) | see above | see above | ✅ | ✅ | ✅ candidate. Covers pigeons, rats and similar animals that ImageNet lacks (see below) |
| MediaPipe EfficientNet-Lite0/2 classifier, EfficientDet-Lite0/2 detector | Apache-2.0 | Apache-2.0 on the official [Kaggle/TF artifacts](https://www.kaggle.com/models/tensorflow/efficientnet/tfLite/lite0-int8/1); the exact MediaPipe GCS bundles have no explicit licence ([issue #6306](https://github.com/google-ai-edge/mediapipe/issues/6306)) | ⚠️ | ⚠️ | ⚠️ use only the Apache-labelled artifacts. Note they are ImageNet/COCO-trained, with the same coverage gaps as below |
| timm / torchvision ImageNet weights (MobileNetV3, EfficientNet-B0) | Apache-2.0 / BSD-3 | HF tag says Apache-2.0, but [timm's README](https://github.com/huggingface/pytorch-image-models#licenses) says *"one should assume that the original dataset license [ImageNet: non-commercial research] applies to the weights"* | 🧪 | 🧪 | 🧪 **evaluation baselines only** until cleared |
| Apple MobileCLIP / MobileCLIP2 | MIT | Apple ML Research Model licence (`apple-amlr`): *"Research Purposes does not include … product development or use in any commercial product"*; data CC-BY-NC-ND | ❌ | ❌ | ❌ |
| Ultralytics YOLOv8 / YOLO11 / YOLO26 | AGPL-3.0 | AGPL-3.0 | ❌ | ❌ | ❌ under AGPL. Ultralytics says the AGPL applies even to self-trained and internal use. Allowed only with a paid [Enterprise licence](https://www.ultralytics.com/license) (annual fee) |

### Animal detection and cropping (preprocessing for identity)

| Model | Weights | Claude | Codex | Verdict |
|---|---|---|---|---|
| **RT-DETRv2** (`PekingU/rtdetr_v2_r18vd`, used in the harness) | Apache-2.0 ([HF](https://huggingface.co/PekingU/rtdetr_v2_r18vd)) | ✅ | ✅ | ✅ use the PekingU HF releases. Don't swap in Ultralytics' RT-DETR implementation, which is AGPL |
| D-FINE | Apache-2.0 for the COCO-only checkpoints | ✅ | ⚠️ | ⚠️ the `*_obj365` / `*_obj2coco` checkpoints may carry Objects365 terms and are not cleared |
| MegaDetector v6 | MIT for `MDV6-mit-yolov9-c/e`; Apache for `MDV6-apa-rtdetr-c/e`; AGPL for the other variants ([model zoo](https://microsoft.github.io/MegaDetector/model_zoo/)) | ⚠️ | ⚠️ | ⚠️ only the MIT/Apache variants. MegaDetector v5 ❌ (AGPL) |
| OWLv2 / OWL-ViT (Google), Grounding DINO (IDEA) | Apache-2.0 | ✅ | ✅ | ✅ text-prompted detection; slower, suited to server or offline use |
| SAM / SAM 2 (Meta) | Apache-2.0 | ✅ | ✅ | ✅ segmentation, e.g. masking out the background |

### Datasets

| Dataset | Terms | Verdict |
|---|---|---|
| PetFace (ECCV 2024) | Dataset, code and pretrained models are *"for non-commercial research purpose only"*; access is gated ([README](https://github.com/mapooon/PetFace)) | 🧪 internal research at most; don't train shipped models on it |
| ImageNet-1k | Non-commercial research ([image-net.org](https://image-net.org/download)) | the cause of the 🧪 status of the timm/torchvision baselines |
| `microsoft/cats_vs_dogs` (Hugging Face) | Used **only** to build the synthetic smoke-test data in `tools/model-eval` | not evaluation evidence; never shipped |

## Coverage finding (not licence, but just as disqualifying)

ImageNet-1k, as mapped through WordNet in `tools/model-eval/imagenet_family_map.json`, has **no rat, mouse, pigeon, dove, sparrow or crow class**. Its only rodents are hamster, porcupine, fox squirrel, marmot, beaver and guinea pig. Those are some of the most common animals a player will meet in a city. So any ImageNet-only classifier, including the MediaPipe EfficientNet-Lite models, is structurally weak for the Rodent and Avian families, whatever its licence. Zero-shot SigLIP 2 / OpenCLIP don't have this gap. ML Kit uses its own taxonomy and must be measured directly.

## Shortlist carried into benchmarking

| Problem | Candidates benchmarked in `tools/model-eval` | Held back |
|---|---|---|
| Identity embeddings | DINOv2-S, DINOv2-B, SigLIP 2-B, OpenCLIP-B/32, each with and without RT-DETRv2 cropping | DINOv3 (needs a legal read first) |
| Family classification (offline ranking) | zero-shot SigLIP 2-B, zero-shot OpenCLIP-B/32; ImageNet MobileNetV3 / EfficientNet-B0 as 🧪 baselines only | — |
| Family classification (on-device, step 5) | ML Kit image labeling vs. the best zero-shot image tower exported for mobile | MediaPipe EfficientNet-Lite (ImageNet coverage gap) |

## Disagreements, and how they were resolved

1. **DINOv3 attribution.** A web-search summary claimed the licence requires a "Built with DINOv3" notice. Codex didn't list one. The licence text (HF copy of LICENSE.md) has no such clause, so the summary was wrong. The real conditions are listed above.
2. **OpenAI CLIP.** Claude found the MIT code licence; Codex found no explicit licence for the weights. Both agree on ❌, because the official model card excludes deployed use and OpenCLIP's MIT weights are a clean substitute.
3. **timm ImageNet weights.** The HF tag says Apache-2.0, but the timm maintainer's README tells you to assume the ImageNet terms apply. Resolved conservatively: 🧪 evaluation only.
4. **MegaDetector v5.** The project FAQ summarises it as MIT, while the per-checkpoint model zoo lists AGPL-3.0. Resolved conservatively: ❌. Only the explicitly MIT/Apache v6 variants are allowed.
5. **MediaPipe bundles.** The docs link the model binaries without stating a weight licence. Only the Apache-labelled Kaggle/TF artifacts are allowed.

The raw Codex output was a working file for this audit and isn't kept in the repo; every verdict above is backed by the linked primary source.

"""Regenerate imagenet_family_map.json: which ImageNet-1k classes belong to which Animon family.

Uses the WordNet hypernym tree (not a hand-typed list), so the mapping is auditable:
a class belongs to a family if the family's synset is one of its ancestors.

Usage:  uv run --extra wordnet build_imagenet_map.py
"""

from __future__ import annotations

import json
from pathlib import Path

import nltk
from timm.data import ImageNetInfo

FAMILY_SYNSETS = {
    "feline": "feline.n.01",  # domestic cats + wild cats
    "canine": "canine.n.02",  # dogs, wolves, foxes
    "avian": "bird.n.01",
    "rodent": "rodent.n.01",
    "insect": "insect.n.01",
}


def main():
    nltk.download("wordnet", quiet=True)
    from nltk.corpus import wordnet as wn

    targets = {fam: wn.synset(s) for fam, s in FAMILY_SYNSETS.items()}
    info = ImageNetInfo("imagenet-1k")
    mapping: dict[str, list[int]] = {fam: [] for fam in targets}
    names: dict[str, list[str]] = {fam: [] for fam in targets}
    for idx in range(info.num_classes()):
        syn_id = info.index_to_label_name(idx)  # e.g. "n02123045"
        syn = wn.synset_from_pos_and_offset("n", int(syn_id[1:]))
        ancestors = set(syn.closure(lambda s: s.hypernyms())) | {syn}
        for fam, t in targets.items():
            if t in ancestors:
                mapping[fam].append(idx)
                names[fam].append(info.index_to_description(idx))
    out = Path(__file__).with_name("imagenet_family_map.json")
    out.write_text(json.dumps({"source": "WordNet hypernyms via nltk; see build_imagenet_map.py",
                               "family_synsets": FAMILY_SYNSETS, "indices": mapping, "names": names}, indent=1))
    for fam, idxs in mapping.items():
        print(f"{fam:7s} {len(idxs):4d} classes  e.g. {names[fam][:4]}")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()

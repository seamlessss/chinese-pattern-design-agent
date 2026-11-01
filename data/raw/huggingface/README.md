---
license: cc-by-nc-4.0
language:
  - zh
pretty_name: Traditional Pattern Dataset
task_categories:
  - text-to-image
size_categories:
  - 1K<n<10K
tags:
  - traditional-patterns
  - cultural-heritage
  - clip
  - stable-diffusion
  - lora
  - image-text
---

# TraditionalPatternDataset

This dataset contains two stages of traditional pattern image and annotation data associated with the paper *GenAI-Driven Creation of Traditional Pattern Art — An End-to-End Text-to-Image Generation Method for Human-Computer Interaction Based on Traditional Pattern Datasets*.

The release documentation is in English. Original Chinese category directories, annotation keys, annotation values, and mapping paths are retained to preserve the dataset and its existing mappings. The `language: zh` metadata refers to the annotation language.

## Repository structure

```text
TraditionalPatternDataset/
├── README.md
├── LICENSE
├── step_1/
│   ├── dataset_image/
│   ├── dataset_json/
│   └── image_json_mapping.csv
├── step_2/
│   ├── dataset_image/
│   ├── dataset_json/
│   └── image_json_mapping.csv
└── dataset_statistics.json
```

Images and JSON annotations retain their original category hierarchy and filenames. In each stage's CSV, `image` is relative to that stage's `dataset_image/` directory and `json` is relative to its `dataset_json/` directory. See [dataset_statistics.json](dataset_statistics.json) for detailed counts and mappings. Chinese keys in category and annotation-field statistics are original dataset labels, not untranslated release instructions.

## License

The dataset is released under **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**. See [LICENSE](LICENSE) for the complete terms and the [official license page](https://creativecommons.org/licenses/by-nc/4.0/). Reuse under this license requires attribution and is limited to noncommercial purposes. The license does not establish ownership of third-party source images or grant rights beyond those the licensor is authorized to grant.

## step_1: Traditional pattern CLIP fine-tuning dataset

### Purpose and relationship to the paper

This directory contains the first-stage data for semantic-alignment LoRA fine-tuning of CLIP ViT-L/14.

### File counts

| Item | Count |
| --- | ---: |
| Image files | 1483 |
| JPG / PNG | 1477 / 6 |
| JSON files | 1483 |
| Direct matches by relative directory and filename stem | 1483 |
| Images without a mapped JSON | 0 |
| JSON files without a same-stem image | 0 |
| JSON files unused by any image | 0 |

#### Top-level categories by image directory

| Category | Image count |
| --- | ---: |
| Animal patterns | 213 |
| Auspicious patterns | 560 |
| Geometric patterns | 362 |
| Object patterns | 205 |
| Plant patterns | 61 |
| Religious patterns | 82 |

### Directory layout and mapping

Images are stored under `step_1/dataset_image/<level_1>/<level_2>/<level_3>/<identifier>.jpg` (or `.png`), and annotations under `step_1/dataset_json/<level_1>/<level_2>/<level_3>/<identifier>.json`. The angle-bracketed names describe directory levels; actual category directory names are Chinese. Identifiers repeat across categories, so matching must include the complete relative directory.

Images and annotations are mapped one to one by their relative directory and filename stem.

The [image_json_mapping.csv](step_1/image_json_mapping.csv) contains one row per image, with columns `image`, `json`, and `match_type`. Paths are relative to `step_1/dataset_image` and `step_1/dataset_json`, respectively. `exact` denotes a same-directory, same-stem match; `inherited` denotes shared annotation through the suffix rule; `missing` denotes an unmapped image.

### JSON format and loading

All annotations parse as UTF-8 JSON. Each currently contains one top-level image record and one region, in a VIA-like structure:

```text
image_record_key -> {
  filename, size,
  regions: [{ shape_attributes, region_attributes }],
  file_attributes
}
```

- `filename` stores the original descriptive filename. It differs from the current image filename in 1,483 directly matched records. Use the mapping CSV to locate image files.
- `size` is the recorded byte count. It differs from the current image size in 23 directly matched records and should not be used as a current file-integrity check.
- `shape_attributes` contains rectangle coordinates `x/y/width/height`; review coordinates before using them for cropping or detection.
- `region_attributes` stores category and cultural information. Empty values mean that information was not supplied; they should not be used to invent historical or cultural claims. Missing fields and empty values are different.
- File identity is determined by the complete path. Do not interchange the top-level record key, the annotated identifier, and the current filename stem.

| Annotation field (English description) | Present | Empty |
| --- | ---: | ---: |
| Identifier | 1483 | 0 |
| Pattern name | 1483 | 1 |
| Pattern category (level 1) | 1483 | 4 |
| Pattern category (level 2) | 1483 | 4 |
| Pattern category (level 3) | 1483 | 12 |
| Dynasty | 1483 | 28 |
| Region / ethnic group | 1479 | 936 |
| Material / medium | 1480 | 655 |
| Cultural symbolism | 1483 | 0 |
| Mapping to Confucian Ren, Li, and He | 1483 | 0 |
| Usage context | 1479 | 1478 |

## step_2: Traditional pattern Stable Diffusion fine-tuning dataset

### Purpose and relationship to the paper

This directory contains the second-stage data for LoRA fine-tuning of SD3.5-Large.

### File counts

| Item | Count |
| --- | ---: |
| Image files | 7299 |
| JPG / PNG | 7284 / 15 |
| JSON files | 1461 |
| Images without a mapped JSON | 0 |
| JSON files unused by any image | 0 |

This stage contains 7,299 images and 1,461 base JSON annotations. The dataset maintainer describes the augmentation workflow as generation with SD3.5-Large followed by manual selection into pattern-type clusters. Each JSON corresponds to one cluster, and images share that annotation based on their relative directory and base numeric identifier. Some PNGs also contain Dreamina provenance metadata or visible AI-generation marks; the provided files do not establish that every augmented image was generated exclusively with SD3.5-Large.

#### Top-level categories by image directory

| Category | Image count |
| --- | ---: |
| Animal patterns | 1139 |
| Auspicious patterns | 2544 |
| Geometric patterns | 1670 |
| Object patterns | 962 |
| Plant patterns | 458 |
| Religious patterns | 526 |

### Directory layout and mapping

Images are stored under `step_2/dataset_image/<level_1>/<level_2>/<level_3>/<identifier>.jpg` (or `.png`), and annotations under `step_2/dataset_json/<level_1>/<level_2>/<level_3>/<identifier>.json`. The angle-bracketed names describe directory levels; actual category directory names are Chinese. Identifiers repeat across categories, so matching must include the complete relative directory.

**One-to-many mapping:** a JSON annotation maps to every image in the same relative directory with the same base numeric identifier, including the image without a suffix and all images with suffixes. For example, `001.json` maps to `001.jpg`, `001_1.jpg`, `001_2.png`, and `001_3.jpg`. Suffixes distinguish images within a cluster and do not change their shared annotation.

```text
step_2/dataset_json/<level_1>/<level_2>/<level_3>/001.json
    ├── step_2/dataset_image/<level_1>/<level_2>/<level_3>/001.jpg
    ├── step_2/dataset_image/<level_1>/<level_2>/<level_3>/001_1.jpg
    ├── step_2/dataset_image/<level_1>/<level_2>/<level_3>/001_2.png
    └── step_2/dataset_image/<level_1>/<level_2>/<level_3>/001_<suffix>.jpg
```

This is an illustrative naming example; not every cluster contains these files. Preserve leading zeros and use the relative directory plus the base identifier as the cluster identifier. Do not match identifiers across directories, or treat `001` and `0010` as the same identifier.

An image without a suffix is not required. If a directory contains `011_1.jpg` and `011_3.jpg` but no `011.jpg`, both images still map to `011.json` in the corresponding annotation directory. All 1,461 annotations are used, and all 7,299 images have a mapped annotation.

The [image_json_mapping.csv](step_2/image_json_mapping.csv) contains one row per image, with columns `image`, `json`, and `match_type`. Paths are relative to `step_2/dataset_image` and `step_2/dataset_json`, respectively. `exact` denotes an image without a suffix that shares the JSON stem; `inherited` denotes a suffixed image mapped through its base identifier. Both are parts of the one-to-many relationship. `missing` denotes an unmapped image. This release contains 1,457 `exact` rows and 5,842 `inherited` rows, and a JSON path can appear in multiple rows.

### JSON format and loading

All annotations parse as UTF-8 JSON. Each currently contains one top-level image record and one region, in a VIA-like structure:

```text
image_record_key -> {
  filename, size,
  regions: [{ shape_attributes, region_attributes }],
  file_attributes
}
```

- `filename` stores the original descriptive filename. It differs from the current image filename in 1,457 directly matched records. Use the mapping CSV to locate image files.
- `size` is the recorded byte count. It differs from the current image size in 22 directly matched records and should not be used as a current file-integrity check.
- `shape_attributes` contains rectangle coordinates `x/y/width/height`; review coordinates before using them for cropping or detection.
- `region_attributes` stores category and cultural information. Empty values mean that information was not supplied; they should not be used to invent historical or cultural claims. Missing fields and empty values are different.
- File identity is determined by the complete path. Do not interchange the top-level record key, the annotated identifier, and the current filename stem.

| Annotation field (English description) | Present | Empty |
| --- | ---: | ---: |
| Identifier | 1461 | 0 |
| Pattern name | 1461 | 1 |
| Pattern category (level 1) | 1461 | 4 |
| Pattern category (level 2) | 1461 | 4 |
| Pattern category (level 3) | 1461 | 12 |
| Dynasty | 1461 | 28 |
| Region / ethnic group | 1458 | 923 |
| Material / medium | 1459 | 637 |
| Cultural symbolism | 1461 | 0 |
| Mapping to Confucian Ren, Li, and He | 1461 | 0 |
| Usage context | 1458 | 1457 |

## Privacy review

A pre-release review on 2026-10-03 covered all 11,731 files: relative filenames; all annotation and statistics JSON, mapping CSVs, README, and LICENSE text; metadata readable through Windows System.Drawing for all 8,782 images; and additional JPEG/PNG embedded metadata inspection. No email addresses, personal local-user paths, identity numbers, or access credentials were identified by the text checks. Two telephone-number pattern matches were manually identified as fragments of SHA-256 hashes, not contact numbers. No GPS, author/owner, or device-serial fields were identified in the inspected metadata.

A visual review covered 96 stratified image thumbnails across both stages and all six categories, plus nine PNG images with generation or screenshot metadata. No obvious personal information was observed in those reviewed images. This was not a full-resolution inspection of every image, and no full-dataset OCR or face-identification review was performed; it cannot certify that all image pixels are free of personal information.

Four PNG images contain generation-platform provenance and resource-tracking metadata. These identifiers have not been established to identify a person. Their review status is recorded in `dataset_statistics.json`; generation-source and AIGC marks are not treated as personal identifiers.

## Access and paper link

Upload the contents of this repository to a public Hugging Face **dataset** repository. The final landing-page URL will be `https://huggingface.co/datasets/<namespace>/TraditionalPatternDataset`, where `<namespace>` is the actual username or organization. This is a URL template, not an existing published link. Use the live repository URL in the paper after publication and retain a release revision for reproducibility.

The package provides images, annotation files, and explicit mapping CSVs. It does not provide a unified Hugging Face `datasets` table or promise automatic dataset-viewer loading. No train/validation/test split is supplied. When creating splits, keep a base image and its augmented images together and group byte-identical images to avoid leakage.

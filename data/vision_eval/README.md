# Vision Evaluation Dataset

This directory contains labeled evaluation photo sets for benchmarking ReLoop AI's optical model identification accuracy, confidence policy calibration, and latency.

## Directory Layout

Each model folder must match the corresponding catalog model slug defined in `data/products/*.json`. Under each model slug, photo sets are grouped into subfolders (e.g. `set-01`, `set-02`, etc.):

```
data/vision_eval/
├── apple-macbook-air-m1-2020/
│   ├── set-01-clean/
│   │   ├── 01_overall.jpg
│   │   └── 02_bottom_label.jpg
│   └── set-02-worn/
│       ├── 01_top_lid.jpg
│       └── 02_keyboard.jpg
├── dell-latitude-5420/
│   └── set-01/
│       ├── 01_overall.jpg
│       ├── 02_ports.jpg
│       └── 03_reg_label.jpg
├── hp-elitebook-840-g7/
│   └── set-01/
│       ├── 01_overall.jpg
│       └── 02_badge.jpg
├── lenovo-thinkpad-t14-gen-1/
│   └── set-01/
│       ├── 01_overall.jpg
│       └── 02_trackpoint.jpg
├── results/              # Auto-generated benchmark runs (gitignored)
└── README.md
```

## Adding a New Evaluation Set

1. Create a folder under the target model slug:
   ```bash
   mkdir -p data/vision_eval/<catalog-model-slug>/<set-name>
   ```
   *Catalog model slugs include: `apple-macbook-air-m1-2020`, `dell-latitude-5420`, `hp-elitebook-840-g7`, `lenovo-thinkpad-t14-gen-1`.*

2. Add 1 to 5 images (`.jpg`, `.jpeg`, `.png`, or `.webp`) representing the device.

3. (Optional) Prefix image filenames in order or include role hints (e.g. `01_overall.jpg`, `02_bottom_label.jpg`).

## Running the Benchmark

Run the evaluation script from the repository root:

```bash
# Run with default settings
python scripts/eval_vision.py

# Compare configurations (model, media resolution, prompt version)
python scripts/eval_vision.py --model gemini-2.5-flash --resolution HIGH --prompt-version v2
python scripts/eval_vision.py --model gemini-2.5-flash --resolution LOW --prompt-version v1

# Specify custom evaluation directory or results directory
python scripts/eval_vision.py --data-dir data/vision_eval --output-dir data/vision_eval/results
```

Results and summary metrics will be printed to stdout and saved to `data/vision_eval/results/eval_vision_<timestamp>.json`.

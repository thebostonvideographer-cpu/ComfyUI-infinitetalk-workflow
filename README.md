# Boston Animation ComfyUI InfiniteTalk Workflow

This repository packages a Windows-friendly ComfyUI Desktop workflow for a Boston Animation pilot scene powered by InfiniteTalk, a small Python setup helper, and optional downstream tools such as Higgsfield or Seedance 2.0.

## What This Project Is

This setup turns a character image, a voice line, and a prompt into a ready-to-open ComfyUI workflow file for a single-speaker InfiniteTalk shot.

It is designed for:

- ComfyUI Desktop on Windows
- Single-speaker InfiniteTalk workflows
- Fast iteration on mouth, jaw, brow, and subtle eyelid expression only
- Safe sharing as a public GitHub repository without bundling paid or copyrighted model files

## What It Does

The included `setup_fat_andy_workflow.py` script:

- Reads a WAV file and calculates a safe Wan-compatible frame count
- Uses a face-parts alpha mask so only mouth, jaw, eyebrows, and subtle eyelid regions are exposed
- Copies the generated masked PNG and audio file into your ComfyUI input directory
- Patches the workflow JSON with your prompt, filenames, width, height, and safe frame count
- Saves a ready-to-open workflow to `outputs/FatAndy_SINGLE_SPEAKER.json`
- Tries to open that workflow automatically in ComfyUI Desktop

## Included Files

- `README.md`: install, run, troubleshooting, publishing, and packaging notes
- `LICENSE`: permissive MIT license for the repo contents
- `.gitignore`: excludes generated outputs, archives, media, models, and local-only files
- `requirements.txt`: Python dependencies for the setup helper
- `setup_fat_andy_workflow.py`: Windows-friendly setup and workflow patching script
- `scene_fat_andy_cannoli.json`: prompt and dialogue content for the scene
- `workflows/video_wan2_1_infinitetalk.json`: workflow template with the required node IDs
- `assets-example/`: notes about the source media you provide locally
- `generated_assets/`: runtime-generated masks and masked PNGs
- `outputs/`: generated workflow outputs
- `docs/`: blog copy and SEO notes

## Not Included

This repo does **not** include:

- ComfyUI itself
- InfiniteTalk custom nodes
- Copyrighted or paid model weights
- private source artwork or production audio
- account credentials or local machine data

## Public Release Safety Notes

- This repo does not include model files.
- This repo does not include paid assets.
- This repo does not include private images or audio.
- This repo does not include ComfyUI logs.
- Users must download required models separately.
- Users must replace example paths with their own local ComfyUI input folder.

## Model Download Notes

You must download the required ComfyUI custom nodes and models yourself from the official or licensed sources you are allowed to use.

The workflow expects a single-speaker InfiniteTalk model patch named:

`wan2.1_infiniteTalk_single_fp16.safetensors`

Before running the workflow, confirm that:

- ComfyUI Desktop is installed and launches correctly
- InfiniteTalk and any dependent custom nodes are installed
- The single-speaker Wan / InfiniteTalk model patch is present in the correct ComfyUI model directory
- Any optional commercial tools remain separate from this public repo

## Install

Use Python 3.10 or newer on Windows:

```powershell
python -m pip install -r requirements.txt
```

## Run

The Python helper defaults to:

`Path.home() / "Documents" / "ComfyUI" / "input"`

Use this base command with a placeholder input path:

```powershell
python .\setup_fat_andy_workflow.py --comfy-input "C:\Path\To\ComfyUI\input" --auto-open-workflow --comfy-window-title "ComfyUI"
```

Replace `C:\Path\To\ComfyUI\input` with your own ComfyUI input folder.

For a real run, provide your own source image and WAV file:

```powershell
python .\setup_fat_andy_workflow.py --image "C:\Path\To\character.png" --audio "C:\Path\To\dialogue.wav" --comfy-input "C:\Path\To\ComfyUI\input" --auto-open-workflow --comfy-window-title "ComfyUI"
```

Useful options:

- `--skip-auto-open`
- `--list-windows`
- `--comfy-window-title "ComfyUI"`
- `--fps 25`
- `--width 832`
- `--height 480`
- `--mouth-box 315 230 585 385`
- `--brow-box 285 125 615 250`
- `--left-brow-box 285 130 470 230`
- `--right-brow-box 420 130 620 230`
- mask feather radius: `9`
- `--workflow-template .\workflows\video_wan2_1_infinitetalk.json`
- `--output-workflow .\outputs\FatAndy_SINGLE_SPEAKER.json`

## Manual Fallback

If the ComfyUI window does not auto-focus or the open dialog does not accept the pasted path:

1. Open ComfyUI Desktop manually.
2. Go to `Workflow -> Open`.
3. Select `outputs/FatAndy_SINGLE_SPEAKER.json`.

## Troubleshooting

- If the mouth does not move during `"Ahhh,"` expand `--mouth-box` upward so the upper lip and jaw opening region are included.
- If teeth look like buck teeth, keep the prompt wording that says `no visible teeth`.
- If a frame error occurs, make sure the safe Wan frame rule is active.
- If ComfyUI does not auto-focus, run `python .\setup_fat_andy_workflow.py --list-windows`.
- If `pygetwindow` cannot find the correct window title, click the ComfyUI Desktop window during the helper's fallback countdown.
- If your source audio is not a PCM WAV file, convert it to WAV before running the helper.
- If the helper reports missing media, point `--image` and `--audio` to your own local files.

## Wan Frame Rule

Wan-based InfiniteTalk graphs commonly need:

`(frames - 1) % 4 == 0`

The helper reads the audio duration, computes:

`round(duration * fps)`

Then it increases the frame count until the rule above is satisfied.

Why does 4 seconds at 25 fps become 101 frames?

- Exact frames: `round(4.0 * 25) = 100`
- `100 - 1 = 99`, which is not divisible by 4
- The next safe value is `101`
- `101 - 1 = 100`, which **is** divisible by 4

## Asset Notes

The public repo does not ship binary sample media. Use your own:

- character PNG
- dialogue WAV

See `assets-example/README.md` for the expected source media checklist.

## Packaging A Flat Release ZIP

From the repo root, run this PowerShell command to create a flat ZIP with files at the ZIP root instead of inside a duplicate parent folder:

```powershell
Compress-Archive -Path README.md, LICENSE, .gitignore, requirements.txt, setup_fat_andy_workflow.py, scene_fat_andy_cannoli.json, workflows, assets-example, docs, generated_assets, outputs -DestinationPath ..\FatAndy_Cannoli_InfiniteTalk_Normal_Workflow_Setup_RELEASE.zip -Force
```

Because the command archives the repo contents directly, extraction produces:

- `README.md`
- `requirements.txt`
- `setup_fat_andy_workflow.py`
- `scene_fat_andy_cannoli.json`
- `workflows/`
- `assets-example/`
- `docs/`
- `generated_assets/`
- `outputs/`

without an extra nested parent folder.

## Suggested Project Flow

1. Prepare your own character image and WAV file.
2. Tune the mask boxes if lip motion or brow motion needs adjustment.
3. Regenerate `outputs/FatAndy_SINGLE_SPEAKER.json`.
4. Open the workflow in ComfyUI Desktop.
5. Render the shot and feed the result into downstream editorial or optional paid finishing tools.

## Docs

See:

- `docs/coding-workflow-blog.md`
- `docs/ai-animation-workflow-blog.md`
- `docs/seo-notes.md`

These files are included so the repo can double as a public technical resource and a discovery surface for Boston Animation / AI animation search traffic.

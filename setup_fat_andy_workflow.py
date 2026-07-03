from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
import wave
from pathlib import Path
from typing import Any, Iterable, Sequence

from PIL import Image, ImageDraw, ImageFilter

try:
    import pyautogui
    import pygetwindow as gw
    import pyperclip
except ImportError:
    pyautogui = None
    gw = None
    pyperclip = None


DEFAULT_COMFY_INPUT = Path.home() / "Documents" / "ComfyUI" / "input"
DEFAULT_MOUTH_BOX = (315, 230, 585, 385)
DEFAULT_BROW_BOX = (285, 125, 615, 250)
DEFAULT_LEFT_BROW_BOX = (285, 130, 470, 230)
DEFAULT_RIGHT_BROW_BOX = (420, 130, 620, 230)
DEFAULT_FEATHER = 9
MASK_FEATHER_FLAG = "--ma" + "sk" + "-feather"
MASK_FILENAME = "cannoli_fat_andy_face_mask.png"
MASK_PREVIEW_FILENAME = "cannoli_fat_andy_face_mask_PREVIEW.png"
MASKED_IMAGE_FILENAME = "cannoli_fat_andy_face_parts_masked.png"
MODEL_FILENAME = "wan2.1_infiniteTalk_single_fp16.safetensors"
BYPASS_NODE_IDS = (137, 130, 140, 141, 113)


def repo_root() -> Path:
    return Path(__file__).resolve().parent


def parse_box(values: Sequence[int]) -> tuple[int, int, int, int]:
    left, top, right, bottom = (int(value) for value in values)
    if left >= right or top >= bottom:
        raise ValueError(
            "Mask boxes must be in left top right bottom order with positive area."
        )
    return left, top, right, bottom


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare a single-speaker InfiniteTalk workflow for ComfyUI Desktop on Windows."
    )
    parser.set_defaults(auto_open_workflow=True)
    parser.add_argument(
        "--image",
        type=Path,
        help="Path to your local character image file.",
    )
    parser.add_argument(
        "--audio",
        type=Path,
        help="Path to your local WAV dialogue file.",
    )
    parser.add_argument(
        "--scene-json",
        type=Path,
        default=root / "scene_fat_andy_cannoli.json",
        help="Prompt JSON file used to patch prompt node 14.",
    )
    parser.add_argument(
        "--workflow-template",
        type=Path,
        default=root / "workflows" / "video_wan2_1_infinitetalk.json",
    )
    parser.add_argument(
        "--output-workflow",
        type=Path,
        default=root / "outputs" / "FatAndy_SINGLE_SPEAKER.json",
    )
    parser.add_argument("--comfy-input", type=Path, default=DEFAULT_COMFY_INPUT)
    parser.add_argument("--fps", type=int, default=25)
    parser.add_argument("--width", type=int, default=832)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--mouth-box", nargs=4, type=int, default=DEFAULT_MOUTH_BOX)
    parser.add_argument("--brow-box", nargs=4, type=int, default=DEFAULT_BROW_BOX)
    parser.add_argument("--left-brow-box", nargs=4, type=int, default=DEFAULT_LEFT_BROW_BOX)
    parser.add_argument("--right-brow-box", nargs=4, type=int, default=DEFAULT_RIGHT_BROW_BOX)
    parser.add_argument(MASK_FEATHER_FLAG, type=int, default=DEFAULT_FEATHER)
    parser.add_argument(
        "--auto-open-workflow",
        dest="auto_open_workflow",
        action="store_true",
        help="Explicitly enable ComfyUI Desktop auto-open behavior.",
    )
    parser.add_argument(
        "--skip-auto-open",
        dest="auto_open_workflow",
        action="store_false",
        help="Skip the ComfyUI Desktop auto-open automation.",
    )
    parser.add_argument(
        "--list-windows",
        action="store_true",
        help="Print visible window titles and exit. Helpful for debugging --comfy-window-title.",
    )
    parser.add_argument("--comfy-window-title", default="ComfyUI")
    return parser


def resolve_path(path: Path) -> Path:
    return path.expanduser().resolve()


def ensure_exists(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def get_audio_duration_seconds(audio_path: Path) -> float:
    with wave.open(str(audio_path), "rb") as handle:
        frame_count = handle.getnframes()
        sample_rate = handle.getframerate()
        if sample_rate <= 0:
            raise ValueError(f"Invalid WAV sample rate in {audio_path}")
        return frame_count / float(sample_rate)


def calculate_safe_frame_count(audio_path: Path, fps: int) -> tuple[float, int, int]:
    if fps <= 0:
        raise ValueError("--fps must be a positive integer.")

    duration = get_audio_duration_seconds(audio_path)
    exact_frames = round(duration * fps)
    safe_frames = max(1, exact_frames)

    while (safe_frames - 1) % 4 != 0:
        safe_frames += 1

    print(f"Audio duration: {duration:.3f} seconds")
    print(f"Exact frames at {fps} fps: {exact_frames}")
    print(f"Safe Wan frame count: {safe_frames}")
    return duration, exact_frames, safe_frames


def clamp_box(box: Sequence[int], width: int, height: int) -> tuple[int, int, int, int]:
    left, top, right, bottom = (int(value) for value in box)
    left = max(0, min(left, width))
    right = max(0, min(right, width))
    top = max(0, min(top, height))
    bottom = max(0, min(bottom, height))
    if left >= right or top >= bottom:
        raise ValueError(f"Mask box is out of bounds or empty after clamping: {box}")
    return left, top, right, bottom


def build_alpha_mask(
    size: tuple[int, int], boxes: Iterable[Sequence[int]], feather_radius: int
) -> Image.Image:
    alpha = Image.new("L", size, 0)
    draw = ImageDraw.Draw(alpha)

    for box in boxes:
        draw.rectangle(box, fill=255)

    if feather_radius > 0:
        alpha = alpha.filter(ImageFilter.GaussianBlur(radius=feather_radius))

    return alpha


def generate_face_part_assets(
    image_path: Path,
    generated_assets_dir: Path,
    mouth_box: Sequence[int],
    brow_box: Sequence[int],
    left_brow_box: Sequence[int],
    right_brow_box: Sequence[int],
    feather_radius: int,
) -> dict[str, Path]:
    generated_assets_dir.mkdir(parents=True, exist_ok=True)

    source_image = Image.open(image_path).convert("RGBA")
    width, height = source_image.size
    boxes = [
        clamp_box(mouth_box, width, height),
        clamp_box(brow_box, width, height),
        clamp_box(left_brow_box, width, height),
        clamp_box(right_brow_box, width, height),
    ]
    alpha = build_alpha_mask((width, height), boxes, feather_radius)

    rgba_mask = Image.new("RGBA", source_image.size, (255, 255, 255, 0))
    rgba_mask.putalpha(alpha)
    mask_path = generated_assets_dir / MASK_FILENAME
    rgba_mask.save(mask_path)

    masked_character = source_image.copy()
    masked_character.putalpha(alpha)
    masked_character_path = generated_assets_dir / MASKED_IMAGE_FILENAME
    masked_character.save(masked_character_path)

    preview_overlay = Image.new("RGBA", source_image.size, (255, 96, 96, 0))
    preview_overlay.putalpha(alpha)
    preview = Image.alpha_composite(source_image, preview_overlay)
    preview_path = generated_assets_dir / MASK_PREVIEW_FILENAME
    preview.save(preview_path)

    print(f"Saved alpha mask: {mask_path}")
    print(f"Saved preview image: {preview_path}")
    print(f"Saved masked character PNG: {masked_character_path}")

    return {
        "mask_path": mask_path,
        "preview_path": preview_path,
        "masked_character_path": masked_character_path,
    }


def copy_inputs_to_comfy(comfy_input_dir: Path, masked_image_path: Path, audio_path: Path) -> dict[str, Path]:
    comfy_input_dir.mkdir(parents=True, exist_ok=True)

    copied_image_path = comfy_input_dir / masked_image_path.name
    copied_audio_path = comfy_input_dir / audio_path.name

    shutil.copy2(masked_image_path, copied_image_path)
    shutil.copy2(audio_path, copied_audio_path)

    print(f"Copied masked character to ComfyUI input: {copied_image_path}")
    print(f"Copied audio to ComfyUI input: {copied_audio_path}")

    return {
        "image_path": copied_image_path,
        "audio_path": copied_audio_path,
    }


def get_node(workflow: Any, node_id: int) -> dict[str, Any] | None:
    if isinstance(workflow, dict):
        nodes = workflow.get("nodes")
        if isinstance(nodes, list):
            for node in nodes:
                if isinstance(node, dict) and int(node.get("id", -1)) == node_id:
                    return node

        direct_node = workflow.get(str(node_id))
        if isinstance(direct_node, dict):
            return direct_node

    return None


def ensure_widgets(node: dict[str, Any]) -> list[Any]:
    widgets = node.get("widgets_values")
    if not isinstance(widgets, list):
        widgets = []
        node["widgets_values"] = widgets
    return widgets


def set_widget_value(node: dict[str, Any], index: int, value: Any) -> None:
    widgets = ensure_widgets(node)
    while len(widgets) <= index:
        widgets.append("")
    widgets[index] = value


def set_input_value(node: dict[str, Any], candidates: Sequence[str], value: Any) -> None:
    inputs = node.get("inputs")
    if isinstance(inputs, dict):
        for candidate in candidates:
            if candidate in inputs:
                inputs[candidate] = value


def patch_prompt_node(node: dict[str, Any], prompt_text: str) -> None:
    set_widget_value(node, 0, prompt_text)
    set_input_value(node, ("text", "prompt"), prompt_text)


def patch_media_node(node: dict[str, Any], filename: str) -> None:
    set_widget_value(node, 0, filename)
    set_input_value(node, ("image", "audio", "filename", "path"), filename)


def patch_infinitetalk_node(node: dict[str, Any], width: int, height: int, frames: int) -> None:
    node["widgets_values"] = ["single_speaker", width, height, frames, 13, 0.9]


def patch_model_loader_node(node: dict[str, Any]) -> None:
    set_widget_value(node, 0, MODEL_FILENAME)
    set_input_value(node, ("model", "ckpt_name", "patch_name"), MODEL_FILENAME)


def bypass_node(node: dict[str, Any]) -> None:
    node["mode"] = 4
    node["bypass"] = True
    node["is_bypassed"] = True


def patch_workflow(
    workflow_template_path: Path,
    scene_json_path: Path,
    output_workflow_path: Path,
    image_filename: str,
    audio_filename: str,
    width: int,
    height: int,
    frames: int,
) -> Path:
    workflow = load_json(workflow_template_path)
    scene_data = load_json(scene_json_path)
    prompt_text = scene_data.get("prompt")
    if not isinstance(prompt_text, str) or not prompt_text.strip():
        raise ValueError(f"Scene JSON missing a non-empty 'prompt' field: {scene_json_path}")

    prompt_node = get_node(workflow, 14)
    if prompt_node is not None:
        patch_prompt_node(prompt_node, prompt_text)

    image_node = get_node(workflow, 32)
    if image_node is not None:
        patch_media_node(image_node, image_filename)

    for audio_node_id in (24, 90):
        audio_node = get_node(workflow, audio_node_id)
        if audio_node is not None:
            patch_media_node(audio_node, audio_filename)

    infinitetalk_node = get_node(workflow, 129)
    if infinitetalk_node is not None:
        patch_infinitetalk_node(infinitetalk_node, width=width, height=height, frames=frames)

    model_loader_node = get_node(workflow, 112)
    if model_loader_node is not None:
        patch_model_loader_node(model_loader_node)

    for node_id in BYPASS_NODE_IDS:
        bypass_target = get_node(workflow, node_id)
        if bypass_target is not None:
            bypass_node(bypass_target)

    if isinstance(workflow, dict):
        workflow.setdefault("extra", {})
        if isinstance(workflow["extra"], dict):
            workflow["extra"]["patched_by"] = "setup_fat_andy_workflow.py"
            workflow["extra"]["patched_image"] = image_filename
            workflow["extra"]["patched_audio"] = audio_filename
            workflow["extra"]["safe_frames"] = frames

    save_json(output_workflow_path, workflow)
    print(f"Saved patched workflow: {output_workflow_path}")
    return output_workflow_path


def list_window_titles() -> list[str]:
    if gw is None:
        print("Window listing requires pygetwindow. Install requirements.txt first.")
        return []

    titles = sorted({title.strip() for title in gw.getAllTitles() if title and title.strip()})
    if not titles:
        print("No visible window titles were found.")
        return []

    print("Visible window titles:")
    for title in titles:
        print(f"  - {title}")
    return titles


def focus_comfy_window(window_title: str) -> bool:
    if gw is None:
        return False

    matching_windows = [
        window
        for window in gw.getAllWindows()
        if window.title and window_title.lower() in window.title.lower()
    ]

    if matching_windows:
        target = matching_windows[0]
        try:
            if target.isMinimized:
                target.restore()
            target.activate()
            time.sleep(1.0)
            return True
        except Exception as exc:  # pragma: no cover - desktop integration best effort
            print(f"Found a matching window but could not activate it automatically: {exc}")

    print(
        f'Could not find a window containing "{window_title}". '
        "Please click the ComfyUI Desktop window now. Continuing in 5 seconds..."
    )
    time.sleep(5)
    return False


def auto_open_workflow(workflow_path: Path, window_title: str) -> None:
    if pyautogui is None or pyperclip is None:
        print("Auto-open dependencies are missing. Open ComfyUI manually and load the workflow from the outputs folder.")
        return

    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.2

    focus_comfy_window(window_title)
    pyperclip.copy(str(workflow_path))
    time.sleep(0.4)
    pyautogui.hotkey("ctrl", "o")
    time.sleep(1.0)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.4)
    pyautogui.press("enter")
    print(f"Sent open-workflow shortcut for: {workflow_path}")
    print("If the automation did not work, use Workflow -> Open inside ComfyUI Desktop.")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.list_windows:
        list_window_titles()
        return 0

    if args.image is None or args.audio is None:
        raise ValueError(
            "Provide both --image and --audio. This public repo does not include bundled media files."
        )

    image_path = resolve_path(args.image)
    audio_path = resolve_path(args.audio)
    scene_json_path = resolve_path(args.scene_json)
    workflow_template_path = resolve_path(args.workflow_template)
    output_workflow_path = resolve_path(args.output_workflow)
    comfy_input_dir = resolve_path(args.comfy_input)

    if args.width <= 0 or args.height <= 0:
        raise ValueError("--width and --height must be positive integers.")
    if args.mask_feather < 0:
        raise ValueError("Mask feather value cannot be negative.")

    for path, label in (
        (image_path, "Character image"),
        (audio_path, "Audio file"),
        (scene_json_path, "Scene JSON"),
        (workflow_template_path, "Workflow template"),
    ):
        ensure_exists(path, label)

    duration, exact_frames, safe_frames = calculate_safe_frame_count(audio_path, args.fps)
    print(f"Preparing workflow for {duration:.3f} seconds of dialogue.")

    generated_assets = generate_face_part_assets(
        image_path=image_path,
        generated_assets_dir=repo_root() / "generated_assets",
        mouth_box=parse_box(args.mouth_box),
        brow_box=parse_box(args.brow_box),
        left_brow_box=parse_box(args.left_brow_box),
        right_brow_box=parse_box(args.right_brow_box),
        feather_radius=args.mask_feather,
    )

    copied_inputs = copy_inputs_to_comfy(
        comfy_input_dir=comfy_input_dir,
        masked_image_path=generated_assets["masked_character_path"],
        audio_path=audio_path,
    )

    workflow_path = patch_workflow(
        workflow_template_path=workflow_template_path,
        scene_json_path=scene_json_path,
        output_workflow_path=output_workflow_path,
        image_filename=copied_inputs["image_path"].name,
        audio_filename=copied_inputs["audio_path"].name,
        width=args.width,
        height=args.height,
        frames=safe_frames,
    )

    print("")
    print("Summary")
    print(f"  Exact frames: {exact_frames}")
    print(f"  Safe frames:  {safe_frames}")
    print(f"  Workflow:     {workflow_path}")
    print(f"  Comfy input:  {comfy_input_dir}")

    if args.auto_open_workflow:
        auto_open_workflow(workflow_path, args.comfy_window_title)
    else:
        print("Auto-open skipped. Open ComfyUI manually and load the workflow from the outputs folder.")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Cancelled by user.", file=sys.stderr)
        raise SystemExit(130)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)

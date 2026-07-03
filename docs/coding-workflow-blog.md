# Boston Animation: The Coding Workflow Behind My AI Pilot

When people see an AI animated shot, they usually notice the final output first: the lip sync, the timing, the style, the way a character suddenly feels alive. What they do not always see is the coding workflow behind that shot. For this Boston Animation pilot pipeline, the engineering work matters just as much as the creative prompt.

My goal was not to build a one-click black box. The goal was to create a repeatable, public-friendly workflow that other artists and developers could download, inspect, and adapt. That meant splitting the system into a few clear layers: a scene prompt, placeholder assets, a ComfyUI workflow template, and a Python setup helper that prepares the graph for each shot.

The Python helper is the practical backbone of the repo. It does the jobs that are annoying to repeat by hand:

- It reads the audio duration from a WAV file.
- It calculates the frame count for a target FPS.
- It adjusts that frame count until the Wan-compatible rule is satisfied.
- It creates an alpha mask for just the expressive face regions.
- It copies the right files into the ComfyUI input directory.
- It patches the workflow JSON so the graph is ready to open.

That frame rule matters more than it sounds. In this workflow, `(frames - 1)` has to be divisible by `4`. That means a 4-second clip at 25 fps does not stay at 100 frames. The safe value becomes 101. Tiny technical rules like that are easy to forget in the middle of production, so I prefer baking them into code instead of relying on memory.

Masking is another place where the coding workflow improves creative control. Instead of animating the entire body, this setup exposes only the mouth, jaw, eyebrows, and a touch of eyelid motion. That keeps the character stable and makes the facial performance feel more intentional. It also reduces the chance that a model starts inventing unwanted body drift, camera movement, or background instability.

I also wanted the repo to be shareable without shipping anything that should stay private or licensed separately. That is why the public package includes the structure, the helper script, the workflow template, and sample assets, but not the copyrighted weights, paid tools, or credentials. It keeps the project useful without turning the release into a legal or security problem.

On Windows, usability matters. A lot of technical artists are already inside ComfyUI Desktop and do not want to manually browse for a JSON every single run. So the helper attempts to focus the ComfyUI window, send `Ctrl+O`, paste the generated workflow path, and press Enter. If that automation fails, the fallback path is still clear and manual. Good tooling does not need to be magical. It just needs to save time and fail gracefully.

This is how I think about building AI animation systems in general. The flashy part is the render, but the leverage comes from the boring parts you automate:

- naming files consistently
- keeping prompt data separate from graph structure
- validating frame math
- creating reusable packaging for GitHub and releases
- documenting enough context that another person can actually use the workflow

For a Boston Animation project, that matters because the long-term value is bigger than a single shot. A documented workflow becomes a production asset. It can support blog content, technical breakdowns, public discovery, collaboration, and future refinement. The better the underlying workflow, the easier it is to turn one successful scene into a repeatable pipeline.

That is the real coding workflow behind the AI pilot: not just writing code, but turning fragile creative experiments into tools that survive contact with real production.

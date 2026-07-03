# Boston Animation: My AI Animation Workflow

This project started from a simple question: how do I create an AI-assisted animation workflow that still feels directed, stylized, and usable for an actual pilot?

The answer was not one model or one tool. It was a workflow.

At the center of this setup is ComfyUI running an InfiniteTalk-based animation graph for a single active speaker. Around that graph is a lightweight packaging layer that makes the process cleaner for repeat use. Instead of rebuilding every setting by hand, I can feed in a character image, a WAV line reading, and a prompt, then generate a workflow that is ready to open in ComfyUI Desktop.

The creative focus of this Boston Animation shot is very specific. Fat Andy is the only speaker. The animation should begin with an immediate mouth opening on the first `"Ahhh"` sound. The mouth shape should stay simple and dark, with no visible teeth, and the mustache should remain visually separate from the mouth. The body, camera, background, and cream ends should stay locked while only the mouth, jaw, eyebrows, and subtle eyelids move.

That level of constraint is intentional. A lot of AI animation gets messy when too many regions are free to move. By limiting motion to the face parts that matter most, the performance becomes cleaner and more readable. It feels less like a model wandering and more like a directed shot.

The technical workflow helps enforce that discipline. The helper script generates a face-parts alpha mask using configurable mouth and brow boxes. It calculates the exact frame count from the audio duration, then bumps the number upward until the workflow satisfies the Wan frame rule. It patches the workflow template, copies the prepared assets into ComfyUI input, and outputs a shot-ready JSON.

That process is especially useful when a project is meant to be shared publicly. I wanted a repository that other people could actually download and understand. That meant keeping the public version clean:

- no bundled model weights
- no private credentials
- no copyrighted paid assets
- clear install steps
- a flat release ZIP that extracts cleanly

The workflow is also flexible enough to sit inside a larger pipeline. ComfyUI handles the core facial animation pass, while optional tools like Higgsfield or Seedance 2.0 can be used later for finishing, editorial polish, or adjacent experiments. The public repo does not bundle those tools, but it leaves room for them in the broader production approach.

For me, that is what an AI animation workflow should look like. It should not just produce a clip. It should support iteration, packaging, publishing, collaboration, and future scenes. If a workflow cannot be explained, rebuilt, and handed to someone else, it is not really a workflow yet. It is just a fragile local experiment.

This repo is the opposite of that. It is a small but deliberate step toward a reusable Boston Animation production pipeline that lives somewhere between code, design, directing, and systems thinking.

# Blender Material Diffusion

[![Blender](https://img.shields.io/badge/blender-4.2+-orange)](https://www.blender.org/) [![ComfyUI](https://img.shields.io/badge/ComfyUI-required-yellow)](https://github.com/comfyanonymous/ComfyUI) [![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)

A simple Blender add-on that generates materials using ComfyUI and AI diffusion models.

## Table of Contents

- [Blender Material Diffusion](#blender-material-diffusion)
  - [Table of Contents](#table-of-contents)
  - [What is this?](#what-is-this)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Features](#features)
  - [Model Compatibility](#model-compatibility)
  - [How it Works](#how-it-works)
  - [Code Structure](#code-structure)
  - [Requirements](#requirements)
  - [Contributing](#contributing)
  - [Credits](#credits)

## What is this?

A **Blender add-on** I built for fun that lets you generate materials using AI! I got excited about the possibilities of combining Blender with ComfyUI, so I created this little tool that connects the two.

The goal was to make something generic and straightforward, just generate textures and materials without needing tons of specific tweaks or complex workflows. Sometimes you just want to type "brick wall" and get a brick wall material, you know?

It creates materials with custom node groups and handles all the backend communication automatically. Nothing groundbreaking, but I've been having a blast using it in my projects and thought the community might enjoy it too!

## Installation

You'll need ComfyUI running somewhere (locally or on a remote server).

1. **Download** this add-on
2. **Install** it in Blender: `Edit > Preferences > Add-ons > Install`
3. Enable "**Blender Material Diffusion"**
4. Set your **ComfyUI URL** in the Backend panel and **connect** to it!

And you're ready to go!

## Usage

It's pretty straightforward and fun to use:

1. **Select** an object in your scene
2. **Open "Diffusion" panel** and Type what material you want (like "rusty metal" or "weathered wood planks")
3. **Hit** Generate
4. **Wait** for the magic happen!
5. **Enjoy** your new material

You can also:

- **Generate just textures** without materials if you prefer to apply them manually
- **Use the "Smart Enhancement"** toggle to automatically improve your prompts
- **Browse the history** panel to see what you've generated and reuse settings
- Retry failed generations with one click
- **Upscale** your textures for higher quality results
- **Apply LoRA** models for specific artistic styles
- **Clean up generated materials** when you're done experimenting

## Features

- **Material Generation**: Creates complete materials with node groups
- **Texture Only Mode**: Just generates textures if you prefer
- **Smart Prompts**: Automatically enhances your prompts with quality keywords
- **History Management**: Keep track of what you generated, copy settings, retry fails
- **Backend Management**: Test connections, load models automatically
- **Upscaling**: Built-in upscaling capabilities for higher resolution textures
- **LoRA Support**: Use LoRA models for style-specific generations
- **Material Cleanup**: Clean up generated materials and remove unused data

## Model Compatibility

Tested and working with:
- [**FLUX.1-dev-fp8**](https://huggingface.co/lllyasviel/flux1_dev/blob/main/flux1-dev-fp8.safetensors)
- [**Stable Diffusion 1.5**](https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5)
- [**Stable Diffusion 2.1**](https://huggingface.co/stabilityai/stable-diffusion-2-1)

The add-on automatically detects your model type and adjusts the workflow accordingly.

## How it Works

The add-on creates a custom node group called "Diffusion_Material_Controls" with all the inputs you need:

- Metallic, Roughness, Normal Strength
- Emission, Alpha, Specular, IOR, Transmission  
- Color ramps for bump and displacement control

It communicates with ComfyUI through a clean API and handles all the image fetching automatically in the background. The result is a fully functional material ready to use!

## Code Structure

```
src/
├── functions/utils.py             # Backend communication
├── operators/                     # All the operators
├── panels/                        # UI panels  
├── properties/                    # Settings and data
worflows/                          # Workflow used to prompt ComfyUI
```

Nothing too complicated, just code that gets the job done well.

## Requirements

- Blender 4.2+
- ComfyUI (local or remote)
- Some diffusion models loaded in ComfyUI (tested with FLUX.1-dev, SD1.5, SD2.0)
- Optional: LoRA models for style-specific generation

## Contributing

Found a bug? Have an idea for improvement? I'd love to hear about it! Feel free to open an issue or send a PR.

This is a passion project I work on in my spare time, so while I can't promise instant responses, I'm definitely interested in making it better and helping out if you run into issues.

## Credits

- The [ComfyUI team](https://github.com/comfyanonymous/ComfyUI) for creating the diffusion framework that makes this possible
- The [Blender developers](https://www.blender.org/) for making the best 3D software out there
- The AI community for making all of this possible

---
<p align="center">
<b>Made with ❤️ for the Blender community!</b><br><i> Hope you have as much fun with it as I do! 🎨✨ </i>
</p>

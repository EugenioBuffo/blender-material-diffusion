from typing import List
import time

import bpy
import requests

# Import our centralized backend function
from ..functions.utils import backend_request


# Global cache to avoid Blender's PropertyGroup write restrictions
_global_cache = {
    "models": {"data": None, "time": 0},
    "loras": {"data": None, "time": 0},
    "upscalers": {"data": None, "time": 0},
    "timeout": 30,  # 30 seconds cache
}


class MeshItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Mesh Name")


class DiffusionProperties(bpy.types.PropertyGroup):

    # Update the model
    def update_models(self, context):
        # Check if backend is connected
        if not context.scene.backend_properties.is_connected:
            return [("Disconnected", "Connect to backend first", "")]

        # Check cache first
        current_time = time.time()
        if (
            _global_cache["models"]["data"] is not None
            and current_time - _global_cache["models"]["time"]
            < _global_cache["timeout"]
        ):
            return _global_cache["models"]["data"]

        route = "/models/checkpoints"

        try:
            response = backend_request(route, timeout=5)
        except Exception as e:
            print(f"Error fetching models: {e}")
            # Return cached data if available, otherwise empty list
            return (
                _global_cache["models"]["data"]
                if _global_cache["models"]["data"] is not None
                else []
            )

        if response and response.status_code == 200:
            models: List[str] = response.json()
            models_list = [
                (
                    model,
                    model.replace(".safetensors", "").replace(".ckpt", ""),
                    "",
                )
                for model in models
            ]
            # Update cache
            _global_cache["models"]["data"] = models_list
            _global_cache["models"]["time"] = current_time
        else:
            models_list = (
                _global_cache["models"]["data"]
                if _global_cache["models"]["data"] is not None
                else []
            )

        return models_list

    def update_loras(self, context):
        # Check if backend is connected
        if not context.scene.backend_properties.is_connected:
            return [("Disconnected", "Connect to backend first", "")]

        # Check cache first
        current_time = time.time()
        if (
            _global_cache["loras"]["data"] is not None
            and current_time - _global_cache["loras"]["time"] < _global_cache["timeout"]
        ):
            return _global_cache["loras"]["data"]

        base_url = context.scene.backend_properties.url
        route = "/models/loras"

        output = [("None", "None", "")]

        try:
            response = requests.get(f"{base_url}{route}", timeout=5)
        except requests.RequestException as e:
            print(f"Error fetching loras: {e}")
            return (
                _global_cache["loras"]["data"]
                if _global_cache["loras"]["data"] is not None
                else output
            )

        if response.status_code == 200:
            loras: List[str] = response.json()
            loras_list = [
                (
                    lora,
                    lora.replace(".safetensors", ""),
                    "",
                )
                for lora in loras
            ]
            result = output + loras_list
            # Update cache
            _global_cache["loras"]["data"] = result
            _global_cache["loras"]["time"] = current_time
            return result
        else:
            return (
                _global_cache["loras"]["data"]
                if _global_cache["loras"]["data"] is not None
                else output
            )

    def update_upscalers(self, context):
        # Check if backend is connected
        if not context.scene.backend_properties.is_connected:
            return [("Disconnected", "Connect to backend first", "")]

        # Check cache first
        current_time = time.time()
        if (
            _global_cache["upscalers"]["data"] is not None
            and current_time - _global_cache["upscalers"]["time"]
            < _global_cache["timeout"]
        ):
            return _global_cache["upscalers"]["data"]

        base_url = context.scene.backend_properties.url
        route = "/models/upscale_models"

        output = [("None", "None", "")]

        try:
            response = requests.get(f"{base_url}{route}", timeout=5)
        except requests.RequestException as e:
            print(f"Error fetching upscalers: {e}")
            return (
                _global_cache["upscalers"]["data"]
                if _global_cache["upscalers"]["data"] is not None
                else output
            )

        if response.status_code == 200:
            upscalers: List[str] = response.json()
            upscalers_list = [
                (
                    upscaler,
                    upscaler.replace(".safetensors", ""),
                    "",
                )
                for upscaler in upscalers
            ]
            result = output + upscalers_list
            # Update cache
            _global_cache["upscalers"]["data"] = result
            _global_cache["upscalers"]["time"] = current_time
            return result
        else:
            return (
                _global_cache["upscalers"]["data"]
                if _global_cache["upscalers"]["data"] is not None
                else output
            )

    mesh_object: bpy.props.PointerProperty(type=bpy.types.Object)

    models_available: bpy.props.EnumProperty(
        name="Models",
        description="Pick a model from the available models you have downloaded",
        items=update_models,
        default=None,
    )
    loras_available: bpy.props.EnumProperty(
        name="Loras",
        description="Pick a lora from the available loras you have downloaded",
        items=update_loras,
        default=0,
    )
    lora_scale: bpy.props.FloatProperty(
        name="Lora Scale",
        description="Weight for the lora",
        default=1.0,
        min=0.0,
        max=3.0,
    )
    upscaler_available: bpy.props.EnumProperty(
        name="ERSGAN Upscaler",
        description="Pick an upscaler from the available upscalers you have downloaded",
        items=update_upscalers,
        default=0,
    )
    upscaler_scale: bpy.props.FloatProperty(
        name="Upscaler Scale",
        description="Scale multiplier for the upscaler",
        default=1.0,
        min=0.1,
        max=3.0,
    )

    # Properties for the diffusion generation
    prompt: bpy.props.StringProperty(
        name="Prompt",
        description="Text prompt for the diffusion effect",
        default="wood planks",
    )

    # Quality enhancement system
    enhance_prompt: bpy.props.BoolProperty(
        name="Smart Enhancement",
        description="Automatically enhance prompts with quality terms for better texture generation",
        default=True,
    )

    # Enhancement templates (editable in Advanced section)
    quality_prompt_suffix: bpy.props.StringProperty(
        name="Quality Enhancement",
        description="Quality terms automatically added to prompts when Smart Enhancement is enabled",
        default="organic surface, seamless texture, tileable, top-down view, flat lighting, no shadows, no highlights, uniform pattern, albedo map, base color only, PBR texture, high detail, 4k resolution, ultra sharp, no logos, no borders",
    )

    quality_negative_prompt: bpy.props.StringProperty(
        name="Quality Negative Prompt",
        description="Negative terms automatically added when Smart Enhancement is enabled",
        default="shadows, lighting effects, reflections, text, logo, objects, 3D render, depth, photorealistic, noise, background, blur, photo",
    )
    n_steps: bpy.props.IntProperty(
        name="N_Steps",
        description="Number of steps for the diffusion process",
        default=30,
        min=1,
    )
    cfg_scale: bpy.props.FloatProperty(
        name="CFG Scale",
        description="Classifier-Free Guidance scale for the diffusion process",
        default=5.5,
        min=0.0,
    )
    controlnet_scale: bpy.props.FloatProperty(
        name="ControlNet Scale",
        description="Controlnet Strengh for the conditioning. 0 means no depth conditioning",
        default=0.7,
        min=0.0,
    )
    seed: bpy.props.IntProperty(
        name="seed",
        description="Seed for the generation.",
        default=42,
        min=0,
        max=1000000,
    )
    random_seed: bpy.props.BoolProperty(
        name="Random Seed",
        description="Toggle random seed for generationg",
        default=True,
    )

    sampler_name: bpy.props.EnumProperty(
        name="Sampler Name",
        description="Sampler Name",
        items=[
            ("euler", "Euler", ""),
            ("euler_cfg_pp", "Euler CFG PP", ""),
            ("euler_ancestral", "Euler Ancestral", ""),
            ("euler_ancestral_cfg_pp", "Euler Ancestral CFG PP", ""),
            ("heun", "Heun", ""),
            ("heunpp2", "Heun PP2", ""),
            ("dpm_2", "DPM 2", ""),
            ("dpm_2_ancestral", "DPM 2 Ancestral", ""),
            ("lms", "LMS", ""),
            ("dpm_fast", "DPM Fast", ""),
            ("dpm_adaptive", "DPM Adaptive", ""),
            ("dpmpp_2s_ancestral", "DPM++ 2S Ancestral", ""),
            ("dpmpp_2s_ancestral_cfg_pp", "DPM++ 2S Ancestral CFG PP", ""),
            ("dpmpp_sde", "DPM++ SDE", ""),
            ("dpmpp_sde_gpu", "DPM++ SDE GPU", ""),
            ("dpmpp_2m", "DPM++ 2M", ""),
            ("dpmpp_2m_cfg_pp", "DPM++ 2M CFG PP", ""),
            ("dpmpp_2m_sde", "DPM++ 2M SDE", ""),
            ("dpmpp_2m_sde_gpu", "DPM++ 2M SDE GPU", ""),
            ("dpmpp_3m_sde", "DPM++ 3M SDE", ""),
            ("dpmpp_3m_sde_gpu", "DPM++ 3M SDE GPU", ""),
            ("ddpm", "DDPM", ""),
            ("lcm", "LCM", ""),
            ("ipndm", "IPNDM", ""),
            ("ipndm_v", "IPNDM V", ""),
            ("deis", "DEIS", ""),
            ("ddim", "DDIM", ""),
            ("uni_pc", "Uni PC", ""),
            ("uni_pc_bh2", "Uni PC BH2", ""),
        ],
        default="dpmpp_2m_sde_gpu",
    )

    negative_prompt: bpy.props.StringProperty(
        name="Negative Prompt",
        description="Negative text prompt for the diffusion effect",
        default="",
    )
    scheduler: bpy.props.EnumProperty(
        name="Scheduler",
        description="Scheduler for the diffusion process",
        items=[
            ("normal", "Normal", ""),
            ("karras", "Karras", ""),
            ("exponential", "Exponential", ""),
            ("sgm_uniform", "SGM Uniform", ""),
            ("simple", "Simple", ""),
            ("ddim_uniform", "DDIM Uniform", ""),
            ("beta", "Beta", ""),
            ("linear_quadratic", "Linear Quadratic", ""),
        ],
        default="normal",
    )

    height: bpy.props.IntProperty(
        name="Height", description="Height of the generated image", default=1024
    )

    width: bpy.props.IntProperty(
        name="Width", description="Height of the generated image", default=1024
    )


def register():
    bpy.utils.register_class(MeshItem)
    bpy.utils.register_class(DiffusionProperties)
    bpy.types.Scene.diffusion_properties = bpy.props.PointerProperty(
        type=DiffusionProperties
    )


def unregister():
    bpy.utils.unregister_class(MeshItem)
    bpy.utils.unregister_class(DiffusionProperties)
    del bpy.types.Scene.diffusion_properties

from typing import Optional

import bpy

# pyright: reportAttributeAccessIssue=false


class DiffusionPanel(bpy.types.Panel):
    bl_label = "Diffusion Panel"
    bl_idname = "OBJECT_PT_DiffusionPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Diffusion"

    def draw(self, context: Optional[bpy.types.Context]):
        assert context is not None
        layout = self.layout

        scene = context.scene
        diffusion_properties = scene.diffusion_properties

        layout.prop(diffusion_properties, "models_available")

        box = layout.box()
        box.label(text="Prompt Settings:", icon="BRUSH_DATA")
        box.prop(diffusion_properties, "prompt")

        box.prop(diffusion_properties, "negative_prompt")
        box.prop(diffusion_properties, "enhance_prompt")

        box.separator()

        row = box.row()
        row.prop(diffusion_properties, "n_steps")
        row.prop(diffusion_properties, "cfg_scale")

        row = box.row()
        row.prop(diffusion_properties, "seed")
        row.prop(diffusion_properties, "random_seed")

        box.separator()

        generate_op = box.operator(
            "diffusion.generate_unified", text="GENERATE", icon="RENDER_STILL"
        )
        generate_op.create_material = True

        generate_texture_op = box.operator(
            "diffusion.generate_unified",
            text="GENERATE TEXTURE ONLY",
            icon="RENDER_STILL",
        )
        generate_texture_op.create_material = False


class AdvancedDiffusionPanel(bpy.types.Panel):
    bl_label = "Advanced Diffusion"
    bl_idname = "OBJECT_PT_AdvancedDiffusion"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Diffusion"
    bl_parent_id = "OBJECT_PT_DiffusionPanel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: Optional[bpy.types.Context]):
        assert context is not None
        layout = self.layout
        diffusion_properties = context.scene.diffusion_properties

        layout.separator()

        # Smart Enhancement Settings
        box = layout.box()
        box.label(text="Smart Enhancement Settings:", icon="MODIFIER")
        box.prop(diffusion_properties, "quality_prompt_suffix", text="Quality Terms")
        box.prop(
            diffusion_properties, "quality_negative_prompt", text="Quality Negative"
        )

        layout.separator()

        layout.prop(diffusion_properties, "sampler_name")
        layout.prop(diffusion_properties, "scheduler")

        layout.separator()

        size_row = layout.row()
        size_row.prop(diffusion_properties, "width")
        size_row.prop(diffusion_properties, "height")


class LoRAPanel(bpy.types.Panel):
    bl_label = "LoRA"
    bl_idname = "OBJECT_PT_LoRA"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Diffusion"
    bl_parent_id = "OBJECT_PT_DiffusionPanel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: Optional[bpy.types.Context]):
        assert context is not None
        layout = self.layout
        diffusion_properties = context.scene.diffusion_properties

        layout.prop(diffusion_properties, "loras_available")
        layout.prop(diffusion_properties, "lora_scale")


class UpscalerPanel(bpy.types.Panel):
    bl_label = "ERSGAN Upscaler"
    bl_idname = "OBJECT_PT_ERSGAN"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Diffusion"
    bl_parent_id = "OBJECT_PT_DiffusionPanel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: Optional[bpy.types.Context]):
        assert context is not None
        layout = self.layout
        diffusion_properties = context.scene.diffusion_properties

        layout.prop(diffusion_properties, "upscaler_available")


# Register classes
def register():
    bpy.utils.register_class(DiffusionPanel)
    bpy.utils.register_class(AdvancedDiffusionPanel)
    bpy.utils.register_class(LoRAPanel)
    bpy.utils.register_class(UpscalerPanel)


def unregister():
    bpy.utils.unregister_class(DiffusionPanel)
    bpy.utils.unregister_class(AdvancedDiffusionPanel)
    bpy.utils.unregister_class(LoRAPanel)
    bpy.utils.unregister_class(UpscalerPanel)

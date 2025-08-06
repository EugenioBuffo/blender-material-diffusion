import json
import random
import uuid
from pathlib import Path
from typing import Optional, Set

import bpy

# Import our centralized backend function
from ..functions.utils import backend_request

# pyright: reportAttributeAccessIssue=false


class PromptEnhancer:
    """Handles prompt enhancement with quality terms"""

    @staticmethod
    def get_enhanced_prompts(diffusion_props):
        """Get enhanced prompts based on user settings"""
        base_prompt = diffusion_props.prompt.strip()
        base_negative = diffusion_props.negative_prompt.strip()

        if diffusion_props.enhance_prompt:
            # Add quality enhancement to positive prompt
            quality_suffix = diffusion_props.quality_prompt_suffix.strip()
            if quality_suffix:
                enhanced_prompt = (
                    f"{base_prompt}, {quality_suffix}"
                    if base_prompt
                    else quality_suffix
                )
            else:
                enhanced_prompt = base_prompt

            # Add quality negative terms
            quality_negative = diffusion_props.quality_negative_prompt.strip()
            if quality_negative:
                enhanced_negative = (
                    f"{base_negative}, {quality_negative}"
                    if base_negative
                    else quality_negative
                )
            else:
                enhanced_negative = base_negative
        else:
            # Use prompts as-is
            enhanced_prompt = base_prompt
            enhanced_negative = base_negative

        return enhanced_prompt, enhanced_negative


class TextureGeneratorCore:
    """Core texture generation functionality shared between different operators"""

    @staticmethod
    def create_history_item(
        context, generation_uuid: str, mesh_name: str = "", create_material: bool = True
    ):
        """Create and configure a history item for texture generation"""
        scene = context.scene
        history_props = scene.history_properties
        diffusion_props = scene.diffusion_properties

        # Get enhanced prompts
        enhanced_prompt, enhanced_negative = PromptEnhancer.get_enhanced_prompts(
            diffusion_props
        )

        # Create new history item
        new_history_item = history_props.history_collection.add()
        new_history_item.id = history_props.history_counter
        new_history_item.uuid = generation_uuid
        new_history_item.prompt = enhanced_prompt  # Use enhanced prompt
        new_history_item.negative_prompt = enhanced_negative  # Use enhanced negative
        new_history_item.seed = diffusion_props.seed
        new_history_item.cfg_scale = diffusion_props.cfg_scale
        new_history_item.n_steps = diffusion_props.n_steps
        new_history_item.scheduler = diffusion_props.scheduler
        new_history_item.width = diffusion_props.width
        new_history_item.height = diffusion_props.height
        new_history_item.mesh_name = mesh_name
        new_history_item.texture_only = not create_material
        new_history_item.model_name = diffusion_props.models_available
        new_history_item.status = "GENERATING"
        new_history_item.created_time = __import__("time").perf_counter()

        # Increment counter
        history_props.history_counter += 1

        return new_history_item

    @staticmethod
    def start_generation_pipeline(context, generation_uuid: str):
        """Start the complete generation pipeline"""
        # Skip update_history since we already created the complete history item
        # Just send request and start monitoring
        bpy.ops.diffusion.send_request(uuid=generation_uuid)
        bpy.ops.diffusion.fetch_history(uuid=generation_uuid)


class TextureGenerator(bpy.types.Operator):
    """Unified texture generator that can create texture with or without material"""

    bl_idname = "diffusion.generate_unified"
    bl_label = "Generate Texture"
    bl_description = "Generate texture with optional material creation"

    create_material: bpy.props.BoolProperty(
        name="Create Material",
        description="Whether to create a new material with advanced controls",
        default=True,
    )

    def execute(self, context):
        generation_uuid = str(uuid.uuid4())

        if self.create_material:
            # Full material generation - get/create mesh object
            bpy.ops.diffusion.obtain_mesh(uuid=generation_uuid)

            # Get the mesh name from the active object (obtain_mesh sets it)
            active_obj = context.active_object
            if active_obj and active_obj.type == "MESH":
                mesh_name = active_obj.name
            else:
                self.report({"ERROR"}, "No valid mesh object found")
                return {"CANCELLED"}

            # Create history item
            TextureGeneratorCore.create_history_item(
                context, generation_uuid, mesh_name, create_material=True
            )

        else:
            # Texture-only generation - requires selected mesh
            active_object = context.active_object
            if not active_object:
                active_object = (
                    context.selected_objects[0] if context.selected_objects else None
                )

            if not active_object or active_object.type != "MESH":
                self.report(
                    {"ERROR"}, "Please select a mesh object for texture-only generation"
                )
                return {"CANCELLED"}

            # Create history item with mesh reference
            TextureGeneratorCore.create_history_item(
                context, generation_uuid, active_object.name, create_material=False
            )

        # Start generation pipeline
        TextureGeneratorCore.start_generation_pipeline(context, generation_uuid)

        if self.create_material:
            self.report({"INFO"}, "Material generation started")
        else:
            self.report({"INFO"}, "Texture-only generation started")

        return {"FINISHED"}


class MaterialCreator:
    """Handles material creation and texture application logic"""

    @staticmethod
    def create_diffusion_control_nodegroup():
        """Create a reusable node group for diffusion material controls"""
        # Check if the node group already exists
        if "Diffusion_Material_Controls" in bpy.data.node_groups:
            return bpy.data.node_groups["Diffusion_Material_Controls"]

        # Create new node group
        group = bpy.data.node_groups.new(
            "Diffusion_Material_Controls", "ShaderNodeTree"
        )

        # Create group input/output nodes
        group_input = group.nodes.new("NodeGroupInput")
        group_output = group.nodes.new("NodeGroupOutput")

        # Add input sockets (Blender 4.5 API)
        group.interface.new_socket(
            name="Image", in_out="INPUT", socket_type="NodeSocketColor"
        )
        group.interface.new_socket(
            name="Brightness", in_out="INPUT", socket_type="NodeSocketFloat"
        )
        group.interface.new_socket(
            name="Contrast", in_out="INPUT", socket_type="NodeSocketFloat"
        )
        group.interface.new_socket(
            name="Saturation", in_out="INPUT", socket_type="NodeSocketFloat"
        )
        group.interface.new_socket(
            name="Hue Shift", in_out="INPUT", socket_type="NodeSocketFloat"
        )
        group.interface.new_socket(
            name="Roughness", in_out="INPUT", socket_type="NodeSocketFloat"
        )
        group.interface.new_socket(
            name="Bump Strength", in_out="INPUT", socket_type="NodeSocketFloat"
        )
        group.interface.new_socket(
            name="Metallic", in_out="INPUT", socket_type="NodeSocketFloat"
        )
        group.interface.new_socket(
            name="Displacement", in_out="INPUT", socket_type="NodeSocketFloat"
        )

        # Add output sockets
        group.interface.new_socket(
            name="Base Color", in_out="OUTPUT", socket_type="NodeSocketColor"
        )
        group.interface.new_socket(
            name="Roughness", in_out="OUTPUT", socket_type="NodeSocketFloat"
        )
        group.interface.new_socket(
            name="Normal", in_out="OUTPUT", socket_type="NodeSocketVector"
        )
        group.interface.new_socket(
            name="Metallic", in_out="OUTPUT", socket_type="NodeSocketFloat"
        )
        group.interface.new_socket(
            name="Displacement", in_out="OUTPUT", socket_type="NodeSocketVector"
        )

        # Create internal nodes
        hue_sat = group.nodes.new("ShaderNodeHueSaturation")
        bright_contrast = group.nodes.new("ShaderNodeBrightContrast")
        rgb_to_bw = group.nodes.new("ShaderNodeRGBToBW")
        bump = group.nodes.new("ShaderNodeBump")
        displacement = group.nodes.new("ShaderNodeDisplacement")
        bump_colorramp = group.nodes.new("ShaderNodeValToRGB")
        displacement_colorramp = group.nodes.new("ShaderNodeValToRGB")

        # Position nodes
        group_input.location = (-800, 0)
        hue_sat.location = (-550, 300)
        bright_contrast.location = (-300, 300)
        rgb_to_bw.location = (-550, -100)
        bump_colorramp.location = (-400, -100)
        bump.location = (-200, -100)
        displacement_colorramp.location = (-400, -350)
        displacement.location = (-200, -350)
        group_output.location = (50, 0)

        # Create links
        links = group.links
        links.new(group_input.outputs["Image"], hue_sat.inputs["Color"])
        links.new(group_input.outputs["Hue Shift"], hue_sat.inputs["Hue"])
        links.new(group_input.outputs["Saturation"], hue_sat.inputs["Saturation"])
        links.new(hue_sat.outputs["Color"], bright_contrast.inputs["Color"])
        links.new(group_input.outputs["Brightness"], bright_contrast.inputs["Bright"])
        links.new(group_input.outputs["Contrast"], bright_contrast.inputs["Contrast"])
        links.new(group_input.outputs["Image"], rgb_to_bw.inputs["Color"])
        links.new(rgb_to_bw.outputs["Val"], bump_colorramp.inputs["Fac"])
        links.new(bump_colorramp.outputs["Color"], bump.inputs["Height"])
        links.new(group_input.outputs["Bump Strength"], bump.inputs["Strength"])
        links.new(rgb_to_bw.outputs["Val"], displacement_colorramp.inputs["Fac"])
        links.new(
            displacement_colorramp.outputs["Color"], displacement.inputs["Height"]
        )
        links.new(group_input.outputs["Displacement"], displacement.inputs["Scale"])
        links.new(bright_contrast.outputs["Color"], group_output.inputs["Base Color"])
        links.new(group_input.outputs["Roughness"], group_output.inputs["Roughness"])
        links.new(bump.outputs["Normal"], group_output.inputs["Normal"])
        links.new(group_input.outputs["Metallic"], group_output.inputs["Metallic"])
        links.new(
            displacement.outputs["Displacement"], group_output.inputs["Displacement"]
        )

        return group

    @staticmethod
    def get_texture_image(history_item):
        """Get the texture image from Blender's data"""
        # Try new naming system first, fallback to old system
        if hasattr(history_item, "image_name") and history_item.image_name:
            image_name = history_item.image_name.replace(".png", "")
        else:
            image_name = f"Generation_{history_item.id}_{history_item.uuid}"

        # Find image in Blender's data
        if image_name + ".png" in bpy.data.images:
            return bpy.data.images[image_name + ".png"]
        elif image_name in bpy.data.images:
            return bpy.data.images[image_name]
        return None

    @staticmethod
    def apply_texture_only(material, texture_image):
        """Apply texture to existing material (simple mode)"""
        tree = material.node_tree
        if not tree:
            return False

        nodes = tree.nodes
        links = tree.links

        # Find existing image texture node
        image_node = None
        for node in nodes:
            if node.type == "TEX_IMAGE":
                image_node = node
                break

        if image_node:
            # Replace existing image
            image_node.image = texture_image
        else:
            # Create basic image node
            image_node = nodes.new("ShaderNodeTexImage")
            image_node.image = texture_image
            image_node.location = (-300, 300)

            # Connect to principled BSDF
            principled = None
            for node in nodes:
                if node.type == "BSDF_PRINCIPLED":
                    principled = node
                    break

            if principled:
                links.new(image_node.outputs["Color"], principled.inputs["Base Color"])

        return True

    @staticmethod
    def create_full_material(mesh, history_item, texture_image):
        """Create complete material with diffusion controls"""
        from ..operators.history_collection_operators import create_user_friendly_name

        # Create material name
        material_name = create_user_friendly_name(
            history_item.prompt, history_item.id, "Material", 20
        )
        base_name = material_name
        counter = 1
        while material_name in bpy.data.materials:
            material_name = f"{base_name}_{counter}"
            counter += 1

        # Create material
        material = bpy.data.materials.new(name=material_name)
        material.use_nodes = True

        tree = material.node_tree
        nodes = tree.nodes
        links = tree.links

        # Create diffusion control group
        diffusion_control_group = MaterialCreator.create_diffusion_control_nodegroup()

        # Create nodes
        textcoord_node = nodes.new("ShaderNodeTexCoord")
        mapping_node = nodes.new("ShaderNodeMapping")
        image_node = nodes.new("ShaderNodeTexImage")
        control_node = nodes.new("ShaderNodeGroup")

        # Configure control node
        control_node.node_tree = diffusion_control_group
        control_node.name = "Diffusion_Controls"
        control_node.label = "Diffusion Controls"

        # Set default values
        control_node.inputs["Brightness"].default_value = 0.0
        control_node.inputs["Contrast"].default_value = 0.0
        control_node.inputs["Saturation"].default_value = 1.0
        control_node.inputs["Hue Shift"].default_value = 0.5
        control_node.inputs["Roughness"].default_value = 0.8
        control_node.inputs["Bump Strength"].default_value = 0.1
        control_node.inputs["Metallic"].default_value = 0.0
        control_node.inputs["Displacement"].default_value = 0.05

        # Position nodes
        textcoord_node.location = (-600, 0)
        mapping_node.location = (-400, 0)
        image_node.location = (-200, 0)
        control_node.location = (0, 0)

        # Set texture
        image_node.image = texture_image

        # Create connections
        try:
            links.new(textcoord_node.outputs[2], mapping_node.inputs[0])
            links.new(mapping_node.outputs[0], image_node.inputs[0])
            links.new(image_node.outputs[0], control_node.inputs["Image"])
            links.new(
                control_node.outputs["Base Color"], nodes["Principled BSDF"].inputs[0]
            )
            links.new(
                control_node.outputs["Roughness"], nodes["Principled BSDF"].inputs[2]
            )
            links.new(
                control_node.outputs["Normal"], nodes["Principled BSDF"].inputs[5]
            )
            links.new(
                control_node.outputs["Metallic"], nodes["Principled BSDF"].inputs[1]
            )
            if "Displacement" in control_node.outputs:
                links.new(
                    control_node.outputs["Displacement"],
                    nodes["Material Output"].inputs[2],
                )
        except Exception as e:
            print(f"Warning: Could not create some node connections: {e}")
            # Fallback to basic connections
            try:
                links.new(textcoord_node.outputs[2], mapping_node.inputs[0])
                links.new(mapping_node.outputs[0], image_node.inputs[0])
                links.new(image_node.outputs[0], nodes["Principled BSDF"].inputs[0])
            except Exception as e2:
                print(f"Error: Could not create basic connections: {e2}")
                return None

        # Add material to mesh
        # mesh.data.materials.append(material)
        mesh.active_material = material

        return material


class ApplyTextureOperator(bpy.types.Operator):
    """Apply generated texture to material"""

    bl_idname = "diffusion.apply_texture"
    bl_label = "Apply Texture"
    bl_description = "Apply generated texture to material"

    id: bpy.props.IntProperty(name="ID")

    def find_history_item(self, collection):
        for history_item in collection:
            if history_item.id == self.id:
                return history_item
        return None

    def execute(self, context: Optional[bpy.types.Context]):
        if not context:
            return {"CANCELLED"}

        scene = context.scene
        history_props = scene.history_properties

        # Find history item
        history_item = self.find_history_item(history_props.history_collection)
        if not history_item:
            self.report({"ERROR"}, "History item not found")
            return {"CANCELLED"}

        # Validate mesh exists
        mesh_name = history_item.mesh_name
        if mesh_name not in bpy.data.objects:
            self.report({"ERROR"}, f"Mesh '{mesh_name}' not found in scene")
            return {"CANCELLED"}

        mesh = bpy.data.objects[mesh_name]

        # Get texture image
        texture_image = MaterialCreator.get_texture_image(history_item)
        if not texture_image:
            self.report({"ERROR"}, "Texture image not found")
            return {"CANCELLED"}

        # Check if texture-only mode
        is_texture_only = getattr(history_item, "texture_only", False)

        if is_texture_only:
            # Texture-only: use existing material or create basic one
            if mesh.active_material:
                material = mesh.active_material
            else:
                material = bpy.data.materials.new(name=f"{mesh.name}_TextureOnly")
                material.use_nodes = True
                mesh.data.materials.append(material)
                mesh.active_material = material

            success = MaterialCreator.apply_texture_only(material, texture_image)
            if success:
                self.report({"INFO"}, f"Applied texture to material: {material.name}")
            else:
                self.report({"ERROR"}, "Failed to apply texture")
                return {"CANCELLED"}
        else:
            # Full material creation
            material = MaterialCreator.create_full_material(
                mesh, history_item, texture_image
            )
            if material:
                self.report({"INFO"}, f"Created material: {material.name}")
            else:
                self.report({"ERROR"}, "Failed to create material")
                return {"CANCELLED"}

        return {"FINISHED"}


class SendRequestOperator(bpy.types.Operator):
    """Operator used to send request to the comfyUI backend"""

    bl_idname = "diffusion.send_request"
    bl_label = "Send Request"
    bl_description = "Send a request to the comfyUI backend to generate the image"

    uuid: bpy.props.StringProperty(name="UUID")

    # TODO: change from diffusion props to history item props
    def get_history_item(self, context: bpy.types.Context) -> Optional[dict]:
        history_props = context.scene.history_properties
        for item in history_props.history_collection:
            if item.uuid == self.uuid:
                return item
        return None

    def execute(self, context: Optional[bpy.types.Context]) -> Set[str]:
        assert context is not None
        assert bpy.context is not None

        scene = context.scene
        diffusion_props = scene.diffusion_properties

        output_prefix = f"blender-texture/{self.uuid}_output"

        # Get History Item to save properties
        history_item = self.get_history_item(context)
        if history_item is None:
            self.report({"ERROR"}, "History item not found")
            return {"CANCELLED"}

        # Prepare Request

        model_name = diffusion_props.models_available

        is_flux = "flux" in model_name.lower()

        if is_flux:
            json_path = Path(__file__).parent.parent.parent / "workflows" / "flux.json"
        else:
            json_path = (
                Path(__file__).parent.parent.parent / "workflows" / "generic.json"
            )

        with open(json_path) as f:
            prompt_workflow_json = f.read()
        prompt_request = json.loads(prompt_workflow_json)

        # Seed Logic
        seed = diffusion_props.seed

        if diffusion_props.random_seed:
            seed = random.randint(1, 1000000)
            diffusion_props.seed = seed
            history_item.seed = seed

        # Get enhanced prompts for the request
        enhanced_prompt, enhanced_negative = PromptEnhancer.get_enhanced_prompts(
            diffusion_props
        )

        prompt_request["3"]["inputs"]["seed"] = seed
        prompt_request["4"]["inputs"]["ckpt_name"] = diffusion_props.models_available
        # Use enhanced prompt
        prompt_request["6"]["inputs"]["text"] = enhanced_prompt
        # Use enhanced negative
        prompt_request["7"]["inputs"]["text"] = enhanced_negative

        if is_flux:
            prompt_request["5"]["inputs"]["guidance"] = diffusion_props.cfg_scale
        else:
            prompt_request["3"]["inputs"]["cfg"] = diffusion_props.cfg_scale

        prompt_request["3"]["inputs"]["steps"] = diffusion_props.n_steps
        prompt_request["3"]["inputs"]["sampler_name"] = diffusion_props.sampler_name
        prompt_request["3"]["inputs"]["scheduler"] = diffusion_props.scheduler

        # Input-Output Name format
        prompt_request["9"]["inputs"]["filename_prefix"] = output_prefix

        if diffusion_props.loras_available != "None":
            print("Using LoRA")
            prompt_request["3"]["inputs"]["model"] = ["2", 0]
            prompt_request["2"]["inputs"]["lora_name"] = diffusion_props.loras_available
            prompt_request["2"]["inputs"]["strength_model"] = diffusion_props.lora_scale
            prompt_request["6"]["inputs"]["clip"] = ["2", 1]
            prompt_request["7"]["inputs"]["clip"] = ["2", 1]

        if diffusion_props.upscaler_available != "None":
            print("Using Upscaler")
            prompt_request["38"]["inputs"]["image"] = ["8", 0]
            prompt_request["9"]["inputs"]["images"] = ["38", 0]
            prompt_request["37"]["inputs"][
                "model_name"
            ] = diffusion_props.upscaler_available
            # prompt_request["2"]["inputs"]["strength_model"] = diffusion_props.upscaler_scale

        # Send Request to queue
        try:
            prompt_data = {"prompt": prompt_request}

            response = backend_request("/prompt", method="POST", json_data=prompt_data)

            if response and response.status_code == 200:
                print("Request Sent!")
            else:
                error_msg = f"Backend returned status code: {response.status_code if response else 'No response'}"
                self.report({"ERROR"}, f"Failed to send request: {error_msg}")
                print(f"Error sending request: {error_msg}")
                return {"CANCELLED"}

        except Exception as e:
            self.report({"ERROR"}, f"Failed to send request: {str(e)}")
            print(f"Error sending request: {e}")
            return {"CANCELLED"}

        return {"FINISHED"}


def generation_register():
    bpy.utils.register_class(TextureGenerator)
    bpy.utils.register_class(ApplyTextureOperator)
    bpy.utils.register_class(SendRequestOperator)


def generation_unregister():
    bpy.utils.unregister_class(TextureGenerator)
    bpy.utils.unregister_class(ApplyTextureOperator)
    bpy.utils.unregister_class(SendRequestOperator)

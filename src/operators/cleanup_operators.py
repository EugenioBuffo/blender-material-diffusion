import bpy


class CleanupOrphanedOperator(bpy.types.Operator):
    bl_idname = "diffusion.cleanup_orphaned"
    bl_label = "Clean Orphaned Data"
    bl_description = "Remove all unused materials and images (0 users)"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        removed_materials = 0
        removed_images = 0

        # Remove orphaned materials
        for mat in list(bpy.data.materials):
            if mat.users == 0:
                bpy.data.materials.remove(mat)
                removed_materials += 1

        # Remove orphaned images
        for img in list(bpy.data.images):
            if img.users == 0:
                bpy.data.images.remove(img)
                removed_images += 1

        total_removed = removed_materials + removed_images
        self.report(
            {"INFO"},
            f"Removed {removed_materials} materials and {removed_images} images ({total_removed} total)",
        )
        return {"FINISHED"}


class CleanupAllDiffusionOperator(bpy.types.Operator):
    bl_idname = "diffusion.cleanup_all_diffusion"
    bl_label = "Clean All Diffusion Data"
    bl_description = "Remove ALL materials and images created by diffusion addon"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        removed_materials = 0
        removed_images = 0

        # Remove diffusion materials
        for mat in list(bpy.data.materials):
            if (
                mat.name.startswith("Diffusion_")
                or
                # Material_XXX_prompt pattern (specific diffusion naming)
                (
                    mat.name.startswith("Material_")
                    and len(mat.name.split("_")) >= 3
                    and mat.name.split("_")[1].isdigit()
                )
                or
                # Legacy patterns
                ("Material " in mat.name and "_" in mat.name)
                or "diffusion" in mat.name.lower()
            ):
                bpy.data.materials.remove(mat)
                removed_materials += 1

        # Remove diffusion images
        for img in list(bpy.data.images):
            if (
                img.name.startswith("Diffusion_")
                or ("Generation_" in img.name)
                or ("_output_" in img.name)
                or ("diffusion" in img.name.lower())
            ):
                bpy.data.images.remove(img)
                removed_images += 1

        total_removed = removed_materials + removed_images
        self.report(
            {"INFO"},
            f"Removed {removed_materials} diffusion materials and {removed_images} diffusion images ({total_removed} total)",
        )
        return {"FINISHED"}


class CleanupMaterialsOperator(bpy.types.Operator):
    bl_idname = "diffusion.cleanup_materials"
    bl_label = "Clean All Diffusion Materials"
    bl_description = "Remove all materials created by diffusion addon"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        removed_count = 0

        for mat in list(bpy.data.materials):
            if (
                mat.name.startswith("Diffusion_")
                or
                # Material_XXX_prompt pattern (specific diffusion naming)
                (
                    mat.name.startswith("Material_")
                    and len(mat.name.split("_")) >= 3
                    and mat.name.split("_")[1].isdigit()
                )
                or
                # Legacy patterns
                ("Material " in mat.name and "_" in mat.name)
                or "diffusion" in mat.name.lower()
            ):
                bpy.data.materials.remove(mat)
                removed_count += 1

        self.report({"INFO"}, f"Removed {removed_count} diffusion materials")
        return {"FINISHED"}


class CleanupImagesOperator(bpy.types.Operator):
    bl_idname = "diffusion.cleanup_images"
    bl_label = "Clean All Diffusion Images"
    bl_description = "Remove all images created by diffusion addon"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        removed_count = 0

        for img in list(bpy.data.images):
            if (
                img.name.startswith("Diffusion_")
                or ("Generation_" in img.name)
                or ("_output_" in img.name)
                or ("diffusion" in img.name.lower())
            ):
                bpy.data.images.remove(img)
                removed_count += 1

        self.report({"INFO"}, f"Removed {removed_count} diffusion images")
        return {"FINISHED"}


class DeleteMaterialOperator(bpy.types.Operator):
    bl_idname = "diffusion.delete_material"
    bl_label = "Delete Material"
    bl_description = "Delete a specific material"
    bl_options = {"REGISTER", "UNDO"}

    material_name: bpy.props.StringProperty(name="Material Name")

    def execute(self, context):
        mat = bpy.data.materials.get(self.material_name)
        if mat:
            bpy.data.materials.remove(mat)
            self.report({"INFO"}, f"Removed material '{self.material_name}'")
        else:
            self.report({"ERROR"}, f"Material '{self.material_name}' not found")
        return {"FINISHED"}


class DeleteImageOperator(bpy.types.Operator):
    bl_idname = "diffusion.delete_image"
    bl_label = "Delete Image"
    bl_description = "Delete a specific image"
    bl_options = {"REGISTER", "UNDO"}

    image_name: bpy.props.StringProperty(name="Image Name")

    def execute(self, context):
        img = bpy.data.images.get(self.image_name)
        if img:
            bpy.data.images.remove(img)
            self.report({"INFO"}, f"Removed image '{self.image_name}'")
        else:
            self.report({"ERROR"}, f"Image '{self.image_name}' not found")
        return {"FINISHED"}


class HistoryCleanupOperator(bpy.types.Operator):
    bl_idname = "diffusion.cleanup_history"
    bl_label = "Clean History"
    bl_description = (
        "Remove completed or failed history items and their associated data"
    )
    bl_options = {"REGISTER", "UNDO"}

    cleanup_type: bpy.props.EnumProperty(
        name="Cleanup Type",
        items=[
            ("COMPLETED", "Completed Only", "Remove only completed generations"),
            ("FAILED", "Failed Only", "Remove only failed generations"),
            ("ALL", "All", "Remove all history items"),
        ],
        default="COMPLETED",
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        history_props = context.scene.history_properties
        items_to_remove = []

        for i, item in enumerate(history_props.history_collection):
            should_remove = False

            if self.cleanup_type == "COMPLETED" and item.status == "COMPLETED":
                should_remove = True
            elif self.cleanup_type == "FAILED" and item.status == "FAILED":
                should_remove = True
            elif self.cleanup_type == "ALL":
                should_remove = True

            if should_remove:
                items_to_remove.append(i)

                # Import the utility function for naming
                from ..operators.history_collection_operators import (
                    create_user_friendly_name,
                )

                # Remove associated material using new naming pattern
                material_name = create_user_friendly_name(
                    item.prompt, item.id, "Material", 20
                )
                mat = bpy.data.materials.get(material_name)
                if mat:
                    bpy.data.materials.remove(mat)
                else:
                    # Fallback to old naming pattern
                    old_mat_name = f"Material {item.id}_{item.uuid}"
                    mat = bpy.data.materials.get(old_mat_name)
                    if mat:
                        bpy.data.materials.remove(mat)

                # Remove associated image using new naming pattern
                image_name = (
                    create_user_friendly_name(item.prompt, item.id, "Diffusion", 20)
                    + ".png"
                )
                img = bpy.data.images.get(image_name)
                if img:
                    bpy.data.images.remove(img)
                else:
                    # Fallback to old naming pattern
                    old_img_name = f"Generation_{item.id}_{item.uuid}.png"
                    img = bpy.data.images.get(old_img_name)
                    if img:
                        # Remove history items in reverse order to maintain indices
                        bpy.data.images.remove(img)
        for i in reversed(items_to_remove):
            history_props.history_collection.remove(i)

        self.report(
            {"INFO"},
            f"Cleaned {len(items_to_remove)} history items and their associated data",
        )
        return {"FINISHED"}


class SelectMaterialOperator(bpy.types.Operator):
    bl_idname = "diffusion.select_material"
    bl_label = "Select Material"
    bl_description = "Select and show material in Shader Editor"
    bl_options = {"REGISTER"}

    material_name: bpy.props.StringProperty(name="Material Name")

    def execute(self, context):
        mat = bpy.data.materials.get(self.material_name)
        if mat:
            # Switch to Shading workspace if available
            if "Shading" in bpy.data.workspaces:
                bpy.context.window.workspace = bpy.data.workspaces["Shading"]

            # Set the material as active in shader editor
            for area in bpy.context.screen.areas:
                if area.type == "NODE_EDITOR":
                    for space in area.spaces:
                        if space.type == "NODE_EDITOR":
                            space.tree_type = "ShaderNodeTree"
                            space.node_tree = mat.node_tree
                            break

            # If there's an active object, assign the material
            if context.active_object and context.active_object.type == "MESH":
                if mat.name not in [
                    slot.material.name
                    for slot in context.active_object.material_slots
                    if slot.material
                ]:
                    context.active_object.data.materials.append(mat)
                # Set as active material
                for i, slot in enumerate(context.active_object.material_slots):
                    if slot.material and slot.material.name == mat.name:
                        context.active_object.active_material_index = i
                        break

            self.report({"INFO"}, f"Selected material '{self.material_name}'")
        else:
            self.report({"ERROR"}, f"Material '{self.material_name}' not found")
        return {"FINISHED"}


class SelectImageOperator(bpy.types.Operator):
    bl_idname = "diffusion.select_image"
    bl_label = "Select Image"
    bl_description = "Select and show image in Image Editor"
    bl_options = {"REGISTER"}

    image_name: bpy.props.StringProperty(name="Image Name")

    def execute(self, context):
        img = bpy.data.images.get(self.image_name)
        if img:
            # Find and switch to Image Editor
            for area in bpy.context.screen.areas:
                if area.type == "IMAGE_EDITOR":
                    for space in area.spaces:
                        if space.type == "IMAGE_EDITOR":
                            space.image = img
                            break
                    break
            else:
                # If no Image Editor found, try to switch to UV Editing workspace
                if "UV Editing" in bpy.data.workspaces:
                    bpy.context.window.workspace = bpy.data.workspaces["UV Editing"]
                    # Try again to find Image Editor
                    for area in bpy.context.screen.areas:
                        if area.type == "IMAGE_EDITOR":
                            for space in area.spaces:
                                if space.type == "IMAGE_EDITOR":
                                    space.image = img
                                    break
                            break

            self.report({"INFO"}, f"Selected image '{self.image_name}'")
        else:
            self.report({"ERROR"}, f"Image '{self.image_name}' not found")
        return {"FINISHED"}


def register():
    bpy.utils.register_class(CleanupOrphanedOperator)
    bpy.utils.register_class(CleanupAllDiffusionOperator)
    bpy.utils.register_class(CleanupMaterialsOperator)
    bpy.utils.register_class(CleanupImagesOperator)
    bpy.utils.register_class(DeleteMaterialOperator)
    bpy.utils.register_class(DeleteImageOperator)
    bpy.utils.register_class(HistoryCleanupOperator)
    bpy.utils.register_class(SelectMaterialOperator)
    bpy.utils.register_class(SelectImageOperator)


def unregister():
    bpy.utils.unregister_class(CleanupOrphanedOperator)
    bpy.utils.unregister_class(CleanupAllDiffusionOperator)
    bpy.utils.unregister_class(CleanupMaterialsOperator)
    bpy.utils.unregister_class(CleanupImagesOperator)
    bpy.utils.unregister_class(DeleteMaterialOperator)
    bpy.utils.unregister_class(DeleteImageOperator)
    bpy.utils.unregister_class(HistoryCleanupOperator)
    bpy.utils.unregister_class(SelectMaterialOperator)
    bpy.utils.unregister_class(SelectImageOperator)

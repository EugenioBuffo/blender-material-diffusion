from typing import Optional
import bpy

# pyright: reportAttributeAccessIssue=false


class CleanupPanel(bpy.types.Panel):
    bl_label = "Cleanup & Management"
    bl_idname = "OBJECT_PT_DiffusionCleanup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Diffusion"
    bl_options = {"DEFAULT_CLOSED"}

    def get_diffusion_materials(self):
        """Get all materials created by the diffusion addon"""
        diffusion_materials = []
        for mat in bpy.data.materials:
            # Check if material was created by diffusion
            # Use more specific patterns to avoid false positives
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
                diffusion_materials.append(mat)
        return diffusion_materials

    def get_diffusion_images(self):
        """Get all images created by the diffusion addon"""
        diffusion_images = []
        for img in bpy.data.images:
            # Check if image was created by diffusion
            if (
                img.name.startswith("Diffusion_")
                or ("Generation_" in img.name)
                or ("_output_" in img.name)
                or ("diffusion" in img.name.lower())
            ):
                diffusion_images.append(img)
        return diffusion_images

    def get_orphaned_data(self):
        """Get materials and images with 0 users"""
        orphaned_materials = [mat for mat in bpy.data.materials if mat.users == 0]
        orphaned_images = [img for img in bpy.data.images if img.users == 0]
        return orphaned_materials, orphaned_images

    def draw(self, context: Optional[bpy.types.Context]):
        assert context is not None
        layout = self.layout

        # Get data counts
        diffusion_materials = self.get_diffusion_materials()
        diffusion_images = self.get_diffusion_images()
        orphaned_materials, orphaned_images = self.get_orphaned_data()

        # Statistics section
        stats_box = layout.box()
        stats_box.label(text="Statistics", icon="INFO")

        col = stats_box.column(align=True)
        col.label(text=f"Diffusion Materials: {len(diffusion_materials)}")
        col.label(text=f"Diffusion Images: {len(diffusion_images)}")
        col.label(text=f"Orphaned Materials: {len(orphaned_materials)}")
        col.label(text=f"Orphaned Images: {len(orphaned_images)}")

        layout.separator()

        # Quick cleanup section
        cleanup_box = layout.box()
        cleanup_box.label(text="Quick Cleanup", icon="BRUSH_DATA")

        col = cleanup_box.column(align=True)

        # Clean orphaned data
        if orphaned_materials or orphaned_images:
            cleanup_op = col.operator(
                "diffusion.cleanup_orphaned",
                text=f"Clean Orphaned Data ({len(orphaned_materials + orphaned_images)})",
                icon="TRASH",
            )
        else:
            row = col.row()
            row.enabled = False
            row.operator(
                "diffusion.cleanup_orphaned", text="No Orphaned Data", icon="CHECKMARK"
            )

        # Clean all diffusion data
        if diffusion_materials or diffusion_images:
            cleanup_all_op = col.operator(
                "diffusion.cleanup_all_diffusion",
                text=f"Clean All Diffusion Data ({len(diffusion_materials + diffusion_images)})",
                icon="ERROR",
            )
        else:
            row = col.row()
            row.enabled = False
            row.operator(
                "diffusion.cleanup_all_diffusion",
                text="No Diffusion Data",
                icon="CHECKMARK",
            )

        layout.separator()

        # Detailed management section
        detail_box = layout.box()
        detail_box.label(text="Detailed Management", icon="OUTLINER")

        # Materials section
        if diffusion_materials:
            mat_row = detail_box.row()
            mat_row.label(
                text=f"Materials ({len(diffusion_materials)}):", icon="MATERIAL"
            )
            mat_row.operator("diffusion.cleanup_materials", text="Clean All", icon="X")

            # Show first few materials with individual delete buttons
            for i, mat in enumerate(diffusion_materials[:5]):  # Show max 5
                row = detail_box.row()

                # Check if this material is active on current object
                is_active = False
                if context.active_object and context.active_object.active_material:
                    is_active = context.active_object.active_material.name == mat.name

                icon = "RADIOBUT_ON" if is_active else "MATERIAL_DATA"

                # Make material name clickable to select it
                select_op = row.operator(
                    "diffusion.select_material", text=f"  {mat.name}", icon=icon
                )
                select_op.material_name = mat.name

                users_text = f"({mat.users} users)" if mat.users > 0 else "(unused)"
                row.label(text=users_text)
                delete_op = row.operator("diffusion.delete_material", text="", icon="X")
                delete_op.material_name = mat.name

            if len(diffusion_materials) > 5:
                detail_box.label(text=f"  ... and {len(diffusion_materials) - 5} more")

        # Images section
        if diffusion_images:
            img_row = detail_box.row()
            img_row.label(text=f"Images ({len(diffusion_images)}):", icon="IMAGE_DATA")
            img_row.operator("diffusion.cleanup_images", text="Clean All", icon="X")

            # Show first few images with individual delete buttons
            for i, img in enumerate(diffusion_images[:5]):  # Show max 5
                row = detail_box.row()

                # Make image name clickable to select it
                select_op = row.operator(
                    "diffusion.select_image", text=f"  {img.name}", icon="IMAGE_DATA"
                )
                select_op.image_name = img.name

                users_text = f"({img.users} users)" if img.users > 0 else "(unused)"
                row.label(text=users_text)
                delete_op = row.operator("diffusion.delete_image", text="", icon="X")
                delete_op.image_name = img.name

            if len(diffusion_images) > 5:
                detail_box.label(text=f"  ... and {len(diffusion_images) - 5} more")

        if not diffusion_materials and not diffusion_images:
            detail_box.label(text="No diffusion data found", icon="CHECKMARK")


def register():
    bpy.utils.register_class(CleanupPanel)


def unregister():
    bpy.utils.unregister_class(CleanupPanel)

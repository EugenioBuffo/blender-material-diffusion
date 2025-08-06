from typing import Optional

import bpy

# pyright: reportAttributeAccessIssue=false


class HistoryPanel(bpy.types.Panel):
    bl_label = "History Panel"
    bl_idname = "OBJECT_PT_HistoryPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Diffusion"

    def draw(self, context: Optional[bpy.types.Context]):
        assert context is not None

        layout = self.layout
        scene = context.scene
        history_props = scene.history_properties

        layout.label(text="Generation History", icon="PACKAGE")

        # Add cleanup button at the top
        if len(history_props.history_collection) > 0:
            cleanup_row = layout.row()
            cleanup_row.operator(
                "diffusion.cleanup_history_list",
                text="Clean History",
                icon="BRUSH_DATA",
            )

        if len(history_props.history_collection) == 0:
            layout.label(text="No generations yet", icon="INFO")
            return

        # Iterate in reverse order to show most recent items first
        for i, history_item in enumerate(reversed(history_props.history_collection)):
            # Calculate original index for removal operations
            original_index = len(history_props.history_collection) - 1 - i

            # Main item box
            box = layout.box()

            # Header row with ID, status and actions
            header_row = box.row()
            header_row.label(text=f"#{history_item.id}", icon="RENDER_STILL")

            # Status with appropriate icon and color
            status_icons = {
                "PENDING": "TIME",
                "GENERATING": "SETTINGS",
                "FETCHING": "IMPORT",
                "COMPLETED": "CHECKMARK",
                "FAILED": "ERROR",
            }

            status_row = header_row.row()
            status_row.label(
                text=history_item.status.title(),
                icon=status_icons.get(history_item.status, "QUESTION"),
            )

            # Action buttons
            actions_row = header_row.row(align=True)
            if history_item.status == "COMPLETED":
                assign_op = actions_row.operator(
                    "diffusion.assign_history", text="", icon="RESTRICT_SELECT_OFF"
                )
                assign_op.id = history_item.id
            elif history_item.status == "FAILED":
                retry_op = actions_row.operator(
                    "diffusion.retry_generation", text="", icon="FILE_REFRESH"
                )
                retry_op.id = history_item.id

            remove_op = actions_row.operator(
                "diffusion.remove_history", text="", icon="X"
            )
            remove_op.index = original_index
            remove_op.id = history_item.id

            # Details section (collapsible)
            details_row = box.row()
            details_col = details_row.column()

            # Prompt (truncated with tooltip button)
            prompt_row = details_col.row(align=True)
            prompt_display = (
                history_item.prompt[:50] + "..."
                if len(history_item.prompt) > 50
                else history_item.prompt
            )
            prompt_row.label(text=f"Prompt: {prompt_display}")

            # Add tooltip button if prompt is truncated
            if len(history_item.prompt) > 50:
                tooltip_op = prompt_row.operator(
                    "diffusion.show_full_prompt", text="", icon="COPY_ID"
                )
                tooltip_op.full_prompt = history_item.prompt

            # Technical details in a grid
            grid = details_col.grid_flow(columns=2, even_columns=True)
            grid.label(text=f"Seed: {history_item.seed}")
            grid.label(text=f"Steps: {history_item.n_steps}")
            grid.label(text=f"CFG: {history_item.cfg_scale}")
            grid.label(text=f"Size: {history_item.width}x{history_item.height}")

            if history_item.model_name:
                grid.label(text=f"Model: {history_item.model_name}")
            if history_item.mesh_name:
                grid.label(text=f"Mesh: {history_item.mesh_name}")

            # Time info for completed items
            if history_item.status == "COMPLETED":
                if history_item.completed_time > 0 and history_item.created_time > 0:
                    elapsed = history_item.completed_time - history_item.created_time
                    if elapsed > 0:
                        details_col.label(text=f"Completed in {elapsed:.1f}s")
                    else:
                        details_col.label(
                            text=f"Timing error: created={history_item.created_time:.1f}, completed={history_item.completed_time:.1f}"
                        )
                else:
                    missing_data = []
                    if history_item.completed_time <= 0:
                        missing_data.append("completed_time")
                    if history_item.created_time <= 0:
                        missing_data.append("created_time")
                    details_col.label(text=f"Missing: {', '.join(missing_data)}")

            layout.separator()


def register():
    bpy.utils.register_class(HistoryPanel)


def unregister():
    bpy.utils.unregister_class(HistoryPanel)

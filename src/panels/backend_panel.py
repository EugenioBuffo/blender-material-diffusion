import bpy


class BackendPanel(bpy.types.Panel):
    bl_label = "Backend Panel"
    bl_idname = "OBJECT_PT_BackendPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Diffusion"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        backend_properties = scene.backend_properties

        layout.label(text="Backend Settings")
        layout.prop(backend_properties, "backend_availables")
        layout.prop(backend_properties, "url")

        layout.separator()

        # Connection status and button
        if backend_properties.is_connecting:
            layout.label(text="Status: Connecting...", icon="SETTINGS")
            # Disable the button while connecting
            col = layout.column()
            col.enabled = False
            col.operator("backend.connect", text="Connecting...", icon="SETTINGS")
        elif backend_properties.is_connected:
            layout.label(text="Status: Connected", icon="LINKED")
            layout.operator("backend.disconnect", text="Disconnect", icon="UNLINKED")
        else:
            layout.label(text="Status: Disconnected", icon="UNLINKED")
            layout.operator("backend.connect", text="Connect", icon="LINKED")

        layout.separator()

        layout.prop(backend_properties, "timeout")
        layout.prop(backend_properties, "timeout_retries")


def register():
    bpy.utils.register_class(BackendPanel)


def unregister():
    bpy.utils.unregister_class(BackendPanel)

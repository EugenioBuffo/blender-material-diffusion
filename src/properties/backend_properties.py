import bpy
import requests

# Import our centralized backend function
from ..functions.utils import backend_request


class ConnectBackendOperator(bpy.types.Operator):
    bl_idname = "backend.connect"
    bl_label = "Connect to Backend"
    bl_description = "Connect to the backend server"

    def execute(self, context):
        backend_props = context.scene.backend_properties

        # Set connecting state
        backend_props.is_connecting = True

        # Show progress indicator in cursor
        context.window_manager.progress_begin(0, 100)
        context.window_manager.progress_update(25)

        # Update UI to show we're connecting
        self.report({"INFO"}, "Connecting to backend...")

        # Force UI update to show the message immediately
        bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)

        try:
            context.window_manager.progress_update(50)
            # Test connection with a simple endpoint that should always exist
            response = backend_request("/models/checkpoints", timeout=5)

            context.window_manager.progress_update(75)

            if response and response.status_code == 200:
                backend_props.is_connected = True
                context.window_manager.progress_update(100)
                self.report({"INFO"}, "Connected to backend successfully")
            else:
                backend_props.is_connected = False
                status_code = response.status_code if response else "No response"
                self.report(
                    {"ERROR"},
                    f"Backend is online but returned error: HTTP {status_code}",
                )
        except requests.exceptions.ConnectTimeout:
            backend_props.is_connected = False
            self.report(
                {"ERROR"}, "Connection timeout - Backend is offline or not responding"
            )
        except requests.exceptions.ConnectionError:
            backend_props.is_connected = False
            self.report(
                {"ERROR"}, "Connection error - Backend is offline or URL is incorrect"
            )
        except requests.exceptions.Timeout:
            backend_props.is_connected = False
            self.report({"ERROR"}, "Request timeout - Backend is too slow to respond")
        except requests.RequestException as e:
            backend_props.is_connected = False
            self.report({"ERROR"}, f"Connection failed: {str(e)}")
        except Exception as e:
            backend_props.is_connected = False
            self.report({"ERROR"}, f"Unexpected error: {str(e)}")
        finally:
            # Always end progress indicator and reset connecting state
            backend_props.is_connecting = False
            context.window_manager.progress_end()

        return {"FINISHED"}


class DisconnectBackendOperator(bpy.types.Operator):
    bl_idname = "backend.disconnect"
    bl_label = "Disconnect from Backend"
    bl_description = "Disconnect from the backend server"

    def execute(self, context):
        backend_props = context.scene.backend_properties
        backend_props.is_connected = False

        # Clear all caches in diffusion properties - import here to avoid circular imports
        from . import diffusion_properties

        diffusion_properties._global_cache["models"]["data"] = None
        diffusion_properties._global_cache["loras"]["data"] = None
        diffusion_properties._global_cache["upscalers"]["data"] = None

        self.report({"INFO"}, "Disconnected from backend")
        return {"FINISHED"}


class BackendProperties(bpy.types.PropertyGroup):

    backend_availables: bpy.props.EnumProperty(
        name="Backend",
        description="Pick a backend from the supported ones",
        items=[
            ("comfyui", "ComfyUI", "A self-hosted diffusion backend"),
            ("replicate", "Replicate", "Online interaface to run models using API"),
        ],
        default="comfyui",  # Set a default instead of None
    )
    url: bpy.props.StringProperty(
        name="URL",
        description="URL to access the backend",
        default="http://127.0.0.1:8188",
    )

    timeout: bpy.props.IntProperty(
        name="Timeout (seconds)",
        description="Maximum number of seconds to wait for a response before timing out",
        default=60,
        min=1,
        max=1000,
    )

    timeout_retries: bpy.props.IntProperty(
        name="Max Retry (per timeout)",
        description="Maximum number of retries (1 per second) to fetch the image before a timeout",
        default=3,
        min=1,
        max=15,
    )

    expected_completion: bpy.props.IntProperty(
        name="Expected Completion",
        description="Expected time in seconds to complete the image generation",
        default=60,
        min=1,
        max=1000,
    )

    history_collection_name: bpy.props.StringProperty(
        name="History Collection Name", default="Diffusion Camera History"
    )

    # Connection status
    is_connected: bpy.props.BoolProperty(
        name="Connected",
        description="Whether the backend is connected",
        default=False,
    )

    is_connecting: bpy.props.BoolProperty(
        name="Connecting",
        description="Whether a connection attempt is in progress",
        default=False,
    )


def register():
    bpy.utils.register_class(ConnectBackendOperator)
    bpy.utils.register_class(DisconnectBackendOperator)
    bpy.utils.register_class(BackendProperties)
    bpy.types.Scene.backend_properties = bpy.props.PointerProperty(
        type=BackendProperties
    )


def unregister():
    bpy.utils.unregister_class(ConnectBackendOperator)
    bpy.utils.unregister_class(DisconnectBackendOperator)
    bpy.utils.unregister_class(BackendProperties)
    del bpy.types.Scene.backend_properties

import functools
from io import BytesIO
from typing import Optional
import time
import re

import bpy
from PIL import Image

# Import our centralized backend function
from ..functions.utils import backend_request

# pyright: reportAttributeAccessIssue=false


def create_user_friendly_name(
    prompt: str, item_id: int, prefix: str = "Diffusion", max_length: int = 20
) -> str:
    """Create a user-friendly name from prompt and ID"""
    if not prompt:
        prompt = "untitled"

    # Clean the prompt for safe use in names
    prompt_clean = prompt[:max_length].replace(" ", "_")
    prompt_clean = re.sub(r'[<>:"/\\|?*]', "", prompt_clean)
    prompt_clean = re.sub(r"[^\w\-_]", "", prompt_clean)

    return f"{prefix}_{item_id:03d}_{prompt_clean}"


def fetch_image(history_item):
    """Simplified fetch function that just tries to get the image"""

    uuid = history_item.uuid
    file_name = f"{uuid}_output_00001_.png"

    print(f"Fetching image: {file_name} for UUID: {uuid}")

    # Validate URL (this is now done in backend_request, but keep basic validation)
    from ..functions.utils import get_backend_url

    base_url = get_backend_url()
    print(f"Using backend URL: {base_url}")

    if not base_url or not base_url.startswith(("http://", "https://")):
        print(f"Invalid base URL '{base_url}'")
        history_item.status = "FAILED"
        return None

    # Check if we've exceeded maximum attempts (prevent infinite retries)
    history_item.fetch_attempts += 1
    max_attempts = 60  # 2 minutes with 2-second intervals

    if history_item.fetch_attempts > max_attempts:
        print(f"Error: Max fetch attempts ({max_attempts}) exceeded for {uuid}")
        history_item.status = "FAILED"
        return None

    try:
        params = {
            "filename": file_name,
            "subfolder": "blender-texture",
            "type": "output",
        }

        # Update status to fetching
        history_item.status = "FETCHING"

        # print(f"Calling backend_request with params: {params}")
        response = backend_request("/view", method="GET", params=params, timeout=15)

        if response is None:
            print("Backend request returned None - connection failed")
            history_item.status = "FAILED"
            return None

        # print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            # Check if response has content
            if len(response.content) == 0:
                print("Warning: Empty response content, retrying...")
                return 1.0  # Retry

            try:
                # Success!
                print("Image fetched successfully")

                image = Image.open(BytesIO(response.content))

                # Verify image is complete by trying to load it
                image.verify()
                # Re-open after verify (verify closes the image)
                image = Image.open(BytesIO(response.content))

                file_path = bpy.data.scenes["Scene"].render.filepath

                # Create a user-friendly image name
                image_name = (
                    create_user_friendly_name(
                        history_item.prompt, history_item.id, "Diffusion", 20
                    )
                    + ".png"
                )
                save_path = f"{file_path}{image_name}"

                print(f"Saving image to {save_path}")
                image.save(save_path)
                bpy.data.images.load(save_path, check_existing=True)

                # Save the image name in the history item for later reference
                history_item.image_name = image_name

                # Update status and completion time
                history_item.status = "COMPLETED"
                history_item.completed_time = time.perf_counter()

                print(
                    f"Timing data: created={history_item.created_time:.4f}, completed={history_item.completed_time:.4f}, elapsed={history_item.completed_time - history_item.created_time:.4f}s"
                )

                print(f"Applying the Texture {history_item.uuid}")
                bpy.ops.diffusion.apply_texture(id=history_item.id)

                return None  # Stop the timer

            except Exception as img_error:
                print(f"Error processing image: {img_error}")
                # Retry if image is corrupted/truncated
                return 1.0

        elif response.status_code == 404:
            # Still generating, try again in 2 seconds
            print("Image not ready yet (404), retrying in 2 seconds...")
            return 2.0
        else:
            # Other error
            print(f"Error fetching image: HTTP {response.status_code}")
            history_item.status = "FAILED"
            return None

    except Exception as e:
        print(f"Failed to retrieve image. Error: {e}")
        history_item.status = "FAILED"
        return None


class ObtainMeshObject(bpy.types.Operator):
    bl_idname = "diffusion.obtain_mesh"
    bl_label = "Obtain Mesh Object"

    uuid: bpy.props.StringProperty(name="UUID")

    def execute(self, context):
        assert context is not None
        scene = context.scene
        diffusion_props = scene.diffusion_properties

        active_object = bpy.context.active_object
        if active_object is None:
            active_object = (
                context.selected_objects[0] if context.selected_objects else None
            )

        if active_object and active_object.type == "MESH":
            print("Selected mesh object:", active_object.name)
            diffusion_props.mesh_object = active_object
        else:
            print("No mesh object selected.")
            self.report({"ERROR"}, "No mesh object selected")
            return {"CANCELLED"}

        return {"FINISHED"}


class UpdateHistoryItem(bpy.types.Operator):
    bl_idname = "diffusion.update_history"
    bl_label = "Update History Item"

    uuid: bpy.props.StringProperty(name="UUID")

    def execute(self, context):
        assert context is not None
        scene = context.scene
        history_props = scene.history_properties
        diffusion_props = scene.diffusion_properties

        # Update the history item at the given index
        history_item = history_props.history_collection.add()
        history_item.id = history_props.history_counter
        history_item.prompt = diffusion_props.prompt
        history_item.seed = diffusion_props.seed
        history_item.cfg_scale = diffusion_props.cfg_scale
        history_item.n_steps = diffusion_props.n_steps
        history_item.scheduler = diffusion_props.scheduler
        history_item.negative_prompt = diffusion_props.negative_prompt
        history_item.width = diffusion_props.width
        history_item.height = diffusion_props.height
        history_item.uuid = self.uuid
        history_item.mesh_name = (
            diffusion_props.mesh_object.name if diffusion_props.mesh_object else "None"
        )
        history_item.model_name = diffusion_props.models_available

        # Set initial status and timestamp
        history_item.status = "GENERATING"
        history_item.created_time = time.perf_counter()

        history_props.history_counter = history_props.history_counter + 1
        return {"FINISHED"}


class FetchHistoryItem(bpy.types.Operator):
    """Launch the texture fetching process using the given uuid"""

    bl_idname = "diffusion.fetch_history"
    bl_label = "Fetch History Item"
    uuid: bpy.props.StringProperty(name="UUID")

    def get_history_item(self, context: bpy.types.Context) -> Optional[dict]:
        history_props = context.scene.history_properties
        for item in history_props.history_collection:
            if item.uuid == self.uuid:
                return item
        return None

    def execute(self, context: Optional[bpy.types.Context]) -> set[str]:
        assert context is not None
        assert bpy.context is not None

        history_item = self.get_history_item(context)
        if history_item is None:
            self.report({"ERROR"}, "History item not found")
            return {"CANCELLED"}

        # Add a register on a 1Hz frequency to fetch image result using the id / uuid
        bpy.app.timers.register(
            functools.partial(fetch_image, history_item), first_interval=1.0
        )

        return {"FINISHED"}


class RemoveHistoryItem(bpy.types.Operator):
    bl_idname = "diffusion.remove_history"
    bl_label = "Remove History Item"
    index: bpy.props.IntProperty()
    id: bpy.props.IntProperty()

    def check_collection(self, collections):
        for collection in collections:
            if collection.name == "Diffusion Camera History":
                return collection
        camera_history_collection = bpy.data.collections.new("Diffusion Camera History")
        assert bpy.context is not None

        bpy.context.scene.collection.children.link(camera_history_collection)
        return camera_history_collection

    def execute(self, context):
        assert context is not None

        scene = context.scene
        history_props = scene.history_properties

        # Remove the history item at the given index
        history_props.history_collection.remove(self.index)

        # Loop through the cameras in the diffusion history collection
        # remove the camera with the right id

        history_camera_collection = self.check_collection(scene.collection.children)
        for obj in history_camera_collection.objects:
            if obj.name == f"Camera {self.id}":
                history_camera_collection.objects.unlink(obj)
                bpy.data.objects.remove
                break

        return {"FINISHED"}


class AssignHistoryItem(bpy.types.Operator):
    bl_idname = "diffusion.assign_history"
    bl_label = "Assign History Item"
    id: bpy.props.IntProperty()

    def execute(self, context):
        assert context is not None

        scene = context.scene
        history_props = scene.history_properties
        diffusion_props = scene.diffusion_properties

        # Loop through the history collection and find the item with the right id
        for history_item in history_props.history_collection:
            if history_item.id == self.id:
                # Update all props
                diffusion_props.prompt = history_item.prompt
                diffusion_props.seed = history_item.seed
                diffusion_props.cfg_scale = history_item.cfg_scale
                diffusion_props.n_steps = history_item.n_steps
                diffusion_props.scheduler = history_item.scheduler
                diffusion_props.negative_prompt = history_item.negative_prompt

                # Show feedback to user
                self.report(
                    {"INFO"}, f"✓ Settings loaded from generation #{history_item.id}"
                )
                break
        else:
            self.report({"ERROR"}, f"Generation #{self.id} not found")

        return {"FINISHED"}


class ShowFullPromptOperator(bpy.types.Operator):
    """Operator to display full prompt in tooltip"""

    bl_idname = "diffusion.show_full_prompt"
    bl_label = "Copy Full Prompt"
    bl_description = "Click to copy full prompt to clipboard"

    full_prompt: bpy.props.StringProperty(name="Full Prompt")

    @classmethod
    def description(cls, context, properties):
        # Show the full prompt as tooltip description
        return f"Full prompt: {properties.full_prompt}\n\nClick to copy to clipboard"

    def execute(self, context):
        # Copy full prompt to clipboard
        context.window_manager.clipboard = self.full_prompt
        self.report({"INFO"}, "✓ Prompt copied to clipboard")
        return {"FINISHED"}


class RetryGenerationOperator(bpy.types.Operator):
    bl_idname = "diffusion.retry_generation"
    bl_label = "Retry Generation"
    bl_description = "Retry a failed generation"
    bl_options = {"REGISTER", "UNDO"}

    id: bpy.props.IntProperty(name="History ID")

    def execute(self, context):
        scene = context.scene
        history_props = scene.history_properties
        diffusion_props = scene.diffusion_properties

        # Find the failed history item
        for history_item in history_props.history_collection:
            if history_item.id == self.id:
                # Copy settings to diffusion properties
                diffusion_props.prompt = history_item.prompt
                diffusion_props.seed = history_item.seed
                diffusion_props.cfg_scale = history_item.cfg_scale
                diffusion_props.n_steps = history_item.n_steps
                diffusion_props.scheduler = history_item.scheduler
                diffusion_props.negative_prompt = history_item.negative_prompt

                # Set the mesh object if it exists
                if (
                    history_item.mesh_name
                    and history_item.mesh_name in bpy.data.objects
                ):
                    diffusion_props.mesh_obj = bpy.data.objects[history_item.mesh_name]

                # Reset timing and counters for fresh retry
                history_item.created_time = time.perf_counter()
                history_item.completed_time = 0.0
                history_item.fetch_attempts = 0  # Reset fetch attempts

                # Clear any existing image name for fresh generation
                history_item.image_name = ""

                # Trigger the generation using the correct operator
                try:
                    # Instead of creating a new generation, reuse this history item
                    # Reset the status to generating
                    history_item.status = "GENERATING"

                    # Send request using the existing UUID
                    bpy.ops.diffusion.send_request(uuid=history_item.uuid)

                    # Launch watchdog to get the result
                    bpy.ops.diffusion.fetch_history(uuid=history_item.uuid)
                    self.report({"INFO"}, f"Retrying generation #{history_item.id}")
                except Exception as e:
                    # If there's an error during generation, mark as failed
                    history_item.status = "FAILED"
                    self.report(
                        {"ERROR"},
                        f"Failed to retry generation #{history_item.id}: {str(e)}",
                    )
                    return {"CANCELLED"}
                break
        else:
            self.report({"ERROR"}, f"History item #{self.id} not found")
            return {"CANCELLED"}

        return {"FINISHED"}


class CleanupHistoryOperator(bpy.types.Operator):
    bl_idname = "diffusion.cleanup_history_list"
    bl_label = "Clean History List"
    bl_description = "Remove completed and failed generations from history list only"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        scene = context.scene
        history_props = scene.history_properties

        # Count items to be removed
        completed_items = 0
        failed_items = 0

        # Remove completed and failed items (keep pending and generating)
        items_to_remove = []
        for i, history_item in enumerate(history_props.history_collection):
            if history_item.status in ["COMPLETED", "FAILED"]:
                items_to_remove.append(i)
                if history_item.status == "COMPLETED":
                    completed_items += 1
                else:
                    failed_items += 1

        # Remove from highest index to lowest to avoid index shifting
        for i in reversed(items_to_remove):
            history_props.history_collection.remove(i)

        total_removed = completed_items + failed_items
        if total_removed > 0:
            self.report(
                {"INFO"},
                f"Cleaned {total_removed} history items ({completed_items} completed, {failed_items} failed)",
            )
        else:
            self.report({"INFO"}, "No completed or failed items to clean")

        return {"FINISHED"}


def history_collection_register():
    bpy.utils.register_class(ObtainMeshObject)
    bpy.utils.register_class(UpdateHistoryItem)
    bpy.utils.register_class(RemoveHistoryItem)
    bpy.utils.register_class(AssignHistoryItem)
    bpy.utils.register_class(FetchHistoryItem)
    bpy.utils.register_class(RetryGenerationOperator)
    bpy.utils.register_class(CleanupHistoryOperator)
    bpy.utils.register_class(ShowFullPromptOperator)


def history_collection_unregister():
    bpy.utils.unregister_class(ObtainMeshObject)
    bpy.utils.unregister_class(UpdateHistoryItem)
    bpy.utils.unregister_class(RemoveHistoryItem)
    bpy.utils.unregister_class(AssignHistoryItem)
    bpy.utils.unregister_class(FetchHistoryItem)
    bpy.utils.unregister_class(RetryGenerationOperator)
    bpy.utils.unregister_class(CleanupHistoryOperator)
    bpy.utils.unregister_class(ShowFullPromptOperator)

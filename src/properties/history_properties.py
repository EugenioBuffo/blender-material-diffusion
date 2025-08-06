import bpy


class HistoryItem(bpy.types.PropertyGroup):
    id: bpy.props.IntProperty(name="History ID")
    prompt: bpy.props.StringProperty(name="Prompt")
    seed: bpy.props.IntProperty(name="Seed")
    cfg_scale: bpy.props.FloatProperty(name="CFG")
    n_steps: bpy.props.IntProperty(name="Steps")
    scheduler: bpy.props.StringProperty(name="Scheduler")
    negative_prompt: bpy.props.StringProperty(name="Negative Prompt")
    uuid: bpy.props.StringProperty(name="UUID")
    url: bpy.props.StringProperty(name="URL")
    mesh_name: bpy.props.StringProperty(name="Mesh Name")

    # Simplified status system
    status: bpy.props.EnumProperty(
        name="Status",
        items=[
            ("PENDING", "Pending", "Generation queued"),
            ("GENERATING", "Generating", "Currently generating"),
            ("FETCHING", "Fetching", "Downloading result"),
            ("COMPLETED", "Completed", "Successfully completed"),
            ("FAILED", "Failed", "Generation failed"),
        ],
        default="PENDING",
    )

    # Timestamps for better tracking
    created_time: bpy.props.FloatProperty(name="Created Time", default=0.0)
    completed_time: bpy.props.FloatProperty(name="Completed Time", default=0.0)

    # Model info
    model_name: bpy.props.StringProperty(name="Model")

    # Image dimensions
    width: bpy.props.IntProperty(name="Width", default=1024)
    height: bpy.props.IntProperty(name="Height", default=1024)

    # Image name (for new user-friendly naming system)
    image_name: bpy.props.StringProperty(name="Image Name")

    # Retry tracking
    fetch_attempts: bpy.props.IntProperty(name="Fetch Attempts", default=0)

    # Texture-only generation flag
    texture_only: bpy.props.BoolProperty(name="Texture Only", default=False)


class HistoryProperties(bpy.types.PropertyGroup):

    history_collection: bpy.props.CollectionProperty(type=HistoryItem)

    # Counter for generation ID
    history_counter: bpy.props.IntProperty(name="History Counter", default=0)


def register():
    bpy.utils.register_class(HistoryItem)
    bpy.utils.register_class(HistoryProperties)
    bpy.types.Scene.history_properties = bpy.props.PointerProperty(
        type=HistoryProperties
    )


def unregister():
    bpy.utils.unregister_class(HistoryItem)
    bpy.utils.unregister_class(HistoryProperties)
    del bpy.types.Scene.history_properties

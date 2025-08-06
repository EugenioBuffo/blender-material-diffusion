from .generation_operators import generation_register, generation_unregister
from .history_collection_operators import (
    history_collection_register,
    history_collection_unregister,
)
from .cleanup_operators import (
    register as cleanup_register,
    unregister as cleanup_unregister,
)


def register():
    generation_register()
    history_collection_register()
    cleanup_register()


def unregister():
    generation_unregister()
    history_collection_unregister()
    cleanup_unregister()

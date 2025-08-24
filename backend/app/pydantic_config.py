"""
Global Pydantic configuration for the NeuraVia application.
This file contains configuration that applies to all Pydantic models.
"""

from pydantic import ConfigDict
from datetime import datetime

# Global Pydantic configuration
GLOBAL_MODEL_CONFIG = ConfigDict(
    from_attributes=True,
    json_encoders={
        datetime: lambda v: v.isoformat() if v else None
    },
    # Allow extra fields to prevent validation errors from unexpected data
    extra="ignore",
    # Use enum values instead of enum names
    use_enum_values=True,
    # Validate assignment
    validate_assignment=True,
    # Allow population of fields by alias
    populate_by_name=True,
)

# Function to get model config with additional settings
def get_model_config(**kwargs) -> ConfigDict:
    """Get a model config with additional settings merged with global config."""
    config = GLOBAL_MODEL_CONFIG.copy()
    config.update(kwargs)
    return config

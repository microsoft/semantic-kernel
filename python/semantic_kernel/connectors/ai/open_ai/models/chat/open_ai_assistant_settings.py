# Copyright (c) Microsoft. All rights reserved.

from typing import Optional

import yaml
from pydantic import Field

from semantic_kernel.sk_pydantic import SKBaseModel


class OpenAIAssistantSettings(SKBaseModel):
    """Settings for creating an OpenAI assistant."""

    name: str = Field(min_length=1, max_length=256)
    description: Optional[str] = Field(max_length=512)
    instructions: Optional[str] = Field(max_length=32768)

    @classmethod
    def load_from_definition_file(cls, path: str) -> "OpenAIAssistantSettings":
        try:
            with open(path, "r") as file:
                yaml_data = yaml.safe_load(file)
            
            return cls(
                name=yaml_data.get("name", None),
                description=yaml_data.get("description", None),
                instructions=yaml_data.get("instructions", None),
            )

        except FileNotFoundError:
            #logging.error(f"File not found: {path}")
            raise

        except yaml.YAMLError as e:
            #logging.error(f"Error parsing YAML file: {e}")
            raise

        except Exception as e:
            #logging.error(f"An unexpected error occurred: {e}")
            raise

from typing import Any, Dict

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


class KernelFunctionFromYaml(KernelFunctionFromPrompt):
    def __init__(self, text: str, **kwargs: Any) -> "KernelFunction":
        import yaml

        yaml_data: Dict[str, Any] = yaml.safe_load(text)

        prompt_template_config = PromptTemplateConfig(
            name=yaml_data["name"],
            description=yaml_data["description"],
            template=yaml_data["template"],
            template_format=yaml_data.get("template_format", "semantic-kernel"),
            input_variables=yaml_data.get("input_variables", []),
            execution_settings=yaml_data.get("execution_settings", {}),
        )

        prompt_execution_settings: PromptExecutionSettings = kwargs.get(
            "execution_settings", prompt_template_config.execution_settings
        )

        super().__init__(
            function_name=prompt_template_config.name,
            description=prompt_template_config.description,
            template_format="semantic-kernel",
            prompt=yaml_data["template"],
            prompt_template_config=prompt_template_config,
            prompt_execution_settings=prompt_execution_settings,
        )

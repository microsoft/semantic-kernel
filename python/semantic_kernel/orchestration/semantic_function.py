import re
from typing import Any

import yaml

from semantic_kernel.skill_definition.parameter_view import ParameterView as Parameter

from ..template_engine.handlebars_prompt_template_handler import (
    HandleBarsPromptTemplateHandler,
)
from .sk_function_new import SKFunctionNew


class SemanticFunction(SKFunctionNew):
    template: HandleBarsPromptTemplateHandler | str
    template_format: str
    execution_settings: dict

    @classmethod
    def from_path(cls, path: str) -> "SemanticFunction":
        with open(path) as file:
            yaml_data = yaml.load(file, Loader=yaml.FullLoader)
        # parse the yaml
        template = yaml_data.get("template", "")
        template_format = yaml_data.get("template_format", "").lower()
        if template_format == "handlebars":
            template = HandleBarsPromptTemplateHandler(template.strip())

        input_variables_data = yaml_data.get("input_variables", [])
        input_variables = [
            Parameter(
                name=var.get("name", ""),
                description=var.get("description", ""),
                default_value=var.get("default_value", ""),
                type=var.get("type", ""),
                required=var.get("is_required", False),
            )
            for var in input_variables_data
        ]

        output_variables_data = yaml_data.get("output_variable", {})
        output_variables = [
            Parameter(
                name=output_variables_data.get("name", "result"),
                description=output_variables_data.get("description", ""),
                default_value=output_variables_data.get("default_value", ""),
                type=output_variables_data.get("type", "string"),
                required=output_variables_data.get("is_required", False),
            )
        ]

        # parse execution settings
        settings = {}
        execution_settings_data = yaml_data.get("execution_settings", [])
        for settings_dict in execution_settings_data:
            model_pattern = settings_dict.get("model_id_pattern")
            if model_pattern:
                model_pattern_compiled = re.compile(model_pattern)
                del settings_dict["model_id_pattern"]
                settings.update({model_pattern_compiled: settings_dict})

        return cls(
            name=yaml_data.get("name", ""),
            description=yaml_data.get("description", ""),
            input_variables=input_variables,
            output_variables=output_variables,
            template=template,
            template_format=template_format,
            execution_settings=settings,
        )

    def _get_service_settings(
        self, service: Any, request_settings: dict[str, Any] | None = None
    ) -> dict:
        for model_id in self.execution_settings.keys():
            if model_id.match(service.name):
                settings = {
                    "request_settings": self.execution_settings[model_id],
                    "service": service,
                }
                if request_settings:
                    settings["request_settings"].update(request_settings)
                return settings

    def _get_service_and_settings(
        self, services: list, request_settings: dict[str, Any] | None = None
    ) -> dict:
        for svc in services:
            for model_id in self.execution_settings.keys():
                if model_id.match(svc.name):
                    settings = {
                        "request_settings": self.execution_settings[model_id],
                        "service": svc,
                    }
                    if request_settings:
                        settings["request_settings"].update(request_settings)
                    return settings

    async def run_async(
        self,
        variables,
        services=None,
        request_settings: dict[str, any] | None = None,
        *args,
        **kwargs,
    ) -> dict:
        if "service" not in kwargs:
            service_settings = self._get_service_and_settings(
                services, request_settings
            )
            kwargs["service"] = service_settings["service"]
        else:
            service_settings = self._get_service_settings(
                kwargs["service"], request_settings
            )
        rendered = await self.template.render(variables, **kwargs)
        result = await service_settings["service"].complete_chat_async(
            rendered,
            request_settings=service_settings["request_settings"],
            output_variables=self.output_variables,
            **kwargs.get("service_kwargs", {}),
        )
        if kwargs.get("called_by_template", False):
            return result[self.output_variable_name]
        return result


# '<message role="user">Can you help me write a Handlebars template that achieves the following goal?
# </message>\n<message role="user">Solve the following math problem: The problem is to find the sum of
# 23847 and 347.</message>\n<message role="system">## Instructions\nCreate a Handlebars template that
# describes the steps necessary to accomplish the user\'s goal in a numbered list.\n</message>\n<message
# role="system">## Tips and tricks\n- Use the `{{set name=\'var\' value=var}}` helper to save the results
# of a helper so that you can use it later in the template without wasting resources calling the same helper
# multiple times.\n- There are no initial variables available to you. You must create them yourself using the
# `{{set}}` helper.\n- Do not chain helpers since you have a tendency to create syntax errors when you do;
#  use the `{{set}}`{{{{raw}}}} helper instead. For example, don\'t do this: {{{{raw}}}}`{{Helper_Function
# input=(array 1 2 3)}}` but instead create the variable and _then_ use it: `{{set name=\'var\' value=(array
# 1 2 3)}}{{Helper_Function input=var}}`\n- Use hash arguments when using custom helpers; this helps ensure
# the template renders correctly.\n- Be extremely careful about types. For example, if you pass an array to
# a helper that expects a number, the template will error out.\n- There is no need to check your results in
# the template.\n\n## Bonus\nIf you can correctly guess the output of the helpers before providing the template,
# you\'ll get extra credit.\nFor example, if you think that the output of the `{{random}}` helper is `42`, then
# provide a guess like this:\n</message>\n<message role="system">User: "Can you generate a random number?"
# \n\nAssistant: "1. Generate a random number (Guess: 42)"\n\n```\n{{set name="randomNumber" value=(random)}}
# \n1. Generate a random number: {{randomNumber}}.\n```</message>\n\n<message role="system">## Out of the box
# helpers\n- `{{#if}}{{/if}}`\n- `{{#unless}}{{/unless}}}`\n- `{{#each}}{{/each}}`\n- `{{#with}}{{/with}}`\n-
# `{{equal}}`\n- `{{lessThan}}`\n- `{{greaterThan}}`\n- `{{lessThanOrEqual}}`\n- `{{greaterThanOrEqual}}`\n\n##
# Custom helpers\nYou also have the following Handlebars helpers that you can use to accomplish the user\'s
# goal:\n\n### set\nDescription: Updates the Handlebars variable with the given name to the given value. It
# does not print anything to the screen.\nInputs:\n  - name: string - The name of the variable to set.\n  -
# value: any - The value to set the variable to.\nOutput: None - This helper does not print anything to the
# screen.\n\n### json\nDescription: Generates a JSON string from the given value.\nInputs:\n  - value: string -
# The value to generate JSON for.\nOutput: string - The JSON string.\n\n### _\nDescription: \nInputs:\nOutput:
#  string - The result of the helper.### _\nDescription: \nInputs:\nOutput: string - The result of the helper.
# ### _\nDescription: \nInputs:\nOutput: string - The result of the helper.### _\nDescription: \nInputs:
# \nOutput: string - The result of the helper.### _\nDescription: \nInputs:\nOutput: string - The result of
# the helper.### _\nDescription: \nInputs:\nOutput: string - The result of the helper.</message>\n\n<message
# role="system">Take a deep breath and accomplish the following:\n1. Describe the steps you\'ll take to
# accomplish the user\'s goal using as few words as possible\n2. Provide the user with an efficient Handlebars
# template that completes the steps; don\'t forget to use the tips and tricks otherwise the template will not
# work</message>\n\n<message role="assistant">I\'ll share the template with you in a bit! In the template,
# you\'ll see that I used the helpers you provided to render the results of each step.</message>\n\n<message
# role="assistant">But first, I\'ll succinctly explain the steps I took to achieve the user\'s goal before
# sharing the actual template in a wrapped ``` code block.\nI even provided guesses for each step to get extra
# credit!</message>\n'

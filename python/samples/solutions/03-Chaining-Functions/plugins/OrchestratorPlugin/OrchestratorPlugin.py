import json

from semantic_kernel import Kernel
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.skill_definition import (
    sk_function,
)


class OrchestratorPlugin:
    def __init__(self, kernel: Kernel):
        self._kernel = kernel

    @sk_function(
        description="Routes the request to the appropriate function",
        name="route_request",
    )
    async def RouteRequest(self, context: SKContext) -> str:
        # Save the original user request
        request = context["input"]

        # Add the list of available functions to the context
        context["options"] = "Sqrt, Add"

        # Retrieve the intent from the user request
        GetIntent = self._kernel.skills.get_function("OrchestratorPlugin", "GetIntent")
        CreateResponse = self._kernel.skills.get_function(
            "OrchestratorPlugin", "CreateResponse"
        )
        await GetIntent.invoke_async(context=context)
        intent = context["input"].strip()

        # Prepare the functions to be called in the pipeline
        GetNumbers = self._kernel.skills.get_function(
            "OrchestratorPlugin", "GetNumbers"
        )
        ExtractNumbersFromJson = self._kernel.skills.get_function(
            "OrchestratorPlugin", "extract_numbers_from_json"
        )

        # Retrieve the correct function based on the intent
        if intent == "Sqrt":
            MathFunction = self._kernel.skills.get_function("MathPlugin", "square_root")
        elif intent == "Add":
            MathFunction = self._kernel.skills.get_function("MathPlugin", "add")
        else:
            return "I'm sorry, I don't understand."

        # Create a new context object with the original request
        pipelineContext = self._kernel.create_new_context()
        pipelineContext["original_request"] = request
        pipelineContext["input"] = request

        # Run the functions in a pipeline
        output = await self._kernel.run_async(
            GetNumbers,
            ExtractNumbersFromJson,
            MathFunction,
            CreateResponse,
            input_context=pipelineContext,
        )

        return output["input"]

    @sk_function(
        description="Extracts numbers from JSON",
        name="extract_numbers_from_json",
    )
    def ExtractNumbersFromJson(self, context: SKContext):
        numbers = json.loads(context["input"])

        # Loop through numbers and add them to the context
        for key, value in numbers.items():
            if key == "number1":
                # Add the first number to the input variable
                context["input"] = str(value)
            else:
                # Add the rest of the numbers to the context
                context[key] = str(value)

        return context

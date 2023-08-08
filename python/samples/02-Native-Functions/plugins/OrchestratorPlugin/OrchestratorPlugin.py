import json

from semantic_kernel import Kernel
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.skill_definition import sk_function


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
        GetIntent(context=context)
        intent = context["input"].strip()

        GetNumbers = self._kernel.skills.get_function(
            "OrchestratorPlugin", "GetNumbers"
        )
        getNumberContext = GetNumbers(request)
        numbers = json.loads(getNumberContext["input"])

        # Call the appropriate function
        if intent == "Sqrt":
            # Call the Sqrt function with the first number
            square_root = self._kernel.skills.get_function("MathPlugin", "square_root")
            sqrtResults = await square_root.invoke_async(numbers["number1"])

            return sqrtResults["input"]
        elif intent == "Add":
            # Call the Add function with both numbers
            add = self._kernel.skills.get_function("MathPlugin", "add")
            context["input"] = numbers["number1"]
            context["number2"] = numbers["number2"]
            addResults = await add.invoke_async(context=context)

            return addResults["input"]
        else:
            return "I'm sorry, I don't understand."

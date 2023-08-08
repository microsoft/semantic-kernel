// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Newtonsoft.Json.Linq;

namespace Plugins.OrchestratorPlugin;

public class Orchestrator
{
    private IKernel _kernel;

    public Orchestrator(IKernel kernel)
    {
        this._kernel = kernel;
    }

    [SKFunction]
    public async Task<string> RouteRequest(SKContext context)
    {
        // Save the original user request
        string request = context.Variables["input"];

        // Add the list of available functions to the context
        context.Variables["options"] = "Sqrt, Add";

        // Retrieve the intent from the user request
        var GetIntent = this._kernel.Skills.GetFunction("OrchestratorPlugin", "GetIntent");
        await GetIntent.InvokeAsync(context);
        string intent = context.Variables["input"].Trim();

        var GetNumbers = this._kernel.Skills.GetFunction("OrchestratorPlugin", "GetNumbers");
        SKContext getNumberContext = await GetNumbers.InvokeAsync(request);
        JObject numbers = JObject.Parse(getNumberContext.Variables["input"]);

        // Call the appropriate function
        switch (intent)
        {
            case "Sqrt":
                // Call the Sqrt function with the first number
                var Sqrt = this._kernel.Skills.GetFunction("MathPlugin", "Sqrt");
                SKContext sqrtResults = await Sqrt.InvokeAsync(numbers["number1"]!.ToString());

                return sqrtResults.Variables["input"];
            case "Add":
                // Call the Add function with both numbers
                var Add = this._kernel.Skills.GetFunction("MathPlugin", "Add");
                context.Variables["input"] = numbers["number1"]!.ToString();
                context.Variables["number2"] = numbers["number2"]!.ToString();
                SKContext addResults = await Add.InvokeAsync(context);

                return addResults.Variables["input"];
            default:
                return "I'm sorry, I don't understand.";
        }
    }
}

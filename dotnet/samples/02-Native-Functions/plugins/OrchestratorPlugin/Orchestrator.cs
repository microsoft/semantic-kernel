// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using System.Text.Json.Nodes;

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

        // Retrieve the intent from the user request
        var GetIntent = this._kernel.Skills.GetFunction("OrchestratorPlugin", "GetIntent");
        var getIntentVariables = new ContextVariables
        {
            ["input"] = context.Variables["input"],
            ["options"] = "Sqrt, Add"
        };
        string intent = (await this._kernel.RunAsync(getIntentVariables, GetIntent)).Result.Trim();

        // Retrieve the numbers from the user request
        var GetNumbers = this._kernel.Skills.GetFunction("OrchestratorPlugin", "GetNumbers");
        string numbersJson = (await this._kernel.RunAsync(request, GetNumbers)).Result;
        JsonObject numbers = JsonObject.Parse(numbersJson).AsObject();

        // Call the appropriate function
        switch (intent)
        {
            case "Sqrt":
                // Call the Sqrt function with the first number
                var Sqrt = this._kernel.Skills.GetFunction("MathPlugin", "Sqrt");
                return (await this._kernel.RunAsync(numbers["number1"]!.ToString(), Sqrt)).Result;
            case "Add":
                // Call the Add function with both numbers
                var Add = this._kernel.Skills.GetFunction("MathPlugin", "Add");
                var addVariables = new ContextVariables
                {
                    ["input"] = numbers["number1"]!.ToString(),
                    ["number2"] = numbers["number2"]!.ToString()
                };
                return (await this._kernel.RunAsync(addVariables, Add)).Result;
            default:
                return "I'm sorry, I don't understand.";
        }
    }
}

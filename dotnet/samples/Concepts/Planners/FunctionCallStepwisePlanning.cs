// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Plugins.Core;

namespace Planners;

public class FunctionCallStepwisePlanning(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task RunAsync()
    {
        string[] questions =
        [
            "What is the current hour number, plus 5?",
            "What is 387 minus 22? Email the solution to John and Mary.",
            "Write a limerick, translate it to Spanish, and send it to Jane",
        ];

        var kernel = InitializeKernel();

        var options = new FunctionCallingStepwisePlannerOptions
        {
            MaxIterations = 15,
            MaxTokens = 4000,
        };
        var planner = new Microsoft.SemanticKernel.Planning.FunctionCallingStepwisePlanner(options);

        foreach (var question in questions)
        {
            FunctionCallingStepwisePlannerResult result = await planner.ExecuteAsync(kernel, question);
            Console.WriteLine($"Q: {question}\nA: {result.FinalAnswer}");

            // You can uncomment the line below to see the planner's process for completing the request.
            // Console.WriteLine($"Chat history:\n{System.Text.Json.JsonSerializer.Serialize(result.ChatHistory)}");
        }
    }

    /// <summary>
    /// Initialize the kernel and load plugins.
    /// </summary>
    /// <returns>A kernel instance</returns>
    private static Kernel InitializeKernel()
    {
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                apiKey: TestConfiguration.OpenAI.ApiKey,
                modelId: "gpt-3.5-turbo-1106")
            .Build();

        kernel.ImportPluginFromType<Plugins.EmailPlugin>();
        kernel.ImportPluginFromType<MathPlugin>();
        kernel.ImportPluginFromType<TimePlugin>();

        return kernel;
    }

    private sealed class MathPlugin
    {
        [KernelFunction, Description("Adds an amount to a value")]
        [return: Description("The sum")]
        public int Add(
            [Description("The value to add")] int value,
            [Description("Amount to add")] int amount) =>
            value + amount;

        [KernelFunction, Description("Subtracts an amount from a value")]
        [return: Description("The difference")]
        public int Subtract(
            [Description("The value to subtract")] int value,
            [Description("Amount to subtract")] int amount) =>
            value - amount;
    }
}

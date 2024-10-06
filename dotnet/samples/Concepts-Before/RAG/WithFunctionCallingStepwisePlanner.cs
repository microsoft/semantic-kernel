// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning;

namespace RAG;

public class WithFunctionCallingStepwisePlanner(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task RunAsync()
    {
        string[] questions =
        [
            "When should I use the name Bob?",
            "When should I use the name Tom?",
            "When should I use the name Alice?",
            "When should I use the name Harry?",
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

        kernel.ImportPluginFromType<RetrievePlugin>();

        return kernel;
    }

    internal sealed class RetrievePlugin
    {
        [KernelFunction, Description("Given a query retrieve relevant information")]
        public string Retrieve(
            [Description("The input query.")] string query,
            Kernel kernel)
        {
            if (query.Contains("Bob", System.StringComparison.OrdinalIgnoreCase) ||
                query.Contains("Alice", System.StringComparison.OrdinalIgnoreCase))
            {
                return "Alice and Bob are fictional characters commonly used as placeholders in discussions about cryptographic systems and protocols,[1] and in other science and engineering literature where there are several participants in a thought experiment.";
            }
            if (query.Contains("Tom", System.StringComparison.OrdinalIgnoreCase) ||
                query.Contains("Dick", System.StringComparison.OrdinalIgnoreCase) ||
                query.Contains("Harry", System.StringComparison.OrdinalIgnoreCase))
            {
                return "The phrase \"Tom, Dick, and Harry\" is a placeholder for unspecified people.[1][2] The phrase most commonly occurs as \"every Tom, Dick, and Harry\", meaning everyone, and \"any Tom, Dick, or Harry\", meaning anyone.";
            }

            return string.Empty;
        }
    }
}

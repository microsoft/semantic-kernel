// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI.Chat;

namespace ChatCompletion;

public class OpenAI_StructuredOutputs(ITestOutputHelper output) : BaseTest(output)
{
    private sealed class MathReasoning
    {
        public List<MathReasoningStep> Steps { get; set; }

        public string FinalAnswer { get; set; }
    }

    private sealed class MathReasoningStep
    {
        public string Explanation { get; set; }

        public string Output { get; set; }
    }

    [Fact]
    public async Task StructuredOutputsWithChatResponseFormatAsync()
    {
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: "gpt-4o-2024-08-06",
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        ChatResponseFormat chatResponseFormat = ChatResponseFormat.CreateJsonSchemaFormat(
            name: "math_reasoning",
            jsonSchema: BinaryData.FromString("""
                {
                    "type": "object",
                    "properties": {
                        "Steps": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "Explanation": { "type": "string" },
                                    "Output": { "type": "string" }
                                },
                            "required": ["Explanation", "Output"],
                            "additionalProperties": false
                            }
                        },
                        "FinalAnswer": { "type": "string" }
                    },
                    "required": ["Steps", "FinalAnswer"],
                    "additionalProperties": false
                }
                """),
            strictSchemaEnabled: true);

        var executionSettings = new OpenAIPromptExecutionSettings
        {
            ResponseFormat = chatResponseFormat
        };

        var result = await kernel.InvokePromptAsync("How can I solve 8x + 7 = -23?", new(executionSettings));

        var mathReasoning = JsonSerializer.Deserialize<MathReasoning>(result.ToString())!;

        this.OutputResult(mathReasoning);

        //  Step #1
        //  Explanation: Start with the given equation.
        //  Output: 8x + 7 = -23

        //  Step #2
        //  Explanation: To isolate the term containing x, subtract 7 from both sides of the equation.
        //  Output: 8x + 7 - 7 = -23 - 7

        //  Step #3
        //  Explanation: To solve for x, divide both sides of the equation by 8, which is the coefficient of x.
        //  Output: (8x)/8 = (-30)/8

        //  Step #4
        //  Explanation: This simplifies to x = -3.75, as dividing -30 by 8 gives -3.75.
        //  Output: x = -3.75

        //  Final answer: x = -3.75
    }

    [Fact]
    public async Task StructuredOutputsWithTypeInExecutionSettingsAsync()
    {
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: "gpt-4o-2024-08-06",
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        var executionSettings = new OpenAIPromptExecutionSettings
        {
            ResponseFormat = typeof(MathReasoning)
        };

        var result = await kernel.InvokePromptAsync("How can I solve 8x + 7 = -23?", new(executionSettings));

        var mathReasoning = JsonSerializer.Deserialize<MathReasoning>(result.ToString())!;

        this.OutputResult(mathReasoning);

        //  Step #1
        //  Explanation: Start with the given equation.
        //  Output: 8x + 7 = -23

        //  Step #2
        //  Explanation: To isolate the term containing x, subtract 7 from both sides of the equation.
        //  Output: 8x + 7 - 7 = -23 - 7

        //  Step #3
        //  Explanation: To solve for x, divide both sides of the equation by 8, which is the coefficient of x.
        //  Output: (8x)/8 = (-30)/8

        //  Step #4
        //  Explanation: This simplifies to x = -3.75, as dividing -30 by 8 gives -3.75.
        //  Output: x = -3.75

        //  Final answer: x = -3.75
    }

    #region private

    private void OutputResult(MathReasoning mathReasoning)
    {
        for (var i = 0; i < mathReasoning.Steps.Count; i++)
        {
            this.Output.WriteLine($"Step #{i + 1}");
            this.Output.WriteLine($"Explanation: {mathReasoning.Steps[i].Explanation}");
            this.Output.WriteLine($"Output: {mathReasoning.Steps[i].Output}");
        }

        this.Output.WriteLine($"Final answer: {mathReasoning.FinalAnswer}");
    }

    #endregion
}

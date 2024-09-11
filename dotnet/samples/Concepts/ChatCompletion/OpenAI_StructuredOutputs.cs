// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI.Chat;

namespace ChatCompletion;

/// <summary>
/// Structured Outputs is a feature in OpenAI API that ensures the model will always generate responses based on provided JSON Schema.
/// This gives more control over model responses, allows to avoid model hallucinations and write simpler prompts without a need to be specific about response format.
/// More information here: <see href="https://platform.openai.com/docs/guides/structured-outputs/structured-outputs"/>.
/// </summary>
public class OpenAI_StructuredOutputs(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>Parent class that will be used as desired chat completion response format (structured output).</summary>
    private sealed class MathReasoning
    {
        public List<MathReasoningStep> Steps { get; set; }

        public string FinalAnswer { get; set; }
    }

    /// <summary>Child class that will be used as desired chat completion response format (structured output).</summary>
    private sealed class MathReasoningStep
    {
        public string Explanation { get; set; }

        public string Output { get; set; }
    }

    /// <summary>
    /// This method shows how to enable Structured Outputs feature with <see cref="ChatResponseFormat"/> object by providing
    /// JSON schema of desired response format.
    /// </summary>
    [Fact]
    public async Task StructuredOutputsWithChatResponseFormatAsync()
    {
        // Initialize kernel.
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: "gpt-4o-2024-08-06",
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Initialize ChatResponseFormat object with JSON schema of desired response format.
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

        // Specify response format by setting ChatResponseFormat object in prompt execution settings.
        var executionSettings = new OpenAIPromptExecutionSettings
        {
            ResponseFormat = chatResponseFormat
        };

        // Send a request and pass prompt execution settings with desired response format.
        var result = await kernel.InvokePromptAsync("How can I solve 8x + 7 = -23?", new(executionSettings));

        // Deserialize string response to a strong type to access type properties.
        // At this point, the deserialization logic won't fail, because MathReasoning type was described using JSON schema.
        // This ensures that response string is a serialized version of MathReasoning type.
        var mathReasoning = JsonSerializer.Deserialize<MathReasoning>(result.ToString())!;

        // Output the result.
        this.OutputResult(mathReasoning);

        // Output:

        // Step #1
        // Explanation: Start with the given equation.
        // Output: 8x + 7 = -23

        // Step #2
        // Explanation: To isolate the term containing x, subtract 7 from both sides of the equation.
        // Output: 8x + 7 - 7 = -23 - 7

        // Step #3
        // Explanation: To solve for x, divide both sides of the equation by 8, which is the coefficient of x.
        // Output: (8x)/8 = (-30)/8

        // Step #4
        // Explanation: This simplifies to x = -3.75, as dividing -30 by 8 gives -3.75.
        // Output: x = -3.75

        // Final answer: x = -3.75
    }

    /// <summary>
    /// This method shows how to enable Structured Outputs feature with <see cref="Type"/> object by providing
    /// the type of desired response format. In this scenario, JSON schema will be created automatically based on provided type.
    /// </summary>
    [Fact]
    public async Task StructuredOutputsWithTypeInExecutionSettingsAsync()
    {
        // Initialize kernel.
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: "gpt-4o-2024-08-06",
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Specify response format by setting Type object in prompt execution settings.
        var executionSettings = new OpenAIPromptExecutionSettings
        {
            ResponseFormat = typeof(MathReasoning)
        };

        // Send a request and pass prompt execution settings with desired response format.
        var result = await kernel.InvokePromptAsync("How can I solve 8x + 7 = -23?", new(executionSettings));

        // Deserialize string response to a strong type to access type properties.
        // At this point, the deserialization logic won't fail, because MathReasoning type was specified as desired response format.
        // This ensures that response string is a serialized version of MathReasoning type.
        var mathReasoning = JsonSerializer.Deserialize<MathReasoning>(result.ToString())!;

        // Output the result.
        this.OutputResult(mathReasoning);

        // Output:

        // Step #1
        // Explanation: Start with the given equation.
        // Output: 8x + 7 = -23

        // Step #2
        // Explanation: To isolate the term containing x, subtract 7 from both sides of the equation.
        // Output: 8x + 7 - 7 = -23 - 7

        // Step #3
        // Explanation: To solve for x, divide both sides of the equation by 8, which is the coefficient of x.
        // Output: (8x)/8 = (-30)/8

        // Step #4
        // Explanation: This simplifies to x = -3.75, as dividing -30 by 8 gives -3.75.
        // Output: x = -3.75

        // Final answer: x = -3.75
    }

    #region private

    /// <summary>Helper method to output <see cref="MathReasoning"/> object content.</summary>
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

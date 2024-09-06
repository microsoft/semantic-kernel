// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI.Chat;

namespace ChatCompletion;

public class OpenAI_StructuredOutputs(ITestOutputHelper output) : BaseTest(output)
{
    private sealed class MathReasoning
    {
        [JsonPropertyName("steps")]
        public List<MathReasoningStep> Steps { get; set; }

        [JsonPropertyName("final_answer")]
        public string FinalAnswer { get; set; }
    }

    private sealed class MathReasoningStep
    {
        [JsonPropertyName("explanation")]
        public string Explanation { get; set; }

        [JsonPropertyName("output")]
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
                    "steps": {
                        "type": "array",
                        "items": {
                        "type": "object",
                        "properties": {
                            "explanation": { "type": "string" },
                            "output": { "type": "string" }
                        },
                        "required": ["explanation", "output"],
                        "additionalProperties": false
                        }
                    },
                    "final_answer": { "type": "string" }
                    },
                    "required": ["steps", "final_answer"],
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

        for (var i = 0; i < mathReasoning.Steps.Count; i++)
        {
            this.Output.WriteLine($"Step #{i + 1}");
            this.Output.WriteLine($"Explanation: {mathReasoning.Steps[i].Explanation}");
            this.Output.WriteLine($"Output: {mathReasoning.Steps[i].Output}");
        }

        this.Output.WriteLine($"Final answer: {mathReasoning.FinalAnswer}");

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
}

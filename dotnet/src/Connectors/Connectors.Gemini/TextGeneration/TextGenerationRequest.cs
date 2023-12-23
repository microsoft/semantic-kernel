#region HEADER
// Copyright (c) Microsoft. All rights reserved.
#endregion

using System.Linq;
using System.Text.Json.Nodes;
using Json.More;
using Microsoft.SemanticKernel.Connectors.Gemini.Settings;

namespace Microsoft.SemanticKernel.Connectors.Gemini;

// todo: maybe better create a class for this instead manual creating JsonObject?
internal static class TextGenerationRequest
{
    public static JsonObject GenerateJsonFromPromptExecutionSettings(string prompt, GeminiPromptExecutionSettings executionSettings)
    {
        JsonObject obj = CreatePromptObject(prompt);
        AddSafetySetting(executionSettings, obj);
        AddConfiguration(executionSettings, obj);
        return obj;
    }

    private static void AddConfiguration(GeminiPromptExecutionSettings executionSettings, JsonNode obj)
    {
        obj["generationConfig"] = new JsonObject()
        {
            ["temperature"] = executionSettings.Temperature,
            ["topP"] = executionSettings.TopP,
            ["topK"] = executionSettings.TopK,
        };

        if (executionSettings.MaxTokens.HasValue)
        {
            obj["maxOutputTokens"] = executionSettings.MaxTokens;
        }

        if (executionSettings.StopSequences is { Count: > 0 } stopSequences)
        {
            obj["stopSequences"] = stopSequences.Select(s => JsonValue.Create(s)).ToJsonArray();
        }

        if (executionSettings.CandidateCount.HasValue)
        {
            obj["candidateCount"] = executionSettings.CandidateCount;
        }
    }

    private static void AddSafetySetting(GeminiPromptExecutionSettings executionSettings, JsonNode obj)
    {
        if (executionSettings.SafetySettings is { } safety)
        {
            obj["safetySettings"] = safety.Select(s => new JsonObject()
            {
                ["category"] = s.Category,
                ["threshold"] = s.Threshold
            }).ToJsonArray();
        }
    }

    private static JsonObject CreatePromptObject(string prompt)
    {
        var obj = new JsonObject
        {
            ["contents"] = new JsonArray()
            {
                new JsonObject()
                {
                    ["parts"] = new JsonArray()
                    {
                        new JsonObject()
                        {
                            ["text"] = prompt
                        }
                    }
                }
            }
        };
        return obj;
    }
}

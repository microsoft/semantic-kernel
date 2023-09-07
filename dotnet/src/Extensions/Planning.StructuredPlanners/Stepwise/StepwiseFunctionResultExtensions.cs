// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Planning.Structured.Stepwise;

using System;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;
using Connectors.AI.OpenAI.FunctionCalling;


public static class StepwiseFunctionResultExtensions
{
    public static StepwiseFunctionCallResult ToFunctionCallResult(this string text)
    {
        Console.WriteLine(text);
        var response = new StepwiseFunctionCallResult();

        text = text.Trim();
        GetPropertyValue(text, "Thought:", out var thought);
        GetPropertyValue(text, "Observation:", out var observation);
        GetPropertyValue(text, "FinalAnswer:", out var answer);
        GetPropertyValue(text, "Function_Call:", out var reasoning);

        response.Thought = thought;
        response.Observation = observation;
        response.FinalAnswer = answer;

        try
        {
            response.FunctionCall = JsonSerializer.Deserialize<FunctionCallResult>(reasoning);
        }
        catch (Exception)
        {
            // ignored
        }

        return response;
    }


    private static void GetPropertyValue(string text, string key, out string value)
    {
        value = "";

        var knownKeys = new[] { "Thought:", "Observation:", "FinalAnswer:", "Function_Call:" };

        var startIndex = text.IndexOf(key, StringComparison.Ordinal);

        if (startIndex < 0)
        {
            return;
        }

        startIndex += key.Length;

        int endIndex;

        var nextPropIndex = GetNextPropertyIndex(text, key, startIndex);

        if (nextPropIndex > 0)
        {
            // Next property found, so end before it
            endIndex = nextPropIndex;
        }
        else
        {
            // No next property, so end at full length
            endIndex = text.Length;
        }

        value = text.Substring(startIndex, endIndex - startIndex).Trim();

        var regex = new Regex($@"^{key}\s*");
        value = regex.Replace(value, "");
    }


    private static int GetNextPropertyIndex(string text, string key, int startIndex)
    {
        var knownKeys = new[] { "Thought:", "Observation:", "FinalAnswer:", "Function_Call:" };

        for (var i = startIndex; i < text.Length; i++)
        {
            if (text[i] == '\n')
            {
                var line = text.Substring(i).Trim();

                if (knownKeys.Any(line.StartsWith))
                {
                    return i;
                }

                if (line.StartsWith(key))
                {
                    return i - 1;
                }
            }
        }

        return text.Length;
    }
}

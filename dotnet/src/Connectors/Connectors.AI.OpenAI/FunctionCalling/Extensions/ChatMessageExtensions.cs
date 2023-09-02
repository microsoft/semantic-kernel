// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.FunctionCalling.Extensions;

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;
using Azure.AI.OpenAI;
using SemanticKernel.AI.ChatCompletion;


/// <summary>
///  Extensions for managing function calls in chat completions
/// </summary>
public static class ChatMessageExtensions
{
    /// <summary>
    ///  Check if the chat choice is a function call
    /// </summary>
    /// <param name="chatChoice"></param>
    /// <param name="name"></param>
    /// <returns></returns>
    public static bool IsFunctionCall(this ChatChoice chatChoice, string? name = null)
    {
        var checkName = name != null && chatChoice.Message.FunctionCall?.Name == name;
        var checkMessage = chatChoice.FinishReason == CompletionsFinishReason.FunctionCall ||
                           chatChoice.Message.Role == ChatRole.Function;
        return checkName || checkMessage;
    }


    /// <summary>
    ///  Checks if any of the choices is a function call
    /// </summary>
    /// <param name="response"></param>
    /// <param name="names"></param>
    /// <returns></returns>
    public static bool IsFunctionCallResponse(this ChatCompletions response, IEnumerable<string> names) =>
        response.Choices.Any(choice => choice.IsFunctionCall(names));


    /// <summary>
    ///  Checks if the chat choice is a function call with a name in the list
    /// </summary>
    /// <param name="chatChoice"></param>
    /// <param name="names"></param>
    /// <returns></returns>
    public static bool IsFunctionCall(this ChatChoice chatChoice, IEnumerable<string> names)
        => names.Any(chatChoice.IsFunctionCall);


    /// <summary>
    /// Used to validate the whether the content of the chat message is valid JSON
    /// </summary>
    /// <param name="strInput"></param>
    /// <returns></returns>
    public static bool IsValidJson(string strInput)
    {
        try
        {
            JsonDocument.Parse(strInput);
            return true;
        }
        catch (JsonException e)
        {
            Console.WriteLine(e);
            return false;
        }
    }


    /// <summary>
    ///  Attempts to fix the JSON in the case that the response is not valid JSON
    /// </summary>
    /// <param name="strInput"></param>
    /// <returns></returns>
    public static string CleanJson(string strInput)
    {
        var json = strInput;

        json = Regex.Replace(json, @"(\\w+): (.*)", @"$1: ""$2""",
            RegexOptions.Multiline);

        json = Regex.Replace(json, @"\[([^\]]*)\]", "[$1]",
            RegexOptions.Multiline);

        json = json.Replace(@"\", @"");
        return json;
    }


    /// <summary>
    /// Returns the content of the chat message as a FunctionCallResult
    /// </summary>
    /// <param name="chatMessage"></param>
    /// <returns></returns>
    public static FunctionCallResult? ToFunctionCall(this ChatMessageBase chatMessage)
    {
        FunctionCallResult? functionCall = default;
        var firstElementJsonString = "";

        try
        {
            using var document = JsonDocument.Parse(chatMessage.Content);

            var root = document.RootElement;

            var propertyEnumerator = root.EnumerateObject();

            if (propertyEnumerator.MoveNext())
            {
                var firstProperty = propertyEnumerator.Current.Value;
                firstElementJsonString = firstProperty.GetRawText().Trim();

                functionCall = JsonSerializer.Deserialize<FunctionCallResult>(firstElementJsonString, new JsonSerializerOptions(JsonSerializerDefaults.Web) { WriteIndented = true });
            }

        }
        catch (JsonException ex)
        {
            Console.WriteLine($"Error while converting '{firstElementJsonString}' to a '{typeof(FunctionCallResult)}': {ex}");
        }

        return functionCall;
    }
}

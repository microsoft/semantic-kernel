// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.RegularExpressions;
using Microsoft.SemanticKernel;

namespace MCPServer;

/// <summary>
/// Defines a filter for automatic function invocation.
/// </summary>
internal sealed class ContentSafetyAutoFunctionInvocationFilter : IAutoFunctionInvocationFilter
{
    /// <inheritdoc/>
    public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
    {
        /// Check for PII in the arguments
        foreach (var argument in context.Arguments!)
        {
            if (ContainsPII(JsonSerializer.Serialize(argument.Value)))
            {
                context.Terminate = true;
                return;
            }
        }

        // Proceed with the function invocation
        await next(context);

        // Check for PII in the result
        if (ContainsPII(JsonSerializer.Serialize((context.Result.GetValue<RestApiOperationResponse>()!.Content))))
        {
            context.Terminate = true;
            return;
        }
    }

    private static bool ContainsPII(string input)
    {
        // Define regex patterns for different types of PII  
        string emailPattern = @"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}";
        string phonePattern = @"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b";
        string ssnPattern = @"\b\d{3}-\d{2}-\d{4}\b";
        string creditCardPattern = @"\b(?:\d[ -]*?){13,16}\b";
        string ipAddressPattern = @"\b(?:\d{1,3}\.){3}\d{1,3}\b";
        string zipCodePattern = @"\b\d{5}(?:-\d{4})?\b";
        string addressPattern = @"\d+\s[A-Za-z]+\s(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd)\b";
        string dobPattern = @"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b";

        // Check for matches against all patterns  
        return Regex.IsMatch(input, emailPattern) ||
               Regex.IsMatch(input, phonePattern) ||
               Regex.IsMatch(input, ssnPattern) ||
               Regex.IsMatch(input, creditCardPattern) ||
               Regex.IsMatch(input, ipAddressPattern) ||
               Regex.IsMatch(input, zipCodePattern) ||
               Regex.IsMatch(input, addressPattern) ||
               Regex.IsMatch(input, dobPattern);
    }
}

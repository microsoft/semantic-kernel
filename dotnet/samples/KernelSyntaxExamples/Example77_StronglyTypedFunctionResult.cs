// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel;
using System.Text.Json;
using System.Diagnostics;
using System.Collections.Generic;
using Xunit;
using Xunit.Abstractions;
using Examples;

// The following example shows how to receive the results from the kernel in a strongly typed object
// which stores the usage in tokens and converts the JSON result to a strongly typed object, where a validation can also
// be performed
public class Example77_StronglyTypedFunctionResult : BaseTest
{
    [Fact]
    public async Task RunAsync()
    {
        this.WriteLine("======== LLMPrompts ========");

        string openAIModelId = TestConfiguration.OpenAI.ChatModelId;
        string openAIApiKey = TestConfiguration.OpenAI.ApiKey;

        if (openAIApiKey == null)
        {
            this.WriteLine("OpenAI credentials not found. Skipping example.");
            return;
        }

        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: openAIModelId,
                apiKey: openAIApiKey)
            .Build();

        var promptTestDataGeneration = "Return a JSON with an array of 3 JSON objects with the following fields: First, an id field with a random GUID, next a name field with a random company name and last a description field with a random short company description. Ensure the JSON is valid and it contains a JSON array named testcompanies with the three fields.";

        // Time it
        var sw = new Stopwatch();
        sw.Start();

        FunctionResult functionResult =
            await kernel.InvokePromptAsync(promptTestDataGeneration);

        // Stop the timer
        sw.Stop();

        var functionResultTestDataGen = new FunctionResultTestDataGen(
            functionResult!,
            sw.ElapsedMilliseconds);

        this.WriteLine($"Test data: {functionResultTestDataGen.Result} \n");
        this.WriteLine($"Milliseconds: {functionResultTestDataGen.ExecutionTimeInMilliseconds} \n");
        this.WriteLine($"Total Tokens: {functionResultTestDataGen.TokenCounts!.TotalTokens} \n");
    }

    public Example77_StronglyTypedFunctionResult(ITestOutputHelper output) : base(output)
    {
    }

    /// <summary>
    /// Helper classes for the example,
    /// put in the same file for simplicity
    /// </summary>
    // The structure to put the JSON result in a strongly typed object
    private sealed class RootObject
    {
        public List<TestCompany> TestCompanies { get; set; }
    }

    private sealed class TestCompany
    {
        public string Id { get; set; }
        public string Name { get; set; }
        public string Description { get; set; }
    }

    // The FunctionResult custom wrapper to parse the result and the tokens
    private sealed class FunctionResultTestDataGen : FunctionResultExtended
    {
        public List<TestCompany> TestCompanies { get; set; }

        public long ExecutionTimeInMilliseconds { get; init; }

        public FunctionResultTestDataGen(
            FunctionResult functionResult,
            long executionTimeInMilliseconds)
            : base(functionResult)
        {
            this.TestCompanies = ParseTestCompanies();
            this.ExecutionTimeInMilliseconds = executionTimeInMilliseconds;
            this.TokenCounts = this.ParseTokenCounts();
        }

        private TokenCounts? ParseTokenCounts()
        {
            CompletionsUsage Usage = (CompletionsUsage)FunctionResult.Metadata?["Usage"];

            return new TokenCounts(
                completionTokens: Usage?.CompletionTokens ?? 0,
                promptTokens: Usage?.PromptTokens ?? 0,
                totalTokens: Usage?.TotalTokens ?? 0);
        }

        private static readonly JsonSerializerOptions s_jsonSerializerOptions = new()
        {
            PropertyNameCaseInsensitive = true
        };

        private List<TestCompany> ParseTestCompanies()
        {
            // This could also perform some validation logic
            var rootObject = JsonSerializer.Deserialize<RootObject>(this.Result, s_jsonSerializerOptions);
            List<TestCompany> companies = rootObject.TestCompanies;

            return companies;
        }
    }

    private sealed class TokenCounts
    {
        public int CompletionTokens { get; init; }
        public int PromptTokens { get; init; }
        public int TotalTokens { get; init; }

        public TokenCounts(int completionTokens, int promptTokens, int totalTokens)
        {
            CompletionTokens = completionTokens;
            PromptTokens = promptTokens;
            TotalTokens = totalTokens;
        }
    }

    // The FunctionResult extension to provide base functionality
    private class FunctionResultExtended
    {
        public string Result { get; init; }
        public TokenCounts? TokenCounts { get; set; }

        public FunctionResult FunctionResult { get; init; }

        public FunctionResultExtended(FunctionResult functionResult)
        {
            this.FunctionResult = functionResult;
            this.Result = this.ParseResultFromFunctionResult();
        }

        private string ParseResultFromFunctionResult()
        {
            return this.FunctionResult.GetValue<string>() ?? string.Empty;
        }
    }
}

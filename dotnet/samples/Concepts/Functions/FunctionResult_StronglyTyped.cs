// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.Text.Json;
using Microsoft.SemanticKernel;
using OpenAI.Chat;

namespace Functions;

// The following example shows how to receive the results from the kernel in a strongly typed object
// which stores the usage in tokens and converts the JSON result to a strongly typed object, where a validation can also
// be performed
public class FunctionResult_StronglyTyped(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task RunAsync()
    {
        Console.WriteLine("======== Extended function result ========");

        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        var promptTestDataGeneration = "Return a JSON with an array of 3 JSON objects with the following fields: " +
            "First, an id field with a random GUID, next a name field with a random company name and last a description field with a random short company description. " +
            "Ensure the JSON is valid and it contains a JSON array named testcompanies with the three fields.";

        // Time it
        var sw = new Stopwatch();
        sw.Start();

        FunctionResult functionResult = await kernel.InvokePromptAsync(promptTestDataGeneration);

        // Stop the timer
        sw.Stop();

        var functionResultTestDataGen = new FunctionResultTestDataGen(functionResult!, sw.ElapsedMilliseconds);

        Console.WriteLine($"Test data: {functionResultTestDataGen.Result} \n");
        Console.WriteLine($"Milliseconds: {functionResultTestDataGen.ExecutionTimeInMilliseconds} \n");
        Console.WriteLine($"Total Tokens: {functionResultTestDataGen.TokenCounts!.TotalTokens} \n");
    }

    /// <summary>
    /// Helper classes for the example,
    /// put in the same file for simplicity
    /// </summary>
    /// <remarks>The structure to put the JSON result in a strongly typed object</remarks>
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

    /// <summary>
    /// The FunctionResult custom wrapper to parse the result and the tokens
    /// </summary>
    private sealed class FunctionResultTestDataGen : FunctionResultExtended
    {
        public List<TestCompany> TestCompanies { get; set; }

        public long ExecutionTimeInMilliseconds { get; init; }

        public FunctionResultTestDataGen(FunctionResult functionResult, long executionTimeInMilliseconds)
            : base(functionResult)
        {
            this.TestCompanies = ParseTestCompanies();
            this.ExecutionTimeInMilliseconds = executionTimeInMilliseconds;
            this.TokenCounts = this.ParseTokenCounts();
        }

        private TokenCounts? ParseTokenCounts()
        {
            var usage = FunctionResult.Metadata?["Usage"] as ChatTokenUsage;

            return new TokenCounts(
                completionTokens: usage?.OutputTokens ?? 0,
                promptTokens: usage?.InputTokens ?? 0,
                totalTokens: usage?.TotalTokens ?? 0);
                completionTokens: usage?.OutputTokens ?? 0,
                promptTokens: usage?.InputTokens ?? 0,
                totalTokens: usage?.TotalTokens ?? 0);
                completionTokens: usage?.OutputTokenCount ?? 0,
                promptTokens: usage?.InputTokenCount ?? 0,
                totalTokens: usage?.TotalTokenCount ?? 0);
                completionTokens: usage?.OutputTokenCount ?? 0,
                promptTokens: usage?.InputTokenCount ?? 0,
                totalTokens: usage?.TotalTokenCount ?? 0);
                completionTokens: usage?.OutputTokenCount ?? 0,
                promptTokens: usage?.InputTokenCount ?? 0,
                totalTokens: usage?.TotalTokenCount ?? 0);
                completionTokens: usage?.OutputTokenCount ?? 0,
                promptTokens: usage?.InputTokenCount ?? 0,
                totalTokens: usage?.TotalTokenCount ?? 0);
        }

        private static readonly JsonSerializerOptions s_jsonSerializerOptions = new()
        {
            PropertyNameCaseInsensitive = true
        };

        private List<TestCompany> ParseTestCompanies()
        {
            // This could also perform some validation logic
            var rootObject = JsonSerializer.Deserialize<RootObject>(this.Result, s_jsonSerializerOptions);
            List<TestCompany> companies = rootObject!.TestCompanies;

            return companies;
        }
    }

    private sealed class TokenCounts(int completionTokens, int promptTokens, int totalTokens)
    {
        public int CompletionTokens { get; init; } = completionTokens;
        public int PromptTokens { get; init; } = promptTokens;
        public int TotalTokens { get; init; } = totalTokens;
    }

    /// <summary>
    /// The FunctionResult extension to provide base functionality
    /// </summary>
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

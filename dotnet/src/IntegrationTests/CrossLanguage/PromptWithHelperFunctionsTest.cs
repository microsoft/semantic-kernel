// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.IntegrationTests.CrossLanguage;

public class PromptWithHelperFunctionsTest
{
    private const string SkPrompt = "<message role=\"system\">The current time is {{Time.Now}}</message><message role=\"user\">Can you help me tell the time in {{$city}} right now?</message>";
    private const string HbPrompt = "<message role=\"system\">The current time is {{Time-Now}}</message><message role=\"user\">Can you help me tell the time in {{city}} right now?</message>";

    [Theory]
    [InlineData(true, false, "semantic-kernel", SkPrompt)]
    [InlineData(true, true, "semantic-kernel", SkPrompt)]
    [InlineData(false, false, "semantic-kernel", SkPrompt)]
    [InlineData(false, true, "semantic-kernel", SkPrompt)]
    [InlineData(false, false, "handlebars", HbPrompt)]
    [InlineData(false, true, "handlebars", HbPrompt)]
    public async Task PromptWithHelperFunctionsAsync(bool isInline, bool isStreaming, string templateFormat, string prompt)
    {
        using var kernelProvider = new KernelRequestTracer();
        Kernel kernel = kernelProvider.GetNewKernel();
        kernel.Plugins.AddFromFunctions("Time",
                [KernelFunctionFactory.CreateFromMethod(() => $"{PromptWithHelperFunctionsTest.UtcNow:r}", "Now", "Gets the current date and time")]);

        await KernelRequestTracer.RunPromptAsync(kernel, isInline, isStreaming, templateFormat, prompt, new()
        {
            { "city", "Seattle" }
        });

        string requestContent = kernelProvider.GetRequestContent();
        JsonNode? obtainedObject = JsonNode.Parse(requestContent);
        Assert.NotNull(obtainedObject);

        string expected = await File.ReadAllTextAsync(isStreaming
            ? "./CrossLanguage/Data/PromptWithHelperFunctionsStreamingTest.json"
            : "./CrossLanguage/Data/PromptWithHelperFunctionsTest.json");

        JsonNode? expectedObject = JsonNode.Parse(expected);
        Assert.NotNull(expectedObject);

        if (isStreaming)
        {
            expectedObject["stream"] = true;
        }

        Assert.True(JsonNode.DeepEquals(obtainedObject, expectedObject));
    }

    /// <summary>
    /// Returns a constant timestamp for test purposes.
    /// </summary>
    internal static DateTime UtcNow => new(1989, 6, 4, 12, 11, 13);
}

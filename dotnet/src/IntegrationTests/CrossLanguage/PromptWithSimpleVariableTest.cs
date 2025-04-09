// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.IntegrationTests.CrossLanguage;

public class PromptWithSimpleVariableTest
{
    private const string SkPrompt = "Can you help me tell the time in {{$city}} right now?";
    private const string HbPrompt = "Can you help me tell the time in {{city}} right now?";

    [Theory]
    [InlineData(true, false, "semantic-kernel", SkPrompt)]
    [InlineData(true, true, "semantic-kernel", SkPrompt)]
    [InlineData(false, false, "semantic-kernel", SkPrompt)]
    [InlineData(false, true, "semantic-kernel", SkPrompt)]
    [InlineData(false, false, "handlebars", HbPrompt)]
    [InlineData(false, true, "handlebars", HbPrompt)]
    public async Task PromptWithSimpleVariableAsync(bool isInline, bool isStreaming, string templateFormat, string prompt)
    {
        using var kernelProvider = new KernelRequestTracer();
        Kernel kernel = kernelProvider.GetNewKernel();

        await KernelRequestTracer.RunPromptAsync(kernel, isInline, isStreaming, templateFormat, prompt, new()
        {
            { "city", "Seattle" }
        });

        string requestContent = kernelProvider.GetRequestContent();
        JsonNode? obtainedObject = JsonNode.Parse(requestContent);
        Assert.NotNull(obtainedObject);

        string expected = await File.ReadAllTextAsync(isStreaming
            ? "./CrossLanguage/Data/PromptWithSimpleVariableStreamingTest.json"
            : "./CrossLanguage/Data/PromptWithSimpleVariableTest.json");

        JsonNode? expectedObject = JsonNode.Parse(expected);
        Assert.NotNull(expectedObject);

        if (isStreaming)
        {
            expectedObject["stream"] = true;
        }

        Assert.True(JsonNode.DeepEquals(obtainedObject, expectedObject));
    }
}

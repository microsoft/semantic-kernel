// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.IntegrationTests.CrossLanguage;

public class SimplePromptTest
{
    private const string Prompt = "Can you help me tell the time in Seattle right now?";

    [Theory]
    [InlineData(true, false, "semantic-kernel", Prompt)]
    [InlineData(true, true, "semantic-kernel", Prompt)]
    [InlineData(false, false, "semantic-kernel", Prompt)]
    [InlineData(false, true, "semantic-kernel", Prompt)]
    [InlineData(false, false, "handlebars", Prompt)]
    [InlineData(false, true, "handlebars", Prompt)]
    public async Task SimplePromptAsync(bool isInline, bool isStreaming, string templateFormat, string prompt)
    {
        using var kernelProvider = new KernelRequestTracer();
        Kernel kernel = kernelProvider.GetNewKernel();

        await KernelRequestTracer.RunPromptAsync(kernel, isInline, isStreaming, templateFormat, prompt);

        string requestContent = kernelProvider.GetRequestContent();
        JsonNode? obtainedObject = JsonNode.Parse(requestContent);
        Assert.NotNull(obtainedObject);

        string expected = await File.ReadAllTextAsync(isStreaming
            ? "./CrossLanguage/Data/SimplePromptStreamingTest.json"
            : "./CrossLanguage/Data/SimplePromptTest.json");

        JsonNode? expectedObject = JsonNode.Parse(expected);
        Assert.NotNull(expectedObject);

        if (isStreaming)
        {
            expectedObject["stream"] = true;
        }

        Assert.True(JsonNode.DeepEquals(obtainedObject, expectedObject));
    }
}

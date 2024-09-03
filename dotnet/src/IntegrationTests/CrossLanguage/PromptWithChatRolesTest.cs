// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.IntegrationTests.CrossLanguage;

public class PromptWithChatRolesTest
{
    private const string Prompt = "<message role=\"user\">Can you help me tell the time in Seattle right now?</message><message role=\"assistant\">Sure! The time in Seattle is currently 3:00 PM.</message><message role=\"user\">What about New York?</message>";

    [Theory]
    [InlineData(true, false, "semantic-kernel", Prompt)]
    [InlineData(true, true, "semantic-kernel", Prompt)]
    [InlineData(false, false, "semantic-kernel", Prompt)]
    [InlineData(false, true, "semantic-kernel", Prompt)]
    [InlineData(false, false, "handlebars", Prompt)]
    [InlineData(false, true, "handlebars", Prompt)]
    public async Task PromptWithChatRolesAsync(bool isInline, bool isStreaming, string templateFormat, string prompt)
    {
        using var kernelProvider = new KernelRequestTracer();
        Kernel kernel = kernelProvider.GetNewKernel();

        await KernelRequestTracer.RunPromptAsync(kernel, isInline, isStreaming, templateFormat, prompt);

        string requestContent = kernelProvider.GetRequestContent();
        JsonNode? obtainedObject = JsonNode.Parse(requestContent);
        Assert.NotNull(obtainedObject);

        string expected = await File.ReadAllTextAsync(isStreaming
            ? "./CrossLanguage/Data/PromptWithChatRolesStreamingTest.json"
            : "./CrossLanguage/Data/PromptWithChatRolesTest.json");

        JsonNode? expectedObject = JsonNode.Parse(expected);
        Assert.NotNull(expectedObject);

        Assert.True(JsonNode.DeepEquals(obtainedObject, expectedObject));
    }
}

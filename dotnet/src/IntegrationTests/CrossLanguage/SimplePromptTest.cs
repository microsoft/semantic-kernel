// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.IntegrationTests.CrossLanguage;

public class SimplePromptTest
{
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task SimplePromptAsync(bool isStreaming)
    {
        const string Prompt = "Can you help me tell the time in Seattle right now?";

        using var kernelProvider = new KernelRequestTracer();

        Kernel kernel = kernelProvider.GetNewKernel();
        if (isStreaming)
        {
            await KernelRequestTracer.InvokePromptStreamingAsync(kernel, Prompt);
        }
        else
        {
            await kernel.InvokePromptAsync<ChatMessageContent>(Prompt);
        }
        string requestContent = kernelProvider.GetRequestContent();
        JsonNode? obtainedObject = JsonNode.Parse(requestContent);
        Assert.NotNull(obtainedObject);

        string expected = await File.ReadAllTextAsync("./CrossLanguage/Data/SimplePromptTest.json");
        JsonNode? expectedObject = JsonNode.Parse(expected);
        Assert.NotNull(expectedObject);

        if (isStreaming)
        {
            expectedObject["stream"] = true;
        }

        Assert.True(JsonNode.DeepEquals(obtainedObject, expectedObject));
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.IntegrationTests.CrossLanguage;

public class PromptWithSimpleVariableTest
{
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task PromptWithSimpleVariableAsync(bool isStreaming)
    {
        const string Prompt = "Can you help me tell the time in {{$city}} right now?";

        using var kernelProvider = new KernelRequestTracer();

        Kernel kernel = kernelProvider.GetNewKernel();
        if (isStreaming)
        {
            await KernelRequestTracer.InvokePromptStreamingAsync(kernel, Prompt, new()
            {
                { "city", "Seattle" }
            });
        }
        else
        {
            await kernel.InvokePromptAsync<ChatMessageContent>(Prompt, arguments: new()
            {
                { "city", "Seattle" }
            });
        }
        string requestContent = kernelProvider.GetRequestContent();
        JsonNode? obtainedObject = JsonNode.Parse(requestContent);
        Assert.NotNull(obtainedObject);

        string expected = await File.ReadAllTextAsync("./CrossLanguage/Data/PromptWithSimpleVariableTest.json");
        JsonNode? expectedObject = JsonNode.Parse(expected);
        Assert.NotNull(expectedObject);

        if (isStreaming)
        {
            expectedObject["stream"] = true;
        }

        Assert.True(JsonNode.DeepEquals(obtainedObject, expectedObject));
    }
}

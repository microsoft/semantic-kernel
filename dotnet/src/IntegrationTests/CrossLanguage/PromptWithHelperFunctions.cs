// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using System;
using System.IO;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Xunit;

namespace SemanticKernel.IntegrationTests.CrossLanguage;

public class PromptWithHelperFunctions
{
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task PromptWithHelperFunctionsAsync(bool isStreaming)
    {
        const string Prompt = "<message role=\"system\">The current time is {{Time.Now}}</message><message role=\"user\">Can you help me tell the time in {{$city}} right now?</message>";

        using var kernelProvider = new KernelRequestTracer();

        Kernel kernel = kernelProvider.GetNewKernel();
        kernel.Plugins.AddFromFunctions("Time",
                        [KernelFunctionFactory.CreateFromMethod(() => $"{PromptWithHelperFunctions.UtcNow:r}", "Now", "Gets the current date and time")]);
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

        string expected = await File.ReadAllTextAsync("./CrossLanguage/Data/PromptWithHelperFunctionsTest.json");
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

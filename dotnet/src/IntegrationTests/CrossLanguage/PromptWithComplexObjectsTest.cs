// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using System.IO;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.IntegrationTests.CrossLanguage;

public class PromptWithComplexObjectsTest
{
    private const string Prompt = "Can you help me tell the time in {{city.name}} right now?";

    private sealed class City
    {
        public string name;

        public City(string name)
        {
            this.name = name;
        }
    }

    [Theory]
    [InlineData(false, false, "handlebars", Prompt)]
    [InlineData(false, true, "handlebars", Prompt)]
    public async Task PromptWithComplexObjectsAsync(bool isInline, bool isStreaming, string templateFormat, string prompt)
    {
        using var kernelProvider = new KernelRequestTracer();
        Kernel kernel = kernelProvider.GetNewKernel();

        await KernelRequestTracer.RunPromptAsync(kernel, isInline, isStreaming, templateFormat, prompt, new()
        {
            ["city"] = new City("Seattle")
        });

        string requestContent = kernelProvider.GetRequestContent();
        JsonNode? obtainedObject = JsonNode.Parse(requestContent);
        Assert.NotNull(obtainedObject);

        string expected = await File.ReadAllTextAsync(isStreaming
            ? "./CrossLanguage/Data/PromptWithComplexObjectsStreamingTest.json"
            : "./CrossLanguage/Data/PromptWithComplexObjectsTest.json");

        JsonNode? expectedObject = JsonNode.Parse(expected);
        Assert.NotNull(expectedObject);

        Assert.True(JsonNode.DeepEquals(obtainedObject, expectedObject));
    }
}

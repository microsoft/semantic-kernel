// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using Xunit;

namespace SemanticKernel.IntegrationTests.CrossLanguage;

public class YamlPromptTest
{
    [Theory]
    [InlineData(false, "./CrossLanguage/Data/SimplePromptTest.yaml", "./CrossLanguage/Data/SimplePromptTest.json")]
    [InlineData(true, "./CrossLanguage/Data/SimplePromptTest.yaml", "./CrossLanguage/Data/SimplePromptStreamingTest.json")]
    [InlineData(false, "./CrossLanguage/Data/PromptWithChatRolesTest-HB.yaml", "./CrossLanguage/Data/PromptWithChatRolesTest.json")]
    [InlineData(true, "./CrossLanguage/Data/PromptWithChatRolesTest-HB.yaml", "./CrossLanguage/Data/PromptWithChatRolesStreamingTest.json")]
    [InlineData(false, "./CrossLanguage/Data/PromptWithSimpleVariableTest.yaml", "./CrossLanguage/Data/PromptWithSimpleVariableTest.json")]
    [InlineData(true, "./CrossLanguage/Data/PromptWithSimpleVariableTest.yaml", "./CrossLanguage/Data/PromptWithSimpleVariableStreamingTest.json")]
    public async Task YamlPromptAsync(bool isStreaming, string promptPath, string expectedResultPath)
    {
        using var kernelProvider = new KernelRequestTracer();
        Kernel kernel = kernelProvider.GetNewKernel();
        var promptTemplateFactory = new AggregatorPromptTemplateFactory(
                                        new KernelPromptTemplateFactory(),
                                        new HandlebarsPromptTemplateFactory());

        string yamlPrompt = await File.ReadAllTextAsync(promptPath);
        KernelFunction function = kernel.CreateFunctionFromPromptYaml(yamlPrompt, promptTemplateFactory);

        await KernelRequestTracer.RunFunctionAsync(kernel, isStreaming, function);

        string requestContent = kernelProvider.GetRequestContent();
        JsonNode? obtainedObject = JsonNode.Parse(requestContent);
        Assert.NotNull(obtainedObject);

        string expected = await File.ReadAllTextAsync(expectedResultPath);
        JsonNode? expectedObject = JsonNode.Parse(expected);
        Assert.NotNull(expectedObject);

        if (isStreaming)
        {
            expectedObject["stream"] = true;
        }

        Assert.True(JsonNode.DeepEquals(obtainedObject, expectedObject));
    }
}

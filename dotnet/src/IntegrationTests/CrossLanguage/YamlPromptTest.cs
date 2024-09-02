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
    [InlineData(false, "./CrossLanguage/Data/SimplePromptTest.yaml", "./CrossLanguage/Data/SimplePromptTest.json", "./CrossLanguage/Data/SimplePromptTestStreaming.json")]
    [InlineData(true, "./CrossLanguage/Data/SimplePromptTest.yaml", "./CrossLanguage/Data/SimplePromptTest.json", "./CrossLanguage/Data/SimplePromptTestStreaming.json")]
    [InlineData(false, "./CrossLanguage/Data/PromptWithChatRolesTest-HB.yaml", "./CrossLanguage/Data/PromptWithChatRolesTest.json", "./CrossLanguage/Data/PromptWithChatRolesTestStreaming.json")]
    [InlineData(true, "./CrossLanguage/Data/PromptWithChatRolesTest-HB.yaml", "./CrossLanguage/Data/PromptWithChatRolesTest.json", "./CrossLanguage/Data/PromptWithChatRolesTestStreaming.json")]
    [InlineData(false, "./CrossLanguage/Data/PromptWithSimpleVariableTest.yaml", "./CrossLanguage/Data/PromptWithSimpleVariableTest.json", "./CrossLanguage/Data/PromptWithSimpleVariableTestStreaming.json")]
    [InlineData(true, "./CrossLanguage/Data/PromptWithSimpleVariableTest.yaml", "./CrossLanguage/Data/PromptWithSimpleVariableTest.json", "./CrossLanguage/Data/PromptWithSimpleVariableTestStreaming.json")]
    public async Task YamlPromptAsync(bool isStreaming, string promptPath, string expectedResultPath, string expectedStreamingResultPath)
    {
        using var kernelProvider = new KernelRequestTracer();
        Kernel kernel = kernelProvider.GetNewKernel(isStreaming);
        var promptTemplateFactory = new AggregatorPromptTemplateFactory(
                                        new KernelPromptTemplateFactory(),
                                        new HandlebarsPromptTemplateFactory());

        string yamlPrompt = await File.ReadAllTextAsync(promptPath);
        KernelFunction function = kernel.CreateFunctionFromPromptYaml(yamlPrompt, promptTemplateFactory);

        await KernelRequestTracer.RunFunctionAsync(kernel, isStreaming, function);

        string requestContent = kernelProvider.GetRequestContent();
        JsonNode? obtainedObject = JsonNode.Parse(requestContent);
        Assert.NotNull(obtainedObject);

        string expected = await File.ReadAllTextAsync(isStreaming ? expectedStreamingResultPath : expectedResultPath);
        JsonNode? expectedObject = JsonNode.Parse(expected);
        Assert.NotNull(expectedObject);

        Assert.True(JsonNode.DeepEquals(obtainedObject, expectedObject));
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.FileProviders;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit;

namespace SemanticKernel.Functions.Prompty.UnitTests;

public sealed class PromptyTests
{
    [Fact]
    public void ChatPromptyTest()
    {
        // Arrange
        Kernel kernel = new();
        var chatPromptyPath = Path.Combine("TestData", "chat.prompty");
        var promptyTemplate = File.ReadAllText(chatPromptyPath);

        // Act
        var kernelFunction = kernel.CreateFunctionFromPrompty(promptyTemplate);

        // Assert
        Assert.Equal("Contoso_Chat_Prompt", kernelFunction.Name);
        Assert.Equal("A retail assistant for Contoso Outdoors products retailer.", kernelFunction.Description);

        // chat prompty does contain input parameters
        Assert.Equal(5, kernelFunction.Metadata.Parameters.Count);
    }

    [Fact]
    public void ChatPromptyShouldSupportCreatingOpenAIExecutionSettings()
    {
        // Arrange
        Kernel kernel = new();
        var chatPromptyPath = Path.Combine("TestData", "chat.prompty");

        // Act
        var kernelFunction = kernel.CreateFunctionFromPromptyFile(chatPromptyPath);

        // Assert
        // kernel function created from chat.prompty should have a single execution setting
        Assert.Single(kernelFunction.ExecutionSettings!);
        Assert.True(kernelFunction.ExecutionSettings!.ContainsKey("default"));

        // Arrange
        var defaultExecutionSetting = kernelFunction.ExecutionSettings["default"];

        // Act
        var executionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(defaultExecutionSetting);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal("gpt-35-turbo", executionSettings.ModelId);
        Assert.Null(executionSettings.Temperature);
        Assert.Null(executionSettings.TopP);
        Assert.Null(executionSettings.StopSequences);
        Assert.Null(executionSettings.ResponseFormat);
        Assert.Null(executionSettings.TokenSelectionBiases);
        Assert.Null(executionSettings.MaxTokens);
        Assert.Null(executionSettings.Seed);
    }

    [Fact]
    public void ChatPromptyShouldSupportCreatingOpenAIExecutionSettingsWithJsonObject()
    {
        // Arrange
        Kernel kernel = new();
        var chatPromptyPath = Path.Combine("TestData", "chatJsonObject.prompty");

        // Act
        var kernelFunction = kernel.CreateFunctionFromPromptyFile(chatPromptyPath);

        // Assert
        // kernel function created from chat.prompty should have a single execution setting
        Assert.Single(kernelFunction.ExecutionSettings!);
        Assert.True(kernelFunction.ExecutionSettings!.ContainsKey("default"));

        // Arrange
        var defaultExecutionSetting = kernelFunction.ExecutionSettings["default"];

        // Act
        var executionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(defaultExecutionSetting);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal("gpt-4o", executionSettings.ModelId);
        Assert.Equal(0, executionSettings.Temperature);
        Assert.Equal(1.0, executionSettings.TopP);
        Assert.Null(executionSettings.StopSequences);
        Assert.Equal("{\"type\":\"json_object\"}", executionSettings.ResponseFormat?.ToString());
        Assert.Null(executionSettings.TokenSelectionBiases);
        Assert.Equal(3000, executionSettings.MaxTokens);
        Assert.Null(executionSettings.Seed);
    }

    [Fact]
    public void ItShouldCreateFunctionFromPromptYamlWithNoExecutionSettings()
    {
        // Arrange
        Kernel kernel = new();
        var promptyPath = Path.Combine("TestData", "chatNoExecutionSettings.prompty");

        // Act
        var kernelFunction = kernel.CreateFunctionFromPromptyFile(promptyPath);

        // Assert
        Assert.NotNull(kernelFunction);
        Assert.Equal("prompty_with_no_execution_setting", kernelFunction.Name);
        Assert.Equal("prompty without execution setting", kernelFunction.Description);
        Assert.Single(kernelFunction.Metadata.Parameters);
        Assert.Equal("prompt", kernelFunction.Metadata.Parameters[0].Name);
        Assert.Empty(kernelFunction.ExecutionSettings!);
    }

    [Fact]
    public void ItShouldCreateFunctionFromPromptYamlWithEmbeddedFileProvider()
    {
        // Arrange
        Kernel kernel = new();
        var chatPromptyPath = Path.Combine("TestData", "chat.prompty");
        ManifestEmbeddedFileProvider manifestEmbeddedProvider = new(typeof(PromptyTests).Assembly);

        // Act
        var kernelFunction = kernel.CreateFunctionFromPromptyFile(chatPromptyPath,
            fileProvider: manifestEmbeddedProvider);

        // Assert
        Assert.NotNull(kernelFunction);

        var executionSettings = kernelFunction.ExecutionSettings;
        Assert.Single(executionSettings!);
        Assert.True(executionSettings!.ContainsKey("default"));
    }

    [Fact]
    public void ItShouldCreateFunctionFromPromptYamlWithFileProvider()
    {
        // Arrange
        Kernel kernel = new();
        var currentDirectory = Directory.GetCurrentDirectory();
        var chatPromptyPath = Path.Combine("TestData", "chat.prompty");
        using PhysicalFileProvider fileProvider = new(currentDirectory);

        // Act
        var kernelFunction = kernel.CreateFunctionFromPromptyFile(chatPromptyPath,
            fileProvider);

        // Assert
        Assert.NotNull(kernelFunction);

        var executionSettings = kernelFunction.ExecutionSettings;
        Assert.Single(executionSettings!);
        Assert.True(executionSettings!.ContainsKey("default"));
    }

    [Fact]
    public void ItShouldCreateFunctionFromPromptYamlWithFileInfo()
    {
        // Arrange
        Kernel kernel = new();
        var currentDirectory = Directory.GetCurrentDirectory();
        var chatPromptyPath = Path.Combine("TestData", "chat.prompty");
        using PhysicalFileProvider fileProvider = new(currentDirectory);
        var fileInfo = fileProvider.GetFileInfo(chatPromptyPath);

        // Act
        var kernelFunction = kernel.CreateFunctionFromPromptyFile(
            fileInfo: fileInfo);

        // Assert
        Assert.NotNull(kernelFunction);

        var executionSettings = kernelFunction.ExecutionSettings;
        Assert.Single(executionSettings!);
        Assert.True(executionSettings!.ContainsKey("default"));
    }

    [Fact]
    public void ItFailsToParseAnEmptyHeader()
    {
        Kernel kernel = new();

        Assert.NotNull(kernel.CreateFunctionFromPrompty("""
            ---
            name: MyPrompt
            ---
            Hello
            """));

        Assert.Throws<ArgumentException>(() => kernel.CreateFunctionFromPrompty("""
            ---
            ---
            Hello
            """));

        Assert.Throws<ArgumentException>(() => kernel.CreateFunctionFromPrompty("""
            ---



            ---
            Hello
            """));
    }

    [Theory]
    [InlineData("""
         ---
        name: SomePrompt
        ---
        Abc
        """)]
    [InlineData("""
        ---
        name: SomePrompt
         ---
        Abc
        """)]
    [InlineData("""
        ---a
        name: SomePrompt
        ---
        Abc
        """)]
    [InlineData("""
        ---
        name: SomePrompt
        ---b
        Abc
        """)]
    public void ItRequiresStringSeparatorPlacement(string prompt)
    {
        // Arrange
        Kernel kernel = new();

        // Act / Assert
        Assert.Throws<ArgumentException>(() => kernel.CreateFunctionFromPrompty(prompt));
    }

    [Fact]
    public async Task ItSupportsSeparatorInContentAsync()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<ITextGenerationService>(_ => new EchoTextGenerationService());
        Kernel kernel = builder.Build();

        // Act
        var kernelFunction = kernel.CreateFunctionFromPrompty("""
            ---
            name: SomePrompt
            description: This is the description.
            ---
            Abc---def
            ---
            Efg
            """);

        // Assert
        Assert.NotNull(kernelFunction);
        Assert.Equal("SomePrompt", kernelFunction.Name);
        Assert.Equal("This is the description.", kernelFunction.Description);
        Assert.Equal("""
            Abc---def
            ---
            Efg
            """, await kernelFunction.InvokeAsync<string>(kernel));
    }

    [Fact]
    public void ItCreatesInputVariablesForSimpleVariables()
    {
        // Arrange
        const string Prompty = """
            ---
            name: MyPrompt
            ---
            {{a}} {{b}} {{c}}
            """;
        string[] expectedVariables = ["a", "b", "c"];

        // Act
        var kernelFunction = new Kernel().CreateFunctionFromPrompty(Prompty);

        // Assert
        Assert.NotNull(kernelFunction);
        Assert.Equal(expectedVariables, kernelFunction.Metadata.Parameters.Select(p => p.Name));
    }

    [Theory]
    [InlineData("""
        ---
        name: MyPrompt
        ---
        {{a}}
        {% for item in items %}
        {% endfor %}
        """)]
    [InlineData("""
        ---
        name: MyPrompt
        ---
        {{a}} {{b}} {{c.d}}
        """)]
    [InlineData("""
        ---
        name: MyPrompt
        ---
        {{a.b}}
        """)]
    [InlineData("""
        ---
        name: MyPrompt
        ---
        {{a}} {{b}} {{a.c}}
        """)]
    public void ItAvoidsCreatingInputVariablesIfAnythingComplex(string prompty)
    {
        // Act
        var kernelFunction = new Kernel().CreateFunctionFromPrompty(prompty);

        // Assert
        Assert.NotNull(kernelFunction);
        Assert.Empty(kernelFunction.Metadata.Parameters.Select(p => p.Name));
    }

    [Fact]
    public void ItCreatesInputVariablesOnlyWhenNoneAreExplicitlySet()
    {
        // Arrange
        const string Prompty = """
            ---
            name: MyPrompt
            inputs:
              question:
                description: What is the color of the sky?
            ---
            {{a}} {{b}} {{c}}
            """;
        string[] expectedVariables = ["question"];

        // Act
        var kernelFunction = new Kernel().CreateFunctionFromPrompty(Prompty);

        // Assert
        Assert.NotNull(kernelFunction);
        Assert.Equal(expectedVariables, kernelFunction.Metadata.Parameters.Select(p => p.Name));
    }

    [Fact]
    public void ItShouldLoadExecutionSettings()
    {
        // Arrange
        const string Prompty = """
            ---
            name: SomePrompt
            description: This is the description.
            model:
                api: chat
                connection:
                    type: azure_openai_beta
                options:
                    logprobs: true
                    top_logprobs: 2
                    top_p: 1.0
                    user: Bob
                    stop_sequences:
                      - END
                      - COMPLETE
                    token_selection_biases:
                      1: 2
                      3: 4
            ---
            Abc---def
            """;

        // Act
        var kernelFunction = new Kernel().CreateFunctionFromPrompty(Prompty);
        PromptExecutionSettings executionSettings = kernelFunction.ExecutionSettings!["default"];

        // Assert
        Assert.NotNull(kernelFunction);
        Assert.NotNull(executionSettings);
        var openaiExecutionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(executionSettings);
        Assert.NotNull(openaiExecutionSettings);
        Assert.True(openaiExecutionSettings.Logprobs);
        Assert.Equal(2, openaiExecutionSettings.TopLogprobs);
        Assert.Equal(1.0, openaiExecutionSettings.TopP);
        Assert.Equal("Bob", openaiExecutionSettings.User);
        Assert.Equal(["END", "COMPLETE"], openaiExecutionSettings.StopSequences);
        Assert.Equal(new Dictionary<int, int>() { { 1, 2 }, { 3, 4 } }, openaiExecutionSettings.TokenSelectionBiases);
    }

    [Fact]
    public void ItShouldCreateFunctionFromPromptYamlContainingRelativeFileReferences()
    {
        // Arrange
        Kernel kernel = new();
        var promptyPath = Path.Combine("TestData", "relativeFileReference.prompty");

        // Act
        var kernelFunction = kernel.CreateFunctionFromPromptyFile(promptyPath);

        // Assert
        Assert.NotNull(kernelFunction);
        var executionSettings = kernelFunction.ExecutionSettings;
        Assert.Single(executionSettings!);
        Assert.True(executionSettings!.ContainsKey("default"));
        var defaultExecutionSetting = executionSettings["default"];
        Assert.Equal("gpt-35-turbo", defaultExecutionSetting.ModelId);
    }

    [Fact]
    public void ItShouldCreateFunctionFromPromptYamlContainingRelativeFileReferencesWithFileProvider()
    {
        // Arrange
        Kernel kernel = new();
        var currentDirectory = Directory.GetCurrentDirectory();
        var promptyPath = Path.Combine("TestData", "relativeFileReference.prompty");
        using PhysicalFileProvider fileProvider = new(currentDirectory);

        // Act
        var kernelFunction = kernel.CreateFunctionFromPromptyFile(promptyPath,
            fileProvider);

        // Assert
        Assert.NotNull(kernelFunction);
        var executionSettings = kernelFunction.ExecutionSettings;
        Assert.Single(executionSettings!);
        Assert.True(executionSettings!.ContainsKey("default"));
        var defaultExecutionSetting = executionSettings["default"];
        Assert.Equal("gpt-35-turbo", defaultExecutionSetting.ModelId);
    }

    [Fact]
    public void JsonSchemaTest()
    {
        // Arrange
        Kernel kernel = new();
        var chatPromptyPath = Path.Combine("TestData", "chat.prompty");
        var promptyTemplate = File.ReadAllText(chatPromptyPath);

        // Act
        var kernelFunction = kernel.CreateFunctionFromPrompty(promptyTemplate);

        // Assert
        var firstName = kernelFunction.Metadata.Parameters.First(p => p.Name == "firstName");
        Assert.NotNull(firstName);
        Assert.NotNull(firstName.Schema);
        Assert.Equal("{\"type\":\"string\"}", firstName.Schema.ToString());
        var answer = kernelFunction.Metadata.Parameters.First(p => p.Name == "answer");
        Assert.NotNull(answer);
        Assert.NotNull(answer.Schema);
        Assert.Equal("{\"type\":\"object\",\"properties\":{\"answer\":{\"type\":\"string\"},\"citations\":{\"type\":\"array\",\"items\":{\"type\":\"string\",\"format\":\"uri\"}}},\"required\":[\"answer\",\"citations\"],\"additionalProperties\":false}", answer.Schema.ToString());
        var other = kernelFunction.Metadata.Parameters.First(p => p.Name == "other");
        Assert.NotNull(other);
        Assert.NotNull(other.Schema);
        Assert.Equal("{\"type\":\"object\",\"properties\":{\"answer\":{\"type\":\"string\"},\"citations\":{\"type\":\"array\",\"items\":{\"type\":\"string\",\"format\":\"uri\"}}},\"required\":[\"answer\",\"citations\"],\"additionalProperties\":\"false\"}", other.Schema.ToString());
    }

    private sealed class EchoTextGenerationService : ITextGenerationService
    {
        public IReadOnlyDictionary<string, object?> Attributes { get; } = new Dictionary<string, object?>();

        public Task<IReadOnlyList<TextContent>> GetTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default) =>
            Task.FromResult<IReadOnlyList<TextContent>>([new TextContent(prompt)]);

        public async IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            await Task.Delay(0, cancellationToken);
            yield return new StreamingTextContent(prompt);
        }
    }
}

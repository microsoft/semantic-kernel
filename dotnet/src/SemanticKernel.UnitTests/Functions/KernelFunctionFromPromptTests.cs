// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.TextGeneration;
using Moq;
using Xunit;

// ReSharper disable StringLiteralTypo

namespace SemanticKernel.UnitTests.Functions;

public class KernelFunctionFromPromptTests
{
    [Fact]
    public void ItAddsMissingVariablesForPrompt()
    {
        // Arrange & Act
        var function = KernelFunctionFromPrompt.Create("This {{$x11}} {{$a}}{{$missing}} test template {{p.bar $b}} and {{p.foo c='literal \"c\"' d = $d}} and {{p.baz ename=$e}}");

        // Assert
        Assert.NotNull(function);
        Assert.NotNull(function.Metadata);
        Assert.NotNull(function.Metadata.Parameters);
        Assert.Equal(6, function.Metadata.Parameters.Count);
        Assert.Equal("x11", function.Metadata.Parameters[0].Name);
        Assert.Equal("a", function.Metadata.Parameters[1].Name);
        Assert.Equal("missing", function.Metadata.Parameters[2].Name);
        Assert.Equal("b", function.Metadata.Parameters[3].Name);
        Assert.Equal("d", function.Metadata.Parameters[4].Name);
        Assert.Equal("e", function.Metadata.Parameters[5].Name);
    }

    [Fact]
    public void ItProvidesAccessToFunctionsViaFunctionCollection()
    {
        // Arrange
        var factory = new Mock<Func<IServiceProvider, ITextGenerationService>>();
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton(factory.Object);
        Kernel kernel = builder.Build();

        kernel.ImportPluginFromFunctions("jk", functions: new[] { kernel.CreateFunctionFromPrompt(promptTemplate: "Tell me a joke", functionName: "joker", description: "Nice fun") });

        // Act & Assert - 3 functions, var name is not case sensitive
        Assert.True(kernel.Plugins.TryGetFunction("jk", "joker", out _));
        Assert.True(kernel.Plugins.TryGetFunction("JK", "JOKER", out _));
    }

    [Theory]
    [InlineData(null, "Assistant is a large language model.")]
    [InlineData("My Chat Prompt", "My Chat Prompt")]
    public async Task ItUsesChatSystemPromptWhenProvidedAsync(string? providedSystemChatPrompt, string expectedSystemChatPrompt)
    {
        // Arrange
        var mockTextGeneration = new Mock<ITextGenerationService>();
        var fakeTextContent = new TextContent("llmResult");

        mockTextGeneration.Setup(c => c.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { fakeTextContent });

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton("x", mockTextGeneration.Object);
        Kernel kernel = builder.Build();

        var promptConfig = new PromptTemplateConfig();
        promptConfig.Template = "template";
        var openAIExecutionSettings = providedSystemChatPrompt is null
            ? new OpenAIPromptExecutionSettings()
            : new OpenAIPromptExecutionSettings
            {
                ChatSystemPrompt = providedSystemChatPrompt
            };

        promptConfig.AddExecutionSettings(openAIExecutionSettings);
        var func = kernel.CreateFunctionFromPrompt(promptConfig);

        // Act
        await kernel.InvokeAsync(func);

        // Assert
        mockTextGeneration.Verify(a => a.GetTextContentsAsync("template", It.Is<OpenAIPromptExecutionSettings>(c => c.ChatSystemPrompt == expectedSystemChatPrompt), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task ItUsesServiceIdWhenProvidedAsync()
    {
        // Arrange
        var mockTextGeneration1 = new Mock<ITextGenerationService>();
        var mockTextGeneration2 = new Mock<ITextGenerationService>();
        var fakeTextContent = new TextContent("llmResult");

        mockTextGeneration1.Setup(c => c.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { fakeTextContent });
        mockTextGeneration2.Setup(c => c.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { fakeTextContent });

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton("service1", mockTextGeneration1.Object);
        builder.Services.AddKeyedSingleton("service2", mockTextGeneration2.Object);
        Kernel kernel = builder.Build();

        var promptConfig = new PromptTemplateConfig();
        promptConfig.Template = "template";
        promptConfig.AddExecutionSettings(new PromptExecutionSettings(), "service1");
        var func = kernel.CreateFunctionFromPrompt(promptConfig);

        // Act
        await kernel.InvokeAsync(func);

        // Assert
        mockTextGeneration1.Verify(a => a.GetTextContentsAsync("template", It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
        mockTextGeneration2.Verify(a => a.GetTextContentsAsync("template", It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Never());
    }

    [Fact]
    public async Task ItFailsIfInvalidServiceIdIsProvidedAsync()
    {
        // Arrange
        var mockTextGeneration1 = new Mock<ITextGenerationService>();
        var mockTextGeneration2 = new Mock<ITextGenerationService>();

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton("service1", mockTextGeneration1.Object);
        builder.Services.AddKeyedSingleton("service2", mockTextGeneration2.Object);
        Kernel kernel = builder.Build();

        var promptConfig = new PromptTemplateConfig();
        promptConfig.Template = "template";
        promptConfig.AddExecutionSettings(new PromptExecutionSettings(), "service3");
        var func = kernel.CreateFunctionFromPrompt(promptConfig);

        // Act
        var exception = await Assert.ThrowsAsync<KernelException>(() => kernel.InvokeAsync(func));

        // Assert
        Assert.Equal("Required service of type Microsoft.SemanticKernel.TextGeneration.ITextGenerationService not registered. Expected serviceIds: service3.", exception.Message);
    }

    [Fact]
    public async Task ItParsesStandardizedPromptWhenServiceIsChatCompletionAsync()
    {
        var fakeService = new FakeChatAsTextService();
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<ITextGenerationService>((sp) => fakeService);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt(@"
            <message role=""system"">You are a helpful assistant.</message>
            <message role=""user"">How many 20 cents can I get from 1 dollar?</message>
        ");

        // Act + Assert
        await kernel.InvokeAsync(function);

        Assert.NotNull(fakeService.ChatHistory);
        Assert.Equal(2, fakeService.ChatHistory.Count);
        Assert.Equal("You are a helpful assistant.", fakeService.ChatHistory[0].Content);
        Assert.Equal("How many 20 cents can I get from 1 dollar?", fakeService.ChatHistory[1].Content);
    }

    [Fact]
    public async Task ItParsesStandardizedPromptWhenServiceIsStreamingChatCompletionAsync()
    {
        var fakeService = new FakeChatAsTextService();
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<ITextGenerationService>((sp) => fakeService);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt(@"
            <message role=""system"">You are a helpful assistant.</message>
            <message role=""user"">How many 20 cents can I get from 1 dollar?</message>
        ");

        // Act + Assert
        await foreach (var chunk in kernel.InvokeStreamingAsync(function))
        {
        }

        Assert.NotNull(fakeService.ChatHistory);
        Assert.Equal(2, fakeService.ChatHistory.Count);
        Assert.Equal("You are a helpful assistant.", fakeService.ChatHistory[0].Content);
        Assert.Equal("How many 20 cents can I get from 1 dollar?", fakeService.ChatHistory[1].Content);
    }

    [Fact]
    public async Task ItNotParsesStandardizedPromptWhenServiceIsOnlyTextCompletionAsync()
    {
        var mockService = new Mock<ITextGenerationService>();
        var mockResult = mockService.Setup(s => s.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<TextContent>() { new("something") });

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<ITextGenerationService>((sp) => mockService.Object);
        Kernel kernel = builder.Build();

        var inputPrompt = @"
            <message role=""system"">You are a helpful assistant.</message>
            <message role=""user"">How many 20 cents can I get from 1 dollar?</message>
        ";

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt(inputPrompt);

        // Act + Assert
        mockResult.Callback((string prompt, PromptExecutionSettings _, Kernel _, CancellationToken _) =>
        {
            Assert.NotNull(prompt);
            Assert.Equal(inputPrompt, prompt);
        });

        await kernel.InvokeAsync(function);
    }

    [Fact]
    public async Task ItNotParsesStandardizedPromptWhenStreamingWhenServiceIsOnlyTextCompletionAsync()
    {
        var mockService = new Mock<ITextGenerationService>();
        var mockResult = mockService.Setup(s => s.GetStreamingTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()))
            .Returns((new List<StreamingTextContent>() { new("something") }).ToAsyncEnumerable());

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<ITextGenerationService>((sp) => mockService.Object);
        Kernel kernel = builder.Build();

        var inputPrompt = @"
            <message role=""system"">You are a helpful assistant.</message>
            <message role=""user"">How many 20 cents can I get from 1 dollar?</message>
        ";

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt(inputPrompt);

        // Act + Assert
        mockResult.Callback((string prompt, PromptExecutionSettings _, Kernel _, CancellationToken _) =>
        {
            Assert.NotNull(prompt);
            Assert.Equal(inputPrompt, prompt);
        });

        await foreach (var chunk in kernel.InvokeStreamingAsync(function))
        {
        }
    }

    [Fact]
    public async Task InvokeAsyncReturnsTheConnectorResultWhenInServiceIsOnlyTextCompletionAsync()
    {
        var mockService = new Mock<ITextGenerationService>();
        var mockResult = mockService.Setup(s => s.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<TextContent>() { new("something") });

        KernelBuilder builder = new();
        builder.Services.AddTransient<ITextGenerationService>((sp) => mockService.Object);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("Anything");

        var result = await kernel.InvokeAsync(function);

        Assert.Equal("something", result.GetValue<string>());
        Assert.Equal("something", result.GetValue<TextContent>()!.Text);
        Assert.Equal("something", result.GetValue<KernelContent>()!.ToString());
    }

    [Fact]
    public async Task InvokeAsyncReturnsTheConnectorChatResultWhenInServiceIsOnlyChatCompletionAsync()
    {
        var mockService = new Mock<IChatCompletionService>();
        var mockResult = mockService.Setup(s => s.GetChatMessageContentsAsync(It.IsAny<ChatHistory>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<ChatMessageContent>() { new(AuthorRole.User, "something") });

        KernelBuilder builder = new();
        builder.Services.AddTransient<IChatCompletionService>((sp) => mockService.Object);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("Anything");

        var result = await kernel.InvokeAsync(function);

        Assert.Equal("something", result.GetValue<string>());
        Assert.Equal("something", result.GetValue<ChatMessageContent>()!.Content);
        Assert.Equal(AuthorRole.User, result.GetValue<ChatMessageContent>()!.Role);
        Assert.Equal("something", result.GetValue<KernelContent>()!.ToString());
    }

    [Fact]
    public async Task InvokeAsyncReturnsTheConnectorChatResultWhenInServiceIsChatAndTextCompletionAsync()
    {
        var fakeService = new FakeChatAsTextService();
        KernelBuilder builder = new();
        builder.Services.AddTransient<ITextGenerationService>((sp) => fakeService);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("Anything");

        var result = await kernel.InvokeAsync(function);

        Assert.Equal("Something", result.GetValue<string>());
        Assert.Equal("Something", result.GetValue<ChatMessageContent>()!.Content);
        Assert.Equal(AuthorRole.Assistant, result.GetValue<ChatMessageContent>()!.Role);
        Assert.Equal("Something", result.GetValue<KernelContent>()!.ToString());
    }

    [Fact]
    public async Task InvokeAsyncOfTGivesBackTheExpectedResultTypeFromTheConnectorWhenStreamingWhenServiceIsOnlyTextCompletionAsync()
    {
        var expectedContent = new StreamingTextContent("something");
        var mockService = new Mock<ITextGenerationService>();
        var mockResult = mockService.Setup(s => s.GetStreamingTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()))
            .Returns((new List<StreamingTextContent>() { expectedContent }).ToAsyncEnumerable());

        KernelBuilder builder = new();
        builder.Services.AddTransient<ITextGenerationService>((sp) => mockService.Object);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("Anything");

        await foreach (var chunk in kernel.InvokeStreamingAsync<StreamingKernelContent>(function))
        {
            Assert.Equal(expectedContent, chunk);
        }

        await foreach (var chunk in kernel.InvokeStreamingAsync<StreamingTextContent>(function))
        {
            Assert.Equal(expectedContent, chunk);
        }
    }

    [Fact]
    public async Task InvokeAsyncOfTGivesBackTheExpectedResultTypeFromTheConnectorWhenStreamingWhenerviceIsOnlyChatCompletionAsync()
    {
        var expectedContent = new StreamingChatMessageContent(AuthorRole.Assistant, "Something");
        var mockService = new Mock<IChatCompletionService>();
        var mockResult = mockService.Setup(s => s.GetStreamingChatMessageContentsAsync(It.IsAny<ChatHistory>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()))
            .Returns((new List<StreamingChatMessageContent>() { expectedContent }).ToAsyncEnumerable());

        KernelBuilder builder = new();
        builder.Services.AddTransient<IChatCompletionService>((sp) => mockService.Object);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("Anything");

        await foreach (var chunk in kernel.InvokeStreamingAsync<StreamingKernelContent>(function))
        {
            Assert.Equal(expectedContent, chunk);
            Assert.Equal("Something", chunk.ToString());
        }

        await foreach (var chunk in kernel.InvokeStreamingAsync<StreamingChatMessageContent>(function))
        {
            Assert.Equal(expectedContent, chunk);
            Assert.Equal("Something", chunk.Content);
            Assert.Equal(AuthorRole.Assistant, chunk.Role);
        }
    }

    [Fact]
    public async Task InvokeAsyncOfTGivesBackTheExpectedResultTypeFromTheConnectorWhenStreamingWhenServiceIsTextAndChatCompletionAsync()
    {
        var fakeService = new FakeChatAsTextService();
        KernelBuilder builder = new();
        builder.Services.AddTransient<ITextGenerationService>((sp) => fakeService);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("Anything");

        await foreach (var chunk in kernel.InvokeStreamingAsync<StreamingKernelContent>(function))
        {
            Assert.Equal("Something", chunk.ToString());
        }

        await foreach (var chunk in kernel.InvokeStreamingAsync<StreamingChatMessageContent>(function))
        {
            Assert.Equal(AuthorRole.Assistant, chunk.Role);
            Assert.Equal("Something", chunk.Content);
        }
    }

    [Fact]
    public async Task InvokeAsyncUsesPromptExecutionSettingsAsync()
    {
        // Arrange
        var mockTextContent = new TextContent("Result");
        var mockTextCompletion = new Mock<ITextGenerationService>();
        mockTextCompletion.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new List<TextContent> { mockTextContent });
        KernelBuilder builder = new();
        builder.Services.AddTransient<ITextGenerationService>((sp) => mockTextCompletion.Object);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("Anything", new OpenAIPromptExecutionSettings { MaxTokens = 1000 });

        // Act
        var result = await kernel.InvokeAsync(function);

        // Assert
        Assert.Equal("Result", result.GetValue<string>());
        mockTextCompletion.Verify(m => m.GetTextContentsAsync("Anything", It.Is<OpenAIPromptExecutionSettings>(settings => settings.MaxTokens == 1000), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task InvokeAsyncUsesKernelArgumentsExecutionSettingsAsync()
    {
        // Arrange
        var mockTextContent = new TextContent("Result");
        var mockTextCompletion = new Mock<ITextGenerationService>();
        mockTextCompletion.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new List<TextContent> { mockTextContent });
        KernelBuilder builder = new();
        builder.Services.AddTransient<ITextGenerationService>((sp) => mockTextCompletion.Object);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("Anything", new OpenAIPromptExecutionSettings { MaxTokens = 1000 });

        // Act
        var result = await kernel.InvokeAsync(function, new KernelArguments(new OpenAIPromptExecutionSettings { MaxTokens = 2000 }));

        // Assert
        Assert.Equal("Result", result.GetValue<string>());
        mockTextCompletion.Verify(m => m.GetTextContentsAsync("Anything", It.Is<OpenAIPromptExecutionSettings>(settings => settings.MaxTokens == 2000), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task InvokeAsyncWithServiceIdUsesKernelArgumentsExecutionSettingsAsync()
    {
        // Arrange
        var mockTextContent = new TextContent("Result");
        var mockTextCompletion = new Mock<ITextGenerationService>();
        mockTextCompletion.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new List<TextContent> { mockTextContent });
        KernelBuilder builder = new();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service1", mockTextCompletion.Object);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("Anything", new OpenAIPromptExecutionSettings { MaxTokens = 1000 });

        // Act
        var result = await kernel.InvokeAsync(function, new KernelArguments(new OpenAIPromptExecutionSettings { MaxTokens = 2000 }));

        // Assert
        Assert.Equal("Result", result.GetValue<string>());
        mockTextCompletion.Verify(m => m.GetTextContentsAsync("Anything", It.Is<OpenAIPromptExecutionSettings>(settings => settings.MaxTokens == 2000), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task InvokeAsyncWithMultipleServicesUsesKernelArgumentsExecutionSettingsAsync()
    {
        // Arrange
        var mockTextContent1 = new TextContent("Result1");
        var mockTextCompletion1 = new Mock<ITextGenerationService>();
        mockTextCompletion1.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new List<TextContent> { mockTextContent1 });
        var mockTextContent2 = new TextContent("Result2");
        var mockTextCompletion2 = new Mock<ITextGenerationService>();
        mockTextCompletion2.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new List<TextContent> { mockTextContent2 });

        KernelBuilder builder = new();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service1", mockTextCompletion1.Object);
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service2", mockTextCompletion2.Object);
        Kernel kernel = builder.Build();

        KernelFunction function1 = KernelFunctionFactory.CreateFromPrompt(new PromptTemplateConfig { Template = "Prompt1", ExecutionSettings = new() { ["service1"] = new OpenAIPromptExecutionSettings { MaxTokens = 1000 } } });
        KernelFunction function2 = KernelFunctionFactory.CreateFromPrompt(new PromptTemplateConfig { Template = "Prompt2", ExecutionSettings = new() { ["service2"] = new OpenAIPromptExecutionSettings { MaxTokens = 2000 } } });

        // Act
        var result1 = await kernel.InvokeAsync(function1);
        var result2 = await kernel.InvokeAsync(function2);

        // Assert
        Assert.Equal("Result1", result1.GetValue<string>());
        mockTextCompletion1.Verify(m => m.GetTextContentsAsync("Prompt1", It.Is<OpenAIPromptExecutionSettings>(settings => settings.MaxTokens == 1000), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
        Assert.Equal("Result2", result2.GetValue<string>());
        mockTextCompletion2.Verify(m => m.GetTextContentsAsync("Prompt2", It.Is<OpenAIPromptExecutionSettings>(settings => settings.MaxTokens == 2000), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task InvokeAsyncWithMultipleServicesUsesServiceFromKernelArgumentsExecutionSettingsAsync()
    {
        // Arrange
        var mockTextContent1 = new TextContent("Result1");
        var mockTextCompletion1 = new Mock<ITextGenerationService>();
        mockTextCompletion1.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new List<TextContent> { mockTextContent1 });
        var mockTextContent2 = new TextContent("Result2");
        var mockTextCompletion2 = new Mock<ITextGenerationService>();
        mockTextCompletion2.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new List<TextContent> { mockTextContent2 });

        KernelBuilder builder = new();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service1", mockTextCompletion1.Object);
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service2", mockTextCompletion2.Object);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("Prompt");

        // Act
        KernelArguments arguments1 = new();
        arguments1.ExecutionSettings = new Dictionary<string, PromptExecutionSettings>()
        {
            { "service1", new OpenAIPromptExecutionSettings { MaxTokens = 1000 } }
        };
        var result1 = await kernel.InvokeAsync(function, arguments1);

        KernelArguments arguments2 = new();
        arguments2.ExecutionSettings = new Dictionary<string, PromptExecutionSettings>()
        {
            { "service2", new OpenAIPromptExecutionSettings { MaxTokens = 2000 } }
        };
        var result2 = await kernel.InvokeAsync(function, arguments2);

        // Assert
        Assert.Equal("Result1", result1.GetValue<string>());
        mockTextCompletion1.Verify(m => m.GetTextContentsAsync("Prompt", It.Is<OpenAIPromptExecutionSettings>(settings => settings.MaxTokens == 1000), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
        Assert.Equal("Result2", result2.GetValue<string>());
        mockTextCompletion2.Verify(m => m.GetTextContentsAsync("Prompt", It.Is<OpenAIPromptExecutionSettings>(settings => settings.MaxTokens == 2000), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task InvokeAsyncWithMultipleServicesUsesKernelArgumentsExecutionSettingsOverrideAsync()
    {
        // Arrange
        var mockTextContent1 = new TextContent("Result1");
        var mockTextCompletion1 = new Mock<ITextGenerationService>();
        mockTextCompletion1.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new List<TextContent> { mockTextContent1 });
        var mockTextContent2 = new TextContent("Result2");
        var mockTextCompletion2 = new Mock<ITextGenerationService>();
        mockTextCompletion2.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new List<TextContent> { mockTextContent2 });

        KernelBuilder builder = new();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service1", mockTextCompletion1.Object);
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service2", mockTextCompletion2.Object);
        Kernel kernel = builder.Build();

        KernelFunction function1 = KernelFunctionFactory.CreateFromPrompt(new PromptTemplateConfig { Template = "Prompt1", ExecutionSettings = new() { ["service1"] = new OpenAIPromptExecutionSettings { MaxTokens = 1000 } } });
        KernelFunction function2 = KernelFunctionFactory.CreateFromPrompt(new PromptTemplateConfig { Template = "Prompt2", ExecutionSettings = new() { ["service2"] = new OpenAIPromptExecutionSettings { MaxTokens = 2000 } } });

        // Act
        KernelArguments arguments1 = new();
        arguments1.ExecutionSettings = new Dictionary<string, PromptExecutionSettings>()
        {
            { "service2", new OpenAIPromptExecutionSettings { MaxTokens = 2000 } }
        };
        var result1 = await kernel.InvokeAsync(function1, arguments1);

        KernelArguments arguments2 = new();
        arguments2.ExecutionSettings = new Dictionary<string, PromptExecutionSettings>()
        {
            { "service1", new OpenAIPromptExecutionSettings { MaxTokens = 1000 } }
        };
        var result2 = await kernel.InvokeAsync(function2, arguments2);

        // Assert
        Assert.Equal("Result2", result1.GetValue<string>());
        mockTextCompletion2.Verify(m => m.GetTextContentsAsync("Prompt1", It.Is<OpenAIPromptExecutionSettings>(settings => settings.MaxTokens == 2000), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
        Assert.Equal("Result1", result2.GetValue<string>());
        mockTextCompletion1.Verify(m => m.GetTextContentsAsync("Prompt2", It.Is<OpenAIPromptExecutionSettings>(settings => settings.MaxTokens == 1000), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task InvokeAsyncWithNestedPromptsSelectsCorrectServiceAsync()
    {
        // Arrange
        var mockTextContent1 = new TextContent("Result1");
        var mockTextCompletion1 = new Mock<ITextGenerationService>();
        mockTextCompletion1.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new List<TextContent> { mockTextContent1 });
        var mockTextContent2 = new TextContent("Result2");
        var mockTextCompletion2 = new Mock<ITextGenerationService>();
        mockTextCompletion2.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new List<TextContent> { mockTextContent2 });

        KernelBuilder builder = new();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service1", mockTextCompletion1.Object);
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service2", mockTextCompletion2.Object);
        Kernel kernel = builder.Build();

        KernelFunction function1 = KernelFunctionFactory.CreateFromPrompt(new PromptTemplateConfig { Name = "Prompt1", Template = "Prompt1", ExecutionSettings = new() { ["service1"] = new OpenAIPromptExecutionSettings { MaxTokens = 1000 } } });
        KernelFunction function2 = KernelFunctionFactory.CreateFromPrompt(new PromptTemplateConfig { Name = "Prompt2", Template = "Prompt2 {{MyPrompts.Prompt1}}", ExecutionSettings = new() { ["service2"] = new OpenAIPromptExecutionSettings { MaxTokens = 2000 } } });

        kernel.ImportPluginFromFunctions("MyPrompts", new[] { function1, function2 });

        // Act
        var result = await kernel.InvokeAsync(function2);

        // Assert
        Assert.Equal("Result2", result.GetValue<string>());
        mockTextCompletion1.Verify(m => m.GetTextContentsAsync("Prompt1", It.Is<OpenAIPromptExecutionSettings>(settings => settings.MaxTokens == 1000), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
        mockTextCompletion2.Verify(m => m.GetTextContentsAsync("Prompt2 Result1", It.Is<OpenAIPromptExecutionSettings>(settings => settings.MaxTokens == 2000), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task InvokeAsyncWithPromptRenderedHooksExecutesModifiedPromptAsync()
    {
        // Arrange
        var mockTextContent = new TextContent("Result");
        var mockTextCompletion = new Mock<ITextGenerationService>();
        mockTextCompletion.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new List<TextContent> { mockTextContent });

#pragma warning disable CS0618 // Events are deprecated
        void MyRenderedHandler(object? sender, PromptRenderedEventArgs e)
        {
            e.RenderedPrompt += " USE SHORT, CLEAR, COMPLETE SENTENCES.";
        }

        KernelBuilder builder = new();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service", mockTextCompletion.Object);
        Kernel kernel = builder.Build();
        kernel.PromptRendered += MyRenderedHandler;
#pragma warning restore CS0618 // Events are deprecated

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("Prompt");

        // Act
        var result1 = await kernel.InvokeAsync(function);

        // Assert
        mockTextCompletion.Verify(m => m.GetTextContentsAsync("Prompt USE SHORT, CLEAR, COMPLETE SENTENCES.", It.IsAny<OpenAIPromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Theory]
    [InlineData(KernelInvocationType.InvokePrompt)]
    [InlineData(KernelInvocationType.InvokePromptStreaming)]
    [InlineData(KernelInvocationType.InvokeFunction)]
    [InlineData(KernelInvocationType.InvokeFunctionStreaming)]
    public async Task ItUsesPromptAsUserMessageAsync(KernelInvocationType invocationType)
    {
        // Arrange
        const string Prompt = "Test prompt as user message";

        var fakeService = new FakeChatAsTextService();
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<IChatCompletionService>((sp) => fakeService);
        Kernel kernel = builder.Build();

        var function = KernelFunctionFactory.CreateFromPrompt(Prompt);

        // Act
        switch (invocationType)
        {
            case KernelInvocationType.InvokePrompt:
                await kernel.InvokePromptAsync(Prompt);
                break;
            case KernelInvocationType.InvokePromptStreaming:
                await foreach (var result in kernel.InvokePromptStreamingAsync(Prompt)) { }
                break;
            case KernelInvocationType.InvokeFunction:
                await kernel.InvokeAsync(function);
                break;
            case KernelInvocationType.InvokeFunctionStreaming:
                await foreach (var result in kernel.InvokeStreamingAsync(function)) { }
                break;
        }

        // Assert
        Assert.NotNull(fakeService.ChatHistory);
        Assert.Single(fakeService.ChatHistory);

        var messageContent = fakeService.ChatHistory[0];

        Assert.Equal(AuthorRole.User, messageContent.Role);
        Assert.Equal("Test prompt as user message", messageContent.Content);
    }

    public enum KernelInvocationType
    {
        InvokePrompt,
        InvokePromptStreaming,
        InvokeFunction,
        InvokeFunctionStreaming
    }

    #region private

    private sealed class FakeChatAsTextService : ITextGenerationService, IChatCompletionService
    {
        public IReadOnlyDictionary<string, object?> Attributes => throw new NotImplementedException();
        public ChatHistory? ChatHistory { get; private set; }

        public Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            this.ChatHistory = chatHistory;

            return Task.FromResult<IReadOnlyList<ChatMessageContent>>(new List<ChatMessageContent> { new(AuthorRole.Assistant, "Something") });
        }

#pragma warning disable IDE0036 // Order modifiers
#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
        public async IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
#pragma warning restore CS1998 // Async method lacks 'await' operators and will run synchronously
#pragma warning restore IDE0036 // Order modifiers
        {
            this.ChatHistory = chatHistory;
            yield return new StreamingChatMessageContent(AuthorRole.Assistant, "Something");
        }

        public IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }

        public Task<IReadOnlyList<TextContent>> GetTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }
    }

    #endregion
}

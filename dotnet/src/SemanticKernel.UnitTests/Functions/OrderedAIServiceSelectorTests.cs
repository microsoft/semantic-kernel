// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextGeneration;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class OrderedAIServiceSelectorTests
{
    [Fact]
    public void ItThrowsAKernelExceptionForNoServices()
    {
        // Arrange
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromPrompt("Hello AI");
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        // Assert
        Assert.Throws<KernelException>(() => serviceSelector.SelectAIService<ITextGenerationService>(kernel, function, []));
        Assert.Throws<KernelException>(() => serviceSelector.SelectAIService<IChatCompletionService>(kernel, function, []));
    }

    [Fact]
    public void ItGetsAIServiceConfigurationForSingleAIService()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton<IAIService>("service1", new AIService());
        Kernel kernel = builder.Build();

        var function = kernel.CreateFunctionFromPrompt("Hello AI");
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        (var aiService, var defaultExecutionSettings) = serviceSelector.SelectAIService<IAIService>(kernel, function, []);

        // Assert
        Assert.NotNull(aiService);
        Assert.Null(defaultExecutionSettings);
    }

    [Fact]
    public void ItGetsChatClientConfigurationForSingleChatClient()
    {
        // Arrange
        var mockChat = new Mock<IChatClient>();
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton<IChatClient>("chat1", mockChat.Object);
        Kernel kernel = builder.Build();

        var function = kernel.CreateFunctionFromPrompt("Hello AI");
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        serviceSelector.TrySelectChatClient<IChatClient>(kernel, function, [], out var chatClient, out var defaultExecutionSettings);
        chatClient?.Dispose();

        // Assert
        Assert.NotNull(chatClient);
        Assert.Null(defaultExecutionSettings);
    }

    [Fact]
    public void ItGetsAIServiceConfigurationForSingleTextGeneration()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service1", new TextGenerationService("model_id_1"));
        Kernel kernel = builder.Build();

        var function = kernel.CreateFunctionFromPrompt("Hello AI");
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        (var aiService, var defaultExecutionSettings) = serviceSelector.SelectAIService<ITextGenerationService>(kernel, function, []);

        // Assert
        Assert.NotNull(aiService);
        Assert.Null(defaultExecutionSettings);
    }

    [Fact]
    public void ItGetsAIServiceConfigurationForTextGenerationByServiceId()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service1", new TextGenerationService("model_id_1"));
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service2", new TextGenerationService("model_id_2"));
        Kernel kernel = builder.Build();

        var promptConfig = new PromptTemplateConfig() { Template = "Hello AI" };
        var executionSettings = new PromptExecutionSettings();
        promptConfig.AddExecutionSettings(executionSettings, "service2");
        var function = kernel.CreateFunctionFromPrompt(promptConfig);
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        (var aiService, var defaultExecutionSettings) = serviceSelector.SelectAIService<ITextGenerationService>(kernel, function, []);

        // Assert
        Assert.Equal(kernel.GetRequiredService<ITextGenerationService>("service2"), aiService);
        var expectedExecutionSettings = executionSettings.Clone();
        expectedExecutionSettings.Freeze();
        Assert.Equivalent(expectedExecutionSettings, defaultExecutionSettings);
    }

    [Fact]
    public void ItGetsChatClientConfigurationForChatClientByServiceId()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        using var chatClient1 = new ChatClient("model_id_1");
        using var chatClient2 = new ChatClient("model_id_2");
        builder.Services.AddKeyedSingleton<IChatClient>("chat1", chatClient1);
        builder.Services.AddKeyedSingleton<IChatClient>("chat2", chatClient2);
        Kernel kernel = builder.Build();

        var promptConfig = new PromptTemplateConfig() { Template = "Hello AI" };
        var executionSettings = new PromptExecutionSettings();
        promptConfig.AddExecutionSettings(executionSettings, "chat2");
        var function = kernel.CreateFunctionFromPrompt(promptConfig);
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        serviceSelector.TrySelectChatClient<IChatClient>(kernel, function, [], out var aiService, out var defaultExecutionSettings);
        aiService?.Dispose();

        // Assert
        Assert.Equal(kernel.GetRequiredService<IChatClient>("chat2"), aiService);
        var expectedExecutionSettings = executionSettings.Clone();
        expectedExecutionSettings.Freeze();
        Assert.Equivalent(expectedExecutionSettings, defaultExecutionSettings);
    }

    [Fact]
    public void ItThrowsAKernelExceptionForNotFoundService()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service1", new TextGenerationService("model_id_1"));
        builder.Services.AddKeyedSingleton<IChatCompletionService>("service2", new ChatCompletionService("model_id_2"));
        Kernel kernel = builder.Build();

        var promptConfig = new PromptTemplateConfig() { Template = "Hello AI" };
        promptConfig.AddExecutionSettings(new PromptExecutionSettings(), "service3");
        var function = kernel.CreateFunctionFromPrompt(promptConfig);
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        // Assert
        Assert.Throws<KernelException>(() => serviceSelector.SelectAIService<ITextGenerationService>(kernel, function, []));
        Assert.Throws<KernelException>(() => serviceSelector.SelectAIService<IChatCompletionService>(kernel, function, []));
    }

    [Fact]
    public void ItGetsDefaultServiceForNotFoundModel()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service1", new TextGenerationService("model_id_1"));
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service2", new TextGenerationService("model_id_2"));
        Kernel kernel = builder.Build();

        var promptConfig = new PromptTemplateConfig() { Template = "Hello AI" };
        promptConfig.AddExecutionSettings(new PromptExecutionSettings { ModelId = "notfound" });
        var function = kernel.CreateFunctionFromPrompt(promptConfig);
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        // Assert
        (var aiService, var defaultExecutionSettings) = serviceSelector.SelectAIService<ITextGenerationService>(kernel, function, []);
        Assert.Equal(kernel.GetRequiredService<ITextGenerationService>("service2"), aiService);
    }

    [Fact]
    public void ItGetsDefaultChatClientForNotFoundModel()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        using var chatClient1 = new ChatClient("model_id_1");
        using var chatClient2 = new ChatClient("model_id_2");
        builder.Services.AddKeyedSingleton<IChatClient>("chat1", chatClient1);
        builder.Services.AddKeyedSingleton<IChatClient>("chat2", chatClient2);
        Kernel kernel = builder.Build();

        var promptConfig = new PromptTemplateConfig() { Template = "Hello AI" };
        promptConfig.AddExecutionSettings(new PromptExecutionSettings { ModelId = "notfound" });
        var function = kernel.CreateFunctionFromPrompt(promptConfig);
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        // Assert
        serviceSelector.TrySelectChatClient<IChatClient>(kernel, function, [], out var aiService, out var defaultExecutionSettings);
        aiService?.Dispose();

        Assert.Equal(kernel.GetRequiredService<IChatClient>("chat2"), aiService);
    }

    [Fact]
    public void ItUsesDefaultServiceForNoExecutionSettings()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service1", new TextGenerationService("model_id_1"));
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service2", new TextGenerationService("model_id_2"));
        Kernel kernel = builder.Build();
        var function = kernel.CreateFunctionFromPrompt("Hello AI");
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        (var aiService, var defaultExecutionSettings) = serviceSelector.SelectAIService<ITextGenerationService>(kernel, function, []);

        // Assert
        Assert.Equal(kernel.GetRequiredService<ITextGenerationService>("service2"), aiService);
        Assert.Null(defaultExecutionSettings);
    }

    [Fact]
    public void ItUsesDefaultChatClientForNoExecutionSettings()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        using var chatClient1 = new ChatClient("model_id_1");
        using var chatClient2 = new ChatClient("model_id_2");
        builder.Services.AddKeyedSingleton<IChatClient>("chat1", chatClient1);
        builder.Services.AddKeyedSingleton<IChatClient>("chat2", chatClient2);
        Kernel kernel = builder.Build();
        var function = kernel.CreateFunctionFromPrompt("Hello AI");
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        serviceSelector.TrySelectChatClient<IChatClient>(kernel, function, [], out var aiService, out var defaultExecutionSettings);
        aiService?.Dispose();

        // Assert
        Assert.Equal(kernel.GetRequiredService<IChatClient>("chat2"), aiService);
        Assert.Null(defaultExecutionSettings);
    }

    [Fact]
    public void ItUsesDefaultServiceAndSettingsForDefaultExecutionSettings()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service1", new TextGenerationService("model_id_1"));
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service2", new TextGenerationService("model_id_2"));
        Kernel kernel = builder.Build();

        var executionSettings = new PromptExecutionSettings();
        var function = kernel.CreateFunctionFromPrompt("Hello AI", executionSettings);
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        (var aiService, var defaultExecutionSettings) = serviceSelector.SelectAIService<ITextGenerationService>(kernel, function, []);

        // Assert
        Assert.Equal(kernel.GetRequiredService<ITextGenerationService>("service2"), aiService);
        var expectedExecutionSettings = executionSettings.Clone();
        expectedExecutionSettings.Freeze();
        Assert.Equivalent(expectedExecutionSettings, defaultExecutionSettings);
    }

    [Fact]
    public void ItUsesDefaultChatClientAndSettingsForDefaultExecutionSettings()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        using var chatClient1 = new ChatClient("model_id_1");
        using var chatClient2 = new ChatClient("model_id_2");
        builder.Services.AddKeyedSingleton<IChatClient>("chat1", chatClient1);
        builder.Services.AddKeyedSingleton<IChatClient>("chat2", chatClient2);
        Kernel kernel = builder.Build();

        var executionSettings = new PromptExecutionSettings();
        var function = kernel.CreateFunctionFromPrompt("Hello AI", executionSettings);
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        serviceSelector.TrySelectChatClient<IChatClient>(kernel, function, [], out var aiService, out var defaultExecutionSettings);
        aiService?.Dispose();

        // Assert
        Assert.Equal(kernel.GetRequiredService<IChatClient>("chat2"), aiService);
        var expectedExecutionSettings = executionSettings.Clone();
        expectedExecutionSettings.Freeze();
        Assert.Equivalent(expectedExecutionSettings, defaultExecutionSettings);
    }

    [Fact]
    public void ItUsesDefaultServiceAndSettingsForDefaultId()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service1", new TextGenerationService("model_id_1"));
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service2", new TextGenerationService("model_id_2"));
        Kernel kernel = builder.Build();

        var executionSettings = new PromptExecutionSettings();
        var function = kernel.CreateFunctionFromPrompt("Hello AI", executionSettings);
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        (var aiService, var defaultExecutionSettings) = serviceSelector.SelectAIService<ITextGenerationService>(kernel, function, []);

        // Assert
        Assert.Equal(kernel.GetRequiredService<ITextGenerationService>("service2"), aiService);
        var expectedExecutionSettings = executionSettings.Clone();
        expectedExecutionSettings.Freeze();
        Assert.Equivalent(expectedExecutionSettings, defaultExecutionSettings);
    }

    [Fact]
    public void ItUsesDefaultChatClientAndSettingsForDefaultId()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        using var chatClient1 = new ChatClient("model_id_1");
        using var chatClient2 = new ChatClient("model_id_2");
        builder.Services.AddKeyedSingleton<IChatClient>("chat1", chatClient1);
        builder.Services.AddKeyedSingleton<IChatClient>("chat2", chatClient2);
        Kernel kernel = builder.Build();

        var executionSettings = new PromptExecutionSettings();
        var function = kernel.CreateFunctionFromPrompt("Hello AI", executionSettings);
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        serviceSelector.TrySelectChatClient<IChatClient>(kernel, function, [], out var aiService, out var defaultExecutionSettings);
        aiService?.Dispose();

        // Assert
        Assert.Equal(kernel.GetRequiredService<IChatClient>("chat2"), aiService);
        var expectedExecutionSettings = executionSettings.Clone();
        expectedExecutionSettings.Freeze();
        Assert.Equivalent(expectedExecutionSettings, defaultExecutionSettings);
    }

    [Theory]
    [InlineData(new string[] { "modelid_1" }, "modelid_1")]
    [InlineData(new string[] { "modelid_2" }, "modelid_2")]
    [InlineData(new string[] { "modelid_3" }, "modelid_3")]
    [InlineData(new string[] { "modelid_4", "modelid_1" }, "modelid_1")]
    [InlineData(new string[] { "modelid_4", "" }, "modelid_3")]
    public void ItGetsAIServiceConfigurationByOrder(string[] serviceIds, string expectedModelId)
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("modelid_1", new TextGenerationService("modelid_1"));
        builder.Services.AddKeyedSingleton<ITextGenerationService>("modelid_2", new TextGenerationService("modelid_2"));
        builder.Services.AddKeyedSingleton<ITextGenerationService>("modelid_3", new TextGenerationService("modelid_3"));
        Kernel kernel = builder.Build();

        var executionSettings = new Dictionary<string, PromptExecutionSettings>();
        foreach (var serviceId in serviceIds)
        {
            executionSettings.Add(serviceId, new PromptExecutionSettings() { ModelId = serviceId });
        }
        var function = kernel.CreateFunctionFromPrompt(promptConfig: new PromptTemplateConfig() { Template = "Hello AI", ExecutionSettings = executionSettings });
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        (var aiService, var defaultExecutionSettings) = serviceSelector.SelectAIService<ITextGenerationService>(kernel, function, []);

        // Assert
        Assert.Equal(kernel.GetRequiredService<ITextGenerationService>(expectedModelId), aiService);
        if (!string.IsNullOrEmpty(defaultExecutionSettings!.ModelId))
        {
            Assert.Equal(expectedModelId, defaultExecutionSettings!.ModelId);
        }
    }

    [Theory]
    [InlineData(new string[] { "modelid_1" }, "modelid_1")]
    [InlineData(new string[] { "modelid_2" }, "modelid_2")]
    [InlineData(new string[] { "modelid_3" }, "modelid_3")]
    [InlineData(new string[] { "modelid_4", "modelid_1" }, "modelid_1")]
    [InlineData(new string[] { "modelid_4", "" }, "modelid_3")]
    public void ItGetsChatClientConfigurationByOrder(string[] serviceIds, string expectedModelId)
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        using var chatClient1 = new ChatClient("modelid_1");
        using var chatClient2 = new ChatClient("modelid_2");
        using var chatClient3 = new ChatClient("modelid_3");
        builder.Services.AddKeyedSingleton<IChatClient>("modelid_1", chatClient1);
        builder.Services.AddKeyedSingleton<IChatClient>("modelid_2", chatClient2);
        builder.Services.AddKeyedSingleton<IChatClient>("modelid_3", chatClient3);
        Kernel kernel = builder.Build();

        var executionSettings = new Dictionary<string, PromptExecutionSettings>();
        foreach (var serviceId in serviceIds)
        {
            executionSettings.Add(serviceId, new PromptExecutionSettings() { ModelId = serviceId });
        }
        var function = kernel.CreateFunctionFromPrompt(promptConfig: new PromptTemplateConfig() { Template = "Hello AI", ExecutionSettings = executionSettings });
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        serviceSelector.TrySelectChatClient<IChatClient>(kernel, function, [], out var aiService, out var defaultExecutionSettings);
        aiService?.Dispose();

        // Assert
        Assert.Equal(kernel.GetRequiredService<IChatClient>(expectedModelId), aiService);
        if (!string.IsNullOrEmpty(defaultExecutionSettings!.ModelId))
        {
            Assert.Equal(expectedModelId, defaultExecutionSettings!.ModelId);
        }
    }

    [Fact]
    public void ItGetsAIServiceConfigurationForTextGenerationByModelId()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton<ITextGenerationService>(null, new TextGenerationService("model1"));
        builder.Services.AddKeyedSingleton<ITextGenerationService>(null, new TextGenerationService("model2"));
        Kernel kernel = builder.Build();

        var arguments = new KernelArguments();
        var executionSettings = new PromptExecutionSettings() { ModelId = "model2" };
        var function = kernel.CreateFunctionFromPrompt("Hello AI", executionSettings: executionSettings);
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        (var aiService, var defaultExecutionSettings) = serviceSelector.SelectAIService<ITextGenerationService>(kernel, function, arguments);

        // Assert
        Assert.NotNull(aiService);
        Assert.Equal("model2", aiService.GetModelId());
        var expectedExecutionSettings = executionSettings.Clone();
        expectedExecutionSettings.Freeze();
        Assert.Equivalent(expectedExecutionSettings, defaultExecutionSettings);
    }

    [Fact]
    public void ItGetsChatClientConfigurationForChatClientByModelId()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        using var chatClient1 = new ChatClient("model1");
        using var chatClient2 = new ChatClient("model2");
        builder.Services.AddKeyedSingleton<IChatClient>(null, chatClient1);
        builder.Services.AddKeyedSingleton<IChatClient>(null, chatClient2);
        Kernel kernel = builder.Build();

        var arguments = new KernelArguments();
        var executionSettings = new PromptExecutionSettings() { ModelId = "model2" };
        var function = kernel.CreateFunctionFromPrompt("Hello AI", executionSettings: executionSettings);
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        serviceSelector.TrySelectChatClient<IChatClient>(kernel, function, arguments, out var aiService, out var defaultExecutionSettings);
        aiService?.Dispose();

        // Assert
        Assert.NotNull(aiService);
        Assert.Equal("model2", aiService.GetModelId());
        var expectedExecutionSettings = executionSettings.Clone();
        expectedExecutionSettings.Freeze();
        Assert.Equivalent(expectedExecutionSettings, defaultExecutionSettings);
    }

    #region private
    private sealed class AIService : IAIService
    {
        public IReadOnlyDictionary<string, object?> Attributes => new Dictionary<string, object?>();
    }

    private sealed class TextGenerationService : ITextGenerationService
    {
        public IReadOnlyDictionary<string, object?> Attributes => this._attributes;

        private readonly Dictionary<string, object?> _attributes = [];

        public TextGenerationService(string modelId)
        {
            this._attributes.Add("ModelId", modelId);
        }

        public Task<IReadOnlyList<Microsoft.SemanticKernel.TextContent>> GetTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }

        public IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }
    }

    private sealed class ChatCompletionService : IChatCompletionService
    {
        public IReadOnlyDictionary<string, object?> Attributes => this._attributes;

        private readonly Dictionary<string, object?> _attributes = [];

        public ChatCompletionService(string modelId)
        {
            this._attributes.Add("ModelId", modelId);
        }

        public Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }

        public IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }
    }

    private sealed class ChatClient : IChatClient
    {
        public ChatClientMetadata Metadata { get; }

        public ChatClient(string modelId)
        {
            this.Metadata = new ChatClientMetadata(defaultModelId: modelId);
        }

        public Task<IReadOnlyList<Microsoft.SemanticKernel.TextContent>> GetTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }

        public IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }

        public Task<ChatResponse> GetResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }

        public IAsyncEnumerable<ChatResponseUpdate> GetStreamingResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }

        /// <inheritdoc />
        public object? GetService(Type serviceType, object? serviceKey = null)
        {
            Verify.NotNull(serviceType);

            return
                serviceKey is not null ? null :
                serviceType.IsInstanceOfType(this) ? this :
                serviceType.IsInstanceOfType(this.Metadata) ? this.Metadata :
                null;
        }

        public void Dispose()
        {
        }
    }
    #endregion
}

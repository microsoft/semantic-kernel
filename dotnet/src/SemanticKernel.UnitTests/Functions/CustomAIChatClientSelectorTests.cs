// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Services;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class CustomAIChatClientSelectorTests
{
    [Fact]
    public void ItGetsChatClientUsingModelIdAttribute()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        using var chatClient = new ChatClientTest();
        builder.Services.AddKeyedSingleton<IChatClient>("service1", chatClient);
        Kernel kernel = builder.Build();

        var function = kernel.CreateFunctionFromPrompt("Hello AI");
        IChatClientSelector chatClientSelector = new CustomChatClientSelector();

        // Act
        chatClientSelector.TrySelectChatClient<IChatClient>(kernel, function, [], out var selectedChatClient, out var defaultExecutionSettings);

        // Assert
        Assert.NotNull(selectedChatClient);
        Assert.Equal("Value1", selectedChatClient.GetModelId());
        Assert.Null(defaultExecutionSettings);
        selectedChatClient.Dispose();
    }

    private sealed class CustomChatClientSelector : IChatClientSelector
    {
#pragma warning disable CS8769 // Nullability of reference types in value doesn't match target type. Cannot use [NotNullWhen] because of access to internals from abstractions.
        public bool TrySelectChatClient<T>(Kernel kernel, KernelFunction function, KernelArguments arguments, [NotNullWhen(true)] out T? service, out PromptExecutionSettings? serviceSettings)
            where T : class, IChatClient
        {
            var keyedService = (kernel.Services as IKeyedServiceProvider)?.GetKeyedService<T>("service1");
            if (keyedService is null || keyedService.GetModelId() is null)
            {
                service = null;
                serviceSettings = null;
                return false;
            }

            service = string.Equals(keyedService.GetModelId(), "Value1", StringComparison.OrdinalIgnoreCase) ? keyedService as T : null;
            serviceSettings = null;

            if (service is null)
            {
                throw new InvalidOperationException("Service not found");
            }

            return true;
        }
    }

    private sealed class ChatClientTest : IChatClient
    {
        private readonly ChatClientMetadata _metadata;

        public ChatClientTest()
        {
            this._metadata = new ChatClientMetadata(defaultModelId: "Value1");
        }

        public void Dispose()
        {
        }

        public Task<ChatResponse> GetResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }

        public object? GetService(Type serviceType, object? serviceKey = null)
        {
            return this._metadata;
        }

        public IAsyncEnumerable<ChatResponseUpdate> GetStreamingResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }
    }
}

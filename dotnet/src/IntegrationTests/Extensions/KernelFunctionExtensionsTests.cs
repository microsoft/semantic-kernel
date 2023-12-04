// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextGeneration;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using SemanticKernel.IntegrationTests.Fakes;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests;

public sealed class KernelFunctionExtensionsTests : IDisposable
{
    public KernelFunctionExtensionsTests(ITestOutputHelper output)
    {
        this._logger = new RedirectOutput(output);
    }

    [Fact]
    public async Task ItSupportsFunctionCallsAsync()
    {
        Kernel target = new KernelBuilder()
            .WithLoggerFactory(this._logger)
            .WithServices(c => c.AddSingleton<ITextGenerationService>(new RedirectTextGenerationService()))
            .WithPlugins(plugins => plugins.AddPluginFromObject<EmailPluginFake>())
            .Build();

        var prompt = $"Hey {{{{{nameof(EmailPluginFake)}.GetEmailAddress}}}}";

        // Act
        FunctionResult actual = await target.InvokePromptAsync(prompt, new(new OpenAIPromptExecutionSettings() { MaxTokens = 150 }));

        // Assert
        Assert.Equal("Hey johndoe1234@example.com", actual.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsFunctionCallsWithInputAsync()
    {
        Kernel target = new KernelBuilder()
            .WithLoggerFactory(this._logger)
            .WithServices(c => c.AddSingleton<ITextGenerationService>(new RedirectTextGenerationService()))
            .WithPlugins(plugins => plugins.AddPluginFromObject<EmailPluginFake>())
            .Build();

        var prompt = $"Hey {{{{{nameof(EmailPluginFake)}.GetEmailAddress \"a person\"}}}}";

        // Act
        FunctionResult actual = await target.InvokePromptAsync(prompt, new(new OpenAIPromptExecutionSettings() { MaxTokens = 150 }));

        // Assert
        Assert.Equal("Hey a person@example.com", actual.GetValue<string>());
    }

    private readonly RedirectOutput _logger;

    public void Dispose()
    {
        this._logger.Dispose();
    }

    private sealed class RedirectTextGenerationService : ITextGenerationService
    {
        public string? ModelId => null;

        public IReadOnlyDictionary<string, object?> Attributes => new Dictionary<string, object?>();

        Task<IReadOnlyList<ITextResult>> ITextGenerationService.GetCompletionsAsync(string prompt, PromptExecutionSettings? executionSettings, Kernel? kernel, CancellationToken cancellationToken)
        {
            return Task.FromResult<IReadOnlyList<ITextResult>>(new List<ITextResult> { new RedirectTextResult(prompt) });
        }

        public IAsyncEnumerable<T> GetStreamingContentAsync<T>(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }
    }

    internal sealed class RedirectTextResult : ITextResult
    {
        private readonly string _completion;

        public RedirectTextResult(string completion)
        {
            this._completion = completion;
        }

        public ModelResult ModelResult => new(this._completion);

        public Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
        {
            return Task.FromResult(this._completion);
        }
    }
}

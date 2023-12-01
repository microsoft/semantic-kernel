// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Orchestration;
using SemanticKernel.IntegrationTests.Fakes;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Extensions;

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
            .ConfigureServices(c => c.AddSingleton<ITextCompletion>(new RedirectTextCompletion()))
            .ConfigurePlugins(plugins => plugins.AddPluginFromObject<EmailPluginFake>())
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
            .ConfigureServices(c => c.AddSingleton<ITextCompletion>(new RedirectTextCompletion()))
            .ConfigurePlugins(plugins => plugins.AddPluginFromObject<EmailPluginFake>())
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

    private sealed class RedirectTextCompletion : ITextCompletion
    {
        public string? ModelId => null;

        public IReadOnlyDictionary<string, object?> Attributes => new Dictionary<string, object?>();

        Task<IReadOnlyList<ITextResult>> ITextCompletion.GetCompletionsAsync(string text, PromptExecutionSettings? executionSettings, Kernel? kernel, CancellationToken cancellationToken)
        {
            return Task.FromResult<IReadOnlyList<ITextResult>>(new List<ITextResult> { new RedirectTextCompletionResult(text) });
        }

        public IAsyncEnumerable<T> GetStreamingContentAsync<T>(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }
    }

    internal sealed class RedirectTextCompletionResult : ITextResult
    {
        private readonly string _completion;

        public RedirectTextCompletionResult(string completion)
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

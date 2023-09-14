// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.TemplateEngine.Prompt;
using SemanticKernel.IntegrationTests.Fakes;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.SkillDefinition;

public sealed class InlineFunctionsDefinitionExtensionsTests : IDisposable
{
    public InlineFunctionsDefinitionExtensionsTests(ITestOutputHelper output)
    {
        this._logger = new RedirectOutput(output);
        this._target = new PromptTemplateEngine();
    }

    [Fact]
    public async Task ItSupportsFunctionCalls()
    {
        var builder = Kernel.Builder
                .WithAIService<ITextCompletion>(null, new RedirectTextCompletion(), true)
                .WithLoggerFactory(this._logger);
        IKernel target = builder.Build();

        var emailSkill = target.ImportSkill(new EmailSkillFake());

        var prompt = "Hey {{_GLOBAL_FUNCTIONS_.GetEmailAddress}}";

        // Act
        SKContext actual = await target.InvokeSemanticFunctionAsync(prompt, requestSettings: new { MaxTokens = 150 });

        // Assert
        Assert.Equal("Hey johndoe1234@example.com", actual.Result);
    }

    [Fact]
    public async Task ItSupportsFunctionCallsWithInput()
    {
        var builder = Kernel.Builder
                .WithAIService<ITextCompletion>(null, new RedirectTextCompletion(), true)
                .WithLoggerFactory(this._logger);
        IKernel target = builder.Build();

        var emailSkill = target.ImportSkill(new EmailSkillFake());

        var prompt = "Hey {{_GLOBAL_FUNCTIONS_.GetEmailAddress \"a person\"}}";

        // Act
        SKContext actual = await target.InvokeSemanticFunctionAsync(prompt, requestSettings: new { MaxTokens = 150 });

        // Assert
        Assert.Equal("Hey a person@example.com", actual.Result);
    }

    private readonly RedirectOutput _logger;
    private readonly PromptTemplateEngine _target;

    public void Dispose()
    {
        this._logger.Dispose();
    }

    private sealed class RedirectTextCompletion : ITextCompletion
    {
        Task<IReadOnlyList<ITextResult>> ITextCompletion.GetCompletionsAsync(string text, object? requestSettings, CancellationToken cancellationToken)
        {
            return Task.FromResult<IReadOnlyList<ITextResult>>(new List<ITextResult> { new RedirectTextCompletionResult(text) });
        }

        IAsyncEnumerable<ITextStreamingResult> ITextCompletion.GetStreamingCompletionsAsync(string text, object? requestSettings, CancellationToken cancellationToken)
        {
            throw new NotImplementedException(); // TODO
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

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Examples;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Xunit;
using Xunit.Abstractions;

namespace GettingStarted;

public sealed class Step6_Responsible_AI : BaseTest
{
    /// <summary>
    /// Show how to use prompt filters to ensure that prompts are rendered in a responsible manner.
    /// </summary>
    [Fact]
    public async Task RunAsync()
    {
        // Create a kernel with OpenAI chat completion
        var builder = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey);

        builder.Services.AddSingleton<ITestOutputHelper>(this.Output);

        // Add prompt filter to the kernel
        builder.Services.AddSingleton<IPromptFilter, PromptFilter>();

        var kernel = builder.Build();

        KernelArguments arguments = new() { { "card_number", "4444 3333 2222 1111" } };

        var result = await kernel.InvokePromptAsync("Tell me some useful information about this credit card number {{$card_number}}?", arguments);

        WriteLine(result);

        // Output: Sorry, but I can't assist with that.
    }

    public Step6_Responsible_AI(ITestOutputHelper output) : base(output)
    {
    }

    private sealed class PromptFilter : IPromptFilter
    {
        private readonly ITestOutputHelper _output;

        public PromptFilter(ITestOutputHelper output)
        {
            this._output = output;
        }

        /// <summary>
        /// Method which is called asynchronously before prompt rendering.
        /// </summary>
        /// <param name="context">Instance of <see cref="PromptRenderingContext"/> with prompt rendering details.</param>
        /// <param name="next">Delegate to the next filter in pipeline or prompt rendering operation itself. If it's not invoked, next filter or prompt rendering won't be invoked.</param>
        public async Task OnPromptRenderingAsync(PromptRenderingContext context, Func<PromptRenderingContext, Task> next)
        {
            if (context.Arguments.ContainsName("card_number"))
            {
                context.Arguments["card_number"] = "**** **** **** ****";
            }

            await next(context);

            context.RenderedPrompt += " NO SEXISM, RACISM OR OTHER BIAS/BIGOTRY";

            this._output.WriteLine(context.RenderedPrompt);
        }
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.TextGeneration;
using Moq;

namespace SemanticKernel.UnitTests.Filters;

public abstract class FilterBaseTest
{
    protected Kernel GetKernelWithFilters(
        Func<FunctionInvocationContext, Func<FunctionInvocationContext, Task>, Task>? onFunctionInvocation = null,
        Func<PromptRenderContext, Func<PromptRenderContext, Task>, Task>? onPromptRender = null,
        ITextGenerationService? textGenerationService = null)
    {
        var builder = Kernel.CreateBuilder();

        // Add function filter before kernel construction
        if (onFunctionInvocation is not null)
        {
            var functionFilter = new FakeFunctionFilter(onFunctionInvocation);
            builder.Services.AddSingleton<IFunctionInvocationFilter>(functionFilter);
        }

        if (textGenerationService is not null)
        {
            builder.Services.AddSingleton<ITextGenerationService>(textGenerationService);
        }

        var kernel = builder.Build();

        if (onPromptRender is not null)
        {
            // Add prompt filter after kernel construction
            kernel.PromptRenderFilters.Add(new FakePromptFilter(onPromptRender));
        }

        return kernel;
    }

    protected Mock<ITextGenerationService> GetMockTextGeneration(string? textResult = null, IReadOnlyDictionary<string, object?>? metadata = null)
    {
        var mockTextGeneration = new Mock<ITextGenerationService>();
        mockTextGeneration
            .Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync([new(textResult ?? "result text", metadata: metadata)]);

        mockTextGeneration
            .Setup(s => s.GetStreamingTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()))
            .Returns(new List<StreamingTextContent>() { new(textResult ?? "result chunk", metadata: metadata) }.ToAsyncEnumerable());

        return mockTextGeneration;
    }

    protected sealed class FakeFunctionFilter(
        Func<FunctionInvocationContext, Func<FunctionInvocationContext, Task>, Task>? onFunctionInvocation) : IFunctionInvocationFilter
    {
        public Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next) =>
            onFunctionInvocation?.Invoke(context, next) ?? Task.CompletedTask;
    }

    protected sealed class FakePromptFilter(
        Func<PromptRenderContext, Func<PromptRenderContext, Task>, Task>? onPromptRender) : IPromptRenderFilter
    {
        public Task OnPromptRenderAsync(PromptRenderContext context, Func<PromptRenderContext, Task> next) =>
            onPromptRender?.Invoke(context, next) ?? Task.CompletedTask;
    }

    protected sealed class FakeAutoFunctionFilter(
        Func<AutoFunctionInvocationContext, Func<AutoFunctionInvocationContext, Task>, Task>? onAutoFunctionInvocation) : IAutoFunctionInvocationFilter
    {
        public Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next) =>
            onAutoFunctionInvocation?.Invoke(context, next) ?? Task.CompletedTask;
    }
}

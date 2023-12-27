// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.TextGeneration;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Filters;

public class KernelFilterTests
{
    [Fact]
    public async Task PreInvocationFunctionFilterIsTriggeredAsync()
    {
        // Arrange
        var functionInvocations = 0;
        var filterInvocations = 0;
        var function = KernelFunctionFactory.CreateFromMethod(() => functionInvocations++);

        var kernel = this.GetKernelWithFilter(onFunctionInvoking: (context) =>
        {
            filterInvocations++;
        });

        // Act
        var result = await kernel.InvokeAsync(function);

        // Assert
        Assert.Equal(1, functionInvocations);
        Assert.Equal(1, filterInvocations);
    }

    [Fact]
    public async Task PreInvocationFunctionFilterChangesArgumentAsync()
    {
        // Arrange
        const string OriginalInput = "OriginalInput";
        const string NewInput = "NewInput";

        var kernel = this.GetKernelWithFilter(onFunctionInvoking: (context) =>
        {
            context.Arguments["originalINput"] = NewInput;
        });

        var function = KernelFunctionFactory.CreateFromMethod((string originalInput) => originalInput);

        // Act
        var result = await kernel.InvokeAsync(function, new() { ["originalInput"] = OriginalInput });

        // Assert
        Assert.Equal(NewInput, result.GetValue<string>());
    }

    [Fact]
    public async Task PreInvocationFunctionFilterCancellationWorksCorrectlyAsync()
    {
        // Arrange
        var functionInvocations = 0;
        var filterPreInvocations = 0;
        var filterPostInvocations = 0;

        var function = KernelFunctionFactory.CreateFromMethod(() => functionInvocations++);

        var kernel = this.GetKernelWithFilter(
            onFunctionInvoking: (context) =>
            {
                filterPreInvocations++;
                context.Cancel = true;
            },
            onFunctionInvoked: (context) =>
            {
                filterPostInvocations++;
            });

        // Act
        var exception = await Assert.ThrowsAsync<KernelFunctionCanceledException>(() => kernel.InvokeAsync(function));

        // Assert
        Assert.Equal(1, filterPreInvocations);
        Assert.Equal(0, functionInvocations);
        Assert.Equal(0, filterPostInvocations);
        Assert.Same(function, exception.Function);
        Assert.Null(exception.FunctionResult);
    }

    [Fact]
    public async Task PostInvocationFunctionFilterIsTriggeredAsync()
    {
        // Arrange
        var functionInvocations = 0;
        var filterInvocations = 0;
        var function = KernelFunctionFactory.CreateFromMethod(() => functionInvocations++);

        var kernel = this.GetKernelWithFilter(onFunctionInvoked: (context) =>
        {
            filterInvocations++;
        });

        // Act
        var result = await kernel.InvokeAsync(function);

        // Assert
        Assert.Equal(1, functionInvocations);
        Assert.Equal(1, filterInvocations);
    }

    [Fact]
    public async Task PostInvocationFunctionFilterReturnsModifiedResultAsync()
    {
        // Arrange
        const int OriginalResult = 42;
        const int NewResult = 84;

        var function = KernelFunctionFactory.CreateFromMethod(() => OriginalResult);

        var kernel = this.GetKernelWithFilter(onFunctionInvoked: (context) =>
        {
            context.SetResultValue(NewResult);
        });

        // Act
        var result = await kernel.InvokeAsync(function);

        // Assert
        Assert.Equal(NewResult, result.GetValue<int>());
    }

    [Fact]
    public async Task PostInvocationFunctionFilterCancellationWorksCorrectlyAsync()
    {
        // Arrange
        const int Result = 42;

        var function = KernelFunctionFactory.CreateFromMethod(() => Result);
        var args = new KernelArguments() { { "a", "b" } };

        var kernel = this.GetKernelWithFilter(onFunctionInvoked: (context) =>
        {
            context.Cancel = true;
        });

        // Act
        var exception = await Assert.ThrowsAsync<KernelFunctionCanceledException>(() => kernel.InvokeAsync(function, args));

        // Assert
        Assert.Same(kernel, exception.Kernel);
        Assert.Same(function, exception.Function);
        Assert.Same(args, exception.Arguments);
        Assert.NotNull(exception.FunctionResult);
        Assert.Equal(Result, exception.FunctionResult.GetValue<int>());
    }

    [Fact]
    public async Task PostInvocationFunctionFilterCancellationWithModifiedResultAsync()
    {
        // Arrange
        const int OriginalResult = 42;
        const int NewResult = 84;

        var function = KernelFunctionFactory.CreateFromMethod(() => OriginalResult);
        var args = new KernelArguments() { { "a", "b" } };

        var kernel = this.GetKernelWithFilter(onFunctionInvoked: (context) =>
        {
            context.SetResultValue(NewResult);
            context.Cancel = true;
        });

        // Act
        var exception = await Assert.ThrowsAsync<KernelFunctionCanceledException>(() => kernel.InvokeAsync(function, args));

        // Assert
        Assert.Same(kernel, exception.Kernel);
        Assert.Same(function, exception.Function);
        Assert.Same(args, exception.Arguments);
        Assert.NotNull(exception.FunctionResult);
        Assert.Equal(NewResult, exception.FunctionResult.GetValue<int>());
    }

    [Fact]
    public async Task PostInvocationFunctionFilterWithPromptsWorksCorrectlyAsync()
    {
        // Arrange
        var invoked = 0;
        var mockTextGeneration = new Mock<ITextGenerationService>();
        mockTextGeneration
            .Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<TextContent> { new TextContent("result text") });

        var filter = new TestFunctionFilter(onFunctionInvoked: (context) =>
        {
            invoked++;
        });

        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton<ITextGenerationService>(mockTextGeneration.Object);
        builder.Services.AddSingleton<IFunctionFilter>(filter);

        var kernel = builder.Build();

        var function = KernelFunctionFactory.CreateFromPrompt("Write a simple phrase about UnitTests");

        // Act
        var result = await kernel.InvokeAsync(function);

        // Assert
        Assert.Equal(1, invoked);
        mockTextGeneration.Verify(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Exactly(1));
    }

    private Kernel GetKernelWithFilter(
        Action<FunctionInvokingContext>? onFunctionInvoking = null,
        Action<FunctionInvokedContext>? onFunctionInvoked = null)
    {
        var builder = Kernel.CreateBuilder();
        var filter = new TestFunctionFilter(onFunctionInvoking, onFunctionInvoked);

        builder.Services.AddSingleton<IFunctionFilter>(filter);

        return builder.Build();
    }

    private class TestFunctionFilter : IFunctionFilter
    {
        private readonly Action<FunctionInvokingContext>? _onFunctionInvoking;
        private readonly Action<FunctionInvokedContext>? _onFunctionInvoked;

        public TestFunctionFilter(
            Action<FunctionInvokingContext>? onFunctionInvoking = null,
            Action<FunctionInvokedContext>? onFunctionInvoked = null)
        {
            this._onFunctionInvoking = onFunctionInvoking;
            this._onFunctionInvoked = onFunctionInvoked;
        }

        public void OnFunctionInvoked(FunctionInvokedContext context) =>
            this._onFunctionInvoked?.Invoke(context);

        public void OnFunctionInvoking(FunctionInvokingContext context) =>
            this._onFunctionInvoking?.Invoke(context);
    }
}

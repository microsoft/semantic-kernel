// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.TextGeneration;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Filters;

public class PromptRenderFilterTests : FilterBaseTest
{
    [Fact]
    public async Task PromptFiltersAreNotTriggeredForMethodsAsync()
    {
        // Arrange
        var functionInvocations = 0;
        var filterInvocations = 0;

        var function = KernelFunctionFactory.CreateFromMethod(() => functionInvocations++);

        var kernel = this.GetKernelWithFilters(onPromptRender: async (context, next) =>
        {
            filterInvocations++;
            await next(context);
            filterInvocations++;
        });

        // Act
        var result = await kernel.InvokeAsync(function);

        // Assert
        Assert.Equal(1, functionInvocations);
        Assert.Equal(0, filterInvocations);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task PromptFiltersAreTriggeredForPromptsAsync(bool isStreaming)
    {
        // Arrange
        Kernel? contextKernel = null;

        var filterInvocations = 0;
        var mockTextGeneration = this.GetMockTextGeneration();

        var arguments = new KernelArguments() { ["key1"] = "value1" };
        var function = KernelFunctionFactory.CreateFromPrompt("Prompt");

        var kernel = this.GetKernelWithFilters(textGenerationService: mockTextGeneration.Object,
            onPromptRender: async (context, next) =>
            {
                Assert.Same(arguments, context.Arguments);
                Assert.Same(function, context.Function);

                contextKernel = context.Kernel;

                filterInvocations++;
                await next(context);
                filterInvocations++;

                Assert.Equal("Prompt", context.RenderedPrompt);
            });

        // Act
        if (isStreaming)
        {
            await foreach (var item in kernel.InvokeStreamingAsync(function, arguments))
            { }
        }
        else
        {
            await kernel.InvokeAsync(function, arguments);
        }

        // Assert
        Assert.Equal(2, filterInvocations);
        Assert.Same(contextKernel, kernel);
    }

    [Fact]
    public async Task DifferentWaysOfAddingPromptFiltersWorkCorrectlyAsync()
    {
        // Arrange
        var mockTextGeneration = this.GetMockTextGeneration();
        var function = KernelFunctionFactory.CreateFromPrompt("Prompt");
        var executionOrder = new List<string>();

        var promptFilter1 = new FakePromptFilter(onPromptRender: async (context, next) =>
        {
            executionOrder.Add("PromptFilter1-Rendering");
            await next(context);
        });

        var promptFilter2 = new FakePromptFilter(onPromptRender: async (context, next) =>
        {
            executionOrder.Add("PromptFilter2-Rendering");
            await next(context);
        });

        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<ITextGenerationService>(mockTextGeneration.Object);

        // Act
        // Case #1 - Add filter to services
        builder.Services.AddSingleton<IPromptRenderFilter>(promptFilter1);

        var kernel = builder.Build();

        // Case #2 - Add filter to kernel
        kernel.PromptRenderFilters.Add(promptFilter2);

        var result = await kernel.InvokeAsync(function);

        // Assert
        Assert.Equal("PromptFilter1-Rendering", executionOrder[0]);
        Assert.Equal("PromptFilter2-Rendering", executionOrder[1]);
    }

    [Fact]
    public async Task MultipleFiltersAreExecutedInOrderAsync()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();
        var mockTextGeneration = this.GetMockTextGeneration();
        var function = KernelFunctionFactory.CreateFromPrompt("Prompt");

        var executionOrder = new List<string>();

        var promptFilter1 = new FakePromptFilter(onPromptRender: async (context, next) =>
        {
            executionOrder.Add("PromptFilter1-Rendering");
            await next(context);
            executionOrder.Add("PromptFilter1-Rendered");
        });

        var promptFilter2 = new FakePromptFilter(onPromptRender: async (context, next) =>
        {
            executionOrder.Add("PromptFilter2-Rendering");
            await next(context);
            executionOrder.Add("PromptFilter2-Rendered");
        });

        var promptFilter3 = new FakePromptFilter(onPromptRender: async (context, next) =>
        {
            executionOrder.Add("PromptFilter3-Rendering");
            await next(context);
            executionOrder.Add("PromptFilter3-Rendered");
        });

        builder.Services.AddSingleton<IPromptRenderFilter>(promptFilter1);
        builder.Services.AddSingleton<IPromptRenderFilter>(promptFilter2);
        builder.Services.AddSingleton<IPromptRenderFilter>(promptFilter3);

        builder.Services.AddSingleton<ITextGenerationService>(mockTextGeneration.Object);

        var kernel = builder.Build();

        // Act
        await kernel.InvokeAsync(function);

        // Assert
        Assert.Equal("PromptFilter1-Rendering", executionOrder[0]);
        Assert.Equal("PromptFilter2-Rendering", executionOrder[1]);
        Assert.Equal("PromptFilter3-Rendering", executionOrder[2]);
        Assert.Equal("PromptFilter3-Rendered", executionOrder[3]);
        Assert.Equal("PromptFilter2-Rendered", executionOrder[4]);
        Assert.Equal("PromptFilter1-Rendered", executionOrder[5]);
    }

    [Fact]
    public async Task PromptFilterCanOverrideArgumentsAsync()
    {
        // Arrange
        const string OriginalInput = "OriginalInput";
        const string NewInput = "NewInput";

        var mockTextGeneration = this.GetMockTextGeneration();

        var kernel = this.GetKernelWithFilters(textGenerationService: mockTextGeneration.Object,
            onPromptRender: async (context, next) =>
            {
                context.Arguments["originalInput"] = NewInput;
                await next(context);
            });

        var function = KernelFunctionFactory.CreateFromPrompt("Prompt: {{$originalInput}}");

        // Act
        var result = await kernel.InvokeAsync(function, new() { ["originalInput"] = OriginalInput });

        // Assert
        mockTextGeneration.Verify(m => m.GetTextContentsAsync("Prompt: NewInput", It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task PostInvocationPromptFilterCanOverrideRenderedPromptAsync()
    {
        // Arrange
        var mockTextGeneration = this.GetMockTextGeneration();
        var function = KernelFunctionFactory.CreateFromPrompt("Prompt");
        var kernel = this.GetKernelWithFilters(textGenerationService: mockTextGeneration.Object,
            onPromptRender: async (context, next) =>
            {
                await next(context);
                context.RenderedPrompt += " - updated from filter";
            });

        // Act
        var result = await kernel.InvokeAsync(function);

        // Assert
        mockTextGeneration.Verify(m => m.GetTextContentsAsync("Prompt - updated from filter", It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task PostInvocationPromptFilterSkippingWorksCorrectlyAsync()
    {
        // Arrange
        var mockTextGeneration = this.GetMockTextGeneration();
        var function = KernelFunctionFactory.CreateFromPrompt("Prompt");
        var kernel = this.GetKernelWithFilters(textGenerationService: mockTextGeneration.Object,
            onPromptRender: (context, next) =>
            {
                // next(context) is not called here, prompt rendering is cancelled.
                return Task.CompletedTask;
            });

        // Act
        var result = await kernel.InvokeAsync(function);

        // Assert
        mockTextGeneration.Verify(m => m.GetTextContentsAsync("", It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task PromptFilterCanOverrideFunctionResultAsync()
    {
        // Arrange
        var mockTextGeneration = this.GetMockTextGeneration();
        var function = KernelFunctionFactory.CreateFromPrompt("Prompt");

        var kernel = this.GetKernelWithFilters(textGenerationService: mockTextGeneration.Object,
            onPromptRender: async (context, next) =>
            {
                await next(context);

                context.Result = new FunctionResult(context.Function, "Result from prompt filter");
            },
            onFunctionInvocation: async (context, next) =>
            {
                await next(context);
            });

        // Act
        var result = await kernel.InvokeAsync(function);

        // Assert
        mockTextGeneration.Verify(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Never());

        Assert.Equal("Result from prompt filter", result.ToString());
    }

    [Fact]
    public async Task FilterContextHasCancellationTokenAsync()
    {
        // Arrange
        using var cancellationTokenSource = new CancellationTokenSource();
        var mockTextGeneration = this.GetMockTextGeneration();
        var function = KernelFunctionFactory.CreateFromPrompt("Prompt");

        var kernel = this.GetKernelWithFilters(onPromptRender: async (context, next) =>
        {
            Assert.Equal(cancellationTokenSource.Token, context.CancellationToken);
            Assert.True(context.CancellationToken.IsCancellationRequested);

            context.CancellationToken.ThrowIfCancellationRequested();

            await next(context);
        });

        // Act & Assert
        cancellationTokenSource.Cancel();

        await Assert.ThrowsAsync<KernelFunctionCanceledException>(()
            => kernel.InvokeAsync(function, cancellationToken: cancellationTokenSource.Token));
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task FilterContextHasValidStreamingFlagAsync(bool isStreaming)
    {
        // Arrange
        bool? actualStreamingFlag = null;

        var mockTextGeneration = this.GetMockTextGeneration();

        var kernel = this.GetKernelWithFilters(textGenerationService: mockTextGeneration.Object,
            onPromptRender: async (context, next) =>
            {
                actualStreamingFlag = context.IsStreaming;
                await next(context);
            });

        // Act
        if (isStreaming)
        {
            await kernel.InvokePromptStreamingAsync("Prompt").ToListAsync();
        }
        else
        {
            await kernel.InvokePromptAsync("Prompt");
        }

        // Assert
        Assert.Equal(isStreaming, actualStreamingFlag);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task PromptExecutionSettingsArePropagatedToFilterContextAsync(bool isStreaming)
    {
        // Arrange
        PromptExecutionSettings? actualExecutionSettings = null;

        var mockTextGeneration = this.GetMockTextGeneration();

        var function = KernelFunctionFactory.CreateFromPrompt("Prompt");

        var kernel = this.GetKernelWithFilters(textGenerationService: mockTextGeneration.Object,
            onPromptRender: (context, next) =>
            {
                actualExecutionSettings = context.ExecutionSettings;
                return next(context);
            });

        var expectedExecutionSettings = new PromptExecutionSettings();

        var arguments = new KernelArguments(expectedExecutionSettings);

        // Act
        if (isStreaming)
        {
            await foreach (var item in kernel.InvokeStreamingAsync(function, arguments))
            { }
        }
        else
        {
            await kernel.InvokeAsync(function, arguments);
        }

        // Assert
        Assert.Same(expectedExecutionSettings, actualExecutionSettings);
    }
}

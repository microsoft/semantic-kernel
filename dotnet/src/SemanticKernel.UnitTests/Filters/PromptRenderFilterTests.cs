// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.TextGeneration;
using Moq;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
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

    [Fact]
    public async Task PromptFiltersAreTriggeredForPromptsAsync()
    {
        // Arrange
        Kernel? contextKernel = null;

        var filterInvocations = 0;
        var mockTextGeneration = this.GetMockTextGeneration();

        var function = KernelFunctionFactory.CreateFromPrompt("Prompt");

        var kernel = this.GetKernelWithFilters(textGenerationService: mockTextGeneration.Object,
            onPromptRender: async (context, next) =>
            {
                contextKernel = context.Kernel;

                filterInvocations++;
                await next(context);
                filterInvocations++;
            });

        // Act
        var result = await kernel.InvokeAsync(function);

        // Assert
        Assert.Equal(2, filterInvocations);
        Assert.Same(contextKernel, kernel);
    }

    [Fact]
    public async Task PromptFiltersAreTriggeredForPromptsStreamingAsync()
    {
        // Arrange
        var filterInvocations = 0;
        var mockTextGeneration = this.GetMockTextGeneration();

        var function = KernelFunctionFactory.CreateFromPrompt("Prompt");

        var kernel = this.GetKernelWithFilters(textGenerationService: mockTextGeneration.Object,
            onPromptRender: async (context, next) =>
            {
                filterInvocations++;
                await next(context);
                filterInvocations++;
            });

        // Act
        await foreach (var chunk in kernel.InvokeStreamingAsync(function))
        {
        }

        // Assert
        Assert.Equal(2, filterInvocations);
    }

    [Fact]
    public async Task PostInvocationPromptFilterChangesRenderedPromptAsync()
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
    public async Task PostInvocationPromptFilterCancellationWorksCorrectlyAsync()
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
}

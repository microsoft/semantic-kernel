// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Filters;

public class KernelFilterTests : FilterBaseTest
{
    [Fact]
    public void FiltersAreClonedWhenRegisteredWithDI()
    {
        // Arrange
        var functionFilter = new FakeFunctionFilter(onFunctionInvocation: async (context, next) => { await next(context); });
        var promptFilter = new FakePromptFilter(onPromptRender: async (context, next) => { await next(context); });
        var autoFunctionFilter = new FakeAutoFunctionFilter(onAutoFunctionInvocation: async (context, next) => { await next(context); });

        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton<IFunctionInvocationFilter>(functionFilter);
        builder.Services.AddSingleton<IPromptRenderFilter>(promptFilter);
        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(autoFunctionFilter);

        var kernel = builder.Build();

        // Act
        var clonedKernel = kernel.Clone();

        // Assert
        Assert.Single(kernel.FunctionInvocationFilters);
        Assert.Single(kernel.PromptRenderFilters);
        Assert.Single(kernel.AutoFunctionInvocationFilters);

        Assert.Single(clonedKernel.FunctionInvocationFilters);
        Assert.Single(clonedKernel.PromptRenderFilters);
        Assert.Single(clonedKernel.AutoFunctionInvocationFilters);
    }

    [Fact]
    public void FiltersAreClonedWhenRegisteredWithKernelProperties()
    {
        // Arrange
        var functionFilter = new FakeFunctionFilter(onFunctionInvocation: async (context, next) => { await next(context); });
        var promptFilter = new FakePromptFilter(onPromptRender: async (context, next) => { await next(context); });
        var autoFunctionFilter = new FakeAutoFunctionFilter(onAutoFunctionInvocation: async (context, next) => { await next(context); });

        var builder = Kernel.CreateBuilder();

        var kernel = builder.Build();

        kernel.FunctionInvocationFilters.Add(functionFilter);
        kernel.PromptRenderFilters.Add(promptFilter);
        kernel.AutoFunctionInvocationFilters.Add(autoFunctionFilter);

        // Act
        var clonedKernel = kernel.Clone();

        // Assert
        Assert.Single(kernel.FunctionInvocationFilters);
        Assert.Single(kernel.PromptRenderFilters);
        Assert.Single(kernel.AutoFunctionInvocationFilters);

        Assert.Single(clonedKernel.FunctionInvocationFilters);
        Assert.Single(clonedKernel.PromptRenderFilters);
        Assert.Single(clonedKernel.AutoFunctionInvocationFilters);
    }
}

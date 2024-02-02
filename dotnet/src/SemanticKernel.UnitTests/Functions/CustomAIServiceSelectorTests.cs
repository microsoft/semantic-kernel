// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Services;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class CustomAIServiceSelectorTests
{
    [Fact]
    public void ItGetsAIServiceUsingArbitraryAttributes()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton<IAIService>("service1", new AIService());
        Kernel kernel = builder.Build();

        var function = kernel.CreateFunctionFromPrompt("Hello AI");
        var serviceSelector = new CustomAIServiceSelector();

        // Act
        (var aiService, var defaultExecutionSettings) = serviceSelector.SelectAIService<IAIService>(kernel, function, new KernelArguments());

        // Assert
        Assert.NotNull(aiService);
        Assert.True(aiService.Attributes?.ContainsKey("Key1"));
        Assert.Null(defaultExecutionSettings);
    }

    private sealed class CustomAIServiceSelector : IAIServiceSelector
    {
#pragma warning disable CS8769 // Nullability of reference types in value doesn't match target type. Cannot use [NotNullWhen] because of access to internals from abstractions.
        bool IAIServiceSelector.TrySelectAIService<T>(Kernel kernel, KernelFunction function, KernelArguments arguments, out T? service, out PromptExecutionSettings? serviceSettings) where T : class
        {
            var keyedService = (kernel.Services as IKeyedServiceProvider)?.GetKeyedService<T>("service1");
            if (keyedService is null || keyedService.Attributes is null)
            {
                service = null;
                serviceSettings = null;
                return false;
            }

            service = keyedService.Attributes.ContainsKey("Key1") ? keyedService as T : null;
            serviceSettings = null;
            return true;
        }
    }

    private sealed class AIService : IAIService
    {
        public IReadOnlyDictionary<string, object?> Attributes => this._attributes;

        public AIService()
        {
            this._attributes = new Dictionary<string, object?>();
            this._attributes.Add("Key1", "Value1");
        }

        private readonly Dictionary<string, object?> _attributes;
    }
}

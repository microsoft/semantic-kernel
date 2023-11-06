// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TemplateEngine;
using Microsoft.SemanticKernel.TemplateEngine.Handlebars;
using Moq;
using SemanticKernel.Extensions.UnitTests.XunitHelpers;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Extensions.UnitTests.TemplateEngine.Handlebars;

public sealed class HandlebarsPromptTemplateTests
{
    private readonly HandlebarsPromptTemplateFactory _factory;
    private readonly IKernel _kernel;
    private readonly ContextVariables _variables;
    private readonly Mock<IReadOnlyFunctionCollection> _functions;
    private readonly ITestOutputHelper _logger;
    private readonly Mock<IFunctionRunner> _functionRunner;
    private readonly Mock<IAIServiceProvider> _serviceProvider;
    private readonly Mock<IAIServiceSelector> _serviceSelector;

    public HandlebarsPromptTemplateTests(ITestOutputHelper testOutputHelper)
    {
        this._logger = testOutputHelper;
        this._factory = new HandlebarsPromptTemplateFactory(TestConsoleLogger.LoggerFactory);
        this._kernel = new KernelBuilder().Build();
        this._variables = new ContextVariables(Guid.NewGuid().ToString("X"));

        this._functions = new Mock<IReadOnlyFunctionCollection>();
        this._functionRunner = new Mock<IFunctionRunner>();
        this._serviceProvider = new Mock<IAIServiceProvider>();
        this._serviceSelector = new Mock<IAIServiceSelector>();
    }

    [Fact]
    public async Task ItRendersVariablesAsync()
    {
        // Arrange
        this._variables.Set("bar", "Bar");
        var template = "Foo {{bar}}";
        var target = (HandlebarsPromptTemplate)this._factory.Create(template, new PromptTemplateConfig() { TemplateFormat = HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat });
        var context = this._kernel.CreateNewContext(this._variables);

        // Act
        var prompt = await target.RenderAsync(context);

        // Assert   
        Assert.Equal("Foo Bar", prompt);
    }
}

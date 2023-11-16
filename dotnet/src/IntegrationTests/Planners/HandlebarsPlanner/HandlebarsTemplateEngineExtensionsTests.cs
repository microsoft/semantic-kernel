// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;
using HandlebarsDotNet;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Planners.Handlebars;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Planners.HandlebarsPlanner;

public sealed class HandlebarsTemplateEngineExtensionsTests : IDisposable
{
    public HandlebarsTemplateEngineExtensionsTests(ITestOutputHelper output)
    {
        this._logger = NullLoggerFactory.Instance;
        this._testOutputHelper = new RedirectOutput(output);

        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<HandlebarsTemplateEngineExtensionsTests>()
            .Build();
    }

    [Fact]
    public void ShouldRenderTemplateWithVariables()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var executionContext = kernel.CreateNewContext();
        var template = "Hello {{name}}!";
        var variables = new Dictionary<string, object?> { { "name", "World" } };

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, executionContext, template, variables);

        // Assert
        Assert.Equal("Hello World!", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithSystemHelpers()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var executionContext = kernel.CreateNewContext();
        var template = "{{#if (equal x y)}}Equal{{else}}Not equal{{/if}}";
        var variables = new Dictionary<string, object?> { { "x", 10 }, { "y", 10 } };

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, executionContext, template, variables);

        // Assert
        Assert.Equal("Equal", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithArrayHelper()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var executionContext = kernel.CreateNewContext();
        var template = "{{#each (array 1 2 3)}}{{this}}{{/each}}";
        var variables = new Dictionary<string, object?>();

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, executionContext, template, variables);

        // Assert
        Assert.Equal("123", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithRangeHelper()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var executionContext = kernel.CreateNewContext();
        var template = "{{#each (range 1 5)}}{{this}}{{/each}}";
        var variables = new Dictionary<string, object?>();

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, executionContext, template, variables);

        // Assert
        Assert.Equal("12345", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithConcatHelper()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var executionContext = kernel.CreateNewContext();
        var template = "{{concat \"Hello\" \" \" \"World\" \"!\"}}";
        var variables = new Dictionary<string, object?>();

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, executionContext, template, variables);

        // Assert
        Assert.Equal("Hello World!", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithJsonHelper()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var executionContext = kernel.CreateNewContext();
        var template = "{{json person}}";
        var variables = new Dictionary<string, object?>
            {
                { "person", new { name = "Alice", age = 25 } }
            };

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, executionContext, template, variables);

        // Assert
        Assert.Equal("{\"name\":\"Alice\",\"age\":25}", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithMessageHelper()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var executionContext = kernel.CreateNewContext();
        var template = "{{#message role=\"title\"}}Hello World!{{/message}}";
        var variables = new Dictionary<string, object?>();

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, executionContext, template, variables);

        // Assert
        Assert.Equal("<title~>Hello World!</title~>", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithRawHelper()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var executionContext = kernel.CreateNewContext();
        var template = "{{{{raw}}}}{{x}}{{{{/raw}}}}";
        var variables = new Dictionary<string, object?>();

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, executionContext, template, variables);

        // Assert
        Assert.Equal("{{x}}", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithSetAndGetHelpers()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var executionContext = kernel.CreateNewContext();
        var template = "{{set name=\"x\" value=10}}{{get name=\"x\"}}";
        var variables = new Dictionary<string, object?>();

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, executionContext, template, variables);

        // Assert
        Assert.Equal("10", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithFunctionHelpers()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var executionContext = kernel.CreateNewContext();
        var template = "Foo {{Foo-Bar}}";
        var variables = new Dictionary<string, object?>();
        kernel.ImportFunctions(new Foo(), "Foo");

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, executionContext, template, variables);

        // Assert   
        Assert.Equal("Foo Bar", result);
    }

    // TODO [@teresaqhoang]: Add this back in when parameter view types are better supported. Currently, parameter type is null when it shouold be string.
    // [Fact]
    // public void ShouldRenderTemplateWithFunctionHelpersWithPositionalArguments()
    // {
    //     // Arrange
    //     var kernel = this.InitializeKernel();
    //     var executionContext = kernel.CreateNewContext();
    //     var template = "{{Foo-Combine \"Bar\" \"Baz\"}}"; // Use positional arguments instead of hashed arguments
    //     var variables = new Dictionary<string, object?>();
    //     kernel.ImportFunctions(new Foo(), "Foo");

    //     // Act
    //     var result = HandlebarsTemplateEngineExtensions.Render(kernel, executionContext, template, variables);

    //     // Assert   
    //     Assert.Equal("BazBar", result);
    // }

    [Fact]
    public void ShouldRenderTemplateWithFunctionHelpersWitHashArguments()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var executionContext = kernel.CreateNewContext();
        var template = "{{Foo-Combine x=\"Bar\" y=\"Baz\"}}"; // Use positional arguments instead of hashed arguments
        var variables = new Dictionary<string, object?>();
        kernel.ImportFunctions(new Foo(), "Foo");

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, executionContext, template, variables);

        // Assert   
        Assert.Equal("BazBar", result);
    }

    [Fact]
    public void ShouldThrowExceptionWhenMissingRequiredParameter()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var executionContext = kernel.CreateNewContext();
        var template = "{{Foo-Combine x=\"Bar\"}}";
        var variables = new Dictionary<string, object?>();
        kernel.ImportFunctions(new Foo(), "Foo");

        // Assert   
        Assert.Throws<SKException>(() => HandlebarsTemplateEngineExtensions.Render(kernel, executionContext, template, variables));
    }

    [Fact]
    public void ShouldThrowExceptionWhenFunctionHelperHasInvalidParameterType()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var executionContext = kernel.CreateNewContext();
        var template = "{{Foo-StringifyInt x=\"twelve\"}}";
        var variables = new Dictionary<string, object?>();
        kernel.ImportFunctions(new Foo(), "Foo");

        // Assert
        Assert.Throws<ArgumentOutOfRangeException>(() => HandlebarsTemplateEngineExtensions.Render(kernel, executionContext, template, variables));
    }

    [Fact]
    public void ShouldThrowExceptionWhenFunctionHelperIsNotDefined()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var executionContext = kernel.CreateNewContext();
        var template = "{{Foo-Random x=\"random\"}}";
        var variables = new Dictionary<string, object?>();
        kernel.ImportFunctions(new Foo(), "Foo");

        // Assert   
        Assert.Throws<HandlebarsRuntimeException>(() => HandlebarsTemplateEngineExtensions.Render(kernel, executionContext, template, variables));
    }

    private IKernel InitializeKernel()
    {
        // Arrange
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        IKernel kernel = new KernelBuilder()
            .WithRetryBasic()
            .WithAzureTextCompletionService(
                deploymentName: azureOpenAIConfiguration.DeploymentName,
                endpoint: azureOpenAIConfiguration.Endpoint,
                apiKey: azureOpenAIConfiguration.ApiKey,
                serviceId: azureOpenAIConfiguration.ServiceId,
                setAsDefault: true)
            .Build();

        return kernel;
    }

    private sealed class Foo
    {
        [SKFunction, Description("Return Bar")]
        public string Bar() => "Bar";

        [SKFunction, Description("Return words concatenated")]
        public string Combine([System.ComponentModel.Description("First word")] string x, [System.ComponentModel.Description("Second word")] string y) => y + x;

        [SKFunction, Description("Return number as string")]
        public string StringifyInt([System.ComponentModel.Description("Number to stringify")] int x) => x.ToString(CultureInfo.InvariantCulture);
    }

    private readonly ILoggerFactory _logger;
    private readonly RedirectOutput _testOutputHelper;
    private readonly IConfigurationRoot _configuration;

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    ~HandlebarsTemplateEngineExtensionsTests()
    {
        this.Dispose(false);
    }

    private void Dispose(bool disposing)
    {
        if (disposing)
        {
            if (this._logger is IDisposable ld)
            {
                ld.Dispose();
            }

            this._testOutputHelper.Dispose();
        }
    }
}

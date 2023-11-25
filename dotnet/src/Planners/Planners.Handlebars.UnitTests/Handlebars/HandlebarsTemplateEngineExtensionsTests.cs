// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Globalization;
using HandlebarsDotNet;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning.Handlebars;
using Xunit;

namespace Microsoft.SemanticKernel.Planners.UnitTests.Handlebars;

public sealed class HandlebarsTemplateEngineExtensionsTests
{
    [Fact]
    public void ShouldRenderTemplateWithVariables()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var contextVariables = new ContextVariables();
        var template = "Hello {{name}}!";
        var variables = new Dictionary<string, object?> { { "name", "World" } };

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, contextVariables, template, variables);

        // Assert
        Assert.Equal("Hello World!", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithSystemHelpers()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var contextVariables = new ContextVariables();
        var template = "{{#if (equal x y)}}Equal{{else}}Not equal{{/if}}";
        var variables = new Dictionary<string, object?> { { "x", 10 }, { "y", 10 } };

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, contextVariables, template, variables);

        // Assert
        Assert.Equal("Equal", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithArrayHelper()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var contextVariables = new ContextVariables();
        var template = "{{#each (array 1 2 3)}}{{this}}{{/each}}";
        var variables = new Dictionary<string, object?>();

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, contextVariables, template, variables);

        // Assert
        Assert.Equal("123", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithRangeHelper()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var contextVariables = new ContextVariables();
        var template = "{{#each (range 1 5)}}{{this}}{{/each}}";
        var variables = new Dictionary<string, object?>();

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, contextVariables, template, variables);

        // Assert
        Assert.Equal("12345", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithConcatHelper()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var contextVariables = new ContextVariables();
        var template = "{{concat \"Hello\" \" \" \"World\" \"!\"}}";
        var variables = new Dictionary<string, object?>();

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, contextVariables, template, variables);

        // Assert
        Assert.Equal("Hello World!", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithJsonHelper()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var contextVariables = new ContextVariables();
        var template = "{{json person}}";
        var variables = new Dictionary<string, object?>
            {
                { "person", new { name = "Alice", age = 25 } }
            };

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, contextVariables, template, variables);

        // Assert
        Assert.Equal("{\"name\":\"Alice\",\"age\":25}", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithMessageHelper()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var contextVariables = new ContextVariables();
        var template = "{{#message role=\"title\"}}Hello World!{{/message}}";
        var variables = new Dictionary<string, object?>();

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, contextVariables, template, variables);

        // Assert
        Assert.Equal("<title~>Hello World!</title~>", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithRawHelper()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var contextVariables = new ContextVariables();
        var template = "{{{{raw}}}}{{x}}{{{{/raw}}}}";
        var variables = new Dictionary<string, object?>();

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, contextVariables, template, variables);

        // Assert
        Assert.Equal("{{x}}", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithSetAndGetHelpers()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var contextVariables = new ContextVariables();
        var template = "{{set name=\"x\" value=10}}{{get name=\"x\"}}";
        var variables = new Dictionary<string, object?>();

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, contextVariables, template, variables);

        // Assert
        Assert.Equal("10", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithFunctionHelpers()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var contextVariables = new ContextVariables();
        var template = "Foo {{Foo-Bar}}";
        var variables = new Dictionary<string, object?>();
        kernel.ImportPluginFromObject(new Foo(), "Foo");

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, contextVariables, template, variables);

        // Assert   
        Assert.Equal("Foo Bar", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithFunctionHelpersWithPositionalArguments()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var contextVariables = new ContextVariables();
        var template = "{{Foo-Combine \"Bar\" \"Baz\"}}"; // Use positional arguments instead of hashed arguments
        var variables = new Dictionary<string, object?>();
        kernel.ImportPluginFromObject(new Foo(), "Foo");

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, contextVariables, template, variables);

        // Assert   
        Assert.Equal("BazBar", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithFunctionHelpersWitHashArguments()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var contextVariables = new ContextVariables();
        var template = "{{Foo-Combine x=\"Bar\" y=\"Baz\"}}"; // Use positional arguments instead of hashed arguments
        var variables = new Dictionary<string, object?>();
        kernel.ImportPluginFromObject(new Foo(), "Foo");

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, contextVariables, template, variables);

        // Assert   
        Assert.Equal("BazBar", result);
    }

    [Fact]
    public void ShouldThrowExceptionWhenMissingRequiredParameter()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var contextVariables = new ContextVariables();
        var template = "{{Foo-Combine x=\"Bar\"}}";
        var variables = new Dictionary<string, object?>();
        kernel.ImportPluginFromObject(new Foo(), "Foo");

        // Assert   
        Assert.Throws<KernelException>(() => HandlebarsTemplateEngineExtensions.Render(kernel, contextVariables, template, variables));
    }

    [Fact]
    public void ShouldThrowExceptionWhenFunctionHelperHasInvalidParameterType()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var contextVariables = new ContextVariables();
        var template = "{{Foo-StringifyInt x=\"twelve\"}}";
        var variables = new Dictionary<string, object?>();
        kernel.ImportPluginFromObject(new Foo(), "Foo");

        // Assert
        Assert.Throws<ArgumentOutOfRangeException>(() => HandlebarsTemplateEngineExtensions.Render(kernel, contextVariables, template, variables));
    }

    [Fact]
    public void ShouldThrowExceptionWhenFunctionHelperIsNotDefined()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var contextVariables = new ContextVariables();
        var template = "{{Foo-Random x=\"random\"}}";
        var variables = new Dictionary<string, object?>();
        kernel.ImportPluginFromObject(new Foo(), "Foo");

        // Assert   
        Assert.Throws<HandlebarsRuntimeException>(() => HandlebarsTemplateEngineExtensions.Render(kernel, contextVariables, template, variables));
    }

    private Kernel InitializeKernel()
    {
        Kernel kernel = new KernelBuilder().Build();
        return kernel;
    }

    private sealed class Foo
    {
        [KernelFunction, Description("Return Bar")]
        public string Bar() => "Bar";

        [KernelFunction, Description("Return words concatenated")]
        public string Combine([Description("First word")] string x, [Description("Second word")] string y) => y + x;

        [KernelFunction, Description("Return number as string")]
        public string StringifyInt([Description("Number to stringify")] int x) => x.ToString(CultureInfo.InvariantCulture);
    }
}

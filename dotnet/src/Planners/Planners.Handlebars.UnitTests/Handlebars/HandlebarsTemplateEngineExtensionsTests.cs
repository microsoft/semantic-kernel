// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Globalization;
using HandlebarsDotNet;
using Microsoft.SemanticKernel.Planning.Handlebars;
using Xunit;

#pragma warning disable CA1812 // Uninstantiated internal types

namespace Microsoft.SemanticKernel.Planners.UnitTests.Handlebars;

public sealed class HandlebarsTemplateEngineExtensionsTests
{
    [Fact]
    public void ShouldRenderTemplateWithVariables()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var template = "Hello {{name}}!";
        var arguments = new KernelArguments { { "name", "World" } };

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, template, arguments);

        // Assert
        Assert.Equal("Hello World!", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithSystemHelpers()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var template = "{{#if (equal x y)}}Equal{{else}}Not equal{{/if}}";
        var arguments = new KernelArguments { { "x", 10 }, { "y", 10 } };

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, template, arguments);

        // Assert
        Assert.Equal("Equal", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithArrayHelper()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var template = "{{#each (array 1 2 3)}}{{this}}{{/each}}";
        var arguments = new KernelArguments();

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, template, arguments);

        // Assert
        Assert.Equal("123", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithRangeHelper()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var template = "{{#each (range 1 5)}}{{this}}{{/each}}";
        var arguments = new KernelArguments();

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, template, arguments);

        // Assert
        Assert.Equal("12345", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithConcatHelper()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var template = "{{concat \"Hello\" \" \" \"World\" \"!\"}}";
        var arguments = new KernelArguments();

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, template, arguments);

        // Assert
        Assert.Equal("Hello World!", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithJsonHelper()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var template = "{{json person}}";
        var arguments = new KernelArguments
            {
                { "person", new { name = "Alice", age = 25 } }
            };

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, template, arguments);

        // Assert
        Assert.Equal("{\"name\":\"Alice\",\"age\":25}", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithMessageHelper()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var template = "{{#message role=\"title\"}}Hello World!{{/message}}";
        var arguments = new KernelArguments();

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, template, arguments);

        // Assert
        Assert.Equal("<title~>Hello World!</title~>", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithRawHelper()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var template = "{{{{raw}}}}{{x}}{{{{/raw}}}}";
        var arguments = new KernelArguments();

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, template, arguments);

        // Assert
        Assert.Equal("{{x}}", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithSetAndGetHelpers()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var template = "{{set name=\"x\" value=10}}{{get name=\"x\"}}";
        var arguments = new KernelArguments();

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, template, arguments);

        // Assert
        Assert.Equal("10", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithFunctionHelpers()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var template = "Foo {{Foo-Bar}}";
        var arguments = new KernelArguments();
        kernel.ImportPluginFromType<Foo>();

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, template, arguments);

        // Assert
        Assert.Equal("Foo Bar", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithFunctionHelpersWithPositionalArguments()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var template = "{{Foo-Combine \"Bar\" \"Baz\"}}"; // Use positional arguments instead of hashed arguments
        var arguments = new KernelArguments();
        kernel.ImportPluginFromType<Foo>();

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, template, arguments);

        // Assert
        Assert.Equal("BazBar", result);
    }

    [Fact]
    public void ShouldRenderTemplateWithFunctionHelpersWitHashArguments()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var template = "{{Foo-Combine x=\"Bar\" y=\"Baz\"}}"; // Use positional arguments instead of hashed arguments
        var variables = new KernelArguments();
        kernel.ImportPluginFromType<Foo>();

        // Act
        var result = HandlebarsTemplateEngineExtensions.Render(kernel, template, variables);

        // Assert
        Assert.Equal("BazBar", result);
    }

    [Fact]
    public void ShouldThrowExceptionWhenMissingRequiredParameter()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var template = "{{Foo-Combine x=\"Bar\"}}";
        var arguments = new KernelArguments();
        kernel.ImportPluginFromType<Foo>();

        // Assert
        Assert.Throws<KernelException>(() => HandlebarsTemplateEngineExtensions.Render(kernel, template, arguments));
    }

    [Fact]
    public void ShouldThrowExceptionWhenFunctionHelperHasInvalidParameterType()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var template = "{{Foo-StringifyInt x=\"twelve\"}}";
        var arguments = new KernelArguments();
        kernel.ImportPluginFromType<Foo>();

        // Assert
        Assert.Throws<ArgumentOutOfRangeException>(() => HandlebarsTemplateEngineExtensions.Render(kernel, template, arguments));
    }

    [Fact]
    public void ShouldThrowExceptionWhenFunctionHelperIsNotDefined()
    {
        // Arrange
        var kernel = this.InitializeKernel();
        var template = "{{Foo-Random x=\"random\"}}";
        var arguments = new KernelArguments();
        kernel.ImportPluginFromType<Foo>();

        // Assert
        Assert.Throws<HandlebarsRuntimeException>(() => HandlebarsTemplateEngineExtensions.Render(kernel, template, arguments));
    }

    private Kernel InitializeKernel() => new();

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

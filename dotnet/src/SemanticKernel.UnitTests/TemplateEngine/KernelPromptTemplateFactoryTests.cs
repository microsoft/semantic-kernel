// Copyright (c) Microsoft. All rights reserved.

<<<<<<<< HEAD:dotnet/src/SemanticKernel.UnitTests/PromptTemplate/KernelPromptTemplateFactoryTests.cs
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.PromptTemplate;
========
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.TemplateEngine;
using Xunit;

namespace SemanticKernel.UnitTests.TemplateEngine;
>>>>>>>> b5e22903 (Python: Make SK compatible with OpenAI 1.0 (#3470)):dotnet/src/SemanticKernel.UnitTests/TemplateEngine/KernelPromptTemplateFactoryTests.cs

public sealed class KernelPromptTemplateFactoryTests
{
    [Fact]
    public void ItCreatesBasicPromptTemplateByDefault()
    {
        // Arrange
        var templateString = "{{$input}}";
        var target = new KernelPromptTemplateFactory();

        // Act
        var result = target.Create(templateString, new PromptTemplateConfig());

        // Assert
        Assert.NotNull(result);
        Assert.True(result is KernelPromptTemplate);
    }

    [Fact]
    public void ItCreatesBasicPromptTemplate()
    {
        // Arrange
        var templateString = "{{$input}}";
        var target = new KernelPromptTemplateFactory();

        // Act
        var result = target.Create(templateString, new PromptTemplateConfig() { TemplateFormat = "semantic-kernel" });

        // Assert
        Assert.NotNull(result);
        Assert.True(result is KernelPromptTemplate);
    }

    [Fact]
    public void ItThrowsExceptionForUnknowPromptTemplateFormat()
    {
        // Arrange
        var templateString = "{{$input}}";
        var target = new KernelPromptTemplateFactory();

        // Act
        // Assert
        Assert.Throws<KernelException>(() => target.Create(templateString, new PromptTemplateConfig() { TemplateFormat = "unknown-format" }));
    }
}

// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Functions.Markdown.Functions;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.Markdown.Functions;

public class KernelFunctionMarkdownTests
{
    [Fact]
    public void ItShouldCreatePromptFunctionConfigFromMarkdown()
    {
        // Arrange
        // Act
        var model = KernelFunctionMarkdown.CreateFromPromptMarkdown(this._markdown, "TellMeAbout");

        // Assert
        Assert.NotNull(model);
        Assert.Equal("TellMeAbout", model.Name);
        Assert.Equal("Hello AI, tell me about {{$input}}", model.Template);
        Assert.Equal(2, model.ExecutionSettings.Count);
        Assert.Equal("gpt4", model.ExecutionSettings[0].ModelId);
        Assert.Equal("gpt3.5", model.ExecutionSettings[1].ModelId);
    }

    [Fact]
    public void ItShouldCreatePromptFunctionFromMarkdown()
    {
        // Arrange
        var kernel = new Kernel();

        // Act
        var function = KernelFunctionMarkdown.CreateFromPromptMarkdown(this._markdown, "TellMeAbout");

        // Assert
        Assert.NotNull(function);
        Assert.Equal("TellMeAbout", function.Name);
    }

    private readonly string _markdown = @"
This is a semantic kernel prompt template
```sk.prompt
Hello AI, tell me about {{$input}}
```
These are AI request settings
```sk.execution_settings
{
    ""model_id"": ""gpt4"",
    ""temperature"": 0.7
}
```
These are more AI request settings
```sk.execution_settings
{
    ""model_id"": ""gpt3.5"",
    ""temperature"": 0.8
}
```
";
}

// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.Markdown.Functions;

public class KernelFunctionMarkdownTests
{
    [Fact]
    public void ItShouldCreatePromptFunctionConfigFromMarkdown()
    {
        // Arrange
        // Act
        var model = KernelFunctionMarkdown.CreateFromPromptMarkdown(Markdown, "TellMeAbout");

        // Assert
        Assert.NotNull(model);
        Assert.Equal("TellMeAbout", model.Name);
        Assert.Equal("Hello AI, tell me about {{$input}}", model.Template);
        Assert.Equal(3, model.ExecutionSettings.Count);
        Assert.Equal("gpt4", model.ExecutionSettings["service1"].ModelId);
        Assert.Equal("gpt3.5", model.ExecutionSettings["service2"].ModelId);
        Assert.Equal("gpt3.5-turbo", model.ExecutionSettings["service3"].ModelId);
    }

    [Fact]
    public void ItShouldInitializeFunctionCallChoicesFromMarkdown()
    {
        // Arrange
        var kernel = new Kernel();

        // Act
        var function = KernelFunctionMarkdown.CreateFromPromptMarkdown(Markdown, "TellMeAbout");

        // Assert
        Assert.NotNull(function);
        Assert.NotEmpty(function.ExecutionSettings);

        Assert.Equal(3, function.ExecutionSettings.Count);

        // AutoFunctionCallChoice for service1
        var service1ExecutionSettings = function.ExecutionSettings["service1"];
        Assert.NotNull(service1ExecutionSettings);

        var service1AutoFunctionChoiceBehavior = service1ExecutionSettings?.FunctionChoiceBehavior as AutoFunctionChoiceBehavior;
        Assert.NotNull(service1AutoFunctionChoiceBehavior);

        Assert.NotNull(service1AutoFunctionChoiceBehavior.Functions);
        Assert.Single(service1AutoFunctionChoiceBehavior.Functions);
        Assert.Equal("p1.f1", service1AutoFunctionChoiceBehavior.Functions.First());

        // RequiredFunctionCallChoice for service2
        var service2ExecutionSettings = function.ExecutionSettings["service2"];
        Assert.NotNull(service2ExecutionSettings);

        var service2RequiredFunctionChoiceBehavior = service2ExecutionSettings?.FunctionChoiceBehavior as RequiredFunctionChoiceBehavior;
        Assert.NotNull(service2RequiredFunctionChoiceBehavior);
        Assert.NotNull(service2RequiredFunctionChoiceBehavior.Functions);
        Assert.Single(service2RequiredFunctionChoiceBehavior.Functions);
        Assert.Equal("p1.f1", service2RequiredFunctionChoiceBehavior.Functions.First());

        // NoneFunctionCallChoice for service3
        var service3ExecutionSettings = function.ExecutionSettings["service3"];
        Assert.NotNull(service3ExecutionSettings);

        var service3NoneFunctionChoiceBehavior = service3ExecutionSettings?.FunctionChoiceBehavior as NoneFunctionChoiceBehavior;
        Assert.NotNull(service3NoneFunctionChoiceBehavior);
    }

    [Fact]
    public void ItShouldCreatePromptFunctionFromMarkdown()
    {
        // Arrange
        var kernel = new Kernel();

        // Act
        var function = KernelFunctionMarkdown.CreateFromPromptMarkdown(Markdown, "TellMeAbout");

        // Assert
        Assert.NotNull(function);
        Assert.Equal("TellMeAbout", function.Name);
    }

    private const string Markdown = """
        This is a semantic kernel prompt template
        ```sk.prompt
        Hello AI, tell me about {{$input}}
        ```
        These are AI execution settings
        ```sk.execution_settings
        {
            "service1" : {
                "model_id": "gpt4",
                "temperature": 0.7,
                "function_choice_behavior": {
                    "type": "auto",
                    "allowAnyRequestedKernelFunction" : true,
                    "functions": ["p1.f1"]
                }
            }
        }
        ```
        These are more AI execution settings
        ```sk.execution_settings
        {
            "service2" : {
                "model_id": "gpt3.5",
                "temperature": 0.8,
                "function_choice_behavior": {
                    "type": "required",
                    "functions": ["p1.f1"]
                }
            }
        }
        ```
        These are AI execution settings as well
        ```sk.execution_settings
        {
            "service3" : {
                "model_id": "gpt3.5-turbo",
                "temperature": 0.8,
                "function_choice_behavior": {
                    "type": "none"
                }
            }
        }
        ```
        """;
}

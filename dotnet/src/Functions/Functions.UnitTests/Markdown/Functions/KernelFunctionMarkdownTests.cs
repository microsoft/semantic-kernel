// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ToolBehaviors;
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
        Assert.NotNull(service1ExecutionSettings?.ToolBehavior);

        var service1FunctionCallBehavior = service1ExecutionSettings.ToolBehavior as FunctionCallBehavior;
        Assert.NotNull(service1FunctionCallBehavior?.Choice);

        var service1AutoFunctionCallChoice = service1FunctionCallBehavior?.Choice as AutoFunctionCallChoice;
        Assert.NotNull(service1AutoFunctionCallChoice);
        Assert.True(service1AutoFunctionCallChoice.AllowAnyRequestedKernelFunction);
        Assert.NotNull(service1AutoFunctionCallChoice.Functions);
        Assert.Single(service1AutoFunctionCallChoice.Functions);
        Assert.Equal("p1.f1", service1AutoFunctionCallChoice.Functions.First());

        // RequiredFunctionCallChoice for service2
        var service2ExecutionSettings = function.ExecutionSettings["service2"];
        Assert.NotNull(service2ExecutionSettings?.ToolBehavior);

        var service2FunctionCallBehavior = service2ExecutionSettings.ToolBehavior as FunctionCallBehavior;
        Assert.NotNull(service2FunctionCallBehavior?.Choice);

        var service2RequiredFunctionCallChoice = service2FunctionCallBehavior?.Choice as RequiredFunctionCallChoice;
        Assert.NotNull(service2RequiredFunctionCallChoice);
        Assert.NotNull(service2RequiredFunctionCallChoice.Functions);
        Assert.Single(service2RequiredFunctionCallChoice.Functions);
        Assert.Equal("p1.f1", service2RequiredFunctionCallChoice.Functions.First());

        // NoneFunctionCallChoice for service3
        var service3ExecutionSettings = function.ExecutionSettings["service3"];
        Assert.NotNull(service3ExecutionSettings?.ToolBehavior);
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
                "tool_behavior": {
                    "type": "function_call_behavior",
                    "choice": {
                        "type": "auto",
                        "allowAnyRequestedKernelFunction" : true,
                        "functions": ["p1.f1"]
                    }
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
                "tool_behavior": {
                    "type": "function_call_behavior",
                    "choice": {
                        "type": "required",
                        "functions": ["p1.f1"]
                    }
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
                "tool_behavior": {
                    "type": "function_call_behavior",
                    "choice": {
                        "type": "none"
                    }
                }
            }
        }
        ```
        """;
}

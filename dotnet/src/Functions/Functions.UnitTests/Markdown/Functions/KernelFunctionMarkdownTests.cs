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
        Assert.Equal(6, model.ExecutionSettings.Count);
        Assert.Equal("gpt4", model.ExecutionSettings["service1"].ModelId);
        Assert.Equal("gpt3.5", model.ExecutionSettings["service2"].ModelId);
        Assert.Equal("gpt3.5-turbo", model.ExecutionSettings["service3"].ModelId);
        Assert.Equal("gpt4", model.ExecutionSettings["service4"].ModelId);
        Assert.Equal("gpt4", model.ExecutionSettings["service5"].ModelId);
        Assert.Equal("gpt4", model.ExecutionSettings["service6"].ModelId);
    }

    [Fact]
    public void ItShouldInitializeFunctionChoiceBehaviorsFromMarkdown()
    {
        // Arrange
        var kernel = new Kernel();
        kernel.Plugins.AddFromFunctions("p1", [KernelFunctionFactory.CreateFromMethod(() => { }, "f1")]);
        kernel.Plugins.AddFromFunctions("p2", [KernelFunctionFactory.CreateFromMethod(() => { }, "f2")]);
        kernel.Plugins.AddFromFunctions("p3", [KernelFunctionFactory.CreateFromMethod(() => { }, "f3")]);

        // Act
        var function = KernelFunctionMarkdown.CreateFromPromptMarkdown(Markdown, "TellMeAbout");

        // Assert
        Assert.NotNull(function);
        Assert.NotEmpty(function.ExecutionSettings);

        Assert.Equal(6, function.ExecutionSettings.Count);

        // AutoFunctionCallChoice for service1
        var service1ExecutionSettings = function.ExecutionSettings["service1"];
        Assert.NotNull(service1ExecutionSettings?.FunctionChoiceBehavior);

        var autoConfig = service1ExecutionSettings.FunctionChoiceBehavior.GetConfiguration(new FunctionChoiceBehaviorConfigurationContext(chatHistory: []) { Kernel = kernel });
        Assert.NotNull(autoConfig);
        Assert.Equal(FunctionChoice.Auto, autoConfig.Choice);
        Assert.NotNull(autoConfig.Functions);
        Assert.Equal("p1", autoConfig.Functions.Single().PluginName);
        Assert.Equal("f1", autoConfig.Functions.Single().Name);

        // RequiredFunctionCallChoice for service2
        var service2ExecutionSettings = function.ExecutionSettings["service2"];
        Assert.NotNull(service2ExecutionSettings?.FunctionChoiceBehavior);

        var requiredConfig = service2ExecutionSettings.FunctionChoiceBehavior.GetConfiguration(new FunctionChoiceBehaviorConfigurationContext(chatHistory: []) { Kernel = kernel });
        Assert.NotNull(requiredConfig);
        Assert.Equal(FunctionChoice.Required, requiredConfig.Choice);
        Assert.NotNull(requiredConfig.Functions);
        Assert.Equal("p2", requiredConfig.Functions.Single().PluginName);
        Assert.Equal("f2", requiredConfig.Functions.Single().Name);

        // NoneFunctionCallChoice for service3
        var service3ExecutionSettings = function.ExecutionSettings["service3"];
        Assert.NotNull(service3ExecutionSettings?.FunctionChoiceBehavior);

        var noneConfig = service3ExecutionSettings.FunctionChoiceBehavior.GetConfiguration(new FunctionChoiceBehaviorConfigurationContext(chatHistory: []) { Kernel = kernel });
        Assert.NotNull(noneConfig);
        Assert.Equal(FunctionChoice.None, noneConfig.Choice);
        Assert.NotNull(noneConfig.Functions);
        Assert.Equal("p3", noneConfig.Functions.Single().PluginName);
        Assert.Equal("f3", noneConfig.Functions.Single().Name);

        // AutoFunctionCallChoice with empty functions collection for service4
        var service4ExecutionSettings = function.ExecutionSettings["service4"];
        Assert.NotNull(service4ExecutionSettings?.FunctionChoiceBehavior);

        var autoWithEmptyFunctionsConfig = service4ExecutionSettings.FunctionChoiceBehavior.GetConfiguration(new FunctionChoiceBehaviorConfigurationContext(chatHistory: []) { Kernel = kernel });
        Assert.NotNull(autoWithEmptyFunctionsConfig);
        Assert.Equal(FunctionChoice.Auto, autoWithEmptyFunctionsConfig.Choice);
        Assert.Null(autoWithEmptyFunctionsConfig.Functions);

        // AutoFunctionCallChoice with no functions collection for service5
        var service5ExecutionSettings = function.ExecutionSettings["service5"];
        Assert.NotNull(service5ExecutionSettings?.FunctionChoiceBehavior);

        var autoWithNoFunctionsConfig = service5ExecutionSettings.FunctionChoiceBehavior.GetConfiguration(new FunctionChoiceBehaviorConfigurationContext(chatHistory: []) { Kernel = kernel });
        Assert.NotNull(autoWithNoFunctionsConfig);
        Assert.Equal(FunctionChoice.Auto, autoWithNoFunctionsConfig.Choice);
        Assert.NotNull(autoWithNoFunctionsConfig.Functions);
        Assert.Equal(3, autoWithNoFunctionsConfig.Functions.Count);
        Assert.Contains(autoWithNoFunctionsConfig.Functions, f => f.PluginName == "p1" && f.Name == "f1");
        Assert.Contains(autoWithNoFunctionsConfig.Functions, f => f.PluginName == "p2" && f.Name == "f2");
        Assert.Contains(autoWithNoFunctionsConfig.Functions, f => f.PluginName == "p3" && f.Name == "f3");

        // No function choice behavior for service6
        var service6ExecutionSettings = function.ExecutionSettings["service6"];
        Assert.Null(service6ExecutionSettings?.FunctionChoiceBehavior);
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
                    "functions": ["p2.f2"]
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
                    "type": "none",
                    "functions": ["p3.f3"]
                }
            }
        }
        ```
        These are AI execution settings
        ```sk.execution_settings
        {
            "service4" : {
                "model_id": "gpt4",
                "temperature": 0.7,
                "function_choice_behavior": {
                    "type": "auto",
                    "functions": []
                }
            }
        }
        ```
        These are AI execution settings
        ```sk.execution_settings
        {
            "service5" : {
                "model_id": "gpt4",
                "temperature": 0.7,
                "function_choice_behavior": {
                    "type": "auto"
                }
            }
        }
        ```
        These are AI execution settings
        ```sk.execution_settings
        {
            "service6" : {
                "model_id": "gpt4",
                "temperature": 0.7
            }
        }
        ```
        """;
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.UnitTests.PromptTemplate;

public class PromptTemplateConfigTests
{
    [Fact]
    public void DeserializingDoNotExpectChatSystemPromptToExist()
    {
        // Arrange
        string configPayload = """
            {
                "max_tokens": 60,
                "temperature": 0.5,
                "top_p": 0.0,
                "presence_penalty": 0.0,
                "frequency_penalty": 0.0
            }
            """;

        // Act
        var settings = JsonSerializer.Deserialize<OpenAIPromptExecutionSettings>(configPayload);

        // Assert
        Assert.NotNull(settings);
        Assert.Null(settings.ChatSystemPrompt);
    }

    [Fact]
    public void DeserializingExpectChatSystemPromptToExists()
    {
        // Arrange
        string configPayload = """
            {
                "max_tokens": 60,
                "temperature": 0.5,
                "top_p": 0.0,
                "presence_penalty": 0.0,
                "frequency_penalty": 0.0,
                "chat_system_prompt": "I am a prompt"
            }
            """;

        // Act
        var settings = JsonSerializer.Deserialize<OpenAIPromptExecutionSettings>(configPayload);

        // Assert
        Assert.NotNull(settings);
        Assert.NotNull(settings.ChatSystemPrompt);
        Assert.Equal("I am a prompt", settings.ChatSystemPrompt);
    }

    [Fact]
    public void DeserializingExpectMultipleModels()
    {
        // Arrange
        string configPayload = """
            {
              "schema": 1,
              "description": "",
              "execution_settings":
              {
                "service1": {
                  "model_id": "gpt-4",
                  "max_tokens": 200,
                  "temperature": 0.2,
                  "top_p": 0.0,
                  "presence_penalty": 0.0,
                  "frequency_penalty": 0.0,
                  "stop_sequences":
                  [
                    "Human",
                    "AI"
                  ]
                },
                "service2": {
                  "model_id": "gpt-3.5_turbo",
                  "max_tokens": 256,
                  "temperature": 0.3,
                  "top_p": 0.0,
                  "presence_penalty": 0.0,
                  "frequency_penalty": 0.0,
                  "stop_sequences":
                  [
                    "Human",
                    "AI"
                  ]
                }
              }
            }
            """;

        // Act
        var promptTemplateConfig = JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload);

        // Assert
        Assert.NotNull(promptTemplateConfig);
        Assert.NotNull(promptTemplateConfig.ExecutionSettings);
        Assert.Equal(2, promptTemplateConfig.ExecutionSettings.Count);
    }

    [Fact]
    public void DeserializingDoesNotAutoSetServiceIdWhenNotProvided()
    {
        // Arrange
        string configPayload = """
            {
              "schema": 1,
              "description": "",
              "execution_settings":
              {
                "service1": {
                  "model_id": "gpt-4",
                  "max_tokens": 200,
                  "temperature": 0.2,
                  "top_p": 0.0,
                  "presence_penalty": 0.0,
                  "frequency_penalty": 0.0,
                  "stop_sequences":
                  [
                    "Human",
                    "AI"
                  ]
                },
                "service2": {
                  "model_id": "gpt-3.5_turbo",
                  "max_tokens": 256,
                  "temperature": 0.3,
                  "top_p": 0.0,
                  "presence_penalty": 0.0,
                  "frequency_penalty": 0.0,
                  "stop_sequences":
                  [
                    "Human",
                    "AI"
                  ]
                }
              }
            }
            """;

        // Act
        var promptTemplateConfig = JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload);

        // Assert
        Assert.NotNull(promptTemplateConfig);
        Assert.Null(promptTemplateConfig.ExecutionSettings["service1"].ServiceId);
        Assert.Null(promptTemplateConfig.ExecutionSettings["service2"].ServiceId);
    }

    [Fact]
    public void DeserializingDoesNotAutoSetServiceIdWhenDefault()
    {
        // Arrange
        string configPayload = """
            {
              "schema": 1,
              "description": "",
              "execution_settings":
              {
                "default": {
                  "model_id": "gpt-4",
                  "max_tokens": 200,
                  "temperature": 0.2,
                  "top_p": 0.0,
                  "presence_penalty": 0.0,
                  "frequency_penalty": 0.0,
                  "stop_sequences":
                  [
                    "Human",
                    "AI"
                  ]
                }
              }
            }
            """;

        // Act
        var promptTemplateConfig = JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload);

        // Assert
        Assert.NotNull(promptTemplateConfig);
        Assert.NotNull(promptTemplateConfig.DefaultExecutionSettings);
        Assert.Null(promptTemplateConfig.DefaultExecutionSettings?.ServiceId);
    }

    [Fact]
    public void DeserializingServiceIdUnmatchingIndexShouldThrow()
    {
        // Arrange
        string configPayload = """
            {
              "schema": 1,
              "description": "",
              "execution_settings":
              {
                "service1": {
                  "model_id": "gpt-4",
                  "max_tokens": 200,
                  "temperature": 0.2,
                  "top_p": 0.0,
                  "presence_penalty": 0.0,
                  "frequency_penalty": 0.0,
                  "stop_sequences":
                  [
                    "Human",
                    "AI"
                  ]
                },
                "service2": {
                  "service_id": "service3",
                  "model_id": "gpt-3.5_turbo",
                  "max_tokens": 256,
                  "temperature": 0.3,
                  "top_p": 0.0,
                  "presence_penalty": 0.0,
                  "frequency_penalty": 0.0,
                  "stop_sequences":
                  [
                    "Human",
                    "AI"
                  ]
                }
              }
            }
            """;

        // Act & Assert
        var exception = Assert.Throws<ArgumentException>(() => JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload));
    }

    [Fact]
    public void ItCannotAddExecutionSettingsWithSameServiceId()
    {
        // Arrange
        var settings = new PromptTemplateConfig();
        settings.AddExecutionSettings(new PromptExecutionSettings(), "service1");

        // Act & Assert
        Assert.Throws<ArgumentException>(() => settings.AddExecutionSettings(new PromptExecutionSettings(), "service1"));
    }

    [Fact]
    public void ItAddExecutionSettingsAndNeverOverwriteServiceId()
    {
        // Arrange
        var promptTemplateConfig = new PromptTemplateConfig();
        var settings1 = new PromptExecutionSettings { ModelId = "model-service-3", ServiceId = "should not override" };

        // Act
        promptTemplateConfig.AddExecutionSettings(new PromptExecutionSettings { ModelId = "model1" });
        promptTemplateConfig.AddExecutionSettings(new PromptExecutionSettings { ModelId = "model2" }, "service1");
        promptTemplateConfig.AddExecutionSettings(new PromptExecutionSettings { ServiceId = "service2", ModelId = "model-service-2" });
        promptTemplateConfig.AddExecutionSettings(new PromptExecutionSettings { ServiceId = "service3", ModelId = "model-service-3" });
        promptTemplateConfig.AddExecutionSettings(settings1);

        // Assert
        Assert.Equal("model1", promptTemplateConfig.ExecutionSettings["default"].ModelId);
        Assert.Null(promptTemplateConfig.ExecutionSettings["default"].ServiceId);

        Assert.Equal("model2", promptTemplateConfig.ExecutionSettings["service1"].ModelId);
        Assert.Null(promptTemplateConfig.ExecutionSettings["service1"].ServiceId);

        Assert.Equal("model-service-2", promptTemplateConfig.ExecutionSettings["service2"].ModelId);
        Assert.Equal("service2", promptTemplateConfig.ExecutionSettings["service2"].ServiceId);

        Assert.Equal("model-service-3", promptTemplateConfig.ExecutionSettings["service3"].ModelId);
        Assert.Equal("service3", promptTemplateConfig.ExecutionSettings["service3"].ServiceId);

        // Never changes settings id
        Assert.Equal("should not override", settings1.ServiceId);
        Assert.True(promptTemplateConfig.ExecutionSettings.ContainsKey("should not override"));
    }

    [Fact]
    public void ItThrowsWhenServiceIdIsProvidedAndExecutionSettingsAlreadyHasAServiceIdPropertySet()
    {
        // Arrange
        var promptTemplateConfig = new PromptTemplateConfig();
        var settings = new PromptExecutionSettings { ModelId = "model-service-3", ServiceId = "service2" };

        // Act & Assert
        Assert.Throws<ArgumentException>(() => promptTemplateConfig.AddExecutionSettings(settings, "service1"));
    }

    [Fact]
    public void DeserializingServiceIdSameIndexKeepsLast()
    {
        // Arrange
        string configPayload = """
            {
              "schema": 1,
              "description": "",
              "execution_settings":
              {
                "service1": {
                  "model_id": "gpt-4",
                  "max_tokens": 200,
                  "temperature": 0.2,
                  "top_p": 0.0,
                  "presence_penalty": 0.0,
                  "frequency_penalty": 0.0,
                  "stop_sequences":
                  [
                    "Human",
                    "AI"
                  ]
                },
                "service1": {
                  "model_id": "gpt-3.5_turbo",
                  "max_tokens": 256,
                  "temperature": 0.3,
                  "top_p": 0.0,
                  "presence_penalty": 0.0,
                  "frequency_penalty": 0.0,
                  "stop_sequences":
                  [
                    "Human",
                    "AI"
                  ]
                }
              }
            }
            """;

        // Act
        var promptTemplate = JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload);

        // Assert
        Assert.NotNull(promptTemplate);
        Assert.NotNull(promptTemplate.ExecutionSettings);
        Assert.Single(promptTemplate.ExecutionSettings);
        Assert.Null(promptTemplate.ExecutionSettings["service1"].ServiceId);
        Assert.Equal("gpt-3.5_turbo", promptTemplate.ExecutionSettings["service1"].ModelId);
    }

    [Fact]
    public void DeserializingExpectCompletion()
    {
        // Arrange
        string configPayload = """
            {
              "schema": 1,
              "description": "",
              "execution_settings":
              {
                "default": {
                  "model_id": "gpt-4",
                  "max_tokens": 200,
                  "temperature": 0.2,
                  "top_p": 0.0,
                  "presence_penalty": 0.0,
                  "frequency_penalty": 0.0,
                  "stop_sequences":
                  [
                    "Human",
                    "AI"
                  ]
                }
              }
            }
            """;

        // Act
        var promptTemplateConfig = JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload);

        // Assert
        Assert.NotNull(promptTemplateConfig);
        Assert.NotNull(promptTemplateConfig.DefaultExecutionSettings);
        Assert.Equal("gpt-4", promptTemplateConfig.DefaultExecutionSettings?.ModelId);
    }

    [Fact]
    public void DeserializingAutoFunctionCallingChoice()
    {
        // Arrange
        string configPayload = """
            {
              "schema": 1,
              "execution_settings": {
                "default": {
                  "model_id": "gpt-4",
                  "function_choice_behavior": {
                    "type": "auto",
                    "functions":["p1.f1"],
                    "options":{
                        "allow_concurrent_invocation": true,
                        "allow_strict_schema_adherence": true
                    }
                  }
                }
              }
            }
            """;

        // Act
        var promptTemplateConfig = PromptTemplateConfig.FromJson(configPayload);

        // Assert
        Assert.NotNull(promptTemplateConfig);
        Assert.Single(promptTemplateConfig.ExecutionSettings);

        var executionSettings = promptTemplateConfig.ExecutionSettings.Single().Value;

        var autoFunctionCallChoice = executionSettings.FunctionChoiceBehavior as AutoFunctionChoiceBehavior;
        Assert.NotNull(autoFunctionCallChoice);

        Assert.NotNull(autoFunctionCallChoice.Functions);
        Assert.Equal("p1.f1", autoFunctionCallChoice.Functions.Single());

        Assert.True(autoFunctionCallChoice.Options!.AllowConcurrentInvocation);
        Assert.True(autoFunctionCallChoice.Options!.AllowStrictSchemaAdherence);
    }

    [Fact]
    public void DeserializingRequiredFunctionCallingChoice()
    {
        // Arrange
        string configPayload = """
            {
              "schema": 1,
              "execution_settings": {
                "default": {
                  "model_id": "gpt-4",
                  "function_choice_behavior": {
                    "type": "required",
                    "functions":["p1.f1"],
                    "options":{
                        "allow_concurrent_invocation": true,
                        "allow_strict_schema_adherence": true
                    }
                  }
                }
              }
            }
            """;

        // Act
        var promptTemplateConfig = PromptTemplateConfig.FromJson(configPayload);

        // Assert
        Assert.NotNull(promptTemplateConfig);
        Assert.Single(promptTemplateConfig.ExecutionSettings);

        var executionSettings = promptTemplateConfig.ExecutionSettings.Single().Value;
        Assert.NotNull(executionSettings);

        var requiredFunctionCallChoice = executionSettings.FunctionChoiceBehavior as RequiredFunctionChoiceBehavior;
        Assert.NotNull(requiredFunctionCallChoice);

        Assert.NotNull(requiredFunctionCallChoice.Functions);
        Assert.Equal("p1.f1", requiredFunctionCallChoice.Functions.Single());

        Assert.True(requiredFunctionCallChoice.Options!.AllowConcurrentInvocation);
        Assert.True(requiredFunctionCallChoice.Options!.AllowStrictSchemaAdherence);
    }

    [Fact]
    public void DeserializingNoneFunctionCallingChoice()
    {
        // Arrange
        string configPayload = """
            {
              "schema": 1,
              "execution_settings": {
                "default": {
                  "model_id": "gpt-4",
                  "function_choice_behavior": {
                    "type": "none"
                  }
                }
              }
            }
            """;

        // Act
        var promptTemplateConfig = PromptTemplateConfig.FromJson(configPayload);

        // Assert
        Assert.NotNull(promptTemplateConfig);
        Assert.Single(promptTemplateConfig.ExecutionSettings);

        var executionSettings = promptTemplateConfig.ExecutionSettings.Single().Value;

        var noneFunctionCallChoice = executionSettings.FunctionChoiceBehavior as NoneFunctionChoiceBehavior;
        Assert.NotNull(noneFunctionCallChoice);
    }

    [Fact]
    public void DeserializingExpectInputVariables()
    {
        // Arrange
        string configPayload = """
            {
              "description": "function description",
              "input_variables":
                [
                    {
                        "name": "input variable name",
                        "description": "input variable description",
                        "default": "default value",
                        "is_required": true
                    }
                ]
            }
            """;

        // Act
        var promptTemplateConfig = JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload);

        // Assert
        Assert.NotNull(promptTemplateConfig);
        Assert.NotNull(promptTemplateConfig.InputVariables);
        Assert.Single(promptTemplateConfig.InputVariables);
        Assert.Equal("input variable name", promptTemplateConfig.InputVariables[0].Name);
        Assert.Equal("input variable description", promptTemplateConfig.InputVariables[0].Description);
        Assert.Equal("default value", promptTemplateConfig.InputVariables[0].Default?.ToString());
        Assert.True(promptTemplateConfig.InputVariables[0].IsRequired);
    }

    [Fact]
    public void DeserializingExpectOutputVariable()
    {
        // Arrange
        string configPayload = """
            {
              "description": "function description",
              "output_variable":
                {
                    "description": "output variable description"
                }
            }
            """;

        // Act
        var promptTemplateConfig = JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload);

        // Assert
        Assert.NotNull(promptTemplateConfig);
        Assert.NotNull(promptTemplateConfig.OutputVariable);
        Assert.Equal("output variable description", promptTemplateConfig.OutputVariable.Description);
    }

    [Fact]
    public void ItShouldDeserializeConfigWithDefaultValueOfStringType()
    {
        // Arrange
        static string CreateJson(object defaultValue)
        {
            var obj = new
            {
                description = "function description",
                input_variables = new[]
                {
                    new
                    {
                        name = "name",
                        description = "description",
                        @default = defaultValue,
                        isRequired = true
                    }
                }
            };

            return JsonSerializer.Serialize(obj);
        }

        // string
        var json = CreateJson((string)"123");
        var config = PromptTemplateConfig.FromJson(json);

        Assert.NotNull(config?.InputVariables);
        Assert.Equal("123", config.InputVariables[0].Default?.ToString());
    }

    [Fact]
    // This test checks that the logic of imposing a temporary limitation on the default value being a string is in place and works as expected.
    public void ItShouldThrowExceptionWhenDeserializingConfigWithDefaultValueOtherThanString()
    {
        // Arrange
        static string CreateJson(object defaultValue)
        {
            var obj = new
            {
                description = "function description",
                input_variables = new[]
                {
                    new
                    {
                        name = "name",
                        description = "description",
                        @default = defaultValue,
                        isRequired = true
                    }
                }
            };

            return JsonSerializer.Serialize(obj);
        }

        // int
        var json = CreateJson((int)1);
        Assert.Throws<NotSupportedException>(() => PromptTemplateConfig.FromJson(json));

        // double
        json = CreateJson((double)1.1);
        Assert.Throws<NotSupportedException>(() => PromptTemplateConfig.FromJson(json));

        // bool
        json = CreateJson((bool)true);
        Assert.Throws<NotSupportedException>(() => PromptTemplateConfig.FromJson(json));

        // array
        json = CreateJson(new[] { "1", "2", "3" });
        Assert.Throws<NotSupportedException>(() => PromptTemplateConfig.FromJson(json));

        // object
        json = CreateJson(new { p1 = "v1" });
        Assert.Throws<NotSupportedException>(() => PromptTemplateConfig.FromJson(json));
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
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
    public void DeserializingAutoSetServiceIdWhenNotProvided()
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
        Assert.Equal("service1", promptTemplateConfig.ExecutionSettings["service1"].ServiceId);
        Assert.Equal("service2", promptTemplateConfig.ExecutionSettings["service2"].ServiceId);
    }

    [Fact]
    public void DeserializingAutoSetServiceIdWhenDefault()
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
        Assert.Equal(PromptExecutionSettings.DefaultServiceId, promptTemplateConfig.DefaultExecutionSettings?.ServiceId);
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
    public void ItAddExecutionSettingsAndOverwriteServiceIdAsExpected()
    {
        // Arrange
        var promptTemplateConfig = new PromptTemplateConfig();
        var settings1 = new PromptExecutionSettings { ModelId = "model-service-3", ServiceId = "should not override" };

        // Act
        promptTemplateConfig.AddExecutionSettings(new PromptExecutionSettings { ModelId = "model1" });
        promptTemplateConfig.AddExecutionSettings(new PromptExecutionSettings { ModelId = "model2" }, "service1");
        promptTemplateConfig.AddExecutionSettings(new PromptExecutionSettings { ServiceId = "service2", ModelId = "model-service-2" }, "override");
        promptTemplateConfig.AddExecutionSettings(new PromptExecutionSettings { ServiceId = "service3", ModelId = "model-service-3" });
        promptTemplateConfig.AddExecutionSettings(settings1, "service4");

        // Assert
        // Overwrite with Default
        Assert.Equal("model1", promptTemplateConfig.ExecutionSettings["default"].ModelId);
        Assert.Equal("default", promptTemplateConfig.ExecutionSettings["default"].ServiceId);

        // Overwrite with ServiceId from Argument (Not Defaulting)
        Assert.Equal("model2", promptTemplateConfig.ExecutionSettings["service1"].ModelId);
        Assert.Equal("service1", promptTemplateConfig.ExecutionSettings["service1"].ServiceId);

        // Overwrite with ServiceId from Argument
        Assert.Equal("model-service-2", promptTemplateConfig.ExecutionSettings["override"].ModelId);
        Assert.Equal("override", promptTemplateConfig.ExecutionSettings["override"].ServiceId);

        // Don't override from argument and use ServiceId from ExecutionSettings
        Assert.Equal("model-service-3", promptTemplateConfig.ExecutionSettings["service3"].ModelId);
        Assert.Equal("service3", promptTemplateConfig.ExecutionSettings["service3"].ServiceId);

        // Don't change settings by reference (it was cloned)
        Assert.Equal("should not override", settings1.ServiceId);
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
        Assert.Equal("service1", promptTemplate.ExecutionSettings["service1"].ServiceId);
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

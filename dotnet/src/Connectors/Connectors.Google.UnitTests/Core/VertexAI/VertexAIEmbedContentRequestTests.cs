// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel.Connectors.Google.Core;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Core.VertexAI;

public sealed class VertexAIEmbedContentRequestTests
{
    private const string DimensionalityJsonPropertyName = "\"outputDimensionality\"";
    private const int Dimensions = 512;

    [Fact]
    public void FromTextReturnsValidRequestWithContent()
    {
        // Arrange
        const string Text = "sample text to embed";

        // Act
        var request = VertexAIEmbedContentRequest.FromText(Text);

        // Assert
        Assert.NotNull(request.Content);
        Assert.NotNull(request.Content.Parts);
        Assert.Single(request.Content.Parts);
        Assert.Equal(Text, request.Content.Parts[0].Text);
    }

    [Fact]
    public void FromTextSetsDimensionsToNullWhenNotProvided()
    {
        // Act
        var request = VertexAIEmbedContentRequest.FromText("sample text");

        // Assert
        Assert.Null(request.OutputDimensionality);
    }

    [Fact]
    public void FromTextJsonDoesNotIncludeDimensionsWhenNull()
    {
        // Act
        var request = VertexAIEmbedContentRequest.FromText("sample text");
        string json = JsonSerializer.Serialize(request);

        // Assert
        Assert.DoesNotContain(DimensionalityJsonPropertyName, json);
    }

    [Fact]
    public void FromTextSetsDimensionsWhenProvided()
    {
        // Act
        var request = VertexAIEmbedContentRequest.FromText("sample text", Dimensions);

        // Assert
        Assert.Equal(Dimensions, request.OutputDimensionality);
    }

    [Fact]
    public void FromTextJsonIncludesDimensionsWhenProvided()
    {
        // Act
        var request = VertexAIEmbedContentRequest.FromText("sample text", Dimensions);
        string json = JsonSerializer.Serialize(request);

        // Assert
        Assert.Contains($"{DimensionalityJsonPropertyName}:{Dimensions}", json);
    }

    [Theory]
    [InlineData("TaskType")]
    [InlineData("Task_Type")]
    [InlineData("taskType")]
    [InlineData("task_Type")]
    [InlineData("tasktype")]
    [InlineData("task_type")]
    public void FromTextShouldIncludeTaskTypeWhenProvided(string additionalPropertyKeyName)
    {
        // Arrange
        const string TaskType = "RETRIEVAL_DOCUMENT";
        var options = new EmbeddingGenerationOptions
        {
            AdditionalProperties = new AdditionalPropertiesDictionary
            {
                [additionalPropertyKeyName] = TaskType
            }
        };

        // Act
        var request = VertexAIEmbedContentRequest.FromText("sample text", Dimensions, options);
        string json = JsonSerializer.Serialize(request);

        // Assert
        Assert.Equal(TaskType, request.TaskType);
        Assert.Contains("\"taskType\":\"RETRIEVAL_DOCUMENT\"", json);
    }

    [Fact]
    public void FromTextShouldIncludeTitleWhenProvided()
    {
        // Arrange
        const string Title = "Document Title";
        var options = new EmbeddingGenerationOptions
        {
            AdditionalProperties = new AdditionalPropertiesDictionary
            {
                ["title"] = Title
            }
        };

        // Act
        var request = VertexAIEmbedContentRequest.FromText("sample text", Dimensions, options);
        string json = JsonSerializer.Serialize(request);

        // Assert
        Assert.Equal(Title, request.Title);
        Assert.Contains("\"title\":\"Document Title\"", json);
    }
}

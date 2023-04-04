// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Net.Http;
using Microsoft.SemanticKernel.Skills.OpenAPI.Extensions;
using Microsoft.SemanticKernel.Skills.OpenAPI.Model;
using Microsoft.SemanticKernel.Skills.OpenAPI.OpenApi;
using SemanticKernel.Skills.UnitTests.OpenAPI.TestSkills;
using Xunit;

namespace SemanticKernel.Skills.UnitTests.OpenAPI;

public class OpenApiDocumentParserTests
{
    [Fact]
    public void ItCanParsePutOperationBodyOfV20SpecSuccessfully()
    {
        //Arrange
        using var stream = ResourceSkillsProvider.LoadFromResource("v2_0.operation.json");

        var sut = new OpenApiDocumentParser();

        //Act
        var operations = sut.Parse(stream);

        //Assert
        Assert.NotNull(operations);
        Assert.True(operations.Any());

        var putOperation = operations.Single(o => o.Id == "SetSecret");
        Assert.NotNull(putOperation);

        var payload = putOperation.Payload;
        Assert.NotNull(payload);
        Assert.Equal("application/json", payload.MediaType);

        var properties = payload.Properties;
        Assert.NotNull(properties);
        Assert.Equal(2, properties.Count);

        var valueProperty = properties.FirstOrDefault(p => p.Name == "value");
        Assert.NotNull(valueProperty);
        Assert.True(valueProperty.IsRequired);
        Assert.Equal("The value of the secret.", valueProperty.Description);
        Assert.NotNull(valueProperty.Properties);
        Assert.False(valueProperty.Properties.Any());

        var attributesProperty = properties.FirstOrDefault(p => p.Name == "attributes");
        Assert.NotNull(attributesProperty);
        Assert.False(attributesProperty.IsRequired);
        Assert.Equal("attributes", attributesProperty.Description);
        Assert.NotNull(attributesProperty.Properties);
        Assert.True(attributesProperty.Properties.Any());

        var enabledProperty = attributesProperty.Properties.FirstOrDefault(p => p.Name == "enabled");
        Assert.NotNull(enabledProperty);
        Assert.False(enabledProperty.IsRequired);
        Assert.Equal("Determines whether the object is enabled.", enabledProperty.Description);
        Assert.NotNull(enabledProperty.Properties);
        Assert.False(enabledProperty.Properties.Any());
    }

    [Fact]
    public void ItCanParsePutOperationMetadataOfV20SpecSuccessfully()
    {
        //Arrange
        using var stream = ResourceSkillsProvider.LoadFromResource("v2_0.operation.json");

        var sut = new OpenApiDocumentParser();

        //Act
        var operations = sut.Parse(stream);

        //Assert
        Assert.NotNull(operations);
        Assert.True(operations.Any());

        var putOperation = operations.Single(o => o.Id == "SetSecret");
        Assert.NotNull(putOperation);
        Assert.Equal("Sets a secret in a specified key vault.", putOperation.Description);
        Assert.Equal("https://my-key-vault.vault.azure.net", putOperation.ServerUrl);
        Assert.Equal(HttpMethod.Put, putOperation.Method);
        Assert.Equal("/secrets/{secret-name}", putOperation.Path);

        var parameters = putOperation.GetParameters();
        Assert.NotNull(parameters);
        Assert.Equal(5, parameters.Count);

        var pathParameter = parameters.Single(p => p.Name == "secret-name"); //'secret-name' path parameter.
        Assert.True(pathParameter.IsRequired);
        Assert.Equal(RestApiOperationParameterLocation.Path, pathParameter.Location);
        Assert.Null(pathParameter.DefaultValue);

        var apiVersionParameter = parameters.Single(p => p.Name == "api-version"); //'api-version' query string parameter.
        Assert.True(apiVersionParameter.IsRequired);
        Assert.Equal(RestApiOperationParameterLocation.Query, apiVersionParameter.Location);
        Assert.Equal("7.0", apiVersionParameter.DefaultValue);

        var serverUrlParameter = parameters.Single(p => p.Name == "server-url"); //'server-url' artificial parameter.
        Assert.False(serverUrlParameter.IsRequired);
        Assert.Equal(RestApiOperationParameterLocation.Path, serverUrlParameter.Location);
        Assert.Equal("https://my-key-vault.vault.azure.net", serverUrlParameter.DefaultValue);

        var valueParameter = parameters.Single(p => p.Name == "value"); //'value' body parameter.
        Assert.True(valueParameter.IsRequired);
        Assert.Equal(RestApiOperationParameterLocation.Body, valueParameter.Location);
        Assert.Null(valueParameter.DefaultValue);
        Assert.Equal("The value of the secret.", valueParameter.Description);

        var enabledParameter = parameters.Single(p => p.Name == "enabled"); //'attributes.enabled' body parameter.
        Assert.False(enabledParameter.IsRequired);
        Assert.Equal(RestApiOperationParameterLocation.Body, enabledParameter.Location);
        Assert.Null(enabledParameter.DefaultValue);
        Assert.Equal("Determines whether the object is enabled.", enabledParameter.Description);
    }
}

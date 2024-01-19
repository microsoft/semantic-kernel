// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi;

public class RestApiOperationExtensionsTests
{
    [Theory]
    [InlineData("PUT")]
    [InlineData("POST")]
    public void ItShouldAddPayloadAndContentTypeParametersByDefault(string method)
    {
        //Arrange
        var payload = CreateTestJsonPayload();

        var operation = CreateTestOperation(method, payload);

        //Act
        var parameters = operation.GetParameters(addPayloadParamsFromMetadata: false);

        //Assert
        Assert.NotNull(parameters);

        var payloadParam = parameters.FirstOrDefault(p => p.Name == "payload");
        Assert.NotNull(payloadParam);
        Assert.Equal("object", payloadParam.Type);
        Assert.True(payloadParam.IsRequired);
        Assert.Equal("REST API request body.", payloadParam.Description);

        var contentTypeParam = parameters.FirstOrDefault(p => p.Name == "content-type");
        Assert.NotNull(contentTypeParam);
        Assert.Equal("string", contentTypeParam.Type);
        Assert.False(contentTypeParam.IsRequired);
        Assert.Equal("Content type of REST API request body.", contentTypeParam.Description);
    }

    [Theory]
    [InlineData("PUT")]
    [InlineData("POST")]
    public void ItShouldAddPayloadAndContentTypeParametersWhenSpecified(string method)
    {
        //Arrange
        var payload = CreateTestJsonPayload();

        var operation = CreateTestOperation(method, payload);

        //Act
        var parameters = operation.GetParameters(addPayloadParamsFromMetadata: false);

        //Assert
        Assert.NotNull(parameters);

        var payloadProp = parameters.FirstOrDefault(p => p.Name == "payload");
        Assert.NotNull(payloadProp);
        Assert.Equal("object", payloadProp.Type);
        Assert.True(payloadProp.IsRequired);
        Assert.Equal("REST API request body.", payloadProp.Description);

        var contentTypeProp = parameters.FirstOrDefault(p => p.Name == "content-type");
        Assert.NotNull(contentTypeProp);
        Assert.Equal("string", contentTypeProp.Type);
        Assert.False(contentTypeProp.IsRequired);
        Assert.Equal("Content type of REST API request body.", contentTypeProp.Description);
    }

    [Theory]
    [InlineData("PUT")]
    [InlineData("POST")]
    public void ItShouldAddPayloadAndContentTypePropertiesForPlainTextContentType(string method)
    {
        //Arrange
        var payload = CreateTestTextPayload();

        var operation = CreateTestOperation(method, payload);

        //Act
        var parameters = operation.GetParameters(addPayloadParamsFromMetadata: false);

        //Assert
        Assert.NotNull(parameters);

        var payloadParam = parameters.FirstOrDefault(p => p.Name == "payload");
        Assert.NotNull(payloadParam);
        Assert.Equal("string", payloadParam.Type);
        Assert.True(payloadParam.IsRequired);
        Assert.Equal("REST API request body.", payloadParam.Description);

        var contentTypeParam = parameters.FirstOrDefault(p => p.Name == "content-type");
        Assert.NotNull(contentTypeParam);
        Assert.Equal("string", contentTypeParam.Type);
        Assert.False(contentTypeParam.IsRequired);
        Assert.Equal("Content type of REST API request body.", contentTypeParam.Description);
    }

    [Theory]
    [InlineData("PUT")]
    [InlineData("POST")]
    public void ItShouldAddPayloadAndContentTypePropertiesIfParametersFromPayloadMetadataAreNotRequired(string method)
    {
        //Arrange
        var payload = CreateTestJsonPayload();

        var operation = CreateTestOperation(method, payload);

        //Act
        var parameters = operation.GetParameters(addPayloadParamsFromMetadata: false);

        //Assert
        Assert.NotNull(parameters);

        var payloadParam = parameters.FirstOrDefault(p => p.Name == "payload");
        Assert.NotNull(payloadParam);
        Assert.Equal("object", payloadParam.Type);
        Assert.True(payloadParam.IsRequired);
        Assert.Equal("REST API request body.", payloadParam.Description);

        var contentTypeParam = parameters.FirstOrDefault(p => p.Name == "content-type");
        Assert.NotNull(contentTypeParam);
        Assert.Equal("string", contentTypeParam.Type);
        Assert.False(contentTypeParam.IsRequired);
        Assert.Equal("Content type of REST API request body.", contentTypeParam.Description);
    }

    [Theory]
    [InlineData("PUT")]
    [InlineData("POST")]
    public void ItShouldAddParametersDeclaredInPayloadMetadata(string method)
    {
        //Arrange
        var payload = CreateTestJsonPayload();

        var operation = CreateTestOperation(method, payload);

        //Act
        var parameters = operation.GetParameters(addPayloadParamsFromMetadata: true);

        //Assert
        Assert.NotNull(parameters);

        Assert.Equal(5, parameters.Count); //5 props from payload

        var name = parameters.FirstOrDefault(p => p.Name == "name");
        Assert.NotNull(name);
        Assert.Equal("string", name.Type);
        Assert.True(name.IsRequired);
        Assert.Equal("The name.", name.Description);

        var landmarks = parameters.FirstOrDefault(p => p.Name == "landmarks");
        Assert.NotNull(landmarks);
        Assert.Equal("array", landmarks.Type);
        Assert.False(landmarks.IsRequired);
        Assert.Equal("The landmarks.", landmarks.Description);

        var leader = parameters.FirstOrDefault(p => p.Name == "leader");
        Assert.NotNull(leader);
        Assert.Equal("string", leader.Type);
        Assert.True(leader.IsRequired);
        Assert.Equal("The leader.", leader.Description);

        var population = parameters.FirstOrDefault(p => p.Name == "population");
        Assert.NotNull(population);
        Assert.Equal("integer", population.Type);
        Assert.True(population.IsRequired);
        Assert.Equal("The population.", population.Description);

        var hasMagicWards = parameters.FirstOrDefault(p => p.Name == "hasMagicWards");
        Assert.NotNull(hasMagicWards);
        Assert.Equal("boolean", hasMagicWards.Type);
        Assert.False(hasMagicWards.IsRequired);
        Assert.Null(hasMagicWards.Description);
    }

    [Theory]
    [InlineData("PUT")]
    [InlineData("POST")]
    public void ItShouldAddNamespaceToParametersDeclaredInPayloadMetadata(string method)
    {
        //Arrange
        var payload = CreateTestJsonPayload();

        var operation = CreateTestOperation(method, payload);

        //Act
        var parameters = operation.GetParameters(addPayloadParamsFromMetadata: true, enablePayloadNamespacing: true);

        //Assert
        Assert.NotNull(parameters);

        Assert.Equal(5, parameters.Count); //5 props from payload

        var name = parameters.FirstOrDefault(p => p.Name == "name");
        Assert.NotNull(name);
        Assert.Equal("string", name.Type);
        Assert.True(name.IsRequired);
        Assert.Equal("The name.", name.Description);

        var landmarks = parameters.FirstOrDefault(p => p.Name == "location.landmarks");
        Assert.NotNull(landmarks);
        Assert.Equal("array", landmarks.Type);
        Assert.False(landmarks.IsRequired);
        Assert.Equal("The landmarks.", landmarks.Description);

        var leader = parameters.FirstOrDefault(p => p.Name == "rulingCouncil.leader");
        Assert.NotNull(leader);
        Assert.Equal("string", leader.Type);
        Assert.True(leader.IsRequired);
        Assert.Equal("The leader.", leader.Description);

        var population = parameters.FirstOrDefault(p => p.Name == "population");
        Assert.NotNull(population);
        Assert.Equal("integer", population.Type);
        Assert.True(population.IsRequired);
        Assert.Equal("The population.", population.Description);

        var hasMagicWards = parameters.FirstOrDefault(p => p.Name == "hasMagicWards");
        Assert.NotNull(hasMagicWards);
        Assert.Equal("boolean", hasMagicWards.Type);
        Assert.False(hasMagicWards.IsRequired);
        Assert.Null(hasMagicWards.Description);
    }

    [Theory]
    [InlineData("PUT")]
    [InlineData("POST")]
    public void ItShouldThrowExceptionIfPayloadMetadataDescribingParametersIsMissing(string method)
    {
        //Arrange
        var operation = CreateTestOperation(method, null);

        //Act
        Assert.Throws<KernelException>(() => operation.GetParameters(addPayloadParamsFromMetadata: true, enablePayloadNamespacing: true));
    }

    [Theory]
    [InlineData("PUT")]
    [InlineData("POST")]
    public void ItShouldSetAlternativeNameToParametersForPutAndPostOperation(string method)
    {
        //Arrange
        var latitude = new RestApiOperationPayloadProperty("location.latitude", "number", false, new List<RestApiOperationPayloadProperty>());
        var place = new RestApiOperationPayloadProperty("place", "string", true, new List<RestApiOperationPayloadProperty>());

        var payload = new RestApiOperationPayload("application/json", new[] { place, latitude });

        var operation = CreateTestOperation(method, payload);

        //Act
        var parameters = operation.GetParameters(addPayloadParamsFromMetadata: true);

        //Assert
        Assert.NotNull(parameters);

        var placeProp = parameters.FirstOrDefault(p => p.Name == "place");
        Assert.NotNull(placeProp);
        Assert.Equal("place", placeProp.AlternativeName);

        var personNameProp = parameters.FirstOrDefault(p => p.Name == "location.latitude");
        Assert.NotNull(personNameProp);
        Assert.Equal("location_latitude", personNameProp.AlternativeName);
    }

    private static RestApiOperation CreateTestOperation(string method, RestApiOperationPayload? payload = null, Uri? url = null)
    {
        return new RestApiOperation(
                    id: "fake-id",
                    serverUrl: url,
                    path: "fake-path",
                    method: new HttpMethod(method),
                    description: "fake-description",
                    parameters: new List<RestApiOperationParameter>(),
                    payload: payload);
    }

    private static RestApiOperationPayload CreateTestJsonPayload()
    {
        var name = new RestApiOperationPayloadProperty(
            name: "name",
            type: "string",
            isRequired: true,
            properties: new List<RestApiOperationPayloadProperty>(),
            description: "The name.");

        var leader = new RestApiOperationPayloadProperty(
            name: "leader",
            type: "string",
            isRequired: true,
            properties: new List<RestApiOperationPayloadProperty>(),
            description: "The leader.");

        var landmarks = new RestApiOperationPayloadProperty(
            name: "landmarks",
            type: "array",
            isRequired: false,
            properties: new List<RestApiOperationPayloadProperty>(),
            description: "The landmarks.");

        var location = new RestApiOperationPayloadProperty(
            name: "location",
            type: "object",
            isRequired: true,
            properties: new[] { landmarks },
            description: "The location.");

        var rulingCouncil = new RestApiOperationPayloadProperty(
            name: "rulingCouncil",
            type: "object",
            isRequired: true,
            properties: new[] { leader },
            description: "The ruling council.");

        var population = new RestApiOperationPayloadProperty(
            name: "population",
            type: "integer",
            isRequired: true,
            properties: new List<RestApiOperationPayloadProperty>(),
            description: "The population.");

        var hasMagicWards = new RestApiOperationPayloadProperty(
            name: "hasMagicWards",
            type: "boolean",
            isRequired: false,
            properties: new List<RestApiOperationPayloadProperty>());

        return new RestApiOperationPayload("application/json", new[] { name, location, rulingCouncil, population, hasMagicWards });
    }

    private static RestApiOperationPayload CreateTestTextPayload()
    {
        return new RestApiOperationPayload("text/plain", new List<RestApiOperationPayloadProperty>());
    }
}

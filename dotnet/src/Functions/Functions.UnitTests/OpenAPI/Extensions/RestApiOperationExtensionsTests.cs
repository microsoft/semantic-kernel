// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Functions.OpenAPI.Model;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenAPI.Extensions;
public class RestApiOperationExtensionsTests
{
    [Theory]
    [InlineData("PUT")]
    [InlineData("POST")]
    [InlineData("GET")]
    public void ItShouldAddServerUrlParameterWithDefaultValueFromOperation(string method)
    {
        //Arrange
        var payload = CreateTestJsonPayload();

        var operation = CreateTestOperation(method, payload, new Uri("https://fake-random-test-host"));

        //Act
        var parameters = operation.GetParameters();

        //Assert
        Assert.NotNull(parameters);

        var serverUrl = parameters.FirstOrDefault(p => p.Name == "server-url");
        Assert.NotNull(serverUrl);
        Assert.Equal("string", serverUrl.Type);
        Assert.False(serverUrl.IsRequired);
        Assert.Equal("https://fake-random-test-host/", serverUrl.DefaultValue);
    }

    [Theory]
    [InlineData("PUT")]
    [InlineData("POST")]
    [InlineData("GET")]
    public void ItShouldAddServerUrlParameterWithDefaultValueFromOverrideParameter(string method)
    {
        //Arrange
        var payload = CreateTestJsonPayload();

        var operation = CreateTestOperation(method, payload);

        //Act
        var parameters = operation.GetParameters(serverUrlOverride: new Uri("https://fake-random-test-host"));

        //Assert
        Assert.NotNull(parameters);

        var serverUrl = parameters.FirstOrDefault(p => p.Name == "server-url");
        Assert.NotNull(serverUrl);
        Assert.Equal("string", serverUrl.Type);
        Assert.False(serverUrl.IsRequired);
        Assert.Equal("https://fake-random-test-host/", serverUrl.DefaultValue);
    }

    [Theory]
    [InlineData("PUT")]
    [InlineData("POST")]
    public void ItShouldAddPayloadAndContentTypeParametersByDefault(string method)
    {
        //Arrange
        var payload = CreateTestJsonPayload();

        var operation = CreateTestOperation(method, payload);

        //Act
        var parameters = operation.GetParameters();

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
        var parameters = operation.GetParameters();

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

        Assert.Equal(6, parameters.Count); //5(props from payload) + 1('server-url' property)

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

        Assert.Equal(6, parameters.Count); //5(props from payload) + 1('server-url' property)

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
        Assert.Throws<SKException>(() => operation.GetParameters(addPayloadParamsFromMetadata: true, enablePayloadNamespacing: true));
    }

    [Fact]
    public void ItShouldSetAlternativeNameToParametersForGetOperation()
    {
        //Arrange
        var operation = CreateTestOperation("GET");

        //Act
        var parameters = operation.GetParameters(addPayloadParamsFromMetadata: true);

        //Assert
        Assert.NotNull(parameters);

        var serverUrlProp = parameters.FirstOrDefault(p => p.Name == "server-url");
        Assert.NotNull(serverUrlProp);
        Assert.Equal("server_url", serverUrlProp.AlternativeName);
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

        var serverUrlProp = parameters.FirstOrDefault(p => p.Name == "server-url");
        Assert.NotNull(serverUrlProp);
        Assert.Equal("server_url", serverUrlProp.AlternativeName);

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
                    headers: new Dictionary<string, string>(),
                    payload: payload);
    }

    private static RestApiOperationPayload CreateTestJsonPayload()
    {
        var name = new RestApiOperationPayloadProperty("name", "string", true, new List<RestApiOperationPayloadProperty>(), "The name.");

        var leader = new RestApiOperationPayloadProperty("leader", "string", true, new List<RestApiOperationPayloadProperty>(), "The leader.");

        var landmarks = new RestApiOperationPayloadProperty("landmarks", "array", false, new List<RestApiOperationPayloadProperty>(), "The landmarks.");
        var location = new RestApiOperationPayloadProperty("location", "object", true, new[] { landmarks }, "The location.");

        var rulingCouncil = new RestApiOperationPayloadProperty("rulingCouncil", "object", true, new[] { leader }, "The ruling council.");

        var population = new RestApiOperationPayloadProperty("population", "integer", true, new List<RestApiOperationPayloadProperty>(), "The population.");

        var hasMagicWards = new RestApiOperationPayloadProperty("hasMagicWards", "boolean", false, new List<RestApiOperationPayloadProperty>());

        return new RestApiOperationPayload("application/json", new[] { name, location, rulingCouncil, population, hasMagicWards });
    }

    private static RestApiOperationPayload CreateTestTextPayload()
    {
        return new RestApiOperationPayload("text/plain", new List<RestApiOperationPayloadProperty>());
    }
}

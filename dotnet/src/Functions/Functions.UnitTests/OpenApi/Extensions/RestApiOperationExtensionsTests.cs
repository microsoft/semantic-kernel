// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
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
    public void ItShouldSetArgumentNameToPayloadParameters(string method)
    {
        //Arrange
        var latitude = new RestApiPayloadProperty("location.latitude", "number", false, []);
        var place = new RestApiPayloadProperty("place", "string", true, []);

        var payload = new RestApiPayload("application/json", [place, latitude]);

        var operation = CreateTestOperation(method, payload);

        //Act
        var parameters = operation.GetParameters(addPayloadParamsFromMetadata: true);

        //Assert
        Assert.NotNull(parameters);

        var placeProp = parameters.FirstOrDefault(p => p.Name == "place");
        Assert.NotNull(placeProp);
        Assert.Equal("place", placeProp.ArgumentName);

        var personNameProp = parameters.FirstOrDefault(p => p.Name == "location.latitude");
        Assert.NotNull(personNameProp);
        Assert.Equal("location_latitude", personNameProp.ArgumentName);
    }

    [Theory]
    [InlineData("PUT")]
    [InlineData("POST")]
    public void ItShouldNotSetArgumentNameToPayloadParametersIfItIsAlreadyProvided(string method)
    {
        //Arrange
        var latitude = new RestApiPayloadProperty("location.latitude", "number", false, []) { ArgumentName = "alt.location.latitude" };
        var place = new RestApiPayloadProperty("place", "string", true, []) { ArgumentName = "alt+place" };

        var payload = new RestApiPayload("application/json", [place, latitude]);

        var operation = CreateTestOperation(method, payload);

        //Act
        var parameters = operation.GetParameters(addPayloadParamsFromMetadata: true);

        //Assert
        Assert.NotNull(parameters);

        var placeProp = parameters.FirstOrDefault(p => p.Name == "place");
        Assert.NotNull(placeProp);
        Assert.Equal("alt+place", placeProp.ArgumentName);

        var personNameProp = parameters.FirstOrDefault(p => p.Name == "location.latitude");
        Assert.NotNull(personNameProp);
        Assert.Equal("alt.location.latitude", personNameProp.ArgumentName);
    }

    [Fact]
    public void ItShouldSetArgumentNameToNonPayloadParameters()
    {
        //Arrange
        List<RestApiParameter> parameters = [
            new RestApiParameter("p-1", "number", false, false, RestApiParameterLocation.Path),
            new RestApiParameter("p$2", "string", false, false, RestApiParameterLocation.Query),
            new RestApiParameter("p3", "number", false, false, RestApiParameterLocation.Header)
        ];

        var operation = CreateTestOperation("GET", parameters: parameters);

        //Act
        var processedParameters = operation.GetParameters();

        //Assert
        Assert.NotNull(processedParameters);

        var pathParameter = processedParameters.Single(p => p.Name == "p-1");
        Assert.NotNull(pathParameter);
        Assert.Equal("p_1", pathParameter.ArgumentName);

        var queryStringParameter = processedParameters.Single(p => p.Name == "p$2");
        Assert.NotNull(queryStringParameter);
        Assert.Equal("p_2", queryStringParameter.ArgumentName);

        var headerParameter = processedParameters.Single(p => p.Name == "p3");
        Assert.NotNull(headerParameter);
        Assert.Equal("p3", headerParameter.ArgumentName);
    }

    [Fact]
    public void ItShouldNotSetArgumentNameToNonPayloadParametersIfItIsAlreadyProvided()
    {
        //Arrange
        List<RestApiParameter> parameters = [
            new RestApiParameter("p-1", "number", false, false, RestApiParameterLocation.Path) { ArgumentName = "alt.p1" },
            new RestApiParameter("p$2", "string", false, false, RestApiParameterLocation.Query) { ArgumentName = "alt.p2" },
            new RestApiParameter("p3", "number", false, false, RestApiParameterLocation.Header) { ArgumentName = "alt.p3" }
        ];

        var operation = CreateTestOperation("GET", parameters: parameters);

        //Act
        var processedParameters = operation.GetParameters();

        //Assert
        Assert.NotNull(processedParameters);

        var pathParameter = processedParameters.Single(p => p.Name == "p-1");
        Assert.NotNull(pathParameter);
        Assert.Equal("alt.p1", pathParameter.ArgumentName);

        var queryStringParameter = processedParameters.Single(p => p.Name == "p$2");
        Assert.NotNull(queryStringParameter);
        Assert.Equal("alt.p2", queryStringParameter.ArgumentName);

        var headerParameter = processedParameters.Single(p => p.Name == "p3");
        Assert.NotNull(headerParameter);
        Assert.Equal("alt.p3", headerParameter.ArgumentName);
    }

    private static RestApiOperation CreateTestOperation(string method, RestApiPayload? payload = null, Uri? url = null, List<RestApiParameter>? parameters = null)
    {
        return new RestApiOperation(
            id: "fake-id",
            servers: [new(url?.AbsoluteUri)],
            path: "fake-path",
            method: new HttpMethod(method),
            description: "fake-description",
            parameters: parameters ?? [],
            responses: new Dictionary<string, RestApiExpectedResponse>(),
            securityRequirements: [],
            payload: payload);
    }

    private static RestApiPayload CreateTestJsonPayload()
    {
        var name = new RestApiPayloadProperty(
            name: "name",
            type: "string",
            isRequired: true,
            properties: [],
            description: "The name.");

        var leader = new RestApiPayloadProperty(
            name: "leader",
            type: "string",
            isRequired: true,
            properties: [],
            description: "The leader.");

        var landmarks = new RestApiPayloadProperty(
            name: "landmarks",
            type: "array",
            isRequired: false,
            properties: [],
            description: "The landmarks.");

        var location = new RestApiPayloadProperty(
            name: "location",
            type: "object",
            isRequired: true,
            properties: [landmarks],
            description: "The location.");

        var rulingCouncil = new RestApiPayloadProperty(
            name: "rulingCouncil",
            type: "object",
            isRequired: true,
            properties: [leader],
            description: "The ruling council.");

        var population = new RestApiPayloadProperty(
            name: "population",
            type: "integer",
            isRequired: true,
            properties: [],
            description: "The population.");

        var hasMagicWards = new RestApiPayloadProperty(
            name: "hasMagicWards",
            type: "boolean",
            isRequired: false,
            properties: []);

        return new RestApiPayload("application/json", [name, location, rulingCouncil, population, hasMagicWards]);
    }

    private static RestApiPayload CreateTestTextPayload()
    {
        return new RestApiPayload("text/plain", []);
    }
}

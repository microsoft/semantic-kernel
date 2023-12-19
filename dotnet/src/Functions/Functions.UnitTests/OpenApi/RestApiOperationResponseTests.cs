// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using SemanticKernel.Functions.UnitTests.OpenApi.TestResponses;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi;

public class RestApiOperationResponseTests
{
    [Fact]
    public void ItShouldValidateStringContentWithNoSchema()
    {
        //Arrange
        var response = new RestApiOperationResponse("fake-content", "fake-content-type");

        //Act
        var result = response.IsValid();

        //Assert
        Assert.True(result);
    }

    [Fact]
    public void ItShouldValidateByteContentTWithNoSchema()
    {
        //Arrange
        var response = new RestApiOperationResponse(new byte[] { 00, 01, 02 }, "fake-content-type");

        //Act
        var result = response.IsValid();

        //Assert
        Assert.True(result);
    }

    [Theory]
    [InlineData("fake-content", "application/json", "{\"type\": \"string\"}")]
    [InlineData("{\"fake\": \"content\"}", "text/plain", "{\"type\": \"string\"}")]
    [InlineData("{\"fake\": \"content\"}", "application/json", "{\"type\": \"string\"}")]
    public void ItShouldFailValidationWithSchema(string content, string contentType, string schemaJson)
    {
        //Arrange
        var response = new RestApiOperationResponse(content, contentType, KernelJsonSchema.Parse(schemaJson));

        //Act
        var result = response.IsValid();

        //Assert
        Assert.False(result);
    }

    [Theory]
    [InlineData("\"fake-content\"", "application/json", "{\"type\": \"string\"}")]
    [InlineData("fake-content", "text/plain", "{\"type\": \"string\"}")]
    [InlineData("fake-content", "application/xml", "{\"type\": \"string\"}")]
    [InlineData("fake-content", "image", "{\"type\": \"string\"}")]
    public void ItShouldPassValidationWithSchema(string content, string contentType, string schemaJson)
    {
        //Arrange
        var response = new RestApiOperationResponse(content, contentType, KernelJsonSchema.Parse(schemaJson));

        //Act
        var result = response.IsValid();

        //Assert
        Assert.True(result);
    }

    [Theory]
    [InlineData("ValidProductContent.json", "application/json", "ObjectResponseSchema.json")]
    [InlineData("ValidProductContent.json", "application/json", "ProductResponseSchema.json")]
    public void IsValidShouldBeTrue(string contentFileName, string contentType, string schemaJsonFilename)
    {
        //Arrange
        var contentText = ResourceResponseProvider.LoadFromResource(contentFileName);
        var productJson = ResourceResponseProvider.LoadFromResource(schemaJsonFilename);
        var response = new RestApiOperationResponse(contentText, contentType, KernelJsonSchema.Parse(productJson));

        //Act
        var result = response.IsValid();

        //Assert
        Assert.True(result);
    }

    [Theory]
    [InlineData("NotProductContent.json", "application/json", "ProductResponseSchema.json")]
    [InlineData("InvalidProductContent.json", "application/json", "ProductResponseSchema.json")]
    public void IsValidShouldBeFalse(string contentFileName, string contentType, string schemaJsonFilename)
    {
        //Arrange
        var contentText = ResourceResponseProvider.LoadFromResource(contentFileName);
        var productJson = ResourceResponseProvider.LoadFromResource(schemaJsonFilename);
        var response = new RestApiOperationResponse(contentText, contentType, KernelJsonSchema.Parse(productJson));

        //Act
        var result = response.IsValid();

        //Assert
        Assert.False(result);
    }
}

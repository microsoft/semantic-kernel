// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Functions.OpenAPI.Model;
using Microsoft.SemanticKernel.Functions.OpenAPI.OpenApi;
using SemanticKernel.Functions.UnitTests.OpenAPI.TestPlugins;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenAPI;

public sealed class OpenApiDocumentParserV20Tests : IDisposable
{
    /// <summary>
    /// System under test - an instance of OpenApiDocumentParser class.
    /// </summary>
    private readonly OpenApiDocumentParser _sut;

    /// <summary>
    /// OpenAPI document stream.
    /// </summary>
    private readonly Stream _openApiDocument;

    /// <summary>
    /// Creates an instance of a <see cref="OpenApiDocumentParserV20Tests"/> class.
    /// </summary>
    public OpenApiDocumentParserV20Tests()
    {
        this._openApiDocument = ResourcePluginsProvider.LoadFromResource("documentV2_0.json");

        this._sut = new OpenApiDocumentParser();
    }

    [Fact]
    public async Task ItCanParsePutOperationBodySuccessfullyAsync()
    {
        // Act
        var operations = await this._sut.ParseAsync(this._openApiDocument);

        // Assert
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
        Assert.Equal("string", valueProperty.Type);
        Assert.NotNull(valueProperty.Properties);
        Assert.False(valueProperty.Properties.Any());

        var attributesProperty = properties.FirstOrDefault(p => p.Name == "attributes");
        Assert.NotNull(attributesProperty);
        Assert.False(attributesProperty.IsRequired);
        Assert.Equal("attributes", attributesProperty.Description);
        Assert.Equal("object", attributesProperty.Type);
        Assert.NotNull(attributesProperty.Properties);
        Assert.True(attributesProperty.Properties.Any());

        var enabledProperty = attributesProperty.Properties.FirstOrDefault(p => p.Name == "enabled");
        Assert.NotNull(enabledProperty);
        Assert.False(enabledProperty.IsRequired);
        Assert.Equal("Determines whether the object is enabled.", enabledProperty.Description);
        Assert.Equal("boolean", enabledProperty.Type);
        Assert.False(enabledProperty.Properties?.Any());
    }

    [Fact]
    public async Task ItCanParsePutOperationMetadataSuccessfullyAsync()
    {
        // Act
        var operations = await this._sut.ParseAsync(this._openApiDocument);

        // Assert
        Assert.NotNull(operations);
        Assert.True(operations.Any());

        var putOperation = operations.Single(o => o.Id == "SetSecret");
        Assert.NotNull(putOperation);
        Assert.Equal("Sets a secret in a specified key vault.", putOperation.Description);
        Assert.Equal("https://my-key-vault.vault.azure.net/", putOperation.ServerUrl?.AbsoluteUri);
        Assert.Equal(HttpMethod.Put, putOperation.Method);
        Assert.Equal("/secrets/{secret-name}", putOperation.Path);

        var parameters = putOperation.GetParameters();
        Assert.NotNull(parameters);
        Assert.True(parameters.Count >= 5);

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
        Assert.Equal("https://my-key-vault.vault.azure.net/", serverUrlParameter.DefaultValue);

        var payloadParameter = parameters.Single(p => p.Name == "payload"); //'payload' artificial parameter.
        Assert.True(payloadParameter.IsRequired);
        Assert.Equal(RestApiOperationParameterLocation.Body, payloadParameter.Location);
        Assert.Null(payloadParameter.DefaultValue);
        Assert.Equal("REST API request body.", payloadParameter.Description);

        var contentTypeParameter = parameters.Single(p => p.Name == "content-type"); //'content-type' artificial parameter.
        Assert.False(contentTypeParameter.IsRequired);
        Assert.Equal(RestApiOperationParameterLocation.Body, contentTypeParameter.Location);
        Assert.Null(contentTypeParameter.DefaultValue);
        Assert.Equal("Content type of REST API request body.", contentTypeParameter.Description);
    }

    [Fact]
    public async Task ItCanUseOperationSummaryAsync()
    {
        // Act
        var operations = await this._sut.ParseAsync(this._openApiDocument);

        // Assert
        Assert.NotNull(operations);
        Assert.True(operations.Any());

        var operation = operations.Single(o => o.Id == "Excuses");
        Assert.NotNull(operation);
        Assert.Equal("Turn a scenario into a creative or humorous excuse to send your boss", operation.Description);
    }

    [Fact]
    public async Task ItCanExtractSimpleTypeHeaderParameterMetadataSuccessfullyAsync()
    {
        // Act
        var operations = await this._sut.ParseAsync(this._openApiDocument);

        //Assert string header parameter metadata
        var accept = GetParameterMetadata(operations, "SetSecret", RestApiOperationParameterLocation.Header, "Accept");

        Assert.Equal("string", accept.Type);
        Assert.Equal("application/json", accept.DefaultValue);
        Assert.Equal("Indicates which content types, expressed as MIME types, the client is able to understand.", accept.Description);
        Assert.False(accept.IsRequired);

        //Assert integer header parameter metadata
        var apiVersion = GetParameterMetadata(operations, "SetSecret", RestApiOperationParameterLocation.Header, "X-API-Version");

        Assert.Equal("integer", apiVersion.Type);
        Assert.Equal("10", apiVersion.DefaultValue);
        Assert.Equal("Requested API version.", apiVersion.Description);
        Assert.True(apiVersion.IsRequired);
    }

    [Fact]
    public async Task ItCanExtractCsvStyleHeaderParameterMetadataSuccessfullyAsync()
    {
        // Act
        var operations = await this._sut.ParseAsync(this._openApiDocument);

        //Assert header parameters metadata
        var acceptParameter = GetParameterMetadata(operations, "SetSecret", RestApiOperationParameterLocation.Header, "X-Operation-Csv-Ids");

        Assert.Null(acceptParameter.DefaultValue);
        Assert.False(acceptParameter.IsRequired);
        Assert.Equal("array", acceptParameter.Type);
        Assert.Equal(RestApiOperationParameterStyle.Simple, acceptParameter.Style);
        Assert.Equal("The comma separated list of operation ids.", acceptParameter.Description);
        Assert.Equal("string", acceptParameter.ArrayItemType);
    }

    [Fact]
    public async Task ItCanExtractHeadersSuccessfullyAsync()
    {
        // Act
        var operations = await this._sut.ParseAsync(this._openApiDocument);

        // Assert
        Assert.True(operations.Any());

        var operation = operations.Single(o => o.Id == "SetSecret");
        Assert.NotNull(operation.Headers);
        Assert.Equal(3, operation.Headers.Count);

        Assert.True(operation.Headers.ContainsKey("Accept"));
        Assert.True(operation.Headers.ContainsKey("X-API-Version"));
        Assert.True(operation.Headers.ContainsKey("X-Operation-Csv-Ids"));
    }

    [Fact]
    public async Task ItCanExtractAllPathsAsOperationsAsync()
    {
        // Act
        var operations = await this._sut.ParseAsync(this._openApiDocument);

        // Assert
        Assert.Equal(3, operations.Count);
    }

    [Fact]
    public async Task ItCanParseOperationHavingTextPlainBodySuccessfullyAsync()
    {
        // Act
        var operations = await this._sut.ParseAsync(this._openApiDocument);

        // Assert
        Assert.NotNull(operations);
        Assert.True(operations.Any());

        var operation = operations.Single(o => o.Id == "Excuses");
        Assert.NotNull(operation);

        var payload = operation.Payload;
        Assert.NotNull(payload);
        Assert.Equal("text/plain", payload.MediaType);
        Assert.Equal("excuse event", payload.Description);

        var properties = payload.Properties;
        Assert.NotNull(properties);
        Assert.Equal(0, properties.Count);
    }

    [Fact]
    public async Task ItCanWorkWithDocumentsWithoutHostAndSchemaAttributesAsync()
    {
        //Arrange
        using var stream = OpenApiTestHelper.ModifyOpenApiDocument(this._openApiDocument, (doc) =>
        {
            doc.Remove("host");
            doc.Remove("schemes");
        });

        //Act
        var operations = await this._sut.ParseAsync(stream);

        //Assert
        Assert.All(operations, (op) => Assert.Null(op.ServerUrl));
    }

    private static RestApiOperationParameter GetParameterMetadata(IList<RestApiOperation> operations, string operationId,
        RestApiOperationParameterLocation location, string name)
    {
        Assert.True(operations.Any());

        var operation = operations.Single(o => o.Id == operationId);
        Assert.NotNull(operation.Parameters);
        Assert.True(operation.Parameters.Any());

        var parameters = operation.Parameters.Where(p => p.Location == location);

        var parameter = parameters.Single(p => p.Name == name);
        Assert.NotNull(parameter);

        return parameter;
    }

    public void Dispose()
    {
        this._openApiDocument.Dispose();
    }
}

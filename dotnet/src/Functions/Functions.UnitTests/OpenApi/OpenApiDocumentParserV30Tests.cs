// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.OpenApi.Models;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using SemanticKernel.Functions.UnitTests.OpenApi.TestPlugins;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi;

public sealed class OpenApiDocumentParserV30Tests : IDisposable
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
    /// Logger instance.
    /// </summary>
    private readonly ILogger _logger = new LoggerFactory().CreateLogger<OpenApiDocumentParserV30Tests>();

    /// <summary>
    /// Creates an instance of a <see cref="OpenApiDocumentParserV30Tests"/> class.
    /// </summary>
    public OpenApiDocumentParserV30Tests()
    {
        this._openApiDocument = ResourcePluginsProvider.LoadFromResource("documentV3_0.json");

        this._sut = new OpenApiDocumentParser();
    }

    [Fact]
    public async Task ItCanParsePutOperationBodySuccessfullyAsync()
    {
        // Act
        var restApi = await this._sut.ParseAsync(this._openApiDocument);

        // Assert
        Assert.NotNull(restApi.Operations);
        Assert.True(restApi.Operations.Any());

        var putOperation = restApi.Operations.Single(o => o.Id == "SetSecret");
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
        Assert.NotNull(valueProperty.Schema);
        Assert.Equal("string", valueProperty.Schema.RootElement.GetProperty("type").GetString());
        Assert.Equal("The value of the secret.", valueProperty.Schema.RootElement.GetProperty("description").GetString());

        var attributesProperty = properties.FirstOrDefault(p => p.Name == "attributes");
        Assert.NotNull(attributesProperty);
        Assert.False(attributesProperty.IsRequired);
        Assert.Equal("attributes", attributesProperty.Description);
        Assert.Equal("object", attributesProperty.Type);
        Assert.NotNull(attributesProperty.Properties);
        Assert.True(attributesProperty.Properties.Any());
        Assert.NotNull(attributesProperty.Schema);
        Assert.Equal("object", attributesProperty.Schema.RootElement.GetProperty("type").GetString());
        Assert.Equal("attributes", attributesProperty.Schema.RootElement.GetProperty("description").GetString());

        var enabledProperty = attributesProperty.Properties.FirstOrDefault(p => p.Name == "enabled");
        Assert.NotNull(enabledProperty);
        Assert.True(enabledProperty.IsRequired);
        Assert.Equal("Determines whether the object is enabled.", enabledProperty.Description);
        Assert.Equal("boolean", enabledProperty.Type);
        Assert.False(enabledProperty.Properties?.Any());
        Assert.NotNull(enabledProperty.Schema);
        Assert.Equal("boolean", enabledProperty.Schema.RootElement.GetProperty("type").GetString());
        Assert.Equal("Determines whether the object is enabled.", enabledProperty.Schema.RootElement.GetProperty("description").GetString());

        var encryptedProperty = attributesProperty.Properties.FirstOrDefault(p => p.Name == "encrypted");
        Assert.NotNull(encryptedProperty);
        Assert.False(encryptedProperty.IsRequired);
        Assert.Equal("Determines whether the object is encrypted.", encryptedProperty.Description);
        Assert.Equal("boolean", encryptedProperty.Type);
        Assert.False(encryptedProperty.Properties?.Any());
        Assert.NotNull(encryptedProperty.Schema);
        Assert.Equal("boolean", encryptedProperty.Schema.RootElement.GetProperty("type").GetString());
        Assert.Equal("Determines whether the object is encrypted.", encryptedProperty.Schema.RootElement.GetProperty("description").GetString());
    }

    [Fact]
    public async Task ItCanParsePutOperationMetadataSuccessfullyAsync()
    {
        // Act
        var restApi = await this._sut.ParseAsync(this._openApiDocument);

        // Assert
        Assert.NotNull(restApi.Operations);
        Assert.True(restApi.Operations.Any());

        var putOperation = restApi.Operations.Single(o => o.Id == "SetSecret");
        Assert.NotNull(putOperation);
        Assert.Equal("Sets a secret in a specified key vault.", putOperation.Description);
        Assert.Equal("https://my-key-vault.vault.azure.net", putOperation.Servers[0].Url);
        Assert.Equal(HttpMethod.Put, putOperation.Method);
        Assert.Equal("/secrets/{secret-name}", putOperation.Path);

        var parameters = putOperation.GetParameters(addPayloadParamsFromMetadata: false);
        Assert.NotNull(parameters);
        Assert.True(parameters.Count >= 5);

        var pathParameter = parameters.Single(p => p.Name == "secret-name"); //'secret-name' path parameter.
        Assert.True(pathParameter.IsRequired);
        Assert.Equal(RestApiParameterLocation.Path, pathParameter.Location);
        Assert.Null(pathParameter.DefaultValue);
        Assert.NotNull(pathParameter.Schema);
        Assert.Equal("string", pathParameter.Schema.RootElement.GetProperty("type").GetString());

        var apiVersionParameter = parameters.Single(p => p.Name == "api-version"); //'api-version' query string parameter.
        Assert.True(apiVersionParameter.IsRequired);
        Assert.Equal(RestApiParameterLocation.Query, apiVersionParameter.Location);
        Assert.Equal("7.0", apiVersionParameter.DefaultValue);
        Assert.NotNull(apiVersionParameter.Schema);
        Assert.Equal("string", apiVersionParameter.Schema.RootElement.GetProperty("type").GetString());
        Assert.Equal("7.0", apiVersionParameter.Schema.RootElement.GetProperty("default").GetString());

        var payloadParameter = parameters.Single(p => p.Name == "payload"); //'payload' artificial parameter.
        Assert.True(payloadParameter.IsRequired);
        Assert.Equal(RestApiParameterLocation.Body, payloadParameter.Location);
        Assert.Null(payloadParameter.DefaultValue);
        Assert.Equal("REST API request body.", payloadParameter.Description);
        Assert.NotNull(payloadParameter.Schema);
        Assert.Equal("object", payloadParameter.Schema.RootElement.GetProperty("type").GetString());

        var contentTypeParameter = parameters.Single(p => p.Name == "content-type"); //'content-type' artificial parameter.
        Assert.False(contentTypeParameter.IsRequired);
        Assert.Equal(RestApiParameterLocation.Body, contentTypeParameter.Location);
        Assert.Null(contentTypeParameter.DefaultValue);
        Assert.Equal("Content type of REST API request body.", contentTypeParameter.Description);
        Assert.Null(contentTypeParameter.Schema);
    }

    [Fact]
    public async Task ItCanExtractSimpleTypeHeaderParameterMetadataSuccessfullyAsync()
    {
        // Act
        var restApi = await this._sut.ParseAsync(this._openApiDocument);

        //Assert string header parameter metadata
        var accept = GetParameterMetadata(restApi.Operations, "SetSecret", RestApiParameterLocation.Header, "Accept");

        Assert.Equal("string", accept.Type);
        Assert.Equal("application/json", accept.DefaultValue);
        Assert.Equal("Indicates which content types, expressed as MIME types, the client is able to understand.", accept.Description);
        Assert.False(accept.IsRequired);

        //Assert integer header parameter metadata
        var apiVersion = GetParameterMetadata(restApi.Operations, "SetSecret", RestApiParameterLocation.Header, "X-API-Version");

        Assert.Equal("integer", apiVersion.Type);
        Assert.Equal(10, apiVersion.DefaultValue);
        Assert.Equal("Requested API version.", apiVersion.Description);
        Assert.True(apiVersion.IsRequired);
    }

    [Fact]
    public async Task ItCanUseOperationSummaryAsync()
    {
        // Act
        var restApi = await this._sut.ParseAsync(this._openApiDocument);

        // Assert
        Assert.NotNull(restApi.Operations);
        Assert.True(restApi.Operations.Any());

        var operation = restApi.Operations.Single(o => o.Id == "Excuses");
        Assert.NotNull(operation);
        Assert.Equal("Turn a scenario into a creative or humorous excuse to send your boss", operation.Description);
    }

    [Fact]
    public async Task ItCanExtractCsvStyleHeaderParameterMetadataSuccessfullyAsync()
    {
        // Act
        var restApi = await this._sut.ParseAsync(this._openApiDocument);

        //Assert header parameters metadata
        var acceptParameter = GetParameterMetadata(restApi.Operations, "SetSecret", RestApiParameterLocation.Header, "X-Operation-Csv-Ids");

        Assert.Null(acceptParameter.DefaultValue);
        Assert.False(acceptParameter.IsRequired);
        Assert.Equal("array", acceptParameter.Type);
        Assert.Equal(RestApiParameterStyle.Simple, acceptParameter.Style);
        Assert.Equal("The comma separated list of operation ids.", acceptParameter.Description);
        Assert.Equal("string", acceptParameter.ArrayItemType);
    }

    [Fact]
    public async Task ItCanExtractHeadersSuccessfullyAsync()
    {
        // Act
        var restApi = await this._sut.ParseAsync(this._openApiDocument);

        // Assert
        Assert.True(restApi.Operations.Any());

        var operation = restApi.Operations.Single(o => o.Id == "SetSecret");

        var headerParameters = operation.Parameters.Where(p => p.Location == RestApiParameterLocation.Header);

        Assert.NotNull(headerParameters);
        Assert.Equal(3, headerParameters.Count());

        Assert.Contains(headerParameters, (p) => p.Name == "Accept");
        Assert.Contains(headerParameters, (p) => p.Name == "X-API-Version");
        Assert.Contains(headerParameters, (p) => p.Name == "X-Operation-Csv-Ids");
    }

    [Fact]
    public async Task ItCanExtractAllPathsAsOperationsAsync()
    {
        // Act
        var restApi = await this._sut.ParseAsync(this._openApiDocument);

        // Assert
        Assert.Equal(8, restApi.Operations.Count);
    }

    [Fact]
    public async Task ItCanParseOperationHavingTextPlainBodySuccessfullyAsync()
    {
        // Act
        var restApi = await this._sut.ParseAsync(this._openApiDocument);

        // Assert
        Assert.NotNull(restApi.Operations);
        Assert.True(restApi.Operations.Any());

        var operation = restApi.Operations.Single(o => o.Id == "Excuses");
        Assert.NotNull(operation);

        var payload = operation.Payload;
        Assert.NotNull(payload);
        Assert.Equal("text/plain", payload.MediaType);
        Assert.Equal("excuse event", payload.Description);
        Assert.NotNull(payload.Schema);

        var properties = payload.Properties;
        Assert.NotNull(properties);
        Assert.Empty(properties);
    }

    [Fact]
    public async Task ItShouldThrowExceptionForNonCompliantDocumentAsync()
    {
        // Arrange
        var nonComplaintOpenApiDocument = ResourcePluginsProvider.LoadFromResource("nonCompliant_documentV3_0.json");

        // Act and Assert
        await Assert.ThrowsAsync<KernelException>(async () => await this._sut.ParseAsync(nonComplaintOpenApiDocument));
    }

    [Fact]
    public async Task ItShouldWorkWithNonCompliantDocumentIfAllowedAsync()
    {
        // Arrange
        var nonComplaintOpenApiDocument = ResourcePluginsProvider.LoadFromResource("nonCompliant_documentV3_0.json");

        // Act
        await this._sut.ParseAsync(nonComplaintOpenApiDocument, new OpenApiDocumentParserOptions() { IgnoreNonCompliantErrors = true });

        // Assert
        // The absence of any thrown exceptions serves as evidence of the functionality's success.
    }

    [Fact]
    public async Task ItCanWorkWithDocumentsWithoutServersAttributeAsync()
    {
        //Arrange
        using var stream = ModifyOpenApiDocument(this._openApiDocument, (doc) =>
        {
            doc.Remove("servers");
        });

        //Act
        var restApi = await this._sut.ParseAsync(stream);

        //Assert
        Assert.All(restApi.Operations, (op) => Assert.Empty(op.Servers));
    }

    [Fact]
    public async Task ItCanWorkWithDocumentsWithEmptyServersAttributeAsync()
    {
        //Arrange
        using var stream = ModifyOpenApiDocument(this._openApiDocument, (doc) =>
        {
            doc["servers"] = new JsonArray();
        });

        //Act
        var restApi = await this._sut.ParseAsync(stream);

        //Assert
        Assert.All(restApi.Operations, (op) => Assert.Empty(op.Servers));
    }

    [Theory]
    [InlineData("explodeFormParam")]
    [InlineData("anotherExplodeFormParam")]
    public async Task ItShouldSupportsAmpersandSeparatedParametersForFormStyleArrayQueryStringParametersAsync(string parameterName)
    {
        //Act
        var restApi = await this._sut.ParseAsync(this._openApiDocument);

        //Assert
        Assert.True(restApi.Operations.Any());

        var operation = restApi.Operations.Single(o => o.Id == "GetSecret");

        var explodeFormParam = operation.Parameters.Single(p => p.Name == parameterName);

        Assert.True(explodeFormParam.Expand);
    }

    [Fact]
    public async Task ItShouldSupportsCommaSeparatedValuesForFormStyleArrayQueryStringParametersAsync()
    {
        //Act
        var restApi = await this._sut.ParseAsync(this._openApiDocument);

        //Assert
        Assert.True(restApi.Operations.Any());

        var operation = restApi.Operations.Single(o => o.Id == "GetSecret");

        var explodeFormParam = operation.Parameters.Single(p => p.Name == "nonExplodeFormParam");

        Assert.False(explodeFormParam.Expand);
    }

    [Fact]
    public async Task ItCanParseResponsesSuccessfullyAsync()
    {
        //Act
        var restApi = await this._sut.ParseAsync(this._openApiDocument);

        //Assert
        Assert.NotNull(restApi.Operations);
        Assert.True(restApi.Operations.Any());

        var operation = restApi.Operations.Single(o => o.Id == "Excuses");
        Assert.NotNull(operation);

        operation.Responses.TryGetValue("200", out var response);
        Assert.NotNull(response);
        Assert.Equal("text/plain", response.MediaType);
        Assert.Equal("The OK response", response.Description);
        Assert.NotNull(response.Schema);
        Assert.Equal("string", response.Schema.RootElement.GetProperty("type").GetString());
        Assert.Equal(
            JsonSerializer.Serialize(KernelJsonSchema.Parse("""{"type": "string"}""")),
            JsonSerializer.Serialize(response.Schema));
    }

    [Fact]
    public async Task ItCanWorkWithDefaultParametersOfVariousTypesAsync()
    {
        //Act
        var restApi = await this._sut.ParseAsync(this._openApiDocument);

        //Assert
        Assert.NotNull(restApi.Operations);
        Assert.True(restApi.Operations.Any());

        var operation = restApi.Operations.Single(o => o.Id == "TestDefaultValues");
        Assert.NotNull(operation);

        var parameters = operation.GetParameters();
        Assert.Equal(11, parameters.Count);

        var stringParameter = parameters.Single(p => p.Name == "string-parameter");
        Assert.Equal("string-value", stringParameter.DefaultValue);

        var booleanParameter = parameters.Single(p => p.Name == "boolean-parameter");
        Assert.True(booleanParameter.DefaultValue is bool value);

        var integerParameter = parameters.Single(p => p.Name == "integer-parameter");
        Assert.True(integerParameter.DefaultValue is int);
        Assert.Equal(281, integerParameter.DefaultValue);

        var longParameter = parameters.Single(p => p.Name == "long-parameter");
        Assert.True(longParameter.DefaultValue is long);
        Assert.Equal((long)-2814, longParameter.DefaultValue);

        var floatParameter = parameters.Single(p => p.Name == "float-parameter");
        Assert.True(floatParameter.DefaultValue is float);
        Assert.Equal((float)12.01, floatParameter.DefaultValue);

        var doubleParameter = parameters.Single(p => p.Name == "double-parameter");
        Assert.True(doubleParameter.DefaultValue is double);
        Assert.Equal((double)-12.01, doubleParameter.DefaultValue);

        var encodedCharactersParameter = parameters.Single(p => p.Name == "encoded-characters-parameter");
        Assert.True(encodedCharactersParameter.DefaultValue is byte[]);
        Assert.Equal(new byte[] { 1, 2, 3, 4, 5 }, encodedCharactersParameter.DefaultValue);

        var binaryDataParameter = parameters.Single(p => p.Name == "binary-data-parameter");
        Assert.True(binaryDataParameter.DefaultValue is byte[]);
        Assert.Equal("23456"u8.ToArray(), binaryDataParameter.DefaultValue);

        var dateParameter = parameters.Single(p => p.Name == "date-parameter");
        Assert.True(dateParameter.DefaultValue is DateTime);
        Assert.Equal(new DateTime(2017, 07, 21), dateParameter.DefaultValue);

        var dateTimeParameter = parameters.Single(p => p.Name == "date-time-parameter");
        Assert.True(dateTimeParameter.DefaultValue is DateTimeOffset);
        Assert.Equal(new DateTimeOffset(2017, 07, 21, 17, 32, 28, TimeSpan.Zero), dateTimeParameter.DefaultValue);

        var passwordParameter = parameters.Single(p => p.Name == "password-parameter");
        Assert.True(passwordParameter.DefaultValue is string);
        Assert.Equal("password-value", passwordParameter.DefaultValue);
    }

    [Fact]
    public async Task ItCanParseRestApiInfoAsync()
    {
        //Act
        var restApi = await this._sut.ParseAsync(this._openApiDocument);

        //Assert
        Assert.NotNull(restApi.Info);
        Assert.NotNull(restApi.Info.Title);
        Assert.NotEmpty(restApi.Info.Title);
        Assert.NotNull(restApi.Info.Description);
        Assert.NotEmpty(restApi.Info.Description);
    }

    [Theory]
    [InlineData("string-parameter", "string", null)]
    [InlineData("boolean-parameter", "boolean", null)]
    [InlineData("number-parameter", "number", null)]
    [InlineData("float-parameter", "number", "float")]
    [InlineData("double-parameter", "number", "double")]
    [InlineData("integer-parameter", "integer", null)]
    [InlineData("int32-parameter", "integer", "int32")]
    [InlineData("int64-parameter", "integer", "int64")]
    public async Task ItCanParseParametersOfPrimitiveDataTypeAsync(string name, string type, string? format)
    {
        // Arrange & Act
        var restApiSpec = await this._sut.ParseAsync(this._openApiDocument);

        // Assert
        var parameters = restApiSpec.Operations.Single(o => o.Id == "TestParameterDataTypes").GetParameters();

        var parameter = parameters.FirstOrDefault(p => p.Name == name);
        Assert.NotNull(parameter);

        Assert.Equal(type, parameter.Type);
        Assert.Equal(format, parameter.Format);
    }

    [Fact]
    public async Task ItCanParsePropertiesOfObjectDataTypeAsync()
    {
        // Arrange & Act
        var restApiSpec = await this._sut.ParseAsync(this._openApiDocument);

        // Assert
        var properties = restApiSpec.Operations.Single(o => o.Id == "TestParameterDataTypes").Payload!.Properties;

        var property = properties.Single(p => p.Name == "attributes");
        Assert.Equal("object", property.Type);
        Assert.Null(property.Format);
    }

    [Fact]
    public async Task ItCanParseDocumentWithMultipleServersAsync()
    {
        // Act
        var restApi = await this._sut.ParseAsync(this._openApiDocument);

        // Assert
        Assert.All(restApi.Operations, (operation) => Assert.Equal(2, operation.Servers.Count));

        Assert.Equal("https://my-key-vault.vault.azure.net", restApi.Operations[0].Servers[0].Url);
        Assert.Equal("https://ppe.my-key-vault.vault.azure.net", restApi.Operations[0].Servers[1].Url);
    }

    [Fact]
    public async Task ItCanParsePathItemPathParametersAsync()
    {
        var document =
        """
        {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0"
            },
            "paths": {
                "/items/{itemId}/{format}": {
                    "parameters": [
                        {
                            "name": "itemId",
                            "in": "path",
                            "required": true,
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "get": {
                        "parameters": [
                            {
                                "name": "format",
                                "in": "path",
                                "required": true,
                                "schema": {
                                    "type": "string"
                                }
                            }
                        ],
                        "summary": "Get an item by ID",
                        "responses": {
                            "200": {
                                "description": "Successful response"
                            }
                        }
                    }
                }
            }
        }
        """;

        await using var steam = new MemoryStream(Encoding.UTF8.GetBytes(document));
        var restApi = await this._sut.ParseAsync(steam);

        Assert.NotNull(restApi);
        Assert.NotNull(restApi.Operations);
        Assert.NotEmpty(restApi.Operations);

        var firstOperation = restApi.Operations[0];

        Assert.NotNull(firstOperation);
        Assert.Equal("Get an item by ID", firstOperation.Description);
        Assert.Equal("/items/{itemId}/{format}", firstOperation.Path);

        var parameters = firstOperation.GetParameters();
        Assert.NotNull(parameters);
        Assert.Equal(2, parameters.Count);

        var pathParameter = parameters.Single(static p => "itemId".Equals(p.Name, StringComparison.OrdinalIgnoreCase));
        Assert.NotNull(pathParameter);
        Assert.True(pathParameter.IsRequired);
        Assert.Equal(RestApiParameterLocation.Path, pathParameter.Location);
        Assert.Null(pathParameter.DefaultValue);
        Assert.NotNull(pathParameter.Schema);
        Assert.Equal("string", pathParameter.Schema.RootElement.GetProperty("type").GetString());

        var formatParameter = parameters.Single(static p => "format".Equals(p.Name, StringComparison.OrdinalIgnoreCase));
        Assert.NotNull(formatParameter);
        Assert.True(formatParameter.IsRequired);
        Assert.Equal(RestApiParameterLocation.Path, formatParameter.Location);
        Assert.Null(formatParameter.DefaultValue);
        Assert.NotNull(formatParameter.Schema);
        Assert.Equal("string", formatParameter.Schema.RootElement.GetProperty("type").GetString());
    }

    [Fact]
    public async Task ItCanParsePathItemPathParametersAndOverridesAsync()
    {
        var document =
        """
        {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0"
            },
            "paths": {
                "/items/{itemId}/{format}": {
                    "parameters": [
                        {
                            "name": "itemId",
                            "in": "path",
                            "required": true,
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "get": {
                        "parameters": [
                            {
                                "name": "format",
                                "in": "path",
                                "required": true,
                                "schema": {
                                    "type": "string"
                                }
                            },
                            {
                                "name": "itemId",
                                "in": "path",
                                "description": "item ID override",
                                "required": true,
                                "schema": {
                                    "type": "string"
                                }
                            }
                        ],
                        "summary": "Get an item by ID",
                        "responses": {
                            "200": {
                                "description": "Successful response"
                            }
                        }
                    }
                }
            }
        }
        """;

        await using var steam = new MemoryStream(Encoding.UTF8.GetBytes(document));
        var restApi = await this._sut.ParseAsync(steam);

        Assert.NotNull(restApi);
        Assert.NotNull(restApi.Operations);
        Assert.NotEmpty(restApi.Operations);

        var firstOperation = restApi.Operations[0];

        Assert.NotNull(firstOperation);
        Assert.Equal("Get an item by ID", firstOperation.Description);
        Assert.Equal("/items/{itemId}/{format}", firstOperation.Path);

        var parameters = firstOperation.GetParameters();
        Assert.NotNull(parameters);
        Assert.Equal(2, parameters.Count);

        var pathParameter = parameters.Single(static p => "itemId".Equals(p.Name, StringComparison.OrdinalIgnoreCase));
        Assert.NotNull(pathParameter);
        Assert.True(pathParameter.IsRequired);
        Assert.Equal(RestApiParameterLocation.Path, pathParameter.Location);
        Assert.Null(pathParameter.DefaultValue);
        Assert.NotNull(pathParameter.Schema);
        Assert.Equal("string", pathParameter.Schema.RootElement.GetProperty("type").GetString());
        Assert.Equal("item ID override", pathParameter.Description);

        var formatParameter = parameters.Single(static p => "format".Equals(p.Name, StringComparison.OrdinalIgnoreCase));
        Assert.NotNull(formatParameter);
        Assert.True(formatParameter.IsRequired);
        Assert.Equal(RestApiParameterLocation.Path, formatParameter.Location);
        Assert.Null(formatParameter.DefaultValue);
        Assert.NotNull(formatParameter.Schema);
        Assert.Equal("string", formatParameter.Schema.RootElement.GetProperty("type").GetString());
    }

    [Fact]
    public void ItCanVerifyAllServerLevelsAreStoredCorrectly()
    {
        // Arrange
        var document = new OpenApiDocument
        {
            Servers = new List<OpenApiServer>
        {
            new() { Url = "https://global-server.com", Description = "Global server" }
        }
        };

        var pathItem = new OpenApiPathItem
        {
            Servers = new List<OpenApiServer>
        {
            new() { Url = "https://path-server.com", Description = "Path server" }
        },
            Operations = new Dictionary<OperationType, OpenApiOperation>
            {
                [OperationType.Get] = new OpenApiOperation
                {
                    OperationId = "GetTest",
                    Servers = new List<OpenApiServer>
                {
                    new() { Url = "https://operation-server.com", Description = "Operation server" }
                },
                    Responses = new OpenApiResponses()
                }
            }
        };

        // Act
        var operations = OpenApiDocumentParser.CreateRestApiOperations(document, "/test", pathItem, null, this._logger);
        var operation = operations[0];

        // Assert
        // Verify servers
        Assert.Single(operation.Servers);
        Assert.Equal("https://global-server.com", operation.Servers[0].Url);
        Assert.Equal("Global server", operation.Servers[0].Description);

        // Verify path servers
        Assert.Single(operation.PathServers);
        Assert.Equal("https://path-server.com", operation.PathServers[0].Url);
        Assert.Equal("Path server", operation.PathServers[0].Description);

        // Verify operation servers
        Assert.Single(operation.OperationServers);
        Assert.Equal("https://operation-server.com", operation.OperationServers[0].Url);
        Assert.Equal("Operation server", operation.OperationServers[0].Description);
    }

    private static MemoryStream ModifyOpenApiDocument(Stream openApiDocument, Action<JsonObject> transformer)
    {
        var json = JsonSerializer.Deserialize<JsonObject>(openApiDocument);

        transformer(json!);

        var stream = new MemoryStream();

        JsonSerializer.Serialize(stream, json);

        stream.Seek(0, SeekOrigin.Begin);

        return stream;
    }

    private static RestApiParameter GetParameterMetadata(IList<RestApiOperation> operations, string operationId,
        RestApiParameterLocation location, string name)
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

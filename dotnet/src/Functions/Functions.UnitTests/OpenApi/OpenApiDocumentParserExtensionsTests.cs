// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using SemanticKernel.Functions.UnitTests.OpenApi.TestPlugins;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi;

/// <summary>
/// Contains tests for the open api schema extensions functionality of the <see cref="OpenApiDocumentParser"/> class.
/// See https://swagger.io/docs/specification/openapi-extensions/
/// </summary>
public class OpenApiDocumentParserExtensionsTests
{
    /// <summary>
    /// System under test - an instance of OpenApiDocumentParser class.
    /// </summary>
    private readonly OpenApiDocumentParser _sut;

    /// <summary>
    /// Creates an instance of a <see cref="OpenApiDocumentParserV31Tests"/> class.
    /// </summary>
    public OpenApiDocumentParserExtensionsTests()
    {
        this._sut = new OpenApiDocumentParser();
    }

    [Theory]
    [InlineData("documentV2_0.json")]
    [InlineData("documentV3_0.json")]
    [InlineData("documentV3_1.yaml")]
    public async Task ItCanExtractExtensionsOfAllTypesAsync(string documentName)
    {
        // Arrange.
        using var openApiDocument = ResourcePluginsProvider.LoadFromResource(documentName);

        // Act.
        var restApi = await this._sut.ParseAsync(openApiDocument);

        // Assert.
        Assert.NotNull(restApi.Operations);
        Assert.True(restApi.Operations.Any());

        var operation = restApi.Operations.Single(o => o.Id == "OpenApiExtensions");
        Assert.NotNull(operation);

        // Check the different extension types.
        // No need to test float, since the parser does not differentiate between floats and doubles, and will always return a double.
        // No need to test byte, since the parser does not differentiate between byte and string, and will always return a string.
        // No need to test binary, since the parser does not differentiate between binary and string, and will always return a string.

        Assert.True(operation.Extensions.TryGetValue("x-boolean-extension", out var booleanValue));
        Assert.Equal(true, booleanValue);

        Assert.True(operation.Extensions.TryGetValue("x-double-extension", out var doubleValue));
        Assert.Equal(1.2345d, doubleValue);

        Assert.True(operation.Extensions.TryGetValue("x-integer-extension", out var integerValue));
        Assert.Equal(12345, integerValue);

        Assert.True(operation.Extensions.TryGetValue("x-string-extension", out var stringValue));
        Assert.Equal("value1", stringValue);

        Assert.True(operation.Extensions.TryGetValue("x-date-extension", out var dateValue));
        Assert.Equal(DateTime.Parse("2024-04-16T00:00:00.0000000", CultureInfo.InvariantCulture), dateValue);

        Assert.True(operation.Extensions.TryGetValue("x-datetime-extension", out var datetimeValue));
        Assert.Equal(DateTimeOffset.Parse("2024-04-16T18:37:12.1214643+00:00", CultureInfo.InvariantCulture), datetimeValue);

        Assert.True(operation.Extensions.TryGetValue("x-array-extension", out var arrayValue));
        Assert.Equal("[\"value1\",\"value2\"]", arrayValue);

        Assert.True(operation.Extensions.TryGetValue("x-object-extension", out var objectValue));
        Assert.Equal("{\"key1\":\"value1\",\"key2\":\"value2\"}", objectValue);
    }

    [Theory]
    [InlineData("documentV3_0.json")]
    [InlineData("documentV3_1.yaml")]
    public async Task ItCanParseMediaTypeAsync(string documentName)
    {
        // Arrange.
        using var openApiDocument = ResourcePluginsProvider.LoadFromResource(documentName);

        // Act.
        var restApi = await this._sut.ParseAsync(openApiDocument);

        // Assert.
        Assert.NotNull(restApi.Operations);
        Assert.Equal(8, restApi.Operations.Count);
        var operation = restApi.Operations.Single(o => o.Id == "Joke");
        Assert.NotNull(operation);
        Assert.Equal("application/json; x-api-version=2.0", operation.Payload?.MediaType);
    }
}

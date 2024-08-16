// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using SemanticKernel.Functions.UnitTests.OpenApi.TestPlugins;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi;

public class OpenApiDocumentParserV30FeatureTests
{
    /// <summary>
    /// OpenAPI document stream.
    /// </summary>
    private readonly Stream _openApiDocument;

    /// <summary>
    /// System under test - an instance of OpenApiDocumentParser class.
    /// </summary>
    private readonly OpenApiDocumentParser _parser;

    public OpenApiDocumentParserV30FeatureTests()
    {
        this._openApiDocument = ResourcePluginsProvider.LoadFromResource("openapi_feature_testsV3_0.json");
        this._parser = new OpenApiDocumentParser();
    }

    [Fact]
    public async Task ItCanParseAllOfAsync()
    {
        var spec = await this._parser.ParseAsync(this._openApiDocument);

        Assert.NotEmpty(spec.Operations);
        var op0 = spec.Operations.Single(static x => x.Id == "allOfGet");
        Assert.NotEmpty(op0.Responses);
        var res200 = op0.Responses["200"];
        Assert.NotNull(res200.Schema);
        var foo = res200.Schema.RootElement.GetProperty("allOf")[0];
        Assert.Equal("object", foo.GetProperty("type").GetString());
        var bar = res200.Schema.RootElement.GetProperty("allOf")[1];
        Assert.Equal("object", bar.GetProperty("type").GetString());
    }

    [Fact]
    public async Task ItCanParseAnyOfAsync()
    {
        var spec = await this._parser.ParseAsync(this._openApiDocument);

        Assert.NotEmpty(spec.Operations);
        var op0 = spec.Operations.Single(static x => x.Id == "anyOfGet");
        Assert.NotEmpty(op0.Responses);
        var res200 = op0.Responses["200"];
        Assert.NotNull(res200.Schema);
        var foo = res200.Schema.RootElement.GetProperty("anyOf")[0];
        Assert.Equal("object", foo.GetProperty("type").GetString());
        var bar = res200.Schema.RootElement.GetProperty("anyOf")[1];
        Assert.Equal("string", bar.GetProperty("type").GetString());
    }

    [Fact]
    public async Task ItCanParseOneOfAsync()
    {
        var spec = await this._parser.ParseAsync(this._openApiDocument);

        Assert.NotEmpty(spec.Operations);
        var op0 = spec.Operations.Single(static x => x.Id == "oneOfGet");
        Assert.NotEmpty(op0.Responses);
        var res200 = op0.Responses["200"];
        Assert.NotNull(res200.Schema);
        var foo = res200.Schema.RootElement.GetProperty("oneOf")[0];
        Assert.Equal("object", foo.GetProperty("type").GetString());
        var bar = res200.Schema.RootElement.GetProperty("oneOf")[1];
        Assert.Equal("string", bar.GetProperty("type").GetString());
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using SemanticKernel.Functions.UnitTests.OpenApi.TestPlugins;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi;

public static class OpenApiDocumentParserV30FeatureTests
{
    public class OneOfTests
    {
        /// <summary>
        /// System under test - an instance of OpenApiDocumentParser class.
        /// </summary>
        private readonly OpenApiDocumentParser _parser;

        /// <summary>
        /// OpenAPI document stream.
        /// </summary>
        private readonly Stream _openApiDocument;

        public OneOfTests()
        {
            using var stream0 = ResourcePluginsProvider.LoadFromResource("openapi_any_of.json");
            // /components/schemas/fooBar
            this._openApiDocument = OpenApiTestHelper.ModifyOpenApiDocument(stream0, (doc) =>
            {
                var schemas = doc["components"]!["schemas"]!;
                var anyOf = schemas["fooBar"]!["anyOf"];
                schemas["fooBar"]!["anyOf"] = null;
                var schema = new JsonObject
                {
                    ["oneOf"] = anyOf
                };
                schemas["fooBar"] = schema;
            });
            this._parser = new OpenApiDocumentParser();
        }

        [Fact]
        public async Task ParsesOneOfAsync()
        {
            var spec = await this._parser.ParseAsync(this._openApiDocument);

            Assert.NotEmpty(spec.Operations);
            var op0 = spec.Operations[0];
            Assert.NotEmpty(op0.Responses);
            var res200 = op0.Responses["200"];
            Assert.NotNull(res200.Schema);
            var foo = res200.Schema.RootElement.GetProperty("oneOf")[0];
            Assert.Equal("object", foo.GetProperty("type").GetString());
            var bar = res200.Schema.RootElement.GetProperty("oneOf")[1];
            Assert.Equal("string", bar.GetProperty("type").GetString());
        }
    }

    public class AllOfTests
    {
        /// <summary>
        /// System under test - an instance of OpenApiDocumentParser class.
        /// </summary>
        private readonly OpenApiDocumentParser _parser;

        /// <summary>
        /// OpenAPI document stream.
        /// </summary>
        private readonly Stream _openApiDocument;

        public AllOfTests()
        {
            using var stream0 = ResourcePluginsProvider.LoadFromResource("openapi_any_of.json");
            // /components/schemas/fooBar
            this._openApiDocument = OpenApiTestHelper.ModifyOpenApiDocument(stream0, (doc) =>
            {
                var schemas = doc["components"]!["schemas"]!;
                schemas["bar"]!["type"] = "object";
                schemas["bar"]!["properties"] = new JsonObject
                {
                    ["name"] = new JsonObject
                    {
                        ["type"] = "string"
                    }
                };
                var anyOf = schemas["fooBar"]!["anyOf"];
                schemas["fooBar"]!["anyOf"] = null;
                var schema = new JsonObject
                {
                    ["allOf"] = anyOf
                };
                schemas["fooBar"] = schema;
            });
            this._parser = new OpenApiDocumentParser();
        }

        [Fact]
        public async Task ParsesAllOfAsync()
        {
            var spec = await this._parser.ParseAsync(this._openApiDocument);

            Assert.NotEmpty(spec.Operations);
            var op0 = spec.Operations[0];
            Assert.NotEmpty(op0.Responses);
            var res200 = op0.Responses["200"];
            Assert.NotNull(res200.Schema);
            var foo = res200.Schema.RootElement.GetProperty("allOf")[0];
            Assert.Equal("object", foo.GetProperty("type").GetString());
            var bar = res200.Schema.RootElement.GetProperty("allOf")[1];
            Assert.Equal("object", bar.GetProperty("type").GetString());
        }
    }

    public class AnyOfTests
    {
        /// <summary>
        /// System under test - an instance of OpenApiDocumentParser class.
        /// </summary>
        private readonly OpenApiDocumentParser _parser;

        /// <summary>
        /// OpenAPI document stream.
        /// </summary>
        private readonly Stream _openApiDocument;

        public AnyOfTests()
        {
            this._openApiDocument = ResourcePluginsProvider.LoadFromResource("openapi_any_of.json");
            this._parser = new OpenApiDocumentParser();
        }

        [Fact]
        public async Task ParsesAnyOfAsync()
        {
            var spec = await this._parser.ParseAsync(this._openApiDocument);

            Assert.NotEmpty(spec.Operations);
            var op0 = spec.Operations[0];
            Assert.NotEmpty(op0.Responses);
            var res200 = op0.Responses["200"];
            Assert.NotNull(res200.Schema);
            var foo = res200.Schema.RootElement.GetProperty("anyOf")[0];
            Assert.Equal("object", foo.GetProperty("type").GetString());
            var bar = res200.Schema.RootElement.GetProperty("anyOf")[1];
            Assert.Equal("string", bar.GetProperty("type").GetString());
        }
    }
}

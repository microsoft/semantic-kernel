// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi;

public static class OpenApiDocumentParserV30FeatureTests
{
    public class OneOfTests
    {
        [Fact]
        public async Task ParsesOneOfAsync()
        {
            var api = """
                      {"openapi":"3.0.3","info":{"title":"Test OneOf0","version":"0"},
                      "paths":{"/fooOrBar":{"get":{"responses":{"200":{"content":{"application/json":{
                      "schema":{"$ref":"#/components/schemas/fooOrBar"}}},"description":"response"}}}}},
                      "components":{"schemas":{"foo":{"type":"object","properties":{"name":{"type":"string"},
                      "extra":{"type":"string"}}},"bar":{"type":"string"},
                      "fooOrBar":{"oneOf":[{"$ref":"#/components/schemas/foo"},{"$ref":"#/components/schemas/bar"}]}}}}
                      """.Trim();
            var ms = new MemoryStream(Encoding.Default.GetBytes(api));
            var parser = new OpenApiDocumentParser();

            var spec = await parser.ParseAsync(ms);

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
        [Fact]
        public async Task ParsesAllOfAsync()
        {
            var api = """
                      {"openapi":"3.0.3","info":{"title":"Test AllOf0","version":"0"},
                      "paths":{"/fooOrBar":{"get":{"responses":{"200":{"content":{"application/json":{
                      "schema":{"$ref":"#/components/schemas/fooAndBar"}}},"description":"response"}}}}},
                      "components":{"schemas":{"foo":{"type":"object","properties":{"name":{"type":"string"},
                      "extra":{"type":"string"}}},"bar":{"type":"object","properties":{"description":{"type":"string"}}},
                      "fooAndBar":{"allOf":[{"$ref":"#/components/schemas/foo"},{"$ref":"#/components/schemas/bar"}]}}}}
                      """.Trim();
            var ms = new MemoryStream(Encoding.Default.GetBytes(api));
            var parser = new OpenApiDocumentParser();

            var spec = await parser.ParseAsync(ms);

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
        [Fact]
        public async Task ParsesAnyOfAsync()
        {
            var api = """
                      {"openapi":"3.0.3","info":{"title":"Test AnyOf0","version":"0"},
                      "paths":{"/fooOrBar":{"get":{"responses":{"200":{"content":{"application/json":{
                      "schema":{"$ref":"#/components/schemas/fooOrBar"}}},"description":"response"}}}}},
                      "components":{"schemas":{"foo":{"type":"object","properties":{"name":{"type":"string"},
                      "extra":{"type":"string"}}},"bar":{"type":"string"},
                      "fooOrBar":{"anyOf":[{"$ref":"#/components/schemas/foo"},{"$ref":"#/components/schemas/bar"}]}}}}
                      """.Trim();
            var ms = new MemoryStream(Encoding.Default.GetBytes(api));
            var parser = new OpenApiDocumentParser();

            var spec = await parser.ParseAsync(ms);

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

// Copyright (c) Microsoft. All rights reserved.

using System;
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
        [Fact(Skip = "OneOf is not supported yet")]
        public async Task ParsesSimpleOneOfAsync()
        {
            var api = """
                      {"openapi":"3.0.3","info":{"title":"Test OneOf0","version":"0"},
                      "paths":{"/fooOrBar":{"get":{"responses":{"200":{"$ref":"#/components/schemas/fooOrBar"}}}}},
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
        }
    }

    public class AllOfTests
    {
        [Fact(Skip = "AllOf is not supported yet")]
        public async Task ParsesSimpleAllOfAsync()
        {
            var api = """
                      {"openapi":"3.0.3","info":{"title":"Test AllOf0","version":"0"},
                      "paths":{"/fooOrBar":{"get":{"responses":{"200":{"$ref":"#/components/schemas/fooAndBar"}}}}},
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
        }
    }

    public class AnyOfTests
    {
        [Fact(Skip = "AnyOf is not supported yet")]
        public async Task ParsesSimpleAllOfAsync()
        {
            var api = """
                      {"openapi":"3.0.3","info":{"title":"Test AnyOf0","version":"0"},
                      "paths":{"/fooOrBar":{"get":{"responses":{"200":{"$ref":"#/components/schemas/fooOrBar"}}}}},
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
        }
    }
}

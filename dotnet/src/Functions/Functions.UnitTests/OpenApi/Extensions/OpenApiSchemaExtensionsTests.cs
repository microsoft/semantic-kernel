// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Globalization;
using Microsoft.OpenApi.Any;
using Microsoft.OpenApi.Models;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi.Extensions;

public class OpenApiSchemaExtensionsTests
{
    [Fact]
    public void ItShouldConvertOpenApiSchemaUsingInvariantCulture()
    {
        // Arrange
        var schema = new OpenApiSchema
        {
            Type = "object",
            Properties = new Dictionary<string, OpenApiSchema>
            {
                ["property1"] = new OpenApiSchema
                {
                    Type = "number",
                    Format = "double",
                    Default = new OpenApiDouble(12.01)
                }
            }
        };

        var currentCulture = CultureInfo.CurrentCulture; // Backup current culture

        // Act & Assert
        try
        {
            CultureInfo.CurrentCulture = new CultureInfo("fr-FR"); // French culture uses comma as decimal separator

            var result = schema.ToJsonSchema(); // Should use invariant culture

            Assert.True(result.RootElement.TryGetProperty("properties", out var properties));
            Assert.True(properties.TryGetProperty("property1", out var property2));
            Assert.Equal(12.01, property2.GetProperty("default").GetDouble());
        }
        finally
        {
            CultureInfo.CurrentCulture = currentCulture; // Restore current culture
        }
    }
}

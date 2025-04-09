// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Xunit;

namespace SemanticKernel.UnitTests.Functions.JsonSerializerContexts;

#pragma warning disable CA1812 // Internal class that is apparently never instantiated
internal sealed class TestJsonSerializerOptionsForPrimitives : TheoryData<JsonSerializerOptions?>
#pragma warning restore CA1812 // Internal class that is apparently never instantiated
{
    public TestJsonSerializerOptionsForPrimitives()
    {
        this.Add(null);
        this.Add(new JsonSerializerOptions { TypeInfoResolver = PrimitiveTypesJsonSerializerContext.Default });
    }
}

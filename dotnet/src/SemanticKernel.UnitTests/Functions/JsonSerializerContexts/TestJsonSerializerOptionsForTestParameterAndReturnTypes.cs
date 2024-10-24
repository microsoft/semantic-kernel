// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Xunit;

namespace SemanticKernel.UnitTests.Functions.JsonSerializerContexts;

#pragma warning disable CA1812 // Internal class that is apparently never instantiated
internal sealed class TestJsonSerializerOptionsForTestParameterAndReturnTypes : TheoryData<JsonSerializerOptions?>
#pragma warning restore CA1812 // Internal class that is apparently never instantiated
{
    public TestJsonSerializerOptionsForTestParameterAndReturnTypes()
    {
        JsonSerializerOptions options = new();
        options.TypeInfoResolverChain.Add(TestParameterTypeJsonSerializerContext.Default);
        options.TypeInfoResolverChain.Add(TestReturnTypeJsonSerializerContext.Default);

        this.Add(null);
        this.Add(options);
    }
}

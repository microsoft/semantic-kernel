// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Text.Json.Serialization.Metadata;

namespace Microsoft.SemanticKernel;

[ExcludeFromCodeCoverage]
internal sealed class FunctionChoiceBehaviorResolver : DefaultJsonTypeInfoResolver
{
    public static FunctionChoiceBehaviorResolver Instance { get; } = new FunctionChoiceBehaviorResolver();

    public override JsonTypeInfo GetTypeInfo(Type type, JsonSerializerOptions options)
    {
        var jsonTypeInfo = base.GetTypeInfo(type, options);

        if (jsonTypeInfo.Type == typeof(FunctionChoiceBehavior))
        {
            jsonTypeInfo.PolymorphismOptions = new JsonPolymorphismOptions();

            jsonTypeInfo.PolymorphismOptions.DerivedTypes.Add(new JsonDerivedType(typeof(RequiredFunctionChoiceBehavior), "required"));
            jsonTypeInfo.PolymorphismOptions.DerivedTypes.Add(new JsonDerivedType(typeof(AutoFunctionChoiceBehavior), "auto"));
            jsonTypeInfo.PolymorphismOptions.DerivedTypes.Add(new JsonDerivedType(typeof(NoneFunctionChoiceBehavior), "none"));

            jsonTypeInfo.PolymorphismOptions.TypeDiscriminatorPropertyName = "type";

            return jsonTypeInfo;
        }

        return jsonTypeInfo;
    }
}

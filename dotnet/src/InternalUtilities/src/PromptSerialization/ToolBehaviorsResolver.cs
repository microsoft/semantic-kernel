// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Text.Json.Serialization.Metadata;
using Microsoft.SemanticKernel.AI.ToolBehaviors;

namespace Microsoft.SemanticKernel;

[ExcludeFromCodeCoverage]
internal sealed class ToolBehaviorsResolver : DefaultJsonTypeInfoResolver
{
    public static ToolBehaviorsResolver Instance { get; } = new ToolBehaviorsResolver();

    public override JsonTypeInfo GetTypeInfo(Type type, JsonSerializerOptions options)
    {
        var jsonTypeInfo = base.GetTypeInfo(type, options);

        if (jsonTypeInfo.Type == typeof(ToolBehavior))
        {
            jsonTypeInfo.PolymorphismOptions = new JsonPolymorphismOptions();

            jsonTypeInfo.PolymorphismOptions.DerivedTypes.Add(new JsonDerivedType(typeof(FunctionCallBehavior), "function_call_behavior"));

            jsonTypeInfo.PolymorphismOptions.TypeDiscriminatorPropertyName = "type";

            return jsonTypeInfo;
        }

        if (jsonTypeInfo.Type == typeof(FunctionCallChoice))
        {
            jsonTypeInfo.PolymorphismOptions = new JsonPolymorphismOptions();

            jsonTypeInfo.PolymorphismOptions.DerivedTypes.Add(new JsonDerivedType(typeof(RequiredFunctionCallChoice), "required"));
            jsonTypeInfo.PolymorphismOptions.DerivedTypes.Add(new JsonDerivedType(typeof(AutoFunctionCallChoice), "auto"));
            jsonTypeInfo.PolymorphismOptions.DerivedTypes.Add(new JsonDerivedType(typeof(NoneFunctionCallChoice), "none"));

            jsonTypeInfo.PolymorphismOptions.TypeDiscriminatorPropertyName = "type";

            return jsonTypeInfo;
        }

        return jsonTypeInfo;
    }
}

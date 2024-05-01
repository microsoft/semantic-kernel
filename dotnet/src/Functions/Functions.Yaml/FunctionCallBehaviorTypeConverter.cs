// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.AI.ToolBehaviors;
using YamlDotNet.Core;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace Microsoft.SemanticKernel;

internal sealed class FunctionCallBehaviorTypeConverter : IYamlTypeConverter
{
    private static IDeserializer? s_deserializer;

    public bool Accepts(Type type)
    {
        return typeof(FunctionCallBehavior) == type;
    }

    public object? ReadYaml(IParser parser, Type type)
    {
        s_deserializer ??= new DeserializerBuilder()
            .WithNamingConvention(CamelCaseNamingConvention.Instance)
            .WithTagMapping("!function_call_behavior", typeof(FunctionCallBehavior))
            .WithTagMapping("!auto", typeof(AutoFunctionCallChoice))
            .WithTagMapping("!required", typeof(RequiredFunctionCallChoice))
            .Build();

        return s_deserializer.Deserialize(parser, type);
    }

    public void WriteYaml(IEmitter emitter, object? value, Type type)
    {
        throw new NotImplementedException();
    }
}

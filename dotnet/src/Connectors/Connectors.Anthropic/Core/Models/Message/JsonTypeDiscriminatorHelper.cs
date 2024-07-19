// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Reflection;
using System.Text.Json.Serialization.Metadata;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

// Temporary solution from https://github.com/dotnet/runtime/issues/72604
// TODO: Remove this once we move to .NET 9

internal static class JsonTypeDiscriminatorHelper
{
    internal static IJsonTypeInfoResolver TypeInfoResolver { get; } = new DefaultJsonTypeInfoResolver
    {
        Modifiers =
        {
            static typeInfo =>
            {
                var propertyNamingPolicy = typeInfo.Options.PropertyNamingPolicy;

                // Temporary hack to ensure subclasses of abstract classes will always include the type field
                if (typeInfo.Type.BaseType is { IsAbstract: true } &&
                    typeInfo.Type.BaseType.GetCustomAttributes<InternalJsonDerivedAttribute>().Any())
                {
                    var discriminatorPropertyName = propertyNamingPolicy?.ConvertName("type") ?? "type";
                    if (typeInfo.Properties.All(p => p.Name != discriminatorPropertyName))
                    {
                        var discriminatorValue = typeInfo.Type.BaseType
                            .GetCustomAttributes<InternalJsonDerivedAttribute>()
                            .First(attr => attr.Subtype == typeInfo.Type).TypeDiscriminator;
                        var propInfo = typeInfo.CreateJsonPropertyInfo(typeof(string), discriminatorPropertyName);
                        propInfo.Get = _ => discriminatorValue;
                        typeInfo.Properties.Insert(0, propInfo);
                    }
                }
            },
        },
    };
}

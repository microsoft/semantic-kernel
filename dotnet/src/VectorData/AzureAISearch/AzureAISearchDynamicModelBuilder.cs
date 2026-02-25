// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

internal class AzureAISearchDynamicModelBuilder() : CollectionModelBuilder(s_modelBuildingOptions)
{
    internal static readonly CollectionModelBuildingOptions s_modelBuildingOptions = new()
    {
        RequiresAtLeastOneVector = false,
        SupportsMultipleVectors = true,
        UsesExternalSerializer = true
    };

    protected override void ValidateKeyProperty(KeyPropertyModel keyProperty)
    {
        base.ValidateKeyProperty(keyProperty);

        var type = keyProperty.Type;

        if (type != typeof(string) && type != typeof(Guid))
        {
            throw new NotSupportedException(
                $"Property '{keyProperty.ModelName}' has unsupported type '{type.Name}'. Key properties must be one of the supported types: string, Guid.");
        }
    }

    protected override bool IsDataPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
        => AzureAISearchModelBuilder.IsDataPropertyTypeValidCore(type, out supportedTypes);

    protected override bool IsVectorPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
        => AzureAISearchModelBuilder.IsVectorPropertyTypeValidCore(type, out supportedTypes);
}

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
        SupportsMultipleKeys = false,
        SupportsMultipleVectors = true,
        UsesExternalSerializer = true
    };

    protected override bool IsKeyPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
        => AzureAISearchModelBuilder.IsKeyPropertyTypeValidCore(type, out supportedTypes);

    protected override bool IsDataPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
        => AzureAISearchModelBuilder.IsDataPropertyTypeValidCore(type, out supportedTypes);

    protected override bool IsVectorPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
        => AzureAISearchModelBuilder.IsVectorPropertyTypeValidCore(type, out supportedTypes);
}

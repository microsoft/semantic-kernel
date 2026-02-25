// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

internal class AzureAISearchModelBuilder() : CollectionJsonModelBuilder(s_modelBuildingOptions)
{
    internal const string SupportedVectorTypes = "ReadOnlyMemory<float>, Embedding<float>, float[]";

    internal static readonly CollectionModelBuildingOptions s_modelBuildingOptions = new()
    {
        RequiresAtLeastOneVector = false,
        SupportsMultipleVectors = true,
        UsesExternalSerializer = true
    };

    protected override void ValidateKeyProperty(KeyPropertyModel keyProperty)
    {
        var type = keyProperty.Type;

        if (type != typeof(string) && type != typeof(Guid))
        {
            throw new NotSupportedException(
                $"Property '{keyProperty.ModelName}' has unsupported type '{type.Name}'. Key properties must be one of the supported types: string, Guid.");
        }
    }

    protected override bool IsDataPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
        => IsDataPropertyTypeValidCore(type, out supportedTypes);

    protected override bool IsVectorPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
        => IsVectorPropertyTypeValidCore(type, out supportedTypes);

    internal static bool IsDataPropertyTypeValidCore(Type type, [NotNullWhen(false)] out string? supportedTypes)
    {
        supportedTypes = "string, int, long, double, float, bool, DateTimeOffset, or arrays/lists of these types";

        if (Nullable.GetUnderlyingType(type) is Type underlyingType)
        {
            type = underlyingType;
        }

        return IsValid(type)
            || (type.IsArray && IsValid(type.GetElementType()!))
            || (type.IsGenericType && type.GetGenericTypeDefinition() == typeof(List<>) && IsValid(type.GenericTypeArguments[0]));

        static bool IsValid(Type type)
            => type == typeof(string) ||
               type == typeof(int) ||
               type == typeof(long) ||
               type == typeof(double) ||
               type == typeof(float) ||
               type == typeof(bool) ||
               type == typeof(DateTimeOffset);
    }

    internal static bool IsVectorPropertyTypeValidCore(Type type, [NotNullWhen(false)] out string? supportedTypes)
    {
        // Azure AI Search is adding support for more types than just float32, but these are not available for use via the
        // SDK yet. We will update this list as the SDK is updated.
        // <see href="https://learn.microsoft.com/en-us/rest/api/searchservice/supported-data-types#edm-data-types-for-vector-fields"/>
        supportedTypes = SupportedVectorTypes;

        return type == typeof(ReadOnlyMemory<float>)
            || type == typeof(ReadOnlyMemory<float>?)
            || type == typeof(Embedding<float>)
            || type == typeof(float[]);
    }

    /// <inheritdoc />
    protected override void ValidateProperty(PropertyModel propertyModel, VectorStoreCollectionDefinition? definition)
    {
        base.ValidateProperty(propertyModel, definition);

        // OData identifiers cannot be escaped; storage names are validated during model building.
        // See https://docs.oasis-open.org/odata/odata/v4.01/odata-v4.01-part2-url-conventions.html#sec_ODataIdentifier
        if (!IsValidIdentifier(propertyModel.StorageName))
        {
            throw new InvalidOperationException(
                $"Property '{propertyModel.ModelName}' has storage name '{propertyModel.StorageName}' which is not a valid OData identifier. " +
                "OData identifiers must start with a letter or underscore, and contain only letters, digits, and underscores.");
        }
    }

    private static bool IsValidIdentifier(string name)
    {
        if (string.IsNullOrEmpty(name))
        {
            return false;
        }

        var first = name[0];
        if (!char.IsLetter(first) && first != '_')
        {
            return false;
        }

        for (var i = 1; i < name.Length; i++)
        {
            var c = name[i];
            if (!char.IsLetterOrDigit(c) && c != '_')
            {
                return false;
            }
        }

        return true;
    }
}

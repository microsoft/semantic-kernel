// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Linq;

namespace Microsoft.Extensions.VectorData.ProviderServices;

#pragma warning disable CS1591 // Missing XML comment for publicly visible type or member

/// <summary>
/// Exposes methods for constructing strings that should be used by providers when throwing exceptions.
/// </summary>
[Experimental("MEVD9001")]
public static class VectorDataStrings
{
    public static string EmbeddingGeneratorWithInvalidEmbeddingType(VectorPropertyModel vectorProperty)
        => $"An embedding generator was configured on property '{vectorProperty.ModelName}', but output embedding type '{vectorProperty.EmbeddingType.Name}' isn't supported by the connector.";

    public static string EmbeddingPropertyTypeIncompatibleWithEmbeddingGenerator(VectorPropertyModel vectorProperty)
        => $"Property '{vectorProperty.ModelName}' has embedding type '{TypeName(vectorProperty.Type)}', but an embedding generator is configured on the property. Remove the embedding generator or change the property's .NET type to a non-embedding input type to the generator (e.g. string).";

    public static string GetCollectionWithDictionaryNotSupported
        => "Dynamic mapping via Dictionary<string, object?> is not supported via this method, call GetDynamicCollection() instead.";

    public static string IncludeVectorsNotSupportedWithEmbeddingGeneration
        => "When an embedding generator is configured, `Include Vectors` cannot be enabled.";

    public static string IncompatibleEmbeddingGenerator(Type embeddingGeneratorType, Type[] supportedInputTypes, Type[] supportedOutputTypes)
        => $"Embedding generator '{embeddingGeneratorType.Name}' is incompatible with the required input and output types. The property input type must be '{string.Join(", ", supportedInputTypes.Select(t => TypeName(t)))}', and the output type must be '{string.Join(", ", supportedOutputTypes.Select(t => TypeName(t)))}'.";

    public static string IncompatibleEmbeddingGeneratorWasConfiguredForInputType(Type inputType, Type embeddingGeneratorType)
        => $"An input of type '{TypeName(inputType)}' was provided, but an incompatible embedding generator of type '{TypeName(embeddingGeneratorType)}' was configured.";

    public static string InvalidSearchInputAndNoEmbeddingGeneratorWasConfigured(Type inputType, string supportedVectorTypes)
        => $"A value of type '{TypeName(inputType)}' was passed to 'SearchAsync', but that isn't a supported vector type by your provider and no embedding generator was configured. The supported vector types are: {supportedVectorTypes}.";

    public static string NonEmbeddingVectorPropertyWithoutEmbeddingGenerator(VectorPropertyModel vectorProperty)
        => $"Property '{vectorProperty.ModelName}' has non-Embedding type '{TypeName(vectorProperty.EmbeddingType)}', but no embedding generator is configured.";

    public static string NonDynamicCollectionWithDictionaryNotSupported(Type dynamicCollectionType)
        => $"Dynamic mapping via Dictionary<string, object?> is not supported via this class, use '{TypeName(dynamicCollectionType)}' instead.";

    private static string TypeName(this Type type)
    {
        var i = type.Name.IndexOf('`');
        if (i == -1)
        {
            return type.Name;
        }

        var genericTypeName = type.Name.Substring(0, i);
        var genericArgs = string.Join(", ", type.GetGenericArguments().Select(t => t.TypeName()));
        return $"{genericTypeName}<{genericArgs}>";
    }
}

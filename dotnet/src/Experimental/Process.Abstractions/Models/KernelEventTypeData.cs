// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;

namespace Microsoft.SemanticKernel.Process.Models;

/// <summary>
/// Properties to describe a serializable object as input or output event of a SK Process
/// </summary>
public record KernelEventTypeData
{
    /// <summary>
    /// Dotnet type of the object
    /// </summary>
    public Type? DataType { get; init; } = null;

    /// <summary>
    /// Gets or sets the short description of the data type.
    /// </summary>
    public string? Description { get; set; }

    /// <summary>
    /// Gets or sets whether the event data is considered required (rather than optional).
    /// </summary>
    /// <remarks>
    /// The default is false.
    /// </remarks>
    public bool Required { get; set; } = false;

    /// <summary>
    /// Gets or sets JSON Schema describing this data type.
    /// </summary>
    public string? JsonSchema { get; set; }
}

/// <summary>
/// Methods to create <see cref="KernelEventTypeData"/> from Semantic Kernel function specific objects
/// </summary>
public static class KernelEventTypeDataExtensions
{
    /// <summary>
    /// Converts the specified <see cref="KernelParameterMetadata"/> instance to a <see cref="KernelEventTypeData"/>
    /// object.
    /// </summary>
    /// <param name="kernelParameterMetadata">The metadata describing the kernel parameter to be converted. Cannot be <see langword="null"/>.</param>
    /// <returns>A <see cref="KernelEventTypeData"/> object containing the schema, data type, description, and required status
    /// derived from the specified <see cref="KernelParameterMetadata"/>.</returns>
    public static KernelEventTypeData ToKernelEventTypeData(this KernelParameterMetadata kernelParameterMetadata)
    {
        Verify.NotNull(kernelParameterMetadata);
        return new KernelEventTypeData
        {
            JsonSchema = kernelParameterMetadata.Schema?.ToString(),
            DataType = kernelParameterMetadata.ParameterType,
            Description = kernelParameterMetadata.Description,
            Required = kernelParameterMetadata.IsRequired,
        };
    }

    /// <summary>
    /// Converts the specified <see cref="KernelReturnParameterMetadata"/> instance to a <see
    /// cref="KernelEventTypeData"/> object.
    /// </summary>
    /// <param name="kernelParameterMetadata">The <see cref="KernelReturnParameterMetadata"/> instance containing metadata about the kernel parameter.</param>
    /// <returns>A <see cref="KernelEventTypeData"/> object populated with the corresponding data from the provided <see
    /// cref="KernelReturnParameterMetadata"/>.</returns>
    public static KernelEventTypeData ToKernelEventTypeData(this KernelReturnParameterMetadata kernelParameterMetadata)
    {
        Verify.NotNull(kernelParameterMetadata);
        return new KernelEventTypeData
        {
            JsonSchema = kernelParameterMetadata.Schema?.ToString(),
            DataType = kernelParameterMetadata.ParameterType,
            Description = kernelParameterMetadata.Description,
            Required = false,
        };
    }

    public static KernelEventTypeData FromObjectType(Type objectType, JsonSerializerOptions jsonSerializerOptions)
    {
        Verify.NotNull(objectType, nameof(objectType));
        // TODO: this is the centralized SK way to generate json schemas 
        var returnType = KernelReturnParameterMetadataFactory.CreateFromType(objectType, jsonSerializerOptions);

        return returnType.ToKernelEventTypeData();
    }
}

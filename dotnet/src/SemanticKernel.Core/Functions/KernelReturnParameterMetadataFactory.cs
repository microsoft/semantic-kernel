// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides factory methods for creating <see cref="KernelReturnParameterMetadata"/> instances.
/// </summary>
public static class KernelReturnParameterMetadataFactory
{
    /// <summary>
    /// Creates a <see cref="KernelReturnParameterMetadata"/> from a .NET type.
    /// </summary>
    /// <param name="returnType">The .NET type from which to create the metadata.</param>
    /// <returns>A <see cref="KernelReturnParameterMetadata"/> instance representing the type.</returns>
    public static KernelReturnParameterMetadata CreateFromType(Type returnType)
    {
        return new KernelReturnParameterMetadata(AbstractionsJsonContext.Default.Options) { ParameterType = returnType };
    }
}

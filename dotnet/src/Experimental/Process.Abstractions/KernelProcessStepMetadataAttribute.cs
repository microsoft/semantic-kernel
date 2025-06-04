// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// Attribute to set Process Step State Metadata related properties
/// </summary>
[AttributeUsage(AttributeTargets.Class, AllowMultiple = false)]
public sealed class KernelProcessStepMetadataAttribute : Attribute
{
    /// <summary>
    /// Attribute that assigns default values to Process Step Metadata
    /// </summary>
    public KernelProcessStepMetadataAttribute() { }

    /// <summary>
    /// Attribute that assigns default version to Process Step Metadata
    /// </summary>
    /// <param name="version"></param>
    public KernelProcessStepMetadataAttribute(string version)
    {
        this.Version = version;
    }

    /// <summary>
    /// Version of the step to be used to save with the step state
    /// </summary>
    public string Version { get; } = "v1";
}

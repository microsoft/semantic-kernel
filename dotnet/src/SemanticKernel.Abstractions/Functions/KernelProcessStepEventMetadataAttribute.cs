// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Specifies metadata for a kernel process step, including the name and type of the output event emitted by the step.
/// </summary>
/// <remarks>This attribute is applied to methods to define the metadata for process steps events. It allows
/// specifying the name of the output event and the type of the data associated with the event. Multiple instances of
/// this attribute can be applied to a single method.</remarks>
[AttributeUsage(AttributeTargets.Method, AllowMultiple = true)]
public sealed class KernelProcessStepEventMetadataAttribute : Attribute
{
    /// <summary>
    /// Attribute that assigns default version to Process Step Metadata
    /// </summary>
    public KernelProcessStepEventMetadataAttribute(string outputEventName, Type? outputType)
    {
        this.OutputEventName = outputEventName;
        this.OutputType = outputType;
    }
    /// <summary>
    /// Name of the output event that will be emitted by the step.
    /// </summary>
    public string OutputEventName { get; }

    /// <summary>
    /// Type of the output event data that will be emitted by the step.
    /// </summary>
    public Type? OutputType { get; } = null;
}

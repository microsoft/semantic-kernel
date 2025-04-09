// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Reflection;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Optional options that can be provided when creating a <see cref="KernelFunction"/> from a method.
/// </summary>
public sealed class KernelFunctionFromMethodOptions
{
    /// <summary>
    /// The name to use for the function. If null, it will default to one derived from the method represented by the passed <see cref="Delegate"/> or <see cref="MethodInfo"/>.
    /// </summary>
    public string? FunctionName { get; init; }

    /// <summary>
    /// The description to use for the function. If null, it will default to one derived from the passed <see cref="Delegate"/> or <see cref="MethodInfo"/>, if possible
    /// (e.g. via a <see cref="DescriptionAttribute"/> on the method).
    /// </summary>
    public string? Description { get; init; }

    /// <summary>
    /// Optional parameter descriptions. If null, it will default to one derived from the passed <see cref="Delegate"/> or <see cref="MethodInfo"/>.
    /// </summary>
    public IEnumerable<KernelParameterMetadata>? Parameters { get; init; }

    /// <summary>
    /// Optional return parameter description. If null, it will default to one derived from the passed <see cref="Delegate"/> or <see cref="MethodInfo"/>.
    /// </summary>
    public KernelReturnParameterMetadata? ReturnParameter { get; init; }

    /// <summary>
    /// The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.
    /// </summary>
    public ILoggerFactory? LoggerFactory { get; init; }

    /// <summary>
    /// Optional metadata in addition to the named values already provided in other arguments.
    /// </summary>
    public ReadOnlyDictionary<string, object?>? AdditionalMetadata { get; init; }
}

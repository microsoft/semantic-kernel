// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Reflection;

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// Options that can be provided when creating a <see cref="KernelFunction"/> from a <see cref="ITextSearch{T}"/>.
/// </summary>
public sealed class KernelFunctionFromTextSearchOptions
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
    /// Optional <see cref="SearchOptions"/> that can be used to configure the search function.
    /// </summary>
    public SearchOptions? SearchOptions { get; init; }

    /// <summary>
    /// The delegate for this search function.
    /// </summary>
    public Delegate? Delegate { get; init; }

    /// <summary>
    /// Create a <see cref="KernelFunction"/> instance.
    /// </summary>
    public KernelFunction CreateKernelFunction()
    {
        return KernelFunctionFactory.CreateFromMethod(
                this.Delegate!,
                this.ToKernelFunctionFromMethodOptions());
    }

    #region private

    /// <summary>
    /// Create an instance of <see cref="KernelFunctionFromMethodOptions"/>
    /// </summary>
    private KernelFunctionFromMethodOptions ToKernelFunctionFromMethodOptions()
    {
        return new()
        {
            FunctionName = this.FunctionName,
            Description = this.Description,
            Parameters = this.Parameters,
            ReturnParameter = this.ReturnParameter,
        };
    }

    #endregion
}

// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Specifies that an argument to a <see cref="KernelFunction"/> should be supplied from the associated
/// <see cref="Kernel"/>'s <see cref="Kernel.Services"/> rather than from <see cref="KernelArguments"/>.
/// </summary>
[AttributeUsage(AttributeTargets.Parameter, AllowMultiple = false)]
public sealed class FromKernelServicesAttribute : Attribute
{
    /// <summary>Initializes the attribute.</summary>
    public FromKernelServicesAttribute() { }

    /// <summary>Initializes the attribute with the specified service key.</summary>
    /// <param name="serviceKey">The optional service key to use when resolving a service.</param>
    public FromKernelServicesAttribute(object? serviceKey) => this.ServiceKey = serviceKey;

    /// <summary>Gets the key to use when searching <see cref="Kernel.Services"/>.</summary>
    public object? ServiceKey { get; }
}

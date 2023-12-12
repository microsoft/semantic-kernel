// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Globalization;
using System.Reflection;
using System.Threading;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Specifies that a method on a class imported as a plugin with should be included as a <see cref="KernelFunction"/>.
/// </summary>
/// <remarks>
/// <para>
/// When the system imports functions from an object, it searches all public methods tagged with this attribute.
/// If a method is not tagged with this attribute, it may still be imported directly via a <see cref="Delegate"/>
/// or <see cref="MethodInfo"/> referencing the method directly.
/// </para>
/// <para>
/// A description of the method should be supplied using the <see cref="DescriptionAttribute"/>.
/// That description will be used both with LLM prompts and embedding comparisons; the quality of
/// the description affects the planner's ability to reason about complex tasks. A <see cref="DescriptionAttribute"/>
/// should also be provided on each parameter to provide a description of the parameter suitable for consumption
/// by an LLM or embedding.
/// </para>
/// <para>
/// Functions may have any number of parameters. A given method function may declare at
/// most one parameter of each of these types - <see cref="Kernel"/>, <see cref="KernelArguments"/>,
/// <see cref="CancellationToken"/>, <see cref="CultureInfo"/>, <see cref="ILogger"/> or <see cref="ILoggerFactory"/>.
/// Parameters are populated based on a arguments of the same name. If no argument of the given name is present, but
/// a default value was specified via either a <see cref="DefaultValueAttribute"/> or an optional value in the signature,
/// that default value is used instead. If no default value was specified and it's the first parameter, the "input"
/// argument will be used.  Otherwise, if no value is available, the invocation will fail.
/// </para>
/// <para>
/// For non-string parameters, the argument value is automatically converted to the appropriate type to be passed
/// in based on the <see cref="TypeConverter"/> for the specified type. Similarly, return values are automatically converted
/// back to strings via the associated <see cref="TypeConverter"/>.
/// </para>
/// </remarks>
[AttributeUsage(AttributeTargets.Method, AllowMultiple = false)]
public sealed class KernelFunctionAttribute : Attribute
{
    /// <summary>Initializes the attribute.</summary>
    public KernelFunctionAttribute() { }

    /// <summary>Initializes the attribute.</summary>
    /// <param name="name">The name to use for the function.</param>
    public KernelFunctionAttribute(string? name) => this.Name = name;

    /// <summary>Gets the function's name.</summary>
    /// <remarks>If null, a name will based on the name of the attributed method will be used.</remarks>
    public string? Name { get; }
}

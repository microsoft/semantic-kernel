// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Globalization;
using System.Reflection;
using System.Threading;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Specifies that a method on a class imported as a plugin should be included as a <see cref="KernelFunction"/> in the resulting <see cref="KernelPlugin"/>.
/// </summary>
/// <remarks>
/// <para>
/// When the system imports functions from an object, it searches for all methods tagged with this attribute.
/// If a method is not tagged with this attribute, it may still be imported directly via a <see cref="Delegate"/>
/// or <see cref="MethodInfo"/> referencing the method directly.
/// </para>
/// <para>
/// Method visibility does not impact whether a method may be imported. Any method tagged with this attribute, regardless
/// of whether it's public or not, will be imported.
/// </para>
/// <para>
/// A description of the method should be supplied using the <see cref="DescriptionAttribute"/>.
/// That description will be used both with LLM prompts and embedding comparisons; the quality of
/// the description affects the planner's ability to reason about complex tasks. A <see cref="DescriptionAttribute"/>
/// should also be provided on each parameter to provide a description of the parameter suitable for consumption
/// by an LLM or embedding.
/// </para>
/// <para>
/// Functions may have any number of parameters. In general, arguments to parameters are supplied via the <see cref="KernelArguments"/>
/// used to invoke the function, with the arguments matched by name to the parameters of the method. If no argument of the given name
/// is present, but a default value was specified in the method's definition, that default value will be used. If the argument value in
/// <see cref="KernelArguments"/> is not of the same type as the parameter, the system will attempt to convert the value to the parameter's
/// type using a <see cref="TypeConverter"/>.
/// </para>
/// <para>
/// However, parameters of the following types are treated specially and are supplied from a source other than from the arguments dictionary:
/// <list type="table">
/// <item>
/// <term><see cref="Kernel"/></term>
/// <description>The <see cref="Kernel"/> supplied when invoking the function.</description>
/// </item>
/// <item>
/// <term><see cref="KernelArguments"/></term>
/// <description>The <see cref="KernelArguments"/> supplied when invoking the function.</description>
/// </item>
/// <item>
/// <term><see cref="KernelFunction"/></term>
/// <description>The <see cref="KernelFunction"/> that represents this function being invoked.</description>
/// </item>
/// <item>
/// <term><see cref="CancellationToken"/></term>
/// <description>The <see cref="CancellationToken"/> supplied when invoking the function.</description>
/// </item>
/// <item>
/// <term><see cref="CultureInfo"/> or <see cref="IFormatProvider"/></term>
/// <description>The result of <see cref="Kernel.Culture"/> from the <see cref="Kernel"/> used when invoking the function.</description>
/// </item>
/// <item>
/// <term><see cref="ILoggerFactory"/> or <see cref="ILogger"/></term>
/// <description>The result of <see cref="Kernel.LoggerFactory"/> from the <see cref="Kernel"/> (or an <see cref="ILogger"/> created from it) used when invoking the function.</description>
/// </item>
/// <item>
/// <term><see cref="IAIServiceSelector"/></term>
/// <description>The result of <see cref="Kernel.ServiceSelector"/> from the <see cref="Kernel"/> used when invoking the function.</description>
/// </item>
/// </list>
/// </para>
/// <para>
/// Arguments may also be fulfilled from the associated <see cref="Kernel"/>'s <see cref="Kernel.Services"/> service provider. If a parameter is attributed
/// with <see cref="FromKernelServicesAttribute"/>, the system will attempt to resolve the parameter by querying the service provider for a service of the
/// parameter's type. If the service provider does not contain a service of the parameter's type and the parameter is not optional, the invocation will fail.
/// </para>
/// <para>
/// If no value can be derived from any of these means for all parameters, the invocation will fail.
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

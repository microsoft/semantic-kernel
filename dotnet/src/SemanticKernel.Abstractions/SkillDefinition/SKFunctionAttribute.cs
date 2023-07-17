// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Specifies that a method is a native function available to Semantic Kernel.
/// </summary>
/// <remarks>
/// <para>
/// When the kernel imports a skill, it searches all public methods tagged with this attribute.
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
/// Functions may have any number of parameters. Parameters of type <see cref="ILogger"/> and
/// <see cref="CancellationToken"/> are filled in from the corresponding members of the <see cref="SKContext"/>;
/// <see cref="SKContext"/> itself may also be a parameter. A given native function may declare at
/// most one parameter of each of these types.  All other parameters must be of a primitive .NET type or
/// a type attributed with <see cref="TypeConverterAttribute"/>. Functions may return a <see cref="Task"/>,
/// <see cref="ValueTask"/>, any primitive .NET type or a type attributed with <see cref="TypeConverterAttribute"/>,
/// or a <see cref="Task{TResult}"/> or <see cref="ValueTask{TResult}"/> of such a type.
/// </para>
/// <para>
/// Parameters are populated based on a context variable of the same name, unless an <see cref="SKNameAttribute"/> is
/// used to override which context variable is targeted. If no context variable of the given name is present, but
/// a default value was specified via either a <see cref="DefaultValueAttribute"/> or an optional value in the siguatre,
/// that default value is used instead. If no default value was specified and it's the first parameter, the "input"
/// context variable will be used.  If no value is available, the invocation will fail.
/// </para>
/// <para>
/// For non-string parameters, the context variable value is automatically converted to the appropriate type to be passed
/// in based on the <see cref="TypeConverter"/> for the specified type. Similarly, return values are automatically converted
/// back to strings via the associated <see cref="TypeConverter"/>.
/// </para>
/// </remarks>
[AttributeUsage(AttributeTargets.Method, AllowMultiple = false)]
public sealed class SKFunctionAttribute : Attribute
{
    /// <summary>Initializes the attribute.</summary>
    public SKFunctionAttribute()
    {
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

/// <summary>
/// Same as <see cref="JsonDerivedTypeAttribute"/> but used to avoid NotSupportedExceptions when using the former.
/// </summary>
[AttributeUsage(AttributeTargets.Class | AttributeTargets.Interface, AllowMultiple = true, Inherited = false)]
internal sealed class InternalJsonDerivedAttribute(Type subtype, string typeDiscriminator) : Attribute
{
    public Type Subtype { get; internal set; } = subtype;
    public string TypeDiscriminator { get; internal set; } = typeDiscriminator;
}

// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Attribute to mark a property on a record class as the value of the source data.
/// </summary>
/// <remarks>
/// The characteristics defined here will influence how the property is treated when converting a record to a <see cref="TextSearchResult"/>.
/// </remarks>
[Experimental("SKEXP0001")]
[AttributeUsage(AttributeTargets.Property, AllowMultiple = false)]
public sealed class TextSearchResultValueAttribute : Attribute
{
}

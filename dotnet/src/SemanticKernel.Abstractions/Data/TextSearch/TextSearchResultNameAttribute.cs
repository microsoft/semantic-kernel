// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Attribute to mark a property on a record class as the name of the source data.
/// </summary>
/// <remarks>
/// The characteristics defined here will influence how the property is treated when converting a record to a <see cref="TextSearchResult"/>.
/// </remarks>
[AttributeUsage(AttributeTargets.Property, AllowMultiple = false)]
public sealed class TextSearchResultNameAttribute : Attribute
{
}

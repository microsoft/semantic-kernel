// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// The REST API security requirement object.
/// </summary>
[Experimental("SKEXP0040")]
public sealed class RestApiSecurityRequirement : Dictionary<RestApiSecurityScheme, IList<string>>
{
    /// <summary>
    /// Creates an instance of a <see cref="RestApiSecurityRequirement"/> class.
    /// </summary>
    /// <param name="dictionary">Dictionary containing the security schemes.</param>
    internal RestApiSecurityRequirement(IDictionary<RestApiSecurityScheme, IList<string>> dictionary) : base(dictionary)
    {
    }

    internal void Freeze()
    {
        foreach (var item in this)
        {
            item.Key.Freeze();
            this[item.Key] = new ReadOnlyCollection<string>(item.Value);
        }
    }
}

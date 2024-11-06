// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Collections.ObjectModel;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// The REST API security requirement object.
/// </summary>
public sealed class RestApiSecurityRequirement : ReadOnlyDictionary<RestApiSecurityScheme, IList<string>>
{
    /// <summary>
    /// Creates an instance of a <see cref="RestApiSecurityRequirement"/> class.
    /// </summary>
    /// <param name="dictionary">Dictionary containing the security schemes.</param>
    internal RestApiSecurityRequirement(IDictionary<RestApiSecurityScheme, IList<string>> dictionary) : base(dictionary)
    {
    }
}

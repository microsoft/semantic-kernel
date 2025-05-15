// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Contains options for <see cref="TextSearchStore{TKey}.UpsertDocumentsAsync(IEnumerable{TextSearchDocument}, TextSearchStoreUpsertOptions?, CancellationToken)"/>.
/// </summary>
[Experimental("SKEXP0130")]
public sealed class TextSearchStoreUpsertOptions
{
    /// <summary>
    /// Gets or sets a value indicating whether the source text should be persisted in the database.
    /// </summary>
    /// <value>
    /// Defaults to <see langword="true"/> if not set.
    /// </value>
    public bool? PersistSourceText { get; init; }
}

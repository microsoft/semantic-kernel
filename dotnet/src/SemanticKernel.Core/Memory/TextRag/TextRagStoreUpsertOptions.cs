// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Memory.TextRag;

/// <summary>
/// Contains options for <see cref="TextRagStore{TKey}.UpsertDocumentsAsync(System.Collections.Generic.IEnumerable{Microsoft.SemanticKernel.Memory.TextRag.TextRagDocument}, Microsoft.SemanticKernel.Memory.TextRag.TextRagStoreUpsertOptions?, System.Threading.CancellationToken)"/>.
/// </summary>
public sealed class TextRagStoreUpsertOptions
{
    /// <summary>
    /// Gets or sets a value indicating whether the source text should be persisted in the database.
    /// </summary>
    /// <value>
    /// Defaults to <see langword="true"/> if not set.
    /// </value>
    public bool? PersistSourceText { get; init; }
}

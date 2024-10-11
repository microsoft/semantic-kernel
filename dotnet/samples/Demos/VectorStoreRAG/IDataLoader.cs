// Copyright (c) Microsoft. All rights reserved.

namespace VectorStoreRAG;

/// <summary>
/// Interface for loading data into a data store.
/// </summary>
internal interface IDataLoader
{
    /// <summary>
    /// Load the text from a PDF file into the data store.
    /// </summary>
    /// <param name="pdfPath">The pdf file to load.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests.</param>
    /// <returns>An async task that completes when the loading is complete.</returns>
    Task LoadPdf(string pdfPath, CancellationToken cancellationToken);
}

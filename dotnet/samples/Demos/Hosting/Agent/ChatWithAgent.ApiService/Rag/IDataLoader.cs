// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Threading;
using System.Threading.Tasks;

namespace ChatWithAgent.ApiService;

/// <summary>
/// Interface for loading data into a data store.
/// </summary>
public interface IDataLoader
{
    /// <summary>
    /// Load the data from a file into the vector store.
    /// </summary>
    /// <param name="content">The pdf file content to load.</param>
    /// <param name="fileName">The name of the file.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests.</param>
    /// <returns>An async task that completes when the loading is complete.</returns>
    Task LoadAsync(Stream content, string fileName, CancellationToken cancellationToken);
}

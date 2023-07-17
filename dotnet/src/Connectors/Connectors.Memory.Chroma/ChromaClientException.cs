// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Chroma;

/// <summary>
/// Exception to identify issues in <see cref="ChromaClient"/> class.
/// </summary>
public class ChromaClientException : Exception
{
    private const string CollectionDoesNotExistErrorFormat = "Collection {0} does not exist";
    private const string DeleteNonExistentCollectionErrorMessage = "list index out of range";

    /// <summary>
    /// Initializes a new instance of the <see cref="ChromaClientException"/> class.
    /// </summary>
    public ChromaClientException() : base()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChromaClientException"/> class.
    /// </summary>
    /// <param name="message">The message that describes the error.</param>
    public ChromaClientException(string message) : base(message)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChromaClientException"/> class.
    /// </summary>
    /// <param name="message">The message that describes the error.</param>
    /// <param name="innerException">Instance of inner exception.</param>
    public ChromaClientException(string message, Exception innerException) : base(message, innerException)
    {
    }

    /// <summary>
    /// Checks if Chroma API error means that collection does not exist.
    /// </summary>
    /// <param name="collectionName">Collection name.</param>
    public bool CollectionDoesNotExistException(string collectionName) =>
        this.Message.Contains(string.Format(CultureInfo.InvariantCulture, CollectionDoesNotExistErrorFormat, collectionName));

    /// <summary>
    /// Checks if Chroma API error means that there was an attempt to delete non-existent collection.
    /// </summary>
    public bool DeleteNonExistentCollectionException() =>
        this.Message.Contains(DeleteNonExistentCollectionErrorMessage);
}

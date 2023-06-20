// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Chroma;

public class ChromaClientException : Exception
{
    private const string CollectionDoesNotExistErrorFormat = "Collection {0} does not exist";
    private const string DeleteNonExistingCollectionErrorMessage = "list index out of range";

    public ChromaClientException() : base()
    {
    }

    public ChromaClientException(string message) : base(message)
    {
    }

    public ChromaClientException(string message, Exception innerException) : base(message, innerException)
    {
    }

    public bool CollectionDoesNotExistException(string collectionName) =>
        this.Message.Contains(string.Format(CultureInfo.InvariantCulture, CollectionDoesNotExistErrorFormat, collectionName));

    public bool DeleteNonExistingCollectionException() =>
        this.Message.Contains(DeleteNonExistingCollectionErrorMessage);
}

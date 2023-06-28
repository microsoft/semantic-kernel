// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.TextCompletion;

internal sealed class OobaboogaInvalidResponseException<T> : AIException
{
    public T? ResponseData { get; }

    public OobaboogaInvalidResponseException(T? responseData, string? message = null) : base(ErrorCodes.InvalidResponseContent, message)
    {
        this.ResponseData = responseData;
    }
}

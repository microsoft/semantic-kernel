// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI;

#pragma warning disable RCS1194 // Implement exception constructors.

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

internal sealed class OpenAIInvalidResponseException<T> : AIException
{
    public T? ResponseData { get; }

    public OpenAIInvalidResponseException(T? responseData, string? message = null) : base(ErrorCodes.InvalidResponseContent, message)
    {
        this.ResponseData = responseData;
    }
}

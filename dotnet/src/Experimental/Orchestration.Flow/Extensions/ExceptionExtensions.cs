// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net;

namespace Microsoft.SemanticKernel.Experimental.Orchestration.Extensions;

internal static class ExceptionExtensions
{
    internal static bool IsNonRetryable(this Exception ex)
    {
        bool isContentFilterException = ex is HttpOperationException
        {
            StatusCode: HttpStatusCode.BadRequest, InnerException: { }
        } hoe && hoe.InnerException?.Message.Contains("content_filter") is true;

        return isContentFilterException || ex.IsCriticalException();
    }
}

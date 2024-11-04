// Copyright (c) Microsoft. All rights reserved.
using System;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Process.Internal;

internal static class ExceptionExtensions
{
    public static Exception Log(this Exception exception, ILogger? logger)
    {
        logger?.LogError(exception, "{ErrorMessage}", exception.Message);
        return exception;
    }
}

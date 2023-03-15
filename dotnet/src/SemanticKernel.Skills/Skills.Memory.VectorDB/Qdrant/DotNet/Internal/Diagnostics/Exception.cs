// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Qdrant.DotNet.Internal.Diagnostics;

public class Exception<TErrorType> : Exception where TErrorType : Enum
{
    public Exception(TErrorType errorType, string? message = null)
        : base(BuildMessage(errorType, message))
    {
    }

    #region private ================================================================================

    private static string BuildMessage(TErrorType errorType, string? message)
    {
        return message != null ? $"{errorType.ToString("G")}: {message}" : errorType.ToString("G");
    }

    public Exception()
    {
    }

    public Exception(string message) : base(message)
    {
    }

    #endregion
}

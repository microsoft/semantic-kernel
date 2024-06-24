// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Threading;

namespace System;

/// <summary>
/// Exception extension methods.
/// </summary>
[ExcludeFromCodeCoverage]
internal static class ExceptionExtensions
{
    /// <summary>
    /// Check if an exception is of a type that should not be caught by the kernel.
    /// </summary>
    /// <param name="ex">Exception.</param>
    /// <returns>True if <paramref name="ex"/> is a critical exception and should not be caught.</returns>
    internal static bool IsCriticalException(this Exception ex)
        => ex is ThreadAbortException
            or AccessViolationException
            or AppDomainUnloadedException
            or BadImageFormatException
            or CannotUnloadAppDomainException
            or InvalidProgramException;
}

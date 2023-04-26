// Copyright (c) Microsoft. All rights reserved.

using System.Threading;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Exception
namespace System;
#pragma warning restore IDE0130

/// <summary>
/// Exception extension methods.
/// </summary>
internal static class ExceptionExtensions
{
    /// <summary>
    /// Check if an exception is of a type that should not be caught by the kernel.
    /// </summary>
    /// <param name="ex">Exception.</param>
    /// <returns>True if <paramref name="ex"/> is a critical exception and should not be caught.</returns>
    internal static bool IsCriticalException(this Exception ex)
        => ex is OutOfMemoryException
            or ThreadAbortException
            or AccessViolationException
            or AppDomainUnloadedException
            or BadImageFormatException
            or CannotUnloadAppDomainException
            or InvalidProgramException
            or StackOverflowException;
}

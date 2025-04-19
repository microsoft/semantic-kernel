// Licensed to the .NET Foundation under one or more agreements.
// The .NET Foundation licenses this file to you under the MIT license.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using Microsoft.Shared.Collections;
using Microsoft.Shared.Diagnostics;

namespace Microsoft.Extensions.AI;

/// <summary>Provides context for an in-flight function invocation.</summary>
public partial class FunctionInvocationContextV2
{
    private static class Throw
    {
        /// <summary>
        /// Throws an <see cref="System.ArgumentNullException"/> if the specified argument is <see langword="null"/>.
        /// </summary>
        /// <typeparam name="T">Argument type to be checked for <see langword="null"/>.</typeparam>
        /// <param name="argument">Object to be checked for <see langword="null"/>.</param>
        /// <param name="paramName">The name of the parameter being checked.</param>
        /// <returns>The original value of <paramref name="argument"/>.</returns>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        [return: NotNull]
        public static T IfNull<T>([NotNull] T argument, [CallerArgumentExpression(nameof(argument))] string paramName = "")
        {
            if (argument is null)
            {
                throw new ArgumentNullException(paramName);
            }

            return argument;
        }

        /// <summary>
        /// Throws an <see cref="System.InvalidOperationException"/>.
        /// </summary>
        /// <param name="message">A message that describes the error.</param>
#if !NET6_0_OR_GREATER
    [MethodImpl(MethodImplOptions.NoInlining)]
#endif
        [DoesNotReturn]
        public static void InvalidOperationException(string message)
            => throw new InvalidOperationException(message);

        /// <summary>
        /// Throws an <see cref="System.ArgumentOutOfRangeException"/>.
        /// </summary>
        /// <param name="paramName">The name of the parameter that caused the exception.</param>
#if !NET6_0_OR_GREATER
    [MethodImpl(MethodImplOptions.NoInlining)]
#endif
        [DoesNotReturn]
        public static void ArgumentOutOfRangeException(string paramName)
            => throw new ArgumentOutOfRangeException(paramName);

        /// <summary>
        /// Throws an <see cref="System.ArgumentOutOfRangeException"/>.
        /// </summary>
        /// <param name="paramName">The name of the parameter that caused the exception.</param>
        /// <param name="message">A message that describes the error.</param>
#if !NET6_0_OR_GREATER
    [MethodImpl(MethodImplOptions.NoInlining)]
#endif
        [DoesNotReturn]
        public static void ArgumentOutOfRangeException(string paramName, string? message)
            => throw new ArgumentOutOfRangeException(paramName, message);

        /// <summary>
        /// Throws an <see cref="System.ArgumentOutOfRangeException"/>.
        /// </summary>
        /// <param name="paramName">The name of the parameter that caused the exception.</param>
        /// <param name="actualValue">The value of the argument that caused this exception.</param>
        /// <param name="message">A message that describes the error.</param>
#if !NET6_0_OR_GREATER
    [MethodImpl(MethodImplOptions.NoInlining)]
#endif
        [DoesNotReturn]
        public static void ArgumentOutOfRangeException(string paramName, object? actualValue, string? message)
            => throw new ArgumentOutOfRangeException(paramName, actualValue, message);

        /// <summary>
        /// Throws an <see cref="System.ArgumentOutOfRangeException"/>  if the specified number is less than min.
        /// </summary>
        /// <param name="argument">Number to be expected being less than min.</param>
        /// <param name="min">The number that must be less than the argument.</param>
        /// <param name="paramName">The name of the parameter being checked.</param>
        /// <returns>The original value of <paramref name="argument"/>.</returns>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static int IfLessThan(int argument, int min, [CallerArgumentExpression(nameof(argument))] string paramName = "")
        {
            if (argument < min)
            {
                ArgumentOutOfRangeException(paramName, argument, $"Argument less than minimum value {min}");
            }

            return argument;
        }
    }

    private static class LoggingHelpers
    {
        /// <summary>Serializes <paramref name="value" /> as JSON for logging purposes.</summary>
        public static string AsJson<T>(T value, System.Text.Json.JsonSerializerOptions? options)
        {
            if (options?.TryGetTypeInfo(typeof(T), out var typeInfo) is true ||
                AIJsonUtilities.DefaultOptions.TryGetTypeInfo(typeof(T), out typeInfo))
            {
                try
                {
                    return System.Text.Json.JsonSerializer.Serialize(value, typeInfo);
                }
#pragma warning disable CA1031 // Do not catch general exception types
                catch
#pragma warning restore CA1031 // Do not catch general exception types
                {
                }
            }

            return "{}";
        }
    }
}

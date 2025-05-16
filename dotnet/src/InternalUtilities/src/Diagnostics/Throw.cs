// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;

// Source Originally from: https://github.com/dotnet/extensions/blob/ef3f0a/src/Shared/Throw/Throw.cs

namespace Microsoft.SemanticKernel;

/// <summary>
/// Defines static methods used to throw exceptions.
/// </summary>
/// <remarks>
/// The main purpose is to reduce code size, improve performance, and standardize exception
/// messages.
/// </remarks>
[SuppressMessage("Minor Code Smell", "S4136:Method overloads should be grouped together", Justification = "Doesn't work with the region layout")]
[SuppressMessage("Minor Code Smell", "S2333:Partial is gratuitous in this context", Justification = "Some projects add additional partial parts.")]
[SuppressMessage("Design", "CA1716", Justification = "Not part of an API")]

[ExcludeFromCodeCoverage]
internal static partial class Throw
{
    #region For Object

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
            ArgumentNullException(paramName);
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentNullException"/> if the specified argument is <see langword="null"/>,
    /// or <see cref="System.ArgumentException" /> if the specified member is <see langword="null"/>.
    /// </summary>
    /// <typeparam name="TParameter">Argument type to be checked for <see langword="null"/>.</typeparam>
    /// <typeparam name="TMember">Member type to be checked for <see langword="null"/>.</typeparam>
    /// <param name="argument">Argument to be checked for <see langword="null"/>.</param>
    /// <param name="member">Object member to be checked for <see langword="null"/>.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <param name="memberName">The name of the member.</param>
    /// <returns>The original value of <paramref name="member"/>.</returns>
    /// <example>
    /// <code language="csharp">
    /// Throws.IfNullOrMemberNull(myObject, myObject?.MyProperty)
    /// </code>
    /// </example>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    [return: NotNull]
    public static TMember IfNullOrMemberNull<TParameter, TMember>(
        [NotNull] TParameter argument,
        [NotNull] TMember member,
        [CallerArgumentExpression(nameof(argument))] string paramName = "",
        [CallerArgumentExpression(nameof(member))] string memberName = "")
    {
        if (argument is null)
        {
            ArgumentNullException(paramName);
        }

        if (member is null)
        {
            ArgumentException(paramName, $"Member {memberName} of {paramName} is null");
        }

        return member;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentException" /> if the specified member is <see langword="null"/>.
    /// </summary>
    /// <typeparam name="TParameter">Argument type.</typeparam>
    /// <typeparam name="TMember">Member type to be checked for <see langword="null"/>.</typeparam>
    /// <param name="argument">Argument to which member belongs.</param>
    /// <param name="member">Object member to be checked for <see langword="null"/>.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <param name="memberName">The name of the member.</param>
    /// <returns>The original value of <paramref name="member"/>.</returns>
    /// <example>
    /// <code language="csharp">
    /// Throws.IfMemberNull(myObject, myObject.MyProperty)
    /// </code>
    /// </example>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    [return: NotNull]
    [SuppressMessage("Style", "IDE0060:Remove unused parameter", Justification = "Analyzer isn't seeing the reference to 'argument' in the attribute")]
    public static TMember IfMemberNull<TParameter, TMember>(
        TParameter argument,
        [NotNull] TMember member,
        [CallerArgumentExpression(nameof(argument))] string paramName = "",
        [CallerArgumentExpression(nameof(member))] string memberName = "")
        where TParameter : notnull
    {
        if (member is null)
        {
            ArgumentException(paramName, $"Member {memberName} of {paramName} is null");
        }

        return member;
    }

    #endregion

    #region For String

    /// <summary>
    /// Throws either an <see cref="System.ArgumentNullException"/> or an <see cref="System.ArgumentException"/>
    /// if the specified string is <see langword="null"/> or whitespace respectively.
    /// </summary>
    /// <param name="argument">String to be checked for <see langword="null"/> or whitespace.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    [return: NotNull]
    public static string IfNullOrWhitespace([NotNull] string? argument, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
#if !NETCOREAPP3_1_OR_GREATER
        if (argument == null)
        {
            ArgumentNullException(paramName);
        }
#endif

        if (string.IsNullOrWhiteSpace(argument))
        {
            if (argument == null)
            {
                ArgumentNullException(paramName);
            }
            else
            {
                ArgumentException(paramName, "Argument is whitespace");
            }
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentNullException"/> if the string is <see langword="null"/>,
    /// or <see cref="System.ArgumentException"/> if it is empty.
    /// </summary>
    /// <param name="argument">String to be checked for <see langword="null"/> or empty.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    [return: NotNull]
    public static string IfNullOrEmpty([NotNull] string? argument, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
#if !NETCOREAPP3_1_OR_GREATER
        if (argument == null)
        {
            ArgumentNullException(paramName);
        }
#endif

        if (string.IsNullOrEmpty(argument))
        {
            if (argument == null)
            {
                ArgumentNullException(paramName);
            }
            else
            {
                ArgumentException(paramName, "Argument is an empty string");
            }
        }

        return argument;
    }

    #endregion

    #region For Buffer

    /// <summary>
    /// Throws an <see cref="System.ArgumentException"/> if the argument's buffer size is less than the required buffer size.
    /// </summary>
    /// <param name="bufferSize">The actual buffer size.</param>
    /// <param name="requiredSize">The required buffer size.</param>
    /// <param name="paramName">The name of the parameter to be checked.</param>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static void IfBufferTooSmall(int bufferSize, int requiredSize, string paramName = "")
    {
        if (bufferSize < requiredSize)
        {
            ArgumentException(paramName, $"Buffer too small, needed a size of {requiredSize} but got {bufferSize}");
        }
    }

    #endregion

    #region For Enums

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the enum value is not valid.
    /// </summary>
    /// <param name="argument">The argument to evaluate.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <typeparam name="T">The type of the enumeration.</typeparam>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static T IfOutOfRange<T>(T argument, [CallerArgumentExpression(nameof(argument))] string paramName = "")
        where T : struct, Enum
    {
#if NET5_0_OR_GREATER
        if (!Enum.IsDefined<T>(argument))
#else
        if (!Enum.IsDefined(typeof(T), argument))
#endif
        {
            ArgumentOutOfRangeException(paramName, $"{argument} is an invalid value for enum type {typeof(T)}");
        }

        return argument;
    }

    #endregion

    #region For Collections

    /// <summary>
    /// Throws an <see cref="System.ArgumentNullException"/> if the collection is <see langword="null"/>,
    /// or <see cref="System.ArgumentException"/> if it is empty.
    /// </summary>
    /// <param name="argument">The collection to evaluate.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <typeparam name="T">The type of objects in the collection.</typeparam>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    [return: NotNull]

    // The method has actually 100% coverage, but due to a bug in the code coverage tool,
    // a lower number is reported. Therefore, we temporarily exclude this method
    // from the coverage measurements. Once the bug in the code coverage tool is fixed,
    // the exclusion attribute can be removed.
    [ExcludeFromCodeCoverage]
    public static IEnumerable<T> IfNullOrEmpty<T>([NotNull] IEnumerable<T>? argument, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        if (argument == null)
        {
            ArgumentNullException(paramName);
        }
        else
        {
            switch (argument)
            {
                case ICollection<T> collection:
                    if (collection.Count == 0)
                    {
                        ArgumentException(paramName, "Collection is empty");
                    }

                    break;
                case IReadOnlyCollection<T> readOnlyCollection:
                    if (readOnlyCollection.Count == 0)
                    {
                        ArgumentException(paramName, "Collection is empty");
                    }

                    break;
                default:
                    using (IEnumerator<T> enumerator = argument.GetEnumerator())
                    {
                        if (!enumerator.MoveNext())
                        {
                            ArgumentException(paramName, "Collection is empty");
                        }
                    }

                    break;
            }
        }

        return argument;
    }

    #endregion

    #region Exceptions

    /// <summary>
    /// Throws an <see cref="System.ArgumentNullException"/>.
    /// </summary>
    /// <param name="paramName">The name of the parameter that caused the exception.</param>
#if !NET6_0_OR_GREATER
    [MethodImpl(MethodImplOptions.NoInlining)]
#endif
    [DoesNotReturn]
    public static void ArgumentNullException(string paramName)
        => throw new ArgumentNullException(paramName);

    /// <summary>
    /// Throws an <see cref="System.ArgumentNullException"/>.
    /// </summary>
    /// <param name="paramName">The name of the parameter that caused the exception.</param>
    /// <param name="message">A message that describes the error.</param>
#if !NET6_0_OR_GREATER
    [MethodImpl(MethodImplOptions.NoInlining)]
#endif
    [DoesNotReturn]
    public static void ArgumentNullException(string paramName, string? message)
        => throw new ArgumentNullException(paramName, message);

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
    /// Throws an <see cref="System.ArgumentException"/>.
    /// </summary>
    /// <param name="paramName">The name of the parameter that caused the exception.</param>
    /// <param name="message">A message that describes the error.</param>
#if !NET6_0_OR_GREATER
    [MethodImpl(MethodImplOptions.NoInlining)]
#endif
    [DoesNotReturn]
    public static void ArgumentException(string paramName, string? message)
        => throw new ArgumentException(message, paramName);

    /// <summary>
    /// Throws an <see cref="System.ArgumentException"/>.
    /// </summary>
    /// <param name="paramName">The name of the parameter that caused the exception.</param>
    /// <param name="message">A message that describes the error.</param>
    /// <param name="innerException">The exception that is the cause of the current exception.</param>
    /// <remarks>
    /// If the <paramref name="innerException"/> is not a <see langword="null"/>, the current exception is raised in a catch
    /// block that handles the inner exception.
    /// </remarks>
#if !NET6_0_OR_GREATER
    [MethodImpl(MethodImplOptions.NoInlining)]
#endif
    [DoesNotReturn]
    public static void ArgumentException(string paramName, string? message, Exception? innerException)
        => throw new ArgumentException(message, paramName, innerException);

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
    /// Throws an <see cref="System.InvalidOperationException"/>.
    /// </summary>
    /// <param name="message">A message that describes the error.</param>
    /// <param name="innerException">The exception that is the cause of the current exception.</param>
#if !NET6_0_OR_GREATER
    [MethodImpl(MethodImplOptions.NoInlining)]
#endif
    [DoesNotReturn]
    public static void InvalidOperationException(string message, Exception? innerException)
        => throw new InvalidOperationException(message, innerException);

    #endregion

    #region For Integer

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

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is greater than max.
    /// </summary>
    /// <param name="argument">Number to be expected being greater than max.</param>
    /// <param name="max">The number that must be greater than the argument.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static int IfGreaterThan(int argument, int max, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        if (argument > max)
        {
            ArgumentOutOfRangeException(paramName, argument, $"Argument greater than maximum value {max}");
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is less or equal than min.
    /// </summary>
    /// <param name="argument">Number to be expected being less or equal than min.</param>
    /// <param name="min">The number that must be less or equal than the argument.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static int IfLessThanOrEqual(int argument, int min, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        if (argument <= min)
        {
            ArgumentOutOfRangeException(paramName, argument, $"Argument less or equal than minimum value {min}");
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is greater or equal than max.
    /// </summary>
    /// <param name="argument">Number to be expected being greater or equal than max.</param>
    /// <param name="max">The number that must be greater or equal than the argument.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static int IfGreaterThanOrEqual(int argument, int max, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        if (argument >= max)
        {
            ArgumentOutOfRangeException(paramName, argument, $"Argument greater or equal than maximum value {max}");
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is not in the specified range.
    /// </summary>
    /// <param name="argument">Number to be expected being greater or equal than max.</param>
    /// <param name="min">The lower bound of the allowed range of argument values.</param>
    /// <param name="max">The upper bound of the allowed range of argument values.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static int IfOutOfRange(int argument, int min, int max, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        if (argument < min || argument > max)
        {
            ArgumentOutOfRangeException(paramName, argument, $"Argument not in the range [{min}..{max}]");
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is equal to 0.
    /// </summary>
    /// <param name="argument">Number to be expected being not equal to zero.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static int IfZero(int argument, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        if (argument == 0)
        {
            ArgumentOutOfRangeException(paramName, "Argument is zero");
        }

        return argument;
    }

    #endregion

    #region For Unsigned Integer

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/>  if the specified number is less than min.
    /// </summary>
    /// <param name="argument">Number to be expected being less than min.</param>
    /// <param name="min">The number that must be less than the argument.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static uint IfLessThan(uint argument, uint min, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        if (argument < min)
        {
            ArgumentOutOfRangeException(paramName, argument, $"Argument less than minimum value {min}");
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is greater than max.
    /// </summary>
    /// <param name="argument">Number to be expected being greater than max.</param>
    /// <param name="max">The number that must be greater than the argument.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static uint IfGreaterThan(uint argument, uint max, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        if (argument > max)
        {
            ArgumentOutOfRangeException(paramName, argument, $"Argument greater than maximum value {max}");
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is less or equal than min.
    /// </summary>
    /// <param name="argument">Number to be expected being less or equal than min.</param>
    /// <param name="min">The number that must be less or equal than the argument.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static uint IfLessThanOrEqual(uint argument, uint min, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        if (argument <= min)
        {
            ArgumentOutOfRangeException(paramName, argument, $"Argument less or equal than minimum value {min}");
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is greater or equal than max.
    /// </summary>
    /// <param name="argument">Number to be expected being greater or equal than max.</param>
    /// <param name="max">The number that must be greater or equal than the argument.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static uint IfGreaterThanOrEqual(uint argument, uint max, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        if (argument >= max)
        {
            ArgumentOutOfRangeException(paramName, argument, $"Argument greater or equal than maximum value {max}");
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is not in the specified range.
    /// </summary>
    /// <param name="argument">Number to be expected being greater or equal than max.</param>
    /// <param name="min">The lower bound of the allowed range of argument values.</param>
    /// <param name="max">The upper bound of the allowed range of argument values.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static uint IfOutOfRange(uint argument, uint min, uint max, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        if (argument < min || argument > max)
        {
            ArgumentOutOfRangeException(paramName, argument, $"Argument not in the range [{min}..{max}]");
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is equal to 0.
    /// </summary>
    /// <param name="argument">Number to be expected being not equal to zero.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static uint IfZero(uint argument, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        if (argument == 0U)
        {
            ArgumentOutOfRangeException(paramName, "Argument is zero");
        }

        return argument;
    }

    #endregion

    #region For Long

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/>  if the specified number is less than min.
    /// </summary>
    /// <param name="argument">Number to be expected being less than min.</param>
    /// <param name="min">The number that must be less than the argument.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static long IfLessThan(long argument, long min, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        if (argument < min)
        {
            ArgumentOutOfRangeException(paramName, argument, $"Argument less than minimum value {min}");
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is greater than max.
    /// </summary>
    /// <param name="argument">Number to be expected being greater than max.</param>
    /// <param name="max">The number that must be greater than the argument.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static long IfGreaterThan(long argument, long max, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        if (argument > max)
        {
            ArgumentOutOfRangeException(paramName, argument, $"Argument greater than maximum value {max}");
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is less or equal than min.
    /// </summary>
    /// <param name="argument">Number to be expected being less or equal than min.</param>
    /// <param name="min">The number that must be less or equal than the argument.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static long IfLessThanOrEqual(long argument, long min, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        if (argument <= min)
        {
            ArgumentOutOfRangeException(paramName, argument, $"Argument less or equal than minimum value {min}");
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is greater or equal than max.
    /// </summary>
    /// <param name="argument">Number to be expected being greater or equal than max.</param>
    /// <param name="max">The number that must be greater or equal than the argument.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static long IfGreaterThanOrEqual(long argument, long max, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        if (argument >= max)
        {
            ArgumentOutOfRangeException(paramName, argument, $"Argument greater or equal than maximum value {max}");
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is not in the specified range.
    /// </summary>
    /// <param name="argument">Number to be expected being greater or equal than max.</param>
    /// <param name="min">The lower bound of the allowed range of argument values.</param>
    /// <param name="max">The upper bound of the allowed range of argument values.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static long IfOutOfRange(long argument, long min, long max, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        if (argument < min || argument > max)
        {
            ArgumentOutOfRangeException(paramName, argument, $"Argument not in the range [{min}..{max}]");
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is equal to 0.
    /// </summary>
    /// <param name="argument">Number to be expected being not equal to zero.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static long IfZero(long argument, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        if (argument == 0L)
        {
            ArgumentOutOfRangeException(paramName, "Argument is zero");
        }

        return argument;
    }

    #endregion

    #region For Unsigned Long

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/>  if the specified number is less than min.
    /// </summary>
    /// <param name="argument">Number to be expected being less than min.</param>
    /// <param name="min">The number that must be less than the argument.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static ulong IfLessThan(ulong argument, ulong min, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        if (argument < min)
        {
            ArgumentOutOfRangeException(paramName, argument, $"Argument less than minimum value {min}");
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is greater than max.
    /// </summary>
    /// <param name="argument">Number to be expected being greater than max.</param>
    /// <param name="max">The number that must be greater than the argument.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static ulong IfGreaterThan(ulong argument, ulong max, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        if (argument > max)
        {
            ArgumentOutOfRangeException(paramName, argument, $"Argument greater than maximum value {max}");
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is less or equal than min.
    /// </summary>
    /// <param name="argument">Number to be expected being less or equal than min.</param>
    /// <param name="min">The number that must be less or equal than the argument.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static ulong IfLessThanOrEqual(ulong argument, ulong min, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        if (argument <= min)
        {
            ArgumentOutOfRangeException(paramName, argument, $"Argument less or equal than minimum value {min}");
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is greater or equal than max.
    /// </summary>
    /// <param name="argument">Number to be expected being greater or equal than max.</param>
    /// <param name="max">The number that must be greater or equal than the argument.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static ulong IfGreaterThanOrEqual(ulong argument, ulong max, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        if (argument >= max)
        {
            ArgumentOutOfRangeException(paramName, argument, $"Argument greater or equal than maximum value {max}");
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is not in the specified range.
    /// </summary>
    /// <param name="argument">Number to be expected being greater or equal than max.</param>
    /// <param name="min">The lower bound of the allowed range of argument values.</param>
    /// <param name="max">The upper bound of the allowed range of argument values.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static ulong IfOutOfRange(ulong argument, ulong min, ulong max, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        if (argument < min || argument > max)
        {
            ArgumentOutOfRangeException(paramName, argument, $"Argument not in the range [{min}..{max}]");
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is equal to 0.
    /// </summary>
    /// <param name="argument">Number to be expected being not equal to zero.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static ulong IfZero(ulong argument, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        if (argument == 0UL)
        {
            ArgumentOutOfRangeException(paramName, "Argument is zero");
        }

        return argument;
    }

    #endregion

    #region For Double

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is less than min.
    /// </summary>
    /// <param name="argument">Number to be expected being less than min.</param>
    /// <param name="min">The number that must be less than the argument.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static double IfLessThan(double argument, double min, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        // strange conditional needed in order to handle NaN values correctly
#pragma warning disable S1940 // Boolean checks should not be inverted
        if (!(argument >= min))
#pragma warning restore S1940 // Boolean checks should not be inverted
        {
            ArgumentOutOfRangeException(paramName, argument, $"Argument less than minimum value {min}");
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is greater than max.
    /// </summary>
    /// <param name="argument">Number to be expected being greater than max.</param>
    /// <param name="max">The number that must be greater than the argument.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static double IfGreaterThan(double argument, double max, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        // strange conditional needed in order to handle NaN values correctly
#pragma warning disable S1940 // Boolean checks should not be inverted
        if (!(argument <= max))
#pragma warning restore S1940 // Boolean checks should not be inverted
        {
            ArgumentOutOfRangeException(paramName, argument, $"Argument greater than maximum value {max}");
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is less or equal than min.
    /// </summary>
    /// <param name="argument">Number to be expected being less or equal than min.</param>
    /// <param name="min">The number that must be less or equal than the argument.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static double IfLessThanOrEqual(double argument, double min, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        // strange conditional needed in order to handle NaN values correctly
#pragma warning disable S1940 // Boolean checks should not be inverted
        if (!(argument > min))
#pragma warning restore S1940 // Boolean checks should not be inverted
        {
            ArgumentOutOfRangeException(paramName, argument, $"Argument less or equal than minimum value {min}");
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is greater or equal than max.
    /// </summary>
    /// <param name="argument">Number to be expected being greater or equal than max.</param>
    /// <param name="max">The number that must be greater or equal than the argument.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static double IfGreaterThanOrEqual(double argument, double max, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        // strange conditional needed in order to handle NaN values correctly
#pragma warning disable S1940 // Boolean checks should not be inverted
        if (!(argument < max))
#pragma warning restore S1940 // Boolean checks should not be inverted
        {
            ArgumentOutOfRangeException(paramName, argument, $"Argument greater or equal than maximum value {max}");
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is not in the specified range.
    /// </summary>
    /// <param name="argument">Number to be expected being greater or equal than max.</param>
    /// <param name="min">The lower bound of the allowed range of argument values.</param>
    /// <param name="max">The upper bound of the allowed range of argument values.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static double IfOutOfRange(double argument, double min, double max, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
        // strange conditional needed in order to handle NaN values correctly
        if (!(min <= argument && argument <= max))
        {
            ArgumentOutOfRangeException(paramName, argument, $"Argument not in the range [{min}..{max}]");
        }

        return argument;
    }

    /// <summary>
    /// Throws an <see cref="System.ArgumentOutOfRangeException"/> if the specified number is equal to 0.
    /// </summary>
    /// <param name="argument">Number to be expected being not equal to zero.</param>
    /// <param name="paramName">The name of the parameter being checked.</param>
    /// <returns>The original value of <paramref name="argument"/>.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static double IfZero(double argument, [CallerArgumentExpression(nameof(argument))] string paramName = "")
    {
#pragma warning disable S1244 // Floating point numbers should not be tested for equality
        if (argument == 0.0)
#pragma warning restore S1244 // Floating point numbers should not be tested for equality
        {
            ArgumentOutOfRangeException(paramName, "Argument is zero");
        }

        return argument;
    }

    #endregion
}

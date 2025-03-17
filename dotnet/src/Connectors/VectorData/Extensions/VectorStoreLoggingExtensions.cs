// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.Extensions.VectorData;

internal static partial class VectorStoreLoggingExtensions
{
    internal static async Task RunWithLoggingAsync(
        ILogger logger,
        string operationName,
        Func<Task> operation)
    {
        logger.LogInvoked(operationName);

        try
        {
            await operation().ConfigureAwait(false);

            logger.LogCompleted(operationName);
        }
        catch (OperationCanceledException)
        {
            logger.LogInvocationCanceled(operationName);
            throw;
        }
        catch (Exception ex)
        {
            logger.LogInvocationFailed(operationName, ex);
            throw;
        }
    }

    internal static async Task<TResult> RunWithLoggingAsync<TResult>(
        ILogger logger,
        string operationName,
        Func<Task<TResult>> operation)
    {
        logger.LogInvoked(operationName);

        try
        {
            var result = await operation().ConfigureAwait(false);

            logger.LogCompleted(operationName);

            return result;
        }
        catch (OperationCanceledException)
        {
            logger.LogInvocationCanceled(operationName);
            throw;
        }
        catch (Exception ex)
        {
            logger.LogInvocationFailed(operationName, ex);
            throw;
        }
    }

    internal static async IAsyncEnumerable<TResult> RunWithLoggingAsync<TResult>(
        ILogger logger,
        string operationName,
        Func<IAsyncEnumerable<TResult>> operation,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        logger.LogInvoked(operationName);

        IAsyncEnumerator<TResult> enumerator;

        try
        {
            enumerator = operation().GetAsyncEnumerator(cancellationToken);
        }
        catch (OperationCanceledException)
        {
            logger.LogInvocationCanceled(operationName);
            throw;
        }
        catch (Exception ex)
        {
            logger.LogInvocationFailed(operationName, ex);
            throw;
        }

        try
        {
            while (true)
            {
                try
                {
                    if (!await enumerator.MoveNextAsync().ConfigureAwait(false))
                    {
                        break;
                    }
                }
                catch (OperationCanceledException)
                {
                    logger.LogInvocationCanceled(operationName);
                    throw;
                }
                catch (Exception ex)
                {
                    logger.LogInvocationFailed(operationName, ex);
                    throw;
                }

                yield return enumerator.Current;
            }

            logger.LogCompleted(operationName);
        }
        finally
        {
            await enumerator.DisposeAsync().ConfigureAwait(false);
        }
    }

    [UnconditionalSuppressMessage("AotAnalysis", "IL3050", Justification = "DefaultJsonTypeInfoResolver is only used when reflection-based serialization is enabled")]
    [UnconditionalSuppressMessage("ReflectionAnalysis", "IL2026", Justification = "DefaultJsonTypeInfoResolver is only used when reflection-based serialization is enabled")]
    internal static string AsJson<T>(T value, JsonSerializerOptions? options)
    {
        options ??= GetDefaultOptions(typeof(T));

        if (options is not null)
        {
            try
            {
                return JsonSerializer.Serialize(value, options);
            }
#pragma warning disable CA1031 // Do not catch general exception types
            catch
#pragma warning restore CA1031 
            {
            }
        }

        // If options are not available, or if we fail to serialize, return an empty JSON object.
        return "{}";
    }

    #region private

    private static JsonSerializerOptions? s_jsonSerializerOptions;

    [UnconditionalSuppressMessage("AotAnalysis", "IL3050", Justification = "DefaultJsonTypeInfoResolver is only used when reflection-based serialization is enabled")]
    [UnconditionalSuppressMessage("ReflectionAnalysis", "IL2026", Justification = "DefaultJsonTypeInfoResolver is only used when reflection-based serialization is enabled")]
    private static JsonSerializerOptions? GetDefaultOptions(Type vectorStoreRecordType)
    {
        if (s_jsonSerializerOptions is null && JsonSerializer.IsReflectionEnabledByDefault)
        {
            JsonSerializerOptions options = new()
            {
                TypeInfoResolver = new DefaultJsonTypeInfoResolver() { Modifiers = { IgnoreVectorProperties } },
                Converters = { new JsonStringEnumConverter() },
                DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
                Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
                WriteIndented = true
            };
            options.MakeReadOnly();
            s_jsonSerializerOptions = options;
        }

        return s_jsonSerializerOptions;

        // Local function to ignore vector properties in type serialization.
        void IgnoreVectorProperties(JsonTypeInfo typeInfo)
        {
            // Only apply to the vector store record type
            if (typeInfo.Type != vectorStoreRecordType)
            {
                return;
            }

            var vectorProperties = vectorStoreRecordType
                .GetProperties()
                .Where(l => l.GetCustomAttributes(typeof(VectorStoreRecordVectorAttribute), false).Length > 0)
                .Select(l => l.Name)
                .ToArray();

            var uniqueVectorProperties = new HashSet<string>(vectorProperties);

            foreach (var property in typeInfo.Properties)
            {
                if (vectorProperties.Contains(property.Name))
                {
                    // Set ShouldSerialize to false to ignore vector property
                    property.ShouldSerialize = static (obj, value) => false;
                }
            }
        }
    }

    [LoggerMessage(LogLevel.Debug, "{OperationName} invoked.")]
    private static partial void LogInvoked(this ILogger logger, string operationName);

    [LoggerMessage(LogLevel.Debug, "{OperationName} completed.")]
    private static partial void LogCompleted(this ILogger logger, string operationName);

    [LoggerMessage(LogLevel.Debug, "{OperationName} canceled.")]
    private static partial void LogInvocationCanceled(this ILogger logger, string operationName);

    [LoggerMessage(LogLevel.Error, "{OperationName} failed.")]
    private static partial void LogInvocationFailed(this ILogger logger, string operationName, Exception exception);

    #endregion
}

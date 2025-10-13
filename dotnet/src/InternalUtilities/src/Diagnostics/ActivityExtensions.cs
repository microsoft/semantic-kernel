// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Text.Json.Serialization.Metadata;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Diagnostics;

[ExcludeFromCodeCoverage]
internal static class ActivityExtensions
{
    /// <summary>
    /// Starts an activity with the appropriate tags for a kernel function execution.
    /// </summary>
    [UnconditionalSuppressMessage("Trimming", "IL2026:Members annotated with 'RequiresUnreferencedCodeAttribute' require dynamic access otherwise can break functionality when trimming application code", Justification = "The warning is shown and should be addressed at the function creation site; there is no need to show it again at the function invocation sites.")]
    [UnconditionalSuppressMessage("AOT", "IL3050:Calling members annotated with 'RequiresDynamicCodeAttribute' may break functionality when AOT compiling.", Justification = "The warning is shown and should be addressed at the function creation site; there is no need to show it again at the function invocation sites.")]
    public static Activity? StartFunctionActivity(
        this ActivitySource source,
        string functionName,
        string functionDescription,
        KernelArguments arguments,
        JsonSerializerOptions? jsonSerializerOptions = null)
    {
        const string OperationName = "execute_tool";

        List<KeyValuePair<string, object?>> tags =
        [
            new KeyValuePair<string, object?>("gen_ai.operation.name", OperationName),
            new KeyValuePair<string, object?>("gen_ai.tool.name", functionName),
            new KeyValuePair<string, object?>("gen_ai.tool.description", functionDescription),
        ];

#pragma warning disable SKEXP0001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
        if (ModelDiagnostics.IsSensitiveEventsEnabled())
        {
            tags.Add(new KeyValuePair<string, object?>("gen_ai.tool.call.arguments", SerializeArguments(arguments, jsonSerializerOptions)));
        }
#pragma warning restore SKEXP0001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

        return source.StartActivityWithTags($"{OperationName} {functionName}", tags, ActivityKind.Internal);

        [RequiresUnreferencedCode("Calls System.Text.Json.JsonSerializer.Serialize<TValue>(TValue, JsonSerializerOptions)")]
        [RequiresDynamicCode("Calls System.Text.Json.JsonSerializer.Serialize<TValue>(TValue, JsonSerializerOptions)")]
        static string SerializeArguments(KernelArguments args, JsonSerializerOptions? jsonSerializerOptions)
        {
            try
            {
                if (jsonSerializerOptions is not null)
                {
                    JsonTypeInfo<KernelArguments> typeInfo = (JsonTypeInfo<KernelArguments>)jsonSerializerOptions.GetTypeInfo(typeof(KernelArguments));
                    return JsonSerializer.Serialize(args, typeInfo);
                }

                return JsonSerializer.Serialize(args);
            }
            catch (NotSupportedException)
            {
                return "Failed to serialize arguments to Json";
            }
        }
    }

    /// <summary>
    /// Sets the function result tag on the activity, serializing the result if necessary.
    /// </summary>
    [UnconditionalSuppressMessage("Trimming", "IL2026:Members annotated with 'RequiresUnreferencedCodeAttribute' require dynamic access otherwise can break functionality when trimming application code", Justification = "The warning is shown and should be addressed at the function creation site; there is no need to show it again at the function invocation sites.")]
    [UnconditionalSuppressMessage("AOT", "IL3050:Calling members annotated with 'RequiresDynamicCodeAttribute' may break functionality when AOT compiling.", Justification = "The warning is shown and should be addressed at the function creation site; there is no need to show it again at the function invocation sites.")]
    public static Activity? SetFunctionResultTag(this Activity? activity, FunctionResult result, JsonSerializerOptions? jsonSerializerOptions = null)
    {
#pragma warning disable SKEXP0001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
        if (ModelDiagnostics.IsSensitiveEventsEnabled())
        {
            activity?.SetTag("gen_ai.tool.call.result", SerializeResult(result, jsonSerializerOptions));
        }
#pragma warning restore SKEXP0001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

        return activity;

        [SuppressMessage("Design", "CA1031:Do not catch general exception types", Justification = "By design. See comment below.")]
        [RequiresUnreferencedCode("Calls System.Text.Json.JsonSerializer.Serialize<TValue>(TValue, JsonSerializerOptions)")]
        [RequiresDynamicCode("Calls System.Text.Json.JsonSerializer.Serialize<TValue>(TValue, JsonSerializerOptions)")]
        static string SerializeResult(FunctionResult result, JsonSerializerOptions? jsonSerializerOptions)
        {
            // Try to retrieve the result as a string first
            try
            {
                return result.GetValue<string>() ?? string.Empty;
            }
            catch { }

            // Fallback to JSON serialization
            try
            {
                if (jsonSerializerOptions is not null)
                {
                    JsonTypeInfo<object?> typeInfo = (JsonTypeInfo<object?>)jsonSerializerOptions.GetTypeInfo(typeof(object));
                    return JsonSerializer.Serialize(result.GetValue<object?>(), typeInfo);
                }
                return JsonSerializer.Serialize(result.GetValue<object?>());
            }
            catch (NotSupportedException)
            {
                return "Failed to serialize result to Json";
            }
        }
    }

    /// <summary>
    /// Starts an activity with the specified name and tags.
    /// </summary>
    public static Activity? StartActivityWithTags(this ActivitySource source, string name, IEnumerable<KeyValuePair<string, object?>> tags, ActivityKind kind = ActivityKind.Internal)
        => source.StartActivity(name, kind, default(ActivityContext), tags);

    /// <summary>
    /// Adds tags to the activity.
    /// </summary>
    public static Activity SetTags(this Activity activity, ReadOnlySpan<KeyValuePair<string, object?>> tags)
    {
        foreach (var tag in tags)
        {
            activity.SetTag(tag.Key, tag.Value);
        }

        return activity;
    }

    /// <summary>
    /// Adds an event to the activity. Should only be used for events that contain sensitive data.
    /// </summary>
    public static Activity AttachSensitiveDataAsEvent(this Activity activity, string name, IEnumerable<KeyValuePair<string, object?>> tags)
    {
        activity.AddEvent(new ActivityEvent(
            name,
            tags: [.. tags]
        ));

        return activity;
    }

    /// <summary>
    /// Sets the error status and type on the activity.
    /// </summary>
    public static Activity SetError(this Activity activity, Exception exception)
    {
        activity.SetTag("error.type", exception.GetType().FullName);
        activity.SetStatus(ActivityStatusCode.Error, exception.Message);
        return activity;
    }

    public static async IAsyncEnumerable<TResult> RunWithActivityAsync<TResult>(
        Func<Activity?> getActivity,
        Func<IAsyncEnumerable<TResult>> operation,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        using var activity = getActivity();

        ConfiguredCancelableAsyncEnumerable<TResult> result;

        try
        {
            result = operation().WithCancellation(cancellationToken).ConfigureAwait(false);
        }
        catch (Exception ex) when (activity is not null)
        {
            activity.SetError(ex);
            throw;
        }

        var resultEnumerator = result.ConfigureAwait(false).GetAsyncEnumerator();

        try
        {
            while (true)
            {
                try
                {
                    if (!await resultEnumerator.MoveNextAsync())
                    {
                        break;
                    }
                }
                catch (Exception ex) when (activity is not null)
                {
                    activity.SetError(ex);
                    throw;
                }

                yield return resultEnumerator.Current;
            }
        }
        finally
        {
            await resultEnumerator.DisposeAsync();
        }
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization.Metadata;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A builder class for creating <see cref="FunctionCallContent"/> objects from incremental function call updates represented by <see cref="StreamingFunctionCallUpdateContent"/>.
/// </summary>
public sealed class FunctionCallContentBuilder
{
    private Dictionary<string, string>? _functionCallIdsByIndex = null;
    private Dictionary<string, string>? _functionNamesByIndex = null;
    private Dictionary<string, StringBuilder>? _functionArgumentBuildersByIndex = null;
    private readonly JsonSerializerOptions? _jsonSerializerOptions;

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionCallContentBuilder"/> class.
    /// </summary>
    [RequiresUnreferencedCode("Uses reflection to deserialize function arguments, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to deserialize function arguments, making it incompatible with AOT scenarios.")]
    public FunctionCallContentBuilder()
    {
    }

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionCallContentBuilder"/> class.
    /// </summary>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for deserializing function arguments.</param>
    [Experimental("SKEXP0120")]
    public FunctionCallContentBuilder(JsonSerializerOptions jsonSerializerOptions)
    {
        this._jsonSerializerOptions = jsonSerializerOptions;
    }

    /// <summary>
    /// Extracts function call updates from the content and track them for later building.
    /// </summary>
    /// <param name="content">The content to extract function call updates from.</param>
    public void Append(StreamingChatMessageContent content)
    {
        var streamingFunctionCallUpdates = content.Items.OfType<StreamingFunctionCallUpdateContent>();

        foreach (var update in streamingFunctionCallUpdates)
        {
            TrackStreamingFunctionCallUpdate(update,
                ref this._functionCallIdsByIndex,
                ref this._functionNamesByIndex,
                ref this._functionArgumentBuildersByIndex);
        }
    }

    /// <summary>
    /// Builds a list of <see cref="FunctionCallContent"/> out of function call updates tracked by the <see cref="Append"/> method.
    /// </summary>
    /// <returns>A list of <see cref="FunctionCallContent"/> objects.</returns>
    public IReadOnlyList<FunctionCallContent> Build()
    {
        FunctionCallContent[]? functionCalls = null;

        if (this._functionCallIdsByIndex is { Count: > 0 })
        {
            functionCalls = new FunctionCallContent[this._functionCallIdsByIndex.Count];

            for (int i = 0; i < this._functionCallIdsByIndex.Count; i++)
            {
                KeyValuePair<string, string> functionCallIndexAndId = this._functionCallIdsByIndex.ElementAt(i);

                string? pluginName = null;
                string functionName = string.Empty;

                if (this._functionNamesByIndex?.TryGetValue(functionCallIndexAndId.Key, out string? fqn) ?? false)
                {
                    var functionFullyQualifiedName = Microsoft.SemanticKernel.FunctionName.Parse(fqn);
                    pluginName = functionFullyQualifiedName.PluginName;
                    functionName = functionFullyQualifiedName.Name;
                }

                (KernelArguments? arguments, Exception? exception) = GetFunctionArgumentsSafe(functionCallIndexAndId.Key);

                functionCalls[i] = new FunctionCallContent(
                    functionName: functionName,
                    pluginName: pluginName,
                    id: functionCallIndexAndId.Value,
                    arguments)
                {
                    Exception = exception
                };
            }

            [UnconditionalSuppressMessage("Trimming", "IL2026:Members annotated with 'RequiresUnreferencedCodeAttribute' require dynamic access otherwise can break functionality when trimming application code", Justification = "The warning is shown and should be addressed at the class creation site; there is no need to show it again at the function invocation sites.")]
            [UnconditionalSuppressMessage("AOT", "IL3050:Calling members annotated with 'RequiresDynamicCodeAttribute' may break functionality when AOT compiling.", Justification = "The warning is shown and should be addressed at the class creation site; there is no need to show it again at the function invocation sites.")]
            (KernelArguments? Arguments, Exception? Exception) GetFunctionArgumentsSafe(string functionCallIndex)
            {
                if (this._jsonSerializerOptions is not null)
                {
                    return this.GetFunctionArguments(functionCallIndex, this._jsonSerializerOptions);
                }

                return this.GetFunctionArguments(functionCallIndex);
            }
        }

        return functionCalls ?? [];
    }

    /// <summary>
    /// Gets function arguments for a given function call index.
    /// </summary>
    /// <param name="functionCallIndex">The function call index to get the function arguments for.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for deserializing function arguments.</param>
    /// <returns>A tuple containing the KernelArguments and an Exception if any.</returns>
    [RequiresUnreferencedCode("Uses reflection to deserialize function arguments if no JSOs are provided, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to deserialize function arguments if no JSOs are provided, making it incompatible with AOT scenarios.")]
    private (KernelArguments? Arguments, Exception? Exception) GetFunctionArguments(string functionCallIndex, JsonSerializerOptions? jsonSerializerOptions = null)
    {
        if (this._functionArgumentBuildersByIndex is null ||
            !this._functionArgumentBuildersByIndex.TryGetValue(functionCallIndex, out StringBuilder? functionArgumentsBuilder))
        {
            return (null, null);
        }

        var argumentsString = functionArgumentsBuilder.ToString();
        if (string.IsNullOrEmpty(argumentsString))
        {
            return (null, null);
        }

        Exception? exception = null;
        KernelArguments? arguments = null;
        try
        {
            if (jsonSerializerOptions is not null)
            {
                var typeInfo = (JsonTypeInfo<KernelArguments>)jsonSerializerOptions.GetTypeInfo(typeof(KernelArguments));
                arguments = JsonSerializer.Deserialize<KernelArguments>(argumentsString, typeInfo);
            }
            else
            {
                arguments = JsonSerializer.Deserialize<KernelArguments>(argumentsString);
            }

            if (arguments is { Count: > 0 })
            {
                var names = arguments.Names.ToArray();
                foreach (var name in names)
                {
                    arguments[name] = arguments[name]?.ToString();
                }
            }
        }
        catch (JsonException ex)
        {
            exception = new KernelException("Error: Function call arguments were invalid JSON.", ex);
        }

        return (arguments, exception);
    }

    /// <summary>
    /// Tracks streaming function call update contents.
    /// </summary>
    /// <param name="update">The streaming function call update content to track.</param>
    /// <param name="functionCallIdsByIndex">The dictionary of function call IDs by function call index.</param>
    /// <param name="functionNamesByIndex">The dictionary of function names by function call index.</param>
    /// <param name="functionArgumentBuildersByIndex">The dictionary of function argument builders by function call index.</param>
    private static void TrackStreamingFunctionCallUpdate(StreamingFunctionCallUpdateContent update, ref Dictionary<string, string>? functionCallIdsByIndex, ref Dictionary<string, string>? functionNamesByIndex, ref Dictionary<string, StringBuilder>? functionArgumentBuildersByIndex)
    {
        if (update is null)
        {
            // Nothing to track.
            return;
        }

        // Create index that is unique across many requests.
        var functionCallIndex = $"{update.RequestIndex}-{update.FunctionCallIndex}";

        // If we have an call id, ensure the index is being tracked. Even if it's not a function update,
        // we want to keep track of it so we can send back an error.
        if (update.CallId is string id && !string.IsNullOrEmpty(id))
        {
            (functionCallIdsByIndex ??= [])[functionCallIndex] = id;
        }

        // Ensure we're tracking the function's name.
        if (update.Name is string name && !string.IsNullOrEmpty(name))
        {
            (functionNamesByIndex ??= [])[functionCallIndex] = name;
        }

        // Ensure we're tracking the function's arguments.
        if (update.Arguments is string argumentsUpdate)
        {
            if (!(functionArgumentBuildersByIndex ??= []).TryGetValue(functionCallIndex, out StringBuilder? arguments))
            {
                functionArgumentBuildersByIndex[functionCallIndex] = arguments = new();
            }

            arguments.Append(argumentsUpdate);
        }
    }
}

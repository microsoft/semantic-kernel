// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text;
using System.Text.Json;
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
using System.Text.Json.Serialization.Metadata;
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
using System.Text.Json.Serialization.Metadata;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
using System.Text.Json.Serialization.Metadata;
>>>>>>> main
>>>>>>> Stashed changes

namespace Microsoft.SemanticKernel;

/// <summary>
/// A builder class for creating <see cref="FunctionCallContent"/> objects from incremental function call updates represented by <see cref="StreamingFunctionCallUpdateContent"/>.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class FunctionCallContentBuilder
{
private Dictionary<int, string> _functionCallIdsByIndex = new();
    private Dictionary<int, string>? _functionNamesByIndex = null;
    private Dictionary<int, StringBuilder>? _functionArgumentBuildersByIndex = null;

    /// <summary>
    /// Extracts function call updates from the content and track them for later building.
    /// </summary>
    /// <param name="content">The content to extract function call updates from.</param>
public void Append(StreamingChatMessageContent content)
{
    if (content == null)
    {
        throw new ArgumentNullException(nameof(content));
    }
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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    public IReadOnlyList<FunctionCallContent> Build()
    {
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    public IReadOnlyList<FunctionCallContent> Build()
    {
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
    public IReadOnlyList<FunctionCallContent> Build()
    {
=======
>>>>>>> Stashed changes
    [RequiresUnreferencedCode("Uses reflection to deserialize function arguments, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to deserialize function arguments, making it incompatible with AOT scenarios.")]
    public IReadOnlyList<FunctionCallContent> Build()
    {
        return this.BuildInternal(jsonSerializerOptions: null);
    }

    /// <summary>
    /// Builds a list of <see cref="FunctionCallContent"/> out of function call updates tracked by the <see cref="Append"/> method.
    /// </summary>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for deserializing function arguments.</param>
    /// <returns>A list of <see cref="FunctionCallContent"/> objects.</returns>
    [UnconditionalSuppressMessage("Trimming", "IL2026:Members annotated with 'RequiresUnreferencedCodeAttribute' require dynamic access otherwise can break functionality when trimming application code", Justification = "This method is AOT save.")]
    [UnconditionalSuppressMessage("AOT", "IL3050:Calling members annotated with 'RequiresDynamicCodeAttribute' may break functionality when AOT compiling.", Justification = "This method is AOT safe.")]
    public IReadOnlyList<FunctionCallContent> Build(JsonSerializerOptions jsonSerializerOptions)
    {
        return this.BuildInternal(jsonSerializerOptions: jsonSerializerOptions);
    }

    /// <summary>
    /// Builds a list of <see cref="FunctionCallContent"/> out of function call updates tracked by the <see cref="Append"/> method.
    /// </summary>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for deserializing function arguments.</param>
    /// <returns>A list of <see cref="FunctionCallContent"/> objects.</returns>
    [RequiresUnreferencedCode("Uses reflection to deserialize function arguments if no JSOs are provided, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to deserialize function arguments if no JSOs are provided, making it incompatible with AOT scenarios.")]
    private FunctionCallContent[] BuildInternal(JsonSerializerOptions? jsonSerializerOptions)
    {
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        FunctionCallContent[]? functionCalls = null;

        if (this._functionCallIdsByIndex is { Count: > 0 })
        {
            functionCalls = new FunctionCallContent[this._functionCallIdsByIndex.Count];

            for (int i = 0; i < this._functionCallIdsByIndex.Count; i++)
            {
                KeyValuePair<int, string> functionCallIndexAndId = this._functionCallIdsByIndex.ElementAt(i);

                string? pluginName = null;
                string functionName = string.Empty;

                if (this._functionNamesByIndex?.TryGetValue(functionCallIndexAndId.Key, out string? fqn) ?? false)
                {
                    var functionFullyQualifiedName = Microsoft.SemanticKernel.FunctionName.Parse(fqn);
                    pluginName = functionFullyQualifiedName.PluginName;
                    functionName = functionFullyQualifiedName.Name;
                }

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                (KernelArguments? arguments, Exception? exception) = this.GetFunctionArguments(functionCallIndexAndId.Key);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
                (KernelArguments? arguments, Exception? exception) = this.GetFunctionArguments(functionCallIndexAndId.Key);
=======
                (KernelArguments? arguments, Exception? exception) = this.GetFunctionArguments(functionCallIndexAndId.Key, jsonSerializerOptions);
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
                (KernelArguments? arguments, Exception? exception) = this.GetFunctionArguments(functionCallIndexAndId.Key, jsonSerializerOptions);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes

                functionCalls[i] = new FunctionCallContent(
                    functionName: functionName,
                    pluginName: pluginName,
                    id: functionCallIndexAndId.Value,
                    arguments)
                {
                    Exception = exception
                };
            }
        }

        return functionCalls ?? Array.Empty<FunctionCallContent>();
    }

    /// <summary>
    /// Gets function arguments for a given function call index.
    /// </summary>
    /// <param name="functionCallIndex">The function call index to get the function arguments for.</param>
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    /// <returns>A tuple containing the KernelArguments and an Exception if any.</returns>
    private (KernelArguments? Arguments, Exception? Exception) GetFunctionArguments(int functionCallIndex)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    /// <returns>A tuple containing the KernelArguments and an Exception if any.</returns>
    private (KernelArguments? Arguments, Exception? Exception) GetFunctionArguments(int functionCallIndex)
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
    /// <returns>A tuple containing the KernelArguments and an Exception if any.</returns>
    private (KernelArguments? Arguments, Exception? Exception) GetFunctionArguments(int functionCallIndex)
=======
>>>>>>> Stashed changes
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for deserializing function arguments.</param>
    /// <returns>A tuple containing the KernelArguments and an Exception if any.</returns>
    [RequiresUnreferencedCode("Uses reflection to deserialize function arguments if no JSOs are provided, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to deserialize function arguments if no JSOs are provided, making it incompatible with AOT scenarios.")]
    private (KernelArguments? Arguments, Exception? Exception) GetFunctionArguments(int functionCallIndex, JsonSerializerOptions? jsonSerializerOptions = null)
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    {
        if (this._functionArgumentBuildersByIndex is null ||
            !this._functionArgumentBuildersByIndex.TryGetValue(functionCallIndex, out StringBuilder? functionArgumentsBuilder))
        {
            return (null, null);
        }

        var argumentsString = functionArgumentsBuilder.ToString();
        if (string.IsNullOrWhiteSpace(argumentsString))
        {
            return (null, null);
        }

        Exception? exception = null;
        KernelArguments? arguments = null;
        try
        {
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            arguments = JsonSerializer.Deserialize<KernelArguments>(argumentsString);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
            arguments = JsonSerializer.Deserialize<KernelArguments>(argumentsString);
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
            arguments = JsonSerializer.Deserialize<KernelArguments>(argumentsString);
=======
>>>>>>> Stashed changes
            if (jsonSerializerOptions is not null)
            {
                var typeInfo = (JsonTypeInfo<KernelArguments>)jsonSerializerOptions.GetTypeInfo(typeof(KernelArguments));
                arguments = JsonSerializer.Deserialize<KernelArguments>(argumentsString, typeInfo);
            }
            else
            {
                arguments = JsonSerializer.Deserialize<KernelArguments>(argumentsString);
            }

<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
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
    private static void TrackStreamingFunctionCallUpdate(StreamingFunctionCallUpdateContent update, ref Dictionary<int, string>? functionCallIdsByIndex, ref Dictionary<int, string>? functionNamesByIndex, ref Dictionary<int, StringBuilder>? functionArgumentBuildersByIndex)
    {
        if (update is null)
        {
            throw new ArgumentNullException(nameof(update));
        }
        {
            // Nothing to track.
            return;
        }

        // If we have an call id, ensure the index is being tracked. Even if it's not a function update,
        // we want to keep track of it so we can send back an error.
        if (update.CallId is string id)
        {
            (functionCallIdsByIndex ??= [])[update.FunctionCallIndex] = id;
        }

        // Ensure we're tracking the function's name.
        if (update.Name is string name)
        {
            (functionNamesByIndex ??= [])[update.FunctionCallIndex] = name;
        }

        // Ensure we're tracking the function's arguments.
        if (update.Arguments is string argumentsUpdate)
        {
            if (!(functionArgumentBuildersByIndex ??= []).TryGetValue(update.FunctionCallIndex, out StringBuilder? arguments))
            {
                functionArgumentBuildersByIndex[update.FunctionCallIndex] = arguments = new();
            }

            arguments.Append(argumentsUpdate);
        }
    }
}

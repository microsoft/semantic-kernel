// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Runtime;

/// <summary>
/// Defines a contract for saving and loading the state of an object.
/// The state must be JSON serializable.
/// </summary>
public interface ISaveState
{
    /// <summary>
    /// Saves the current state of the object.
    /// </summary>
    /// <returns>
    /// A task representing the asynchronous operation, returning a dictionary
    /// containing the saved state. The structure of the state is implementation-defined
    /// but must be JSON serializable.
    /// </returns>
    ValueTask<JsonElement> SaveStateAsync();

    /// <summary>
    /// Loads a previously saved state into the object.
    /// </summary>
    /// <param name="state">
    /// A dictionary representing the saved state. The structure of the state
    /// is implementation-defined but must be JSON serializable.
    /// </param>
    /// <returns>A task representing the asynchronous operation.</returns>
    ValueTask LoadStateAsync(JsonElement state);
}

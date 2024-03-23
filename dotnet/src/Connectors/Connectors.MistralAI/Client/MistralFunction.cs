// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;

/// <summary>
/// A function to be used in the chat completion request.
/// </summary>
internal class MistralFunction
{
    /// <summary>
    /// The name of the function to be called.Must be a-z,A-Z,0-9 or contain underscores and dashes, with a maximum length of 64.
    /// </summary>
    public string Name { get; set; }

    /// <summary>
    /// The description of the function to help the model determine when and how to invoke it.
    /// </summary>
    public String? Description { get; set; }

    /// <summary>
    /// The function parameters, defined using a JSON Schema object. If omitted, the function is considered to have an empty parameter list.
    /// </summary>
    public object? Parameters { get; set; }

    /// <summary>
    /// Construct an instance of <see cref="MistralFunction"/>.
    /// </summary>
    public MistralFunction(string name, string description, object parameters)
    {
        Verify.NotNull(name, nameof(name));
        Verify.ValidFunctionName(name);
        Verify.True(name.Length <= 64, "The name of the function must be less than or equal to 64 characters.", nameof(name));

        this.Name = name;
        this.Description = description;
        this.Parameters = parameters;
    }
}

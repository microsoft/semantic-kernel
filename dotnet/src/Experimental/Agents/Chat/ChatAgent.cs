// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Experimental.Agents.Chat;

/// <summary>
/// $$$
/// </summary>
public sealed class ChatAgent : KernelAgent<ChatChannel>
{
    /// <inheritdoc/>
    public override string? Description { get; }

    /// <inheritdoc/>
    public override string Id { get; }

    /// <inheritdoc/>
    public override string? Instructions { get; }

    /// <inheritdoc/>
    public override string? Name { get; }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="kernel"></param>
    /// <param name="instructions"></param>
    /// <param name="description"></param>
    /// <param name="name"></param>
    public ChatAgent(
        Kernel kernel,
        string? instructions,
        string? description,
        string? name)
       : base(kernel)
    {
        this.Id = Guid.NewGuid().ToString();
        this.Description = description;
        this.Instructions = instructions;
        this.Name = name;
    }
}

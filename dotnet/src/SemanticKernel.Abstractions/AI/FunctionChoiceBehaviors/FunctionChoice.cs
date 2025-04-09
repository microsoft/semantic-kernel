// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents an AI model's decision-making strategy for calling functions, offering predefined choices: Auto, Required, and None.
/// Auto allows the model to decide if and which functions to call, Required enforces calling one or more functions, and None prevents any function calls, generating only a user-facing message.
/// </summary>
public readonly struct FunctionChoice : IEquatable<FunctionChoice>
{
    /// <summary>
    /// This choice instructs the model to decide whether to call the functions or not and, if so, which ones to call.
    /// </summary>
    public static FunctionChoice Auto { get; } = new("auto");

    /// <summary>
    /// This choice forces the model to always call one or more functions. The model will then select which function(s) to call.
    /// </summary>
    public static FunctionChoice Required { get; } = new("required");

    /// <summary>
    /// This behavior forces the model to not call any functions and only generate a user-facing message.
    /// </summary>
    public static FunctionChoice None { get; } = new("none");

    /// <summary>
    /// Gets the label associated with this FunctionChoice.
    /// </summary>
    public string Label { get; }

    /// <summary>
    /// Creates a new FunctionChoice instance with the provided label.
    /// </summary>
    /// <param name="label">The label to associate with this FunctionChoice.</param>
    public FunctionChoice(string label)
    {
        Verify.NotNullOrWhiteSpace(label, nameof(label));
        this.Label = label!;
    }

    /// <summary>
    /// Returns a value indicating whether two FunctionChoice instances are equivalent, as determined by a
    /// case-insensitive comparison of their labels.
    /// </summary>
    /// <param name="left"> the first FunctionChoice instance to compare </param>
    /// <param name="right"> the second FunctionChoice instance to compare </param>
    /// <returns> true if left and right are both null or have equivalent labels; false otherwise </returns>
    public static bool operator ==(FunctionChoice left, FunctionChoice right)
        => left.Equals(right);

    /// <summary>
    /// Returns a value indicating whether two FunctionChoice instances are not equivalent, as determined by a
    /// case-insensitive comparison of their labels.
    /// </summary>
    /// <param name="left"> the first FunctionChoice instance to compare </param>
    /// <param name="right"> the second FunctionChoice instance to compare </param>
    /// <returns> false if left and right are both null or have equivalent labels; true otherwise </returns>
    public static bool operator !=(FunctionChoice left, FunctionChoice right)
        => !(left == right);

    /// <inheritdoc/>
    public override bool Equals([NotNullWhen(true)] object? obj)
        => obj is FunctionChoice other && this == other;

    /// <inheritdoc/>
    public bool Equals(FunctionChoice other)
        => string.Equals(this.Label, other.Label, StringComparison.OrdinalIgnoreCase);

    /// <inheritdoc/>
    public override int GetHashCode()
        => StringComparer.OrdinalIgnoreCase.GetHashCode(this.Label);

    /// <inheritdoc/>
    public override string ToString() => this.Label;
}

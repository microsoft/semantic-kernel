// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Class used to copy and export data about functino output for planner and related scenarios.
/// </summary>
/// <param name="Description">Function output description</param>
/// <param name="Type">Function output return type</param>
public sealed record OutputView(
    string? Description = null,
    System.Type? Type = null);

// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Class used to copy and export data about function output for planner and related scenarios.
/// </summary>
/// <param name="Description">Function output description</param>
public sealed record ReturnParameterView(
    string? Description = null);

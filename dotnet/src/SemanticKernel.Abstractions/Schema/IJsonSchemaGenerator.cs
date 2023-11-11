// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Interface for generating JSON Schema from a type.
/// </summary>
public interface IJsonSchemaGenerator
{
    /// <summary>
    /// Generate a JSON Schema from a type.
    /// </summary>
    /// <param name="type">Type to generate the JSON schema for</param>
    /// <param name="description">Description to use when generating the schema</param>
    /// <returns></returns>
    JsonDocument? GenerateSchema(Type type, string description);
}

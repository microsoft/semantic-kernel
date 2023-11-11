// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;

namespace Microsoft.SemanticKernel.Schema;

/// <summary>
/// Interface for generating JSON Schema from a type.
/// </summary>
public interface IJsonSchemaGenerator
{
    /// <summary>
    /// Generate a JSON Schema from a type.
    /// </summary>
    /// <param name="type"></param>
    /// <param name="description"></param>
    /// <returns></returns>
    JsonDocument? GenerateSchema(Type type, string description);
}

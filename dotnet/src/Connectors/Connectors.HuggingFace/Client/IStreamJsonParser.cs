// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Client;

/// <summary>
/// Represents a JSON parser that can parse a Stream containing JSON data and yield the individual JSON objects.
/// </summary>
internal interface IStreamJsonParser
{
    /// <summary>
    /// Parses a Stream containing JSON data and yields the individual JSON objects.
    /// </summary>
    /// <param name="stream">The Stream containing the JSON data.</param>
    /// <param name="validateJson">Set to true to enable JSON validation. Default is false.</param>
    /// <returns>An enumerable collection of string representing the individual JSON objects.</returns>
    IEnumerable<string> Parse(Stream stream, bool validateJson = false);
}

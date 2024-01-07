#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.Json.Nodes;
using Microsoft.SemanticKernel.Connectors.Gemini.Abstract;

namespace Microsoft.SemanticKernel.Connectors.Gemini.Core;

/// <summary>
/// Internal class for parsing a GEMINI JSON stream into separate GEMINI JSON objects.
/// </summary>
internal sealed class GeminiStreamJsonParser : IStreamJsonParser
{
    /// <inheritdoc />
    public IEnumerable<string> Parse(Stream stream, bool validateJson = false)
    {
        using var reader = new StreamReader(stream, Encoding.UTF8);
        while (ReadNextJsonObject(reader, validateJson) is { } json)
        {
            yield return json;
        }
    }

    private static string? ReadNextJsonObject(TextReader reader, bool validateJson)
    {
        var sb = new StringBuilder();
        int character;
        int bracketsCount = 0;
        bool insideQuotes = false;
        bool isEscaping = false;
        while ((character = reader.Read()) != -1)
        {
            char c = (char)character;

            switch (c)
            {
                // Check whether character is escaped inside quotes
                case '\\' when !isEscaping && insideQuotes:
                    isEscaping = true;
                    AppendToJsonObject(c);
                    continue;
                // Check whether character is start or end of quotes
                case '\"' when !isEscaping:
                    insideQuotes = !insideQuotes;
                    break;
            }

            // When not inside quote and not escaping, handle brackets
            if (!insideQuotes && !isEscaping)
            {
                switch (c)
                {
                    case '{':
                        bracketsCount++;
                        break;
                    case '}':
                        bracketsCount--;
                        if (bracketsCount == 0)
                        {
                            string json = sb.Append(c).ToString();
                            if (validateJson)
                            {
                                _ = JsonNode.Parse(json);
                            }

                            return json;
                        }

                        break;
                }
            }

            // Reset escaping flag
            if (isEscaping)
            {
                isEscaping = false;
            }

            AppendToJsonObject(c);
        }

        return null;

        void AppendToJsonObject(char c)
        {
            if (bracketsCount > 0)
            {
                sb.Append(c);
            }
        }
    }
}

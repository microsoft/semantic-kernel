// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core;

/// <summary>
/// Internal class for parsing a stream of jsons into separate json objects.
/// </summary>
internal sealed class StreamJsonParser
{
    private readonly char[] _buffer = new char[1];

    /// <summary>
    /// Parses a Stream containing JSON data and yields the individual JSON objects.
    /// </summary>
    /// <param name="stream">The Stream containing the JSON data.</param>
    /// <param name="validateJson">Set to true to enable JSON validation. Default is false.</param>
    /// <param name="ct">The cancellation token.</param>
    /// <returns>An enumerable collection of string representing the individual JSON objects.</returns>
    public async IAsyncEnumerable<string> ParseAsync(
        Stream stream,
        bool validateJson = false,
        [EnumeratorCancellation] CancellationToken ct = default)
    {
        using var reader = new StreamReader(stream, Encoding.UTF8);
        while (await this.ExtractNextJsonStringAsync(reader, validateJson, ct).ConfigureAwait(false) is { } json)
        {
            yield return json;
        }
    }

    private async Task<string?> ExtractNextJsonStringAsync(
        TextReader reader,
        bool validateJson,
        CancellationToken ct)
    {
        JsonParserState state = new();
        while (!ct.IsCancellationRequested && await reader.ReadAsync(this._buffer, 0, 1).ConfigureAwait(false) > 0)
        {
            state.CurrentCharacter = this._buffer[0];
            if (IsEscapedCharacterInsideQuotes(state))
            {
                continue;
            }

            DetermineIfQuoteStartOrEnd(state);
            HandleCurrentCharacterOutsideQuotes(state);

            if (state.IsCompleteJson)
            {
                return state.GetJsonString(validateJson);
            }

            state.ResetEscapeFlag();
            state.AppendToJsonObject();
        }

        return null;
    }

    private static void HandleCurrentCharacterOutsideQuotes(JsonParserState state)
    {
        if (state is { InsideQuotes: true })
        {
            return;
        }

        switch (state.CurrentCharacter)
        {
            case '{':
                state.BracketsCount++;
                break;
            case '}':
                state.BracketsCount--;
                if (state.BracketsCount == 0)
                {
                    state.MarkJsonAsComplete(appendCurrentCharacter: true);
                }

                break;
        }
    }

    private static void DetermineIfQuoteStartOrEnd(JsonParserState state)
    {
        if (state is { CurrentCharacter: '\"', IsEscaping: false })
        {
            state.InsideQuotes = !state.InsideQuotes;
        }
    }

    private static bool IsEscapedCharacterInsideQuotes(JsonParserState state)
    {
        if (state is { CurrentCharacter: '\\', IsEscaping: false, InsideQuotes: true })
        {
            state.IsEscaping = true;
            state.AppendToJsonObject();
            return true;
        }

        return false;
    }

    private sealed class JsonParserState
    {
        private readonly StringBuilder _jsonBuilder = new();

        public int BracketsCount { get; set; }
        public bool InsideQuotes { get; set; }
        public bool IsEscaping { get; set; }
        public bool IsCompleteJson { get; private set; }
        public char CurrentCharacter { get; set; }

        public void AppendToJsonObject()
        {
            if (this.BracketsCount > 0 && !this.IsCompleteJson)
            {
                this._jsonBuilder.Append(this.CurrentCharacter);
            }
        }

        public string GetJsonString(bool validateJson)
        {
            if (!this.IsCompleteJson)
            {
                throw new InvalidOperationException("Cannot get JSON string when JSON is not complete.");
            }

            var json = this._jsonBuilder.ToString();
            if (validateJson)
            {
                _ = JsonNode.Parse(json);
            }

            return json;
        }

        public void MarkJsonAsComplete(bool appendCurrentCharacter)
        {
            this.IsCompleteJson = true;
            if (appendCurrentCharacter)
            {
                this._jsonBuilder.Append(this.CurrentCharacter);
            }
        }

        public void ResetEscapeFlag() => this.IsEscaping = false;
    }
}

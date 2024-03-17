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
/// Internal class for parsing a stream of text which contains a series of discrete JSON strings into en enumerable containing each separate JSON string.
/// </summary>
internal sealed class StreamJsonParser
{
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
        while (await new SingleJsonChunkParser().ExtractNextChunkAsync(reader, validateJson, ct).ConfigureAwait(false) is { } json)
        {
            yield return json;
        }
    }

    private sealed class SingleJsonChunkParser
    {
        private readonly StringBuilder _jsonBuilder = new();
        private readonly char[] _buffer = new char[1];

        private int _bracketsCount;
        private bool _insideQuotes;
        private bool _isEscaping;
        private bool _isCompleteJson;

        private char CurrentCharacter => this._buffer[0];

        internal async Task<string?> ExtractNextChunkAsync(
            TextReader reader,
            bool validateJson,
            CancellationToken ct)
        {
            while (!ct.IsCancellationRequested && await reader.ReadAsync(this._buffer, 0, 1).ConfigureAwait(false) > 0)
            {
                if (this.IsEscapedCharacterInsideQuotes())
                {
                    continue;
                }

                this.DetermineIfQuoteStartOrEnd();
                this.HandleCurrentCharacterOutsideQuotes();

                if (this._isCompleteJson)
                {
                    return this.GetJsonString(validateJson);
                }

                this.ResetEscapeFlag();
                this.AppendToJsonObject();
            }

            return null;
        }

        private void AppendToJsonObject()
        {
            if (this._bracketsCount > 0 && !this._isCompleteJson)
            {
                this._jsonBuilder.Append(this.CurrentCharacter);
            }
        }

        private string GetJsonString(bool validateJson)
        {
            if (!this._isCompleteJson)
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

        private void MarkJsonAsComplete(bool appendCurrentCharacter)
        {
            this._isCompleteJson = true;
            if (appendCurrentCharacter)
            {
                this._jsonBuilder.Append(this.CurrentCharacter);
            }
        }

        private void ResetEscapeFlag() => this._isEscaping = false;

        private void HandleCurrentCharacterOutsideQuotes()
        {
            if (this._insideQuotes)
            {
                return;
            }

            switch (this.CurrentCharacter)
            {
                case '{':
                    this._bracketsCount++;
                    break;
                case '}':
                    this._bracketsCount--;
                    if (this._bracketsCount == 0)
                    {
                        this.MarkJsonAsComplete(appendCurrentCharacter: true);
                    }

                    break;
            }
        }

        private void DetermineIfQuoteStartOrEnd()
        {
            if (this is { CurrentCharacter: '\"', _isEscaping: false })
            {
                this._insideQuotes = !this._insideQuotes;
            }
        }

        private bool IsEscapedCharacterInsideQuotes()
        {
            if (this is { CurrentCharacter: '\\', _isEscaping: false, _insideQuotes: true })
            {
                this._isEscaping = true;
                this.AppendToJsonObject();
                return true;
            }

            return false;
        }
    }
}

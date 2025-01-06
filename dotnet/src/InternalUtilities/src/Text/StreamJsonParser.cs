// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Text;

#pragma warning disable CA1812 // Internal class that is apparently never instantiated
#pragma warning disable CA1846 // Prefer 'AsSpan' over 'Substring' when span-based overloads are available

/// <summary>
/// Internal class for parsing a stream of text which contains a series of discrete JSON strings into en enumerable containing each separate JSON string.
/// </summary>
/// <remarks>
/// This is universal parser for parsing stream of text which contains a series of discrete JSON.<br/>
/// If you need a specialized SSE parser, use <see cref="SseJsonParser"/> instead.<br/>
/// This class is thread-safe.
/// </remarks>
[ExcludeFromCodeCoverage]
internal sealed class StreamJsonParser
{
    /// <summary>
    /// Parses a Stream containing JSON data and yields the individual JSON objects.
    /// </summary>
    /// <param name="stream">The Stream containing the JSON data.</param>
    /// <param name="validateJson">Set to true to enable checking json chunks are well-formed. Default is false.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>An enumerable collection of string representing the individual JSON objects.</returns>
    /// <remarks>Stream will be disposed after parsing.</remarks>
    public async IAsyncEnumerable<string> ParseAsync(
        Stream stream,
        bool validateJson = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using var reader = new StreamReader(stream, Encoding.UTF8);
        ChunkParser chunkParser = new(reader);
        while (await chunkParser.ExtractNextChunkAsync(validateJson, cancellationToken).ConfigureAwait(false) is { } json)
        {
            yield return json;
        }
    }

    private sealed class ChunkParser
    {
        private readonly StringBuilder _jsonBuilder = new();
        private readonly StreamReader _reader;

        private int _bracketsCount;
        private int _startBracketIndex = -1;
        private bool _insideQuotes;
        private bool _isEscaping;
        private bool _isCompleteJson;
        private char _currentCharacter;
        private string? _lastLine;

        internal ChunkParser(StreamReader reader)
        {
            this._reader = reader;
        }

        internal async Task<string?> ExtractNextChunkAsync(
            bool validateJson,
            CancellationToken cancellationToken)
        {
            this.ResetState();
            string? line;
            while ((line = await this._reader.ReadLineAsync(
#if NET
                cancellationToken
#endif
                ).ConfigureAwait(false)) is not null || this._lastLine is not null)
            {
                if (this._lastLine is not null)
                {
                    line = this._lastLine + line;
                    this._lastLine = null;
                }

                if (this.ProcessLineUntilCompleteJson(line!))
                {
                    return this.GetJsonString(validateJson);
                }

                this.AppendLine(line!);
            }

            return null;
        }

        private bool ProcessLineUntilCompleteJson(string line)
        {
            for (int i = 0; i < line!.Length; i++)
            {
                this._currentCharacter = line[i];

                if (this.IsEscapedCharacterInsideQuotes())
                {
                    continue;
                }

                this.DetermineIfQuoteStartOrEnd();
                this.HandleCurrentCharacterOutsideQuotes(i);

                if (this._isCompleteJson)
                {
                    int nextIndex = i + 1;
                    if (nextIndex < line.Length)
                    {
                        this._lastLine = line.Substring(nextIndex);
                        this.AppendLine(line.Substring(0, nextIndex));
                    }
                    else
                    {
                        this.AppendLine(line);
                    }

                    return true;
                }

                this.ResetEscapeFlag();
            }

            return false;
        }

        private void ResetState()
        {
            this._jsonBuilder.Clear();
            this._bracketsCount = 0;
            this._startBracketIndex = -1;
            this._insideQuotes = false;
            this._isEscaping = false;
            this._isCompleteJson = false;
            this._currentCharacter = default;
        }

        private void AppendLine(string line)
        {
            switch (this._jsonBuilder)
            {
                case { Length: 0 } when this._startBracketIndex >= 0:
                    this._jsonBuilder.Append(line.Substring(this._startBracketIndex));
                    break;
                case { Length: > 0 }:
                    this._jsonBuilder.Append(line);
                    break;
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

        private void MarkJsonAsComplete()
        {
            this._isCompleteJson = true;
        }

        private void ResetEscapeFlag() => this._isEscaping = false;

        private void HandleCurrentCharacterOutsideQuotes(int index)
        {
            if (this._insideQuotes)
            {
                return;
            }

            switch (this._currentCharacter)
            {
                case '{':
                    if (++this._bracketsCount == 1)
                    {
                        this._startBracketIndex = index;
                    }

                    break;
                case '}':
                    if (--this._bracketsCount < 0)
                    {
                        throw new InvalidOperationException("Invalid JSON in stream.");
                    }

                    if (this._bracketsCount == 0)
                    {
                        this.MarkJsonAsComplete();
                    }

                    break;
            }
        }

        private void DetermineIfQuoteStartOrEnd()
        {
            if (this is { _currentCharacter: '\"', _isEscaping: false })
            {
                this._insideQuotes = !this._insideQuotes;
            }
        }

        private bool IsEscapedCharacterInsideQuotes()
        {
            if (this is { _currentCharacter: '\\', _isEscaping: false, _insideQuotes: true })
            {
                this._isEscaping = true;
                return true;
            }

            return false;
        }
    }
}

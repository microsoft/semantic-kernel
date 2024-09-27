// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.Json.Nodes;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Client;

internal sealed class TextGenerationStreamJsonParser : IStreamJsonParser
{
    /// <inheritdoc />
    public IEnumerable<string> Parse(Stream stream, bool validateJson = false)
    {
        using var reader = new StreamReader(stream, Encoding.UTF8);
        while (ExtractNextJsonObject(reader, validateJson) is { } json)
        {
            yield return json;
        }
    }

    private static string? ExtractNextJsonObject(TextReader reader, bool validateJson)
    {
        JsonParserState state = new();
        while ((state.CharacterInt = reader.Read()) != -1)
        {
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
        public int CharacterInt { get; set; }
        public char CurrentCharacter => (char)this.CharacterInt;

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

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;

/*
{
    "id": "83632e31ce19471f9163a5288cdf0bcb",
    "object": "chat.completion.chunk",
    "created": 1709762658,
    "model": "mistral-tiny",
    "choices": [
        {
            "index": 0,
            "delta": {
                "role": "assistant",
                "content": ""
            },
            "finish_reason": null,
            "logprobs": null
        }
    ],
    "usage": null
}
 */
internal class MistralChatCompletionChunk
{
    internal string? GetText()
    {
        throw new NotImplementedException();
    }

    internal IReadOnlyDictionary<string, object?>? GetMetadata()
    {
        throw new NotImplementedException();
    }

    internal AuthorRole? GetRole()
    {
        throw new NotImplementedException();
    }

    internal string? GetContent()
    {
        throw new NotImplementedException();
    }

    internal int GetChoiceIndex()
    {
        throw new NotImplementedException();
    }

    internal Encoding? GetEncoding()
    {
        throw new NotImplementedException();
    }
}

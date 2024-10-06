<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
﻿// Copyright (c) Microsoft. All rights reserved.

=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
// Copyright (c) Microsoft. All rights reserved.

<<<<<<< main
=======
=======
// Copyright (c) Microsoft. All rights reserved.

>>>>>>> origin/main
using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel.ChatCompletion;
using System;
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Experimental.Orchestration.Execution;

internal static class ChatHistorySerializer
{
    internal static ChatHistory? Deserialize(string input)
    {
        if (string.IsNullOrEmpty(input))
        {
            return null;
        }

        var messages = JsonSerializer.Deserialize<SerializableChatMessage[]>(input) ?? [];
        ChatHistory history = [];
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
        var messages = JsonSerializer.Deserialize<SerializableChatMessage[]>(input) ?? Array.Empty<SerializableChatMessage>();
        ChatHistory history = new();
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        foreach (var message in messages)
        {
            history.AddMessage(new AuthorRole(message.Role!), message.Content!);
        }

        return history;
    }

    internal static string Serialize(ChatHistory? history)
    {
        if (history is null)
        {
            return string.Empty;
        }

        var messages = history.Select(m => new SerializableChatMessage()
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
        var messages = history.Messages.Select(m => new SerializableChatMessage()
>>>>>>> Stashed changes
=======
        var messages = history.Messages.Select(m => new SerializableChatMessage()
>>>>>>> Stashed changes
=======
        var messages = history.Messages.Select(m => new SerializableChatMessage()
>>>>>>> Stashed changes
=======
        var messages = history.Messages.Select(m => new SerializableChatMessage()
>>>>>>> Stashed changes
=======
        var messages = history.Messages.Select(m => new SerializableChatMessage()
>>>>>>> Stashed changes
=======
        var messages = history.Messages.Select(m => new SerializableChatMessage()
>>>>>>> origin/main
        {
            Role = m.Role.Label,
            Content = m.Content,
        });

        return JsonSerializer.Serialize(messages);
    }

    private sealed class SerializableChatMessage
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
    private class SerializableChatMessage
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    {
        public string? Role { get; set; }

        public string? Content { get; set; }
    }
}

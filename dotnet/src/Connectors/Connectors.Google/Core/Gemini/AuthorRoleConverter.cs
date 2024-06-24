// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.Google.Core;

internal sealed class AuthorRoleConverter : JsonConverter<AuthorRole?>
{
    public override AuthorRole? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        string? role = reader.GetString();
        if (role is null)
        {
            return null;
        }

        if (role.Equals("user", StringComparison.OrdinalIgnoreCase))
        {
            return AuthorRole.User;
        }

        if (role.Equals("model", StringComparison.OrdinalIgnoreCase))
        {
            return AuthorRole.Assistant;
        }

        if (role.Equals("function", StringComparison.OrdinalIgnoreCase))
        {
            return AuthorRole.Tool;
        }

        throw new JsonException($"Unexpected author role: {role}");
    }

    public override void Write(Utf8JsonWriter writer, AuthorRole? value, JsonSerializerOptions options)
    {
        if (value is null)
        {
            writer.WriteNullValue();
            return;
        }

        if (value == AuthorRole.Tool)
        {
            writer.WriteStringValue("function");
        }
        else if (value == AuthorRole.Assistant)
        {
            writer.WriteStringValue("model");
        }
        else if (value == AuthorRole.User)
        {
            writer.WriteStringValue("user");
        }
        else
        {
            throw new JsonException($"Gemini API doesn't support author role: {value}");
        }
    }
}

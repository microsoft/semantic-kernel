// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text.Json;
using Microsoft.Extensions.Configuration.UserSecrets;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Pinecone;
public static class PineconeUserSecretsExtensions
{
    public const string PineconeApiKeyUserSecretEntry = "PineconeApiKey";

    public static string ReadPineconeApiKey()
        => JsonSerializer.Deserialize<Dictionary<string, string>>(
            File.ReadAllText(PathHelper.GetSecretsPathFromSecretsId(
                typeof(PineconeUserSecretsExtensions).Assembly.GetCustomAttribute<UserSecretsIdAttribute>()!
                    .UserSecretsId)))![PineconeApiKeyUserSecretEntry].Trim();

    public static bool ContainsPineconeApiKey()
    {
        var userSecretsIdAttribute = typeof(PineconeUserSecretsExtensions).Assembly.GetCustomAttribute<UserSecretsIdAttribute>();
        if (userSecretsIdAttribute == null)
        {
            return false;
        }

        var path = PathHelper.GetSecretsPathFromSecretsId(userSecretsIdAttribute.UserSecretsId);
        if (!File.Exists(path))
        {
            return false;
        }

        return JsonSerializer.Deserialize<Dictionary<string, string>>(
            File.ReadAllText(path))!.ContainsKey(PineconeApiKeyUserSecretEntry);
    }
}

// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Security.Cryptography;
using System.Text;

namespace Microsoft.SemanticKernel.Agents.Internal;

/// <summary>
/// Utility to encode a list of string keys to an base-64 encoded hash.
/// </summary>
internal static class KeyEncoder
{
    /// <summary>
    /// Produces a base-64 encoded hash for a set of input strings.
    /// </summary>
    /// <param name="keys">A set of input strings</param>
    /// <returns>A base-64 encoded hash</returns>
    public static string GenerateHash(IEnumerable<string> keys)
    {
        using SHA256 shaProvider = SHA256Managed.Create();

        byte[] buffer = Encoding.UTF8.GetBytes(string.Join(":", keys));
        byte[] hash = shaProvider.ComputeHash(buffer);
        string encoding = Convert.ToBase64String(hash);

        return encoding;
    }
}

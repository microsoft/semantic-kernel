// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// Settings for the Semantic Kernel.
/// </summary>
public static class KernelSettings
{
    /// <summary>
    /// User agent string to use for all HTTP requests issued by Semantic Kernel.
    /// </summary>
    public static string UserAgent => s_userAgent;

    /// <summary>
    /// Set a prefix for the user agent string to use for all HTTP requests issued by Semantic Kernel.
    /// </summary>
    /// <param name="prefix">Prefix for the user agent string.</param>
    public static void SetUserAgentPrefix(string? prefix)
    {
        if (string.IsNullOrEmpty(prefix))
        {
            s_userAgent = "Semantic-Kernel";
        }
        else
        {
            s_userAgent = $"{prefix}-Semantic-Kernel";
        }
    }

    #region private
    private static string s_userAgent = "Semantic-Kernel";
    #endregion
}

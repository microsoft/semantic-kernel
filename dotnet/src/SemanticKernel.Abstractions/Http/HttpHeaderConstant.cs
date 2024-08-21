// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Http;

/// <summary>
/// Provides HTTP header names and values for common purposes.
/// </summary>
public static class HttpHeaderConstant
{
    /// <summary>
    /// Provides HTTP header names for common purposes.
    /// </summary>
    public static class Names
    {
        /// <summary>
        /// HTTP header name to use to include the Semantic Kernel package version in all HTTP requests issued by Semantic Kernel.
        /// </summary>
        public static string SemanticKernelVersion => "Semantic-Kernel-Version";
    }

    /// <summary>
    /// Provides HTTP header values for common purposes.
    /// </summary>
    public static class Values
    {
        /// <summary>
        /// User agent string to use for all HTTP requests issued by Semantic Kernel.
        /// </summary>
        public static string UserAgent => s_userAgent;

        /// <summary>
        /// Gets the version of the <see cref="System.Reflection.Assembly"/> in which the specific type is declared.
        /// </summary>
        /// <param name="type">Type for which the assembly version is returned.</param>
        public static string GetAssemblyVersion(Type type)
        {
            return type.Assembly.GetName().Version!.ToString();
        }

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
}

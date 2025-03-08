// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Http;

/// <summary>Provides HTTP header names and values for common purposes.</summary>
[ExcludeFromCodeCoverage]
internal static class HttpHeaderConstant
{
    public static class Names
    {
        /// <summary>HTTP header name to use to include the Semantic Kernel package version in all HTTP requests issued by Semantic Kernel.</summary>
        public static string SemanticKernelVersion => "Semantic-Kernel-Version";

        /// <summary>HTTP User-Agent header name.</summary>
        public static string UserAgent => "User-Agent";
    }

    public static class Values
    {
        /// <summary>User agent string to use for all HTTP requests issued by Semantic Kernel.</summary>
        public static string UserAgent => "Semantic-Kernel";

        /// <summary>
        /// Gets the version of the <see cref="System.Reflection.Assembly"/> in which the specific type is declared.
        /// </summary>
        /// <param name="type">Type for which the assembly version is returned.</param>
        public static string GetAssemblyVersion(Type type)
        {
            return type.Assembly.GetName().Version!.ToString();
        }
    }
}

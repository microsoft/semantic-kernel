// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;

#pragma warning disable CA1307 // Specify StringComparison
#pragma warning disable CA1847 // Use StringBuilder.Append when concatenating strings

namespace Microsoft.SemanticKernel.Text;

/// <summary>
/// Data Uri Scheme Parser based on RFC 2397.
/// https://datatracker.ietf.org/doc/html/rfc2397
/// </summary>
[ExcludeFromCodeCoverage]
internal static class DataUriParser
{
    private const string Scheme = "data:";

    private static readonly char[] s_base64Chars = {
            'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '+', '/'
        };
    /// <summary>
    /// Extension method to test whether the value is a base64 string
    /// </summary>
    /// <param name="value">Value to test</param>
    /// <returns>Boolean value, true if the string is base64, otherwise false</returns>
    private static bool IsBase64String(string? value)
    {
        // The quickest test. If the value is null or is equal to 0 it is not base64
        // Base64 string's length is always divisible by four, i.e. 8, 16, 20 etc. 
        // If it is not you can return false. Quite effective
        // Further, if it meets the above criteria, then test for spaces.
        // If it contains spaces, it is not base64
        if (value is null
            || value.Length == 0
            || value.Length % 4 != 0
            || value.Contains(' ')
            || value.Contains('\t')
            || value.Contains('\r')
            || value.Contains('\n'))
        {
            return false;
        }

        // 98% of all non base64 values are invalidated by this time.
        var index = value.Length - 1;

        // if there is padding step back
        if (value[index] == '=') { index--; }

        // if there are two padding chars step back a second time
        if (value[index] == '=') { index--; }

        // Now traverse over characters
        for (var i = 0; i <= index; i++)
        {
            // If any of the character is not from the allowed list
            if (!s_base64Chars.Contains(value[i]))
            {
                // return false
                return false;
            }
        }

        // If we got here, then the value is a valid base64 string
        return true;
    }

    internal static DataUri Parse(string? dataUri)
    {
        Verify.NotNullOrWhiteSpace(dataUri, nameof(dataUri));
        if (!dataUri.StartsWith(Scheme, StringComparison.OrdinalIgnoreCase))
        {
            throw new UriFormatException("Invalid data uri format. The data URI must start with 'data:'.");
        }

        var model = new DataUri();
        int currentIndex = Scheme.Length;
        int dataIndex = dataUri.IndexOf(',', currentIndex);

        if (dataIndex == -1)
        {
            throw new UriFormatException("Invalid data uri format. The data URI must contain a comma separating the metadata and the data.");
        }

        string metadata = dataUri.Substring(currentIndex, dataIndex - currentIndex);
        model.Data = dataUri.Substring(dataIndex + 1);

        // Split the metadata into components
        var metadataParts = metadata.Split(';');
        if (metadataParts.Length > 0)
        {
            if (!string.IsNullOrWhiteSpace(metadataParts[0]) && !metadataParts[0].Contains("/"))
            {
                throw new UriFormatException("Invalid data uri format. When provided, the MIME type must have \"type/subtype\" format.");
            }

            // First part is the MIME type
            model.MimeType = metadataParts[0];
        }

        for (int i = 1; i < metadataParts.Length; i++)
        {
            var part = metadataParts[i];
            if (part!.Contains("="))
            {
                var keyValue = part.Split('=');

                // Parameter must have a name and cannot have more than one '=' for values.
                if (string.IsNullOrWhiteSpace(keyValue[0]) || keyValue.Length != 2)
                {
                    throw new UriFormatException("Invalid data uri format. Parameters must have \"name=value\" format.");
                }

                model.Parameters[keyValue[0]] = keyValue[1];

                continue;
            }

            if (i < metadataParts.Length - 1)
            {
                throw new UriFormatException("Invalid data uri format. Parameters must have \"name=value\" format.");
            }

            model.DataFormat = part;
        }

        if (string.Equals(model.DataFormat, "base64", StringComparison.OrdinalIgnoreCase) && !IsBase64String(model.Data))
        {
            throw new UriFormatException("Invalid data uri format. The data is not a valid Base64 string.");
        }

        if (string.IsNullOrEmpty(model.MimeType))
        {
            // By RFC 2397, the default MIME type if not provided is text/plain;charset=US-ASCII
            model.MimeType = "text/plain";
        }

        return model;
    }

    /// <summary>
    /// Represents the data URI parts.
    /// </summary>
    internal sealed class DataUri
    {
        /// <summary>
        /// The mime type of the data.
        /// </summary>
        internal string? MimeType { get; set; }

        /// <summary>
        /// The optional parameters of the data.
        /// </summary>
        internal Dictionary<string, string> Parameters { get; set; } = new();

        /// <summary>
        /// The optional format of the data. Most common is "base64".
        /// </summary>
        public string? DataFormat { get; set; }

        /// <summary>
        /// The data content.
        /// </summary>
        public string? Data { get; set; }
    }
}

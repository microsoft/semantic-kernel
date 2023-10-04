// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Globalization;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.Model;

/// <summary>
/// Converts a object of <see cref="RestApiOperationResponse"/> type to string type.
/// </summary>
public class RestApiOperationResponseConverter : TypeConverter
{
    /// <inheritdoc/>
    public override bool CanConvertTo(ITypeDescriptorContext context, Type destinationType)
    {
        return destinationType == typeof(string) || base.CanConvertTo(context, destinationType);
    }

    /// <inheritdoc/>
    public override object ConvertTo(ITypeDescriptorContext context, CultureInfo culture, object value, Type destinationType)
    {
        // Convert object content to a string based on the type of the `Content` property.
        // More granular conversion logic can be built based on the value of the `ContentType` property, if needed.
        if (value is RestApiOperationResponse response && destinationType == typeof(string))
        {
            //Case for "text/*", "application/json", "application/xml" content types.
            if (response.Content is string stringContent)
            {
                return stringContent;
            }

            //Case for "image/*" content types and others that are serialized as bytes.
            if (response.Content is byte[] byteContent)
            {
                return Convert.ToBase64String(byteContent);
            }
        }

        return base.ConvertTo(context, culture, value, destinationType);
    }
}

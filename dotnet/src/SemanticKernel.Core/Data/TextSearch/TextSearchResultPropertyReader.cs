// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Reflection;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Contains helpers for reading <see cref="TextSearchResult" /> attributes.
/// </summary>
internal sealed class TextSearchResultPropertyReader
{
    /// <summary>The <see cref="Type"/> of the data model.</summary>
    private readonly Type _dataModelType;

    /// <summary>The <see cref="PropertyInfo"/> of the name property.</summary>
    private readonly PropertyInfo? _nameProperty;

    /// <summary>The <see cref="PropertyInfo"/> of the value property.</summary>
    private readonly PropertyInfo? _valueProperty;

    /// <summary>The <see cref="PropertyInfo"/> of the link property.</summary>
    private readonly PropertyInfo? _linkProperty;

    /// <summary>
    /// Create a new instance of <see cref="TextSearchResultPropertyReader"/>.
    /// </summary>
    /// <param name="dataModelType">Type of the data model.</param>
    public TextSearchResultPropertyReader([DynamicallyAccessedMembers(DynamicallyAccessedMemberTypes.PublicProperties)] Type dataModelType)
    {
        this._dataModelType = dataModelType;

        var (NameProperty, ValueProperty, LinkProperty) = FindPropertiesInfo(dataModelType);
        this._nameProperty = NameProperty;
        this._valueProperty = ValueProperty;
        this._linkProperty = LinkProperty;
    }

    /// <summary>
    /// Get the name property value of the data model.
    /// </summary>
    /// <param name="dataModel">The data model instance.</param>
    public string? GetName(object dataModel)
    {
        return this._nameProperty?.GetValue(dataModel)?.ToString();
    }

    /// <summary>
    /// Get the value property value of the data model.
    /// </summary>
    /// <param name="dataModel">The data model instance.</param>
    public string? GetValue(object dataModel)
    {
        return this._valueProperty?.GetValue(dataModel)?.ToString();
    }

    /// <summary>
    /// Get the link property value of the data model.
    /// </summary>
    /// <param name="dataModel">The data model instance.</param>
    public string? GetLink(object dataModel)
    {
        return this._linkProperty?.GetValue(dataModel)?.ToString();
    }

    /// <summary>
    /// Find the properties with <see cref="TextSearchResultNameAttribute"/>, <see cref="TextSearchResultValueAttribute"/> and <see cref="TextSearchResultLinkAttribute"/> attributes
    /// </summary>
    /// <param name="type">The data model to find the properties on.</param>
    /// <returns>The properties.</returns>
    private static (PropertyInfo? NameProperty, PropertyInfo? ValueProperty, PropertyInfo? LinkProperty) FindPropertiesInfo([DynamicallyAccessedMembers(DynamicallyAccessedMemberTypes.PublicProperties)] Type type)
    {
        PropertyInfo? nameProperty = null;
        PropertyInfo? valueProperty = null;
        PropertyInfo? linkProperty = null;

        foreach (var property in type.GetProperties())
        {
            // Get name property.
            if (property.GetCustomAttribute<TextSearchResultNameAttribute>() is not null)
            {
                if (nameProperty is not null)
                {
                    throw new InvalidOperationException($"Multiple properties with {nameof(TextSearchResultNameAttribute)} found on {type}.");
                }
                nameProperty = property;
            }

            // Get value property.
            if (property.GetCustomAttribute<TextSearchResultValueAttribute>() is not null)
            {
                if (valueProperty is not null)
                {
                    throw new InvalidOperationException($"Multiple properties with {nameof(TextSearchResultValueAttribute)} found on {type}.");
                }
                valueProperty = property;
            }

            // Get link property.
            if (property.GetCustomAttribute<TextSearchResultLinkAttribute>() is not null)
            {
                if (linkProperty is not null)
                {
                    throw new InvalidOperationException($"Multiple properties with {nameof(TextSearchResultLinkAttribute)} found on {type}.");
                }
                linkProperty = property;
            }
        }

        return (nameProperty, valueProperty, linkProperty);
    }
}

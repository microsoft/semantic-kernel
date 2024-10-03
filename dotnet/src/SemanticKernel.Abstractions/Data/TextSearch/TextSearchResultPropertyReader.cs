// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Reflection;

namespace Microsoft.SemanticKernel.Data.TextSearch;
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

    public TextSearchResultPropertyReader(Type dataModelType)
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
    private static (PropertyInfo? NameProperty, PropertyInfo? ValueProperty, PropertyInfo? LinkProperty) FindPropertiesInfo(Type type)
    {
        PropertyInfo? nameProperty = null;
        PropertyInfo? valueProperty = null;
        PropertyInfo? linkProperty = null;

        foreach (var property in type.GetProperties())
        {
            // Get name property.
            if (property.GetCustomAttribute<TextSearchResultNameAttribute>() is not null)
            {
                nameProperty = property;
            }

            // Get value property.
            if (property.GetCustomAttribute<TextSearchResultValueAttribute>() is not null)
            {
                valueProperty = property;
            }

            // Get link property.
            if (property.GetCustomAttribute<TextSearchResultLinkAttribute>() is not null)
            {
                linkProperty = property;
            }
        }

        return (nameProperty, valueProperty, linkProperty);
    }
}

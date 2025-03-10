// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel;

namespace Plugins;

/// <summary>
/// A plugin that creates widgets.
/// </summary>
public sealed class WidgetFactory
{
    [KernelFunction]
    [Description("Creates a new widget of the specified type and colors")]
    public WidgetDetails CreateWidget(
        [Description("The type of widget to be created")] WidgetType widgetType,
        [Description("The colors of the widget to be created")] WidgetColor[] widgetColors)
    {
        return new()
        {
            SerialNumber = $"{widgetType}-{string.Join("-", widgetColors)}-{Guid.NewGuid()}",
            Type = widgetType,
            Colors = widgetColors,
        };
    }
}

/// <summary>
/// A <see cref="JsonConverter"/> is required to correctly convert enum values.
/// </summary>
[JsonConverter(typeof(JsonStringEnumConverter))]
public enum WidgetType
{
    [Description("A widget that is useful.")]
    Useful,

    [Description("A widget that is decorative.")]
    Decorative
}

/// <summary>
/// A <see cref="JsonConverter"/> is required to correctly convert enum values.
/// </summary>
[JsonConverter(typeof(JsonStringEnumConverter))]
public enum WidgetColor
{
    [Description("Use when creating a red item.")]
    Red,

    [Description("Use when creating a green item.")]
    Green,

    [Description("Use when creating a blue item.")]
    Blue
}

public sealed class WidgetDetails
{
    public string SerialNumber { get; init; }
    public WidgetType Type { get; init; }
    public WidgetColor[] Colors { get; init; }
}

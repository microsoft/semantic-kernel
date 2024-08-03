// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;

namespace Plugins;

public sealed class LegacyMenuPlugin
{
    public const string CorrelationIdArgument = "correlationId";

    private readonly List<string> _correlationIds = [];

    public IReadOnlyList<string> CorrelationIds => this._correlationIds;

    /// <summary>
    /// Returns a mock item menu.
    /// </summary>
    [KernelFunction, Description("Provides a list of specials from the menu.")]
    [System.Diagnostics.CodeAnalysis.SuppressMessage("Design", "CA1024:Use properties where appropriate", Justification = "Too smart")]
    public string[] GetSpecials(KernelArguments? arguments)
    {
        CaptureCorrelationId(arguments, nameof(GetSpecials));

        return
            [
                "Special Soup: Clam Chowder",
                "Special Salad: Cobb Salad",
                "Special Drink: Chai Tea",
            ];
    }

    /// <summary>
    /// Returns a mock item price.
    /// </summary>
    [KernelFunction, Description("Provides the price of the requested menu item.")]
    public string GetItemPrice(
            [Description("The name of the menu item.")]
        string menuItem,
            KernelArguments? arguments)
    {
        CaptureCorrelationId(arguments, nameof(GetItemPrice));

        return "$9.99";
    }

    /// <summary>
    /// An item is 86'd when the kitchen cannot serve due to running out of ingredients.
    /// </summary>
    [KernelFunction, Description("Returns true if the kitchen has ran out of the item.")]
    public bool IsItem86d(
            [Description("The name of the menu item.")]
        string menuItem,
            [Description("The number of items requested.")]
        int count,
            KernelArguments? arguments)
    {
        CaptureCorrelationId(arguments, nameof(IsItem86d));

        return count < 3;
    }

    private void CaptureCorrelationId(KernelArguments? arguments, string scope)
    {
        if (arguments?.TryGetValue(CorrelationIdArgument, out object? correlationId) ?? false)
        {
            string? correlationText = correlationId?.ToString();

            if (!string.IsNullOrWhiteSpace(correlationText))
            {
                this._correlationIds.Add($"{scope}:{correlationText}");
            }
        }
    }
}

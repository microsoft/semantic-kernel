﻿// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;

namespace Plugins;

public sealed class LegacyMenuPlugin
{
    /// <summary>
    /// Returns a mock item menu.
    /// </summary>
    [KernelFunction, Description("Provides a list of specials from the menu.")]
    [System.Diagnostics.CodeAnalysis.SuppressMessage("Design", "CA1024:Use properties where appropriate", Justification = "Too smart")]
    public string[] GetSpecials(KernelArguments? arguments)
    {
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
        return count < 3;
    }
}

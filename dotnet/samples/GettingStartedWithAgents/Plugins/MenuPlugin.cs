// Copyright (c) Microsoft. All rights reserved.
using System.ComponentModel;
using Microsoft.SemanticKernel;

namespace Plugins;

public sealed class MenuPlugin
{
    [KernelFunction, Description("Provides a list of specials from the menu.")]
    public MenuItem[] GetMenu()
    {
        return s_menuItems;
    }

    [KernelFunction, Description("Provides a list of specials from the menu.")]
    public MenuItem[] GetSpecials()
    {
        return s_menuItems.Where(i => i.IsSpecial).ToArray();
    }

    [KernelFunction, Description("Provides the price of the requested menu item.")]
    public float? GetItemPrice(
        [Description("The name of the menu item.")]
        string menuItem)
    {
        return s_menuItems.FirstOrDefault(i => i.Name.Equals(menuItem, StringComparison.OrdinalIgnoreCase))?.Price;
    }

    private static readonly MenuItem[] s_menuItems =
        [
            new()
            {
                Category = "Soup",
                Name = "Clam Chowder",
                Price = 4.95f,
                IsSpecial = true,
            },
            new()
            {
                Category = "Soup",
                Name = "Tomato Soup",
                Price = 4.95f,
                IsSpecial = false,
            },
            new()
            {
                Category = "Salad",
                Name = "Cobb Salad",
                Price = 9.99f,
            },
            new()
            {
                Category = "Salad",
                Name = "House Salad",
                Price = 4.95f,
            },
            new()
            {
                Category = "Drink",
                Name = "Chai Tea",
                Price = 2.95f,
                IsSpecial = true,
            },
            new()
            {
                Category = "Drink",
                Name = "Soda",
                Price = 1.95f,
            },
        ];

    public sealed class MenuItem
    {
        public string Category { get; init; }
        public string Name { get; init; }
        public float Price { get; init; }
        public bool IsSpecial { get; init; }
    }
}

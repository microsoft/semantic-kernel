// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace MCPServer.Tools;

/// <summary>
/// A collection of utility methods for working with orders.
/// </summary>
internal sealed class OrderProcessingUtils
{
    /// <summary>
    /// Places an order for the specified item.
    /// </summary>
    /// <param name="itemName">The name of the item to be ordered.</param>
    /// <returns>A string indicating the result of the order placement.</returns>
    [KernelFunction]
    public string PlaceOrder(string itemName)
    {
        return "success";
    }

    /// <summary>
    /// Executes a refund for the specified item.
    /// </summary>
    /// <param name="itemName">The name of the item to be refunded.</param>
    /// <returns>A string indicating the result of the refund execution.</returns>
    [KernelFunction]
    public string ExecuteRefund(string itemName)
    {
        return "success";
    }
}

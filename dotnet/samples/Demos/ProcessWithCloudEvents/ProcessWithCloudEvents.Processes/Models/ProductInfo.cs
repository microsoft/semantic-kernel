// Copyright (c) Microsoft. All rights reserved.

using ProcessWithCloudEvents.Processes.Steps;

namespace ProcessWithCloudEvents.Processes.Models;

/// <summary>
/// Object used in the <see cref="GatherProductInfoStep"/>
/// </summary>
public class ProductInfo
{
    /// <summary>
    /// Title of the product
    /// </summary>
    public string Title { get; set; } = string.Empty;
    /// <summary>
    /// Content of the product
    /// </summary>
    public string Content { get; set; } = string.Empty;
    /// <summary>
    /// User comments
    /// </summary>
    public string UserInput { get; set; } = string.Empty;
}

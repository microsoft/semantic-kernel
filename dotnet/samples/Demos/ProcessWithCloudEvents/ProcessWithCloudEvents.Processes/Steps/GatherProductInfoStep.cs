// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using ProcessWithCloudEvents.Processes.Models;

namespace ProcessWithCloudEvents.Processes.Steps;

/// <summary>
/// Step that receives product information
/// </summary>
public class GatherProductInfoStep : KernelProcessStep
{
    /// <summary>
    /// Only step function that process the information passed
    /// When there is only one function, there is no need to specify functionNames in the KernelFunction annotator
    /// </summary>
    /// <param name="productInfo"></param>
    /// <returns></returns>
    [KernelFunction]
    public ProductInfo OnReceiveUserRequest(ProductInfo productInfo)
    {
        Console.WriteLine($"[GATHER_PRODUCT_INFO] {productInfo.Title} : {productInfo.Content}");
        return productInfo;
    }
}

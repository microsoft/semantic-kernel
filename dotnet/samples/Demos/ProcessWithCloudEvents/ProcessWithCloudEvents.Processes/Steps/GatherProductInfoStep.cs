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
    /// <param name="productInfo">product information</param>
    /// <returns></returns>
    [KernelFunction]
    public ProductInfo OnReceiveUserRequest(ProductInfo productInfo)
    {
        Console.WriteLine($"[{nameof(GatherProductInfoStep)}]:\tGathering product information for product named {productInfo.Title}");

        // For example purposes we just return some fictional information.
        productInfo.Content = """
            Product Description:
            GlowBrew is a revolutionary AI driven coffee machine with industry leading number of LEDs and programmable light shows. The machine is also capable of brewing coffee and has a built in grinder.
            
            Product Features:
            1. **Luminous Brew Technology**: Customize your morning ambiance with programmable LED lights that sync with your brewing process.
            2. **AI Taste Assistant**: Learns your taste preferences over time and suggests new brew combinations to explore.
            3. **Gourmet Aroma Diffusion**: Built-in aroma diffusers enhance your coffee's scent profile, energizing your senses before the first sip.
            
            Troubleshooting:
            - **Issue**: LED Lights Malfunctioning
                - **Solution**: Reset the lighting settings via the app. Ensure the LED connections inside the GlowBrew are secure. Perform a factory reset if necessary.
            """;

        return productInfo;
    }
}

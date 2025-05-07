// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Text.Json;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace FunctionCalling;

/// <summary>
/// This sample shows different options for calling functions with multiple parameters.
/// The scenario is to search for invoices by customer name, purchase order, or vendor number.
///
/// The first sample uses multiple functions, one for each search criteria. One issue is that
/// as the number of functions increases then the reliability of the AI model to select the correct
/// function may decrease. To help avoid this issue, you can try filtering which functions are advertised
/// to the AI model e.g. if your application has come context information which indicates a purchase order
/// is available then you can filter out the customer name and vendor number functions.
///
/// The second sample uses a single function that takes an object with all search criteria. In this case some
/// of the search criteria are optional. Again as the number of parameters increases then the reliability of the
/// AI model may decrease. One advantage of this approach is that if the AI model can extra multiple search criteria
/// for the users ask then your plugin can use this information to provide more reliable results.
///
/// For both options care should be taken to validate the parameters that the AI model provides. E.g. the customer
/// name could be wrong or the purchase order could be invalid. It is worth catching these errors and responding the
/// AI model with a message that explains what has gone wrong to see how it responds. It may be able to retry the search
/// and get a successful response on the second attempt. Or it may decide to revert pack to the human in the loop to ask
/// for more information.
/// </summary>
public class MultipleFunctionsVsParameters(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Shows how to use multiple Search By functions to search for invoices by customer name, purchase order, or vendor number.
    /// </summary>
    [Fact]
    public async Task InvoiceSearchBySampleAsync()
    {
        // Create a kernel with OpenAI chat completion
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Services.AddSingleton<IAutoFunctionInvocationFilter>(
            new AutoFunctionInvocationFilter(this.Output));
        kernelBuilder.AddOpenAIChatCompletion(
            modelId: TestConfiguration.OpenAI.ChatModelId,
            apiKey: TestConfiguration.OpenAI.ApiKey);
        kernelBuilder.Plugins.AddFromType<InvoiceSearchBy>();
        Kernel kernel = kernelBuilder.Build();

        await InvokePromptsAsync(kernel);
    }

    /// <summary>
    /// Shows how to use a single Search function to search for invoices by customer name, purchase order, or vendor number.
    /// </summary>
    [Fact]
    public async Task InvoiceSearchSampleAsync()
    {
        // Create a kernel with OpenAI chat completion
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Services.AddSingleton<IAutoFunctionInvocationFilter>(
            new AutoFunctionInvocationFilter(this.Output));
        kernelBuilder.AddOpenAIChatCompletion(
            modelId: TestConfiguration.OpenAI.ChatModelId,
            apiKey: TestConfiguration.OpenAI.ApiKey);
        kernelBuilder.Plugins.AddFromType<InvoiceSearch>();
        Kernel kernel = kernelBuilder.Build();

        await InvokePromptsAsync(kernel);
    }

    /// <summary>Invoke the various prompts we want to test.</summary>
    private async Task InvokePromptsAsync(Kernel kernel)
    {
        OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        Console.WriteLine("Prompt: Show me the invoices for customer named Contoso Industries.");
        Console.WriteLine(await kernel.InvokePromptAsync("Show me the invoices for customer named Contoso Industries.", new(settings)));
        Console.WriteLine("----------------------------------------------------");
        Console.WriteLine("Prompt: Show me the invoices for purchase order PO123.");
        Console.WriteLine(await kernel.InvokePromptAsync("Show me the invoices for purchase order PO123.", new(settings)));
        Console.WriteLine("----------------------------------------------------");
        Console.WriteLine("Prompt: Show me the invoices for vendor number VN123.");
        Console.WriteLine(await kernel.InvokePromptAsync("Show me the invoices for vendor number VN123.", new(settings)));
        Console.WriteLine("----------------------------------------------------");
        Console.WriteLine("Prompt: Show me the invoices for Contoso Industries.");
        Console.WriteLine(await kernel.InvokePromptAsync("Show me the invoices for Contoso Industries.", new(settings)));
        Console.WriteLine("----------------------------------------------------");
        Console.WriteLine("Prompt: Show me the invoices for PO123.");
        Console.WriteLine(await kernel.InvokePromptAsync("Show me the invoices for PO123.", new(settings)));
        Console.WriteLine("----------------------------------------------------");
        Console.WriteLine("Prompt: Show me the invoices for VN123.");
        Console.WriteLine(await kernel.InvokePromptAsync("Show me the invoices for VN123.", new(settings)));
        Console.WriteLine("----------------------------------------------------");
        Console.WriteLine("Prompt: Zeigen Sie mir die Rechnungen für Contoso Industries.");
        Console.WriteLine(await kernel.InvokePromptAsync("Zeigen Sie mir die Rechnungen für Contoso Industries.", new(settings)));
        Console.WriteLine("----------------------------------------------------");
    }

    /// <summary>Shows available syntax for auto function invocation filter.</summary>
    private sealed class AutoFunctionInvocationFilter(ITestOutputHelper output) : IAutoFunctionInvocationFilter
    {
        public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            var functionName = context.Function.Name;
            var arguments = context.Arguments;

            // Output the details of the function being called
            output.WriteLine($"Function: {functionName} {JsonSerializer.Serialize(arguments)}");

            // Calling next filter in pipeline or function itself.
            await next(context);
        }
    }

    /// <summary>
    /// A plugin that provides methods to search for Invoices using different criteria.
    /// </summary>
    private sealed class InvoiceSearchBy
    {
        [KernelFunction]
        [Description("Search for invoices by customer name.")]
        public IEnumerable<Invoice> SearchByCustomerName([Description("The customer name.")] string customerName)
        {
            return
                [
                    new Invoice { CustomerName = customerName, PurchaseOrder = "PO123", VendorNumber = "VN123" },
                    new Invoice { CustomerName = customerName, PurchaseOrder = "PO124", VendorNumber = "VN124" },
                    new Invoice { CustomerName = customerName, PurchaseOrder = "PO125", VendorNumber = "VN125" },
                ];
        }

        [KernelFunction]
        [Description("Search for invoices by purchase order.")]
        public IEnumerable<Invoice> SearchByPurchaseOrder([Description("The purchase order. Purchase orders begin with a PO prefix.")] string purchaseOrder)
        {
            return
                [
                    new Invoice { CustomerName = "Customer1", PurchaseOrder = purchaseOrder, VendorNumber = "VN123" },
                    new Invoice { CustomerName = "Customer2", PurchaseOrder = purchaseOrder, VendorNumber = "VN124" },
                    new Invoice { CustomerName = "Customer3", PurchaseOrder = purchaseOrder, VendorNumber = "VN125" },
                ];
        }

        [KernelFunction]
        [Description("Search for invoices by vendor number")]
        public IEnumerable<Invoice> SearchByVendorNumber([Description("The vendor number. Vendor numbers begin with a VN prefix.")] string vendorNumber)
        {
            return
                [
                    new Invoice { CustomerName = "Customer1", PurchaseOrder = "PO123", VendorNumber = vendorNumber },
                    new Invoice { CustomerName = "Customer2", PurchaseOrder = "PO124", VendorNumber = vendorNumber },
                    new Invoice { CustomerName = "Customer3", PurchaseOrder = "PO125", VendorNumber = vendorNumber },
                ];
        }
    }

    /// <summary>
    /// A plugin that provides methods to search for Invoices using different criteria.
    /// </summary>
    private sealed class InvoiceSearch
    {
        [KernelFunction]
        [Description("Search for invoices by customer name or purchase order or vendor number.")]
        public IEnumerable<Invoice> Search([Description("The invoice search request. It must contain either a customer name or a purchase order or a vendor number")] InvoiceSearchRequest searchRequest)
        {
            return
                [
                    new Invoice
                    {
                        CustomerName = searchRequest.CustomerName ?? "Customer1",
                        PurchaseOrder = searchRequest.PurchaseOrder ?? "PO123",
                        VendorNumber = searchRequest.VendorNumber ?? "VN123"
                    },
                    new Invoice
                    {
                        CustomerName = searchRequest.CustomerName ?? "Customer2",
                        PurchaseOrder = searchRequest.PurchaseOrder ?? "PO124",
                        VendorNumber = searchRequest.VendorNumber ?? "VN124"
                    },
                    new Invoice
                    {
                        CustomerName = searchRequest.CustomerName ?? "Customer3",
                        PurchaseOrder = searchRequest.PurchaseOrder ?? "PO125",
                        VendorNumber = searchRequest.VendorNumber ?? "VN125"
                    },
                ];
        }
    }

    /// <summary>
    /// Represents an invoice.
    /// </summary>
    private sealed class Invoice
    {
        public string CustomerName { get; set; }
        public string PurchaseOrder { get; set; }
        public string VendorNumber { get; set; }
    }

    /// <summary>
    /// Represents an invoice search request.
    /// </summary>
    [Description("The invoice search request.")]
    private sealed class InvoiceSearchRequest
    {
        [Description("Optional, customer name.")]
        public string? CustomerName { get; set; }
        [Description("Optional, purchase order. Purchase orders begin with a PN prefix.")]
        public string? PurchaseOrder { get; set; }
        [Description("Optional, vendor number. Vendor numbers begin with a VN prefix.")]
        public string? VendorNumber { get; set; }
    }
}

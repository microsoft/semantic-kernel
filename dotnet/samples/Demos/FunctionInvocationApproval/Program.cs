// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using FunctionInvocationApproval.Options;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace FunctionInvocationApproval;

internal sealed class Program
{
    /// <summary>
    /// This console application shows how to use function invocation filter to invoke function only if such operation was approved.
    /// If function invocation was rejected, the result will contain an information about this, so LLM can react accordingly.
    /// Application handles purchase request by using "Bank" and "Store" plugins.
    /// In order to buy a product, specific amount should be withdrawn from "Bank" to provide it to "Store" and get a product.
    /// Each step can be approved or rejected. Based on that, LLM will decide how to proceed.
    /// </summary>
    public static async Task Main()
    {
        var builder = Kernel.CreateBuilder();

        // Add LLM configuration
        AddChatCompletion(builder);

        // Add function approval service and filter
        builder.Services.AddSingleton<IFunctionApprovalService, ConsoleFunctionApprovalService>();
        builder.Services.AddSingleton<IFunctionInvocationFilter, FunctionInvocationFilter>();

        // Add store and bank plugins
        builder.Plugins.AddFromObject(new StorePlugin(products: new()
        {
            ["Laptop"] = new ProductDetails(price: 1000, quantity: 5),
            ["Headphones"] = new ProductDetails(price: 100, quantity: 4),
            ["Sunglasses"] = new ProductDetails(price: 50, quantity: 7),
            ["Backpack"] = new ProductDetails(price: 40, quantity: 3),
            ["Watch"] = new ProductDetails(price: 150, quantity: 9),
        }));

        builder.Plugins.AddFromObject(new BankPlugin(balance: 2000));

        var kernel = builder.Build();

        // Enable automatic function calling and provide limitations to LLM
        var executionSettings = new OpenAIPromptExecutionSettings
        {
            ChatSystemPrompt = "It's possible to buy something only after withdrawing amount from bank.",
            ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions
        };

        // Initialize kernel arguments (it's possible to experiment with values to compare LLM results).
        var arguments = new KernelArguments(executionSettings) { ["productName"] = "Watch", ["quantity"] = 3 };

        // Define purchase request
        var function = KernelFunctionFactory.CreateFromPrompt(
            "I want to buy {{$productName}} of quantity {{$quantity}} and get balance after the purchase.", functionName: "PurchaseRequest");

        // Start execution
        // Try to reject invocation at each stage to compare LLM results.
        var result = await kernel.InvokeAsync(function, arguments);

        Console.WriteLine(result);
    }

    #region Plugins

    /// <summary>
    /// Class that contains product details.
    /// </summary>
    public sealed class ProductDetails(decimal price, int quantity)
    {
        public decimal Price { get; set; } = price;

        public int Quantity { get; set; } = quantity;
    }

    /// <summary>
    /// Store plugin that provides product price and sells the products to buyer.
    /// </summary>
    public sealed class StorePlugin(Dictionary<string, ProductDetails> products)
    {
        private readonly Dictionary<string, ProductDetails> _products = products;

        [KernelFunction]
        [Description("Provides product price to buyer.")]
        public decimal ProvidePrice(string productName)
        {
            var product = this.GetProduct(productName);
            return product.Price;
        }

        [KernelFunction]
        [Description("Sells product to buyer.")]
        public string Sell(decimal amount, string productName, int quantity)
        {
            var product = this.GetProduct(productName);

            if (quantity > product.Quantity)
            {
                throw new Exception("The requested quantity exceeds the available stock for the selected product.");
            }

            if (amount < quantity * product.Price)
            {
                throw new Exception("Insufficient funds to make a purchase.");
            }

            this._products[productName].Quantity -= quantity;

            return productName;
        }

        private ProductDetails GetProduct(string productName)
        {
            if (!this._products.TryGetValue(productName, out ProductDetails? product))
            {
                throw new Exception("Product was not found.");
            }

            return product;
        }
    }

    /// <summary>
    /// Bank plugin with account balance.
    /// </summary>
    public sealed class BankPlugin(decimal balance)
    {
        private decimal _balance = balance;

        [KernelFunction]
        [Description("Returns account balance.")]
        public decimal CheckBalance() => this._balance;

        [KernelFunction]
        [Description("Withdraws specified amount from balance.")]
        public decimal Withdraw(decimal amount)
        {
            if (this._balance < amount)
            {
                throw new Exception("Insufficient funds.");
            }

            return this._balance -= amount;
        }
    }

    #endregion

    #region Approval

    /// <summary>
    /// Service that verifies if function invocation is approved.
    /// </summary>
    public interface IFunctionApprovalService
    {
        bool IsInvocationApproved(KernelFunction function, KernelArguments arguments);
    }

    /// <summary>
    /// Service that verifies if function invocation is approved using console.
    /// </summary>
    public sealed class ConsoleFunctionApprovalService : IFunctionApprovalService
    {
        public bool IsInvocationApproved(KernelFunction function, KernelArguments arguments)
        {
            Console.WriteLine("====================");
            Console.WriteLine($"Function name: {function.Name}");
            Console.WriteLine($"Plugin name: {function.PluginName ?? "N/A"}");

            if (arguments.Count == 0)
            {
                Console.WriteLine("\nArguments: N/A");
            }
            else
            {
                Console.WriteLine("\nArguments:");

                foreach (var argument in arguments)
                {
                    Console.WriteLine($"{argument.Key}: {argument.Value}");
                }
            }

            Console.WriteLine("\nApprove invocation? (yes/no)");

            var input = Console.ReadLine();

            return input?.Equals("yes", StringComparison.OrdinalIgnoreCase) ?? false;
        }
    }

    #endregion

    #region Filter

    /// <summary>
    /// Filter to invoke function only if it's approved.
    /// </summary>
    public sealed class FunctionInvocationFilter(IFunctionApprovalService approvalService) : IFunctionInvocationFilter
    {
        private readonly IFunctionApprovalService _approvalService = approvalService;

        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            // Invoke the function only if it's approved.
            if (this._approvalService.IsInvocationApproved(context.Function, context.Arguments))
            {
                await next(context);
            }
            else
            {
                // Otherwise, return a result that operation was rejected.
                context.Result = new FunctionResult(context.Result, "Operation was rejected.");
            }
        }
    }

    #endregion

    #region Configuration

    private static void AddChatCompletion(IKernelBuilder builder)
    {
        // Get configuration
        var config = new ConfigurationBuilder()
            .AddUserSecrets<Program>()
            .AddEnvironmentVariables()
            .Build();

        var openAIOptions = config.GetSection(OpenAIOptions.SectionName).Get<OpenAIOptions>();
        var azureOpenAIOptions = config.GetSection(AzureOpenAIOptions.SectionName).Get<AzureOpenAIOptions>();

        if (openAIOptions is not null && openAIOptions.IsValid)
        {
            builder.AddOpenAIChatCompletion(openAIOptions.ChatModelId, openAIOptions.ApiKey);
        }
        else if (azureOpenAIOptions is not null && azureOpenAIOptions.IsValid)
        {
            builder.AddAzureOpenAIChatCompletion(
                azureOpenAIOptions.ChatDeploymentName,
                azureOpenAIOptions.Endpoint,
                azureOpenAIOptions.ApiKey);
        }
        else
        {
            throw new Exception("OpenAI/Azure OpenAI configuration was not found.");
        }
    }

    #endregion
}

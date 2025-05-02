// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Plugins.OpenApi;

namespace Plugins;

/// <summary>
/// These samples show different ways OpenAPI operations can be filtered out from the OpenAPI document before creating a plugin out of it.
/// </summary>
public sealed class OpenApiPlugin_Filtering : BaseTest
{
    private readonly Kernel _kernel;
    private readonly ITestOutputHelper _output;

    public OpenApiPlugin_Filtering(ITestOutputHelper output) : base(output)
    {
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.AddOpenAIChatCompletion(
            modelId: TestConfiguration.OpenAI.ChatModelId,
            apiKey: TestConfiguration.OpenAI.ApiKey);

        this._kernel = builder.Build();

        this._output = output;
    }

    /// <summary>
    /// This sample demonstrates how to filter out specified operations from an OpenAPI plugin based on an exclusion list.
    /// In this scenario, only the `listRepairs` operation from the RepairService OpenAPI plugin is allowed to be invoked,
    /// while operations such as `createRepair`, `updateRepair`, and `deleteRepair` are excluded.
    /// Note: The filtering occurs at the pre-parsing stage, which is more efficient from a resource utilization perspective.
    /// </summary>
    [Fact]
    public async Task ExcludeOperationsBasedOnExclusionListAsync()
    {
        // The RepairService OpenAPI plugin being imported below includes the following operations: `listRepairs`, `createRepair`, `updateRepair`, and `deleteRepair`.
        // However, to meet our business requirements, we need to restrict state-modifying operations such as creating, updating, and deleting repairs, allowing only non-state-modifying operations like listing repairs.
        // To enforce this restriction, we will exclude the `createRepair`, `updateRepair`, and `deleteRepair` operations from the OpenAPI document at the plugin import time.
        List<string> operationsToExclude = ["createRepair", "updateRepair", "deleteRepair"];

        OpenApiFunctionExecutionParameters executionParameters = new()
        {
            OperationSelectionPredicate = (OperationSelectionPredicateContext context) => !operationsToExclude.Contains(context.Id!)
        };

        // Import the RepairService OpenAPI plugin
        await this._kernel.ImportPluginFromOpenApiAsync(
            pluginName: "RepairService",
            filePath: "Resources/Plugins/RepairServicePlugin/repair-service.json",
            executionParameters: executionParameters);

        // Tell the AI model not to call any function and show the list of functions it can call instead.
        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.None() };
        FunctionResult result = await this._kernel.InvokePromptAsync(promptTemplate: "Show me the list of the functions you can call", arguments: new KernelArguments(settings));

        this._output.WriteLine(result);

        // The AI model output:
        // I can call the following functions in the current context:
        // 1. `functions.RepairService - listRepairs`: Returns a list of repairs with their details and images. It takes an optional parameter `assignedTo` to filter the repairs based on the assigned individual.
        // I can also utilize the `multi_tool_use.parallel` function to execute multiple tools in parallel if required.
    }

    /// <summary>
    /// This sample demonstrates how to include specified operations from an OpenAPI plugin based on an inclusion list.
    /// In this scenario, only the `createRepair` and `updateRepair` operations from the RepairService OpenAPI plugin are allowed to be invoked,
    /// while operations such as `listRepairs` and `deleteRepair` are excluded.
    /// Note: The filtering occurs at the pre-parsing stage, which is more efficient from a resource utilization perspective.
    /// </summary>
    [Fact]
    public async Task ImportOperationsBasedOnInclusionListAsync()
    {
        // The RepairService OpenAPI plugin, parsed and imported below, has the following operations: `listRepairs`, `createRepair`, `updateRepair`, and `deleteRepair`.  
        // However, for our business scenario, we only want to permit the AI model to invoke the `createRepair` and `updateRepair` operations, excluding all others.
        // To accomplish this, we will define an inclusion list that specifies the allowed operations and filters out the rest.  
        List<string> operationsToInclude = ["createRepair", "updateRepair"];

        // The selection predicate is initialized to evaluate each operation in the OpenAPI document and include only those specified in the inclusion list. 
        OpenApiFunctionExecutionParameters executionParameters = new()
        {
            OperationSelectionPredicate = (OperationSelectionPredicateContext context) => operationsToInclude.Contains(context.Id!)
        };

        // Import the RepairService OpenAPI plugin
        await this._kernel.ImportPluginFromOpenApiAsync(
            pluginName: "RepairService",
            filePath: "Resources/Plugins/RepairServicePlugin/repair-service.json",
            executionParameters: executionParameters);

        // Tell the AI model not to call any function and show the list of functions it can call instead.
        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.None() };
        FunctionResult result = await this._kernel.InvokePromptAsync(promptTemplate: "Show me the list of the functions you can call", arguments: new KernelArguments(settings));

        this._output.WriteLine(result);

        // The AI model output:
        // Here are the functions I can call for you:
        // 1. **RepairService - createRepair **: 
        //    -Adds a new repair to the list with details about the repair.
        // 2. **RepairService - updateRepair **: 
        //    -Updates an existing repair in the list with new details.
        // If you need to perform any repair - related actions such as creating or updating repair records, feel free to ask!
    }

    /// <summary>
    /// This sample demonstrates how to selectively include certain operations from an OpenAPI plugin based on HTTP method used.
    /// In this scenario, only `GET` operations from the RepairService OpenAPI plugin are allowed for invocation,
    /// while `POST`, `PUT`, and `DELETE` operations are excluded.
    /// Note: The filtering occurs at the pre-parsing stage, which is more efficient from a resource utilization perspective.
    /// </summary>
    [Fact]
    public async Task ImportOperationsBasedOnMethodAsync()
    {
        // The parsed RepairService OpenAPI plugin includes operations such as `listRepairs`, `createRepair`, `updateRepair`, and `deleteRepair`.  
        // However, for our business requirements, we only permit non-state-modifying operations like listing repairs, excluding all others.  
        // To achieve this, we set up the selection predicate to evaluate each operation in the OpenAPI document, including only those with the `GET` method.  
        // Note: The selection predicate can assess operations based on operation ID, method, path, and description.  
        OpenApiFunctionExecutionParameters executionParameters = new()
        {
            OperationSelectionPredicate = (OperationSelectionPredicateContext context) => context.Method == "Get"
        };

        // Import the RepairService OpenAPI plugin
        await this._kernel.ImportPluginFromOpenApiAsync(
            pluginName: "RepairService",
            filePath: "Resources/Plugins/RepairServicePlugin/repair-service.json",
            executionParameters: executionParameters);

        // Tell the AI model not to call any function and show the list of functions it can call instead.
        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.None() };
        FunctionResult result = await this._kernel.InvokePromptAsync(promptTemplate: "Show me the list of the functions you can call", arguments: new KernelArguments(settings));

        this._output.WriteLine(result);

        // The AI model output:
        // I can call the following function:
        // 1. `RepairService - listRepairs`: This function returns a list of repairs with their details and images.
        // It can accept an optional parameter `assignedTo` to filter the repairs assigned to a specific person.
    }

    /// <summary>
    /// This example illustrates how to selectively exclude specific operations from an OpenAPI plugin based on the HTTP method used and the presence of a payload.
    /// In this context, GET operations that are defined with a payload, which contradicts the HTTP semantic of being idempotent, are not imported.
    /// Note: The filtering happens at the post-parsing stage, which is less efficient in terms of resource utilization.
    /// </summary>
    [Fact]
    public async Task FilterOperationsAtPostParsingStageAsync()
    {
        OpenApiDocumentParser parser = new();
        using StreamReader reader = System.IO.File.OpenText("Resources/Plugins/RepairServicePlugin/repair-service.json");

        // Parse the OpenAPI document.
        RestApiSpecification specification = await parser.ParseAsync(stream: reader.BaseStream);

        // The parsed RepairService OpenAPI plugin includes operations like `listRepairs`, `createRepair`, `updateRepair`, and `deleteRepair`.  
        // However, based on our business requirements, we need to identify all GET operations that are defined as non-idempotent (i.e., have a payload),  
        // log a warning for each of them, and exclude these operations from the import.  
        // To do this, we will locate all GET operations that contain a payload.
        // Note that the RepairService OpenAPI plugin does not have any GET operations with payloads, so no operations will be found in this case.
        // However, the code below demonstrates how to identify and exclude such operations if they were present.
        IEnumerable<RestApiOperation> operationsToExclude = specification.Operations.Where(o => o.Method == HttpMethod.Get && o.Payload is not null);

        // Exclude operations that are declared as non-idempotent due to having a payload.
        foreach (RestApiOperation operation in operationsToExclude)
        {
            this.Output.WriteLine($"Warning: The `{operation.Id}` operation with `{operation.Method}` has payload which contradicts to being idempotent. This operation will not be imported.");
            specification.Operations.Remove(operation);
        }

        // Import the OpenAPI document specification.
        this._kernel.ImportPluginFromOpenApi("RepairService", specification);

        // Tell the AI model not to call any function and show the list of functions it can call instead.
        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.None() };
        FunctionResult result = await this._kernel.InvokePromptAsync(promptTemplate: "Show me the list of the functions you can call", arguments: new KernelArguments(settings));

        this._output.WriteLine(result);

        // The AI model output:
        // I can call the following functions:
        // 1. **RepairService - listRepairs **: Returns a list of repairs with their details and images.
        // 2. **RepairService - createRepair **: Adds a new repair to the list with the given details and image URL.
        // 3. **RepairService - updateRepair **: Updates an existing repair with new details and image URL.
        // 4. **RepairService - deleteRepair **: Deletes an existing repair from the list using its ID.
    }
}

// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;

namespace Step06;

public class Step06_WorkflowProcess : BaseTest
{
    // Target Open AI Services
    protected override bool ForceOpenAI => true;

    public Step06_WorkflowProcess(ITestOutputHelper output)
        : base(output, redirectSystemConsoleOutput: true) { }

    [Theory]
    [InlineData("testEnd")]
    [InlineData("testGoto")]
    [InlineData("testLoop")]
    [InlineData("testCondition")]
    [InlineData("testExpression")]
    [InlineData("deepResearch")]
    [InlineData("demo250729")]
    public async Task RunWorkflow(string fileName)
    {
        const string InputEventId = "question";

        Console.WriteLine("PROCESS INIT\n");

        using StreamReader yamlReader = File.OpenText(@$"{nameof(Step06)}\{fileName}.yaml");
        KernelProcess process = ObjectModelBuilder.Build(yamlReader, InputEventId);

        Console.WriteLine("\nPROCESS INVOKE\n");

        Kernel kernel = this.CreateKernel();
        await using LocalKernelProcessContext context = await process.StartAsync(kernel, new KernelProcessEvent() { Id = InputEventId, Data = "<placeholder>" });
        Console.WriteLine("\nPROCESS DONE");
    }

    private Kernel CreateKernel(bool withLogger = false)
    {
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();

        if (withLogger)
        {
            kernelBuilder.Services.AddSingleton(this.LoggerFactory);
        }
        this.AddChatCompletionToKernel(kernelBuilder);
        this.AddChatClientToKernel(kernelBuilder);

        return kernelBuilder.Build();
    }
}

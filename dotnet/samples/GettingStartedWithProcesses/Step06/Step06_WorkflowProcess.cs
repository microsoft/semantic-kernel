// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
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
    [InlineData("deepResearch")]
    public async Task RunWorkflow(string fileName)
    {
        const string InputEventId = "question";

        Console.WriteLine("PROCESS INIT\n");

        using StreamReader yamlReader = File.OpenText(@$"{nameof(Step06)}\{fileName}.yaml");
        KernelProcess process = ObjectModelBuilder.Build(yamlReader, InputEventId);

        Console.WriteLine("\nPROCESS INVOKE\n");

        Kernel kernel = this.CreateKernel();
        await using LocalKernelProcessContext context = await process.StartAsync(kernel, new KernelProcessEvent() { Id = InputEventId, Data = "Why is the sky blue?" });
        Console.WriteLine("\nPROCESS DONE");
    }

    private Kernel CreateKernel()
    {
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();

        kernelBuilder.Services.AddSingleton<ILoggerFactory>(this.LoggerFactory);
        this.AddChatCompletionToKernel(kernelBuilder);
        this.AddChatClientToKernel(kernelBuilder);

        return kernelBuilder.Build();
    }
}

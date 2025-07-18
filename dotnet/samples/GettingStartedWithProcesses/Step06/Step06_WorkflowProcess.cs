// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace Step06;

public class Step06_WorkflowProcess : BaseTest
{
    // Target Open AI Services
    protected override bool ForceOpenAI => true;

    public Step06_WorkflowProcess(ITestOutputHelper output)
        : base(output, redirectSystemConsoleOutput: true) { }

    [Theory]
    [InlineData("testLoop")]
    [InlineData("testCondition")]
    [InlineData("deepResearch")]
    public async Task RunWorkflow(string fileName)
    {
        const string InputEventId = "question";

        Console.WriteLine("$$$ PROCESS INIT");

        string yaml = File.ReadAllText(@$"{nameof(Step06)}\{fileName}.yaml");
        KernelProcess process = ObjectModelBuilder.Build(fileName, yaml, InputEventId);

        Console.WriteLine("$$$ PROCESS INVOKE");

        Kernel kernel = this.CreateKernelWithChatCompletion();
        await using LocalKernelProcessContext context = await process.StartAsync(kernel, new KernelProcessEvent() { Id = InputEventId, Data = "Why is the sky blue?" });

        Console.WriteLine("$$$ PROCESS DONE");
    }
}

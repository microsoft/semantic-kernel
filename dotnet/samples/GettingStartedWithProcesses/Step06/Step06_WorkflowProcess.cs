// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace Step06;

public class Step06_WorkflowProcess : BaseTest
{
    // Target Open AI Services
    protected override bool ForceOpenAI => true;

    public Step06_WorkflowProcess(ITestOutputHelper output)
        : base(output, redirectSystemConsoleOutput: true) { }

    [Fact]
    public async Task RunWorkflowProcess()
    {
        const string InputEventId = "question";
        const string FileName = "testLoop";
        //const string FileName = "testCondition";
        //const string FileName = "deepResearch";

        Console.WriteLine("$$$ PROCESS INIT");

        string yaml = File.ReadAllText(@$"{nameof(Step06)}\{FileName}.yaml");
        KernelProcess process = ObjectModelBuilder.Build(FileName, yaml, InputEventId);

        Console.WriteLine("$$$ PROCESS INVOKE");

        Kernel kernel = this.CreateKernelWithChatCompletion();
        await using LocalKernelProcessContext context = await process.StartAsync(kernel, new KernelProcessEvent() { Id = InputEventId, Data = "Why is the sky blue?" });

        Console.WriteLine("$$$ PROCESS DONE");
    }
}

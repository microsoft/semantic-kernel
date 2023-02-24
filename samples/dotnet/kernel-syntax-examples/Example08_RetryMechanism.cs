// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.CoreSkills;
using Microsoft.SemanticKernel.KernelExtensions;
using Reliability;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example08_RetryMechanism
{
    public static async Task RunAsync()
    {
        Console.WriteLine("============================ RetryMechanism ============================");

        IKernel kernel = Kernel.Builder.WithLogger(ConsoleLogger.Log).Build();
        kernel.Config.SetRetryMechanism(new RetryThreeTimesWithBackoff());

        // OpenAI settings
        kernel.Config.AddOpenAICompletionBackend("text-davinci-003", "text-davinci-003", Env.Var("OPENAI_API_KEY"));

        // Load semantic skill defined with prompt templates
        string folder = RepoFiles.SampleSkillsPath();

        kernel.ImportSkill(new TimeSkill(), "time");

        var qaSkill = kernel.ImportSemanticSkillFromDirectory(
            folder,
            "QASkill");

        var question = "How popular is Polly library?";
        var answer = await kernel.RunAsync(question, qaSkill["Question"]);

        Console.WriteLine($"Question: {question}\n\n" + answer);
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Amazon.Runtime;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning.Handlebars;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Plugins;
using Plugins.DictionaryPlugin;
using RepoUtils;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using System.Reflection;
using Microsoft.CodeAnalysis.Emit;
using System.Collections.Generic;
using System.Text.RegularExpressions;

/**
 * This example shows how to use the Handlebars sequential planner.
 */
public static class Example999_AutoPlugin
{
    private static int s_sampleIndex; 
    private static string plannerprompt = @"

        Extract today's featured article text from https://en.wikipedia.org

    ";

    /// <summary>
    /// Show how to create a plan with Handlebars and execute it.
    /// </summary>
    public static async Task RunAsync()
    {
        s_sampleIndex = 1;
        bool shouldPrintPrompt = true;

        // Using primitive types as inputs and outputs

        await AutoPluginSampleAsync();
    }

    private static void WriteSampleHeadingToConsole(string name)
    {
        Console.WriteLine($"======== [Handlebars AutoPlugin Planner] Attempt {s_sampleIndex++} - Create and Execute {name} Plan ========");
    }

    private static async Task RunSamplePluginClassAsync(string goal, bool shouldPrintPrompt = false, KernelPlugin? kp = null)
    {
        string openAIModelId = TestConfiguration.OpenAI.ChatModelId;
        string openAIApiKey = TestConfiguration.OpenAI.ApiKey;

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: openAIModelId,
                apiKey: openAIApiKey)
            .Build();

        if (kp != null)
        {
            kernel.Plugins.Add(kp);
        }

        // Use gpt-4 or newer models if you want to test with loops. 
        var allowLoopsInPlan = true;
        var planner = new HandlebarsPlanner(
            new HandlebarsPlannerConfig()
            {
                // Change this if you want to test with loops regardless of model selection.
                AllowLoops = allowLoopsInPlan
            });

        Console.WriteLine($"Goal: {goal}");

        // Create the plan
        var plan = await planner.CreatePlanAsync(kernel, goal);

        // Print the prompt template
        if (shouldPrintPrompt)
        {
            Console.WriteLine($"\nPrompt template:\n{plan.Prompt}");
        }

        Console.WriteLine($"\nOriginal plan:\n{plan}");

        // Execute the plan
        var result = await plan.InvokeAsync(kernel, new KernelArguments(), CancellationToken.None);
        Console.WriteLine($"\nResult:\n{result}\n");
    }

    private static async Task AutoPluginSampleAsync(bool shouldPrintPrompt = false)
    {
        KernelPlugin kp = null;
        bool needMorePlugins = true;
        while (needMorePlugins)
        {
            WriteSampleHeadingToConsole("AutoPluginSample");
            try
            {
                string testPrompt = plannerprompt;
                await RunSamplePluginClassAsync(testPrompt, shouldPrintPrompt, kp);
                needMorePlugins = false;
            }
            catch (KernelException e)
            {
                Console.WriteLine($"{e.Message.Split("Planner output:")[1]}\n");
                string input = e.Message;
                string code = input.Substring(input.IndexOf("```csharp") + "```csharp".Length, input.IndexOf("```", input.IndexOf("```csharp") + "```csharp".Length) - input.IndexOf("```csharp") - "```csharp".Length);
                if (code.Contains("Assemblies required"))
                {
                    code = input.Substring(input.IndexOf("```csharp") + "```csharp".Length, input.IndexOf("Assemblies required", input.IndexOf("```csharp") + "```csharp".Length) - input.IndexOf("```csharp") - "```csharp".Length);
                }
                string[] lines = input.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);

                List<string> assemblies = new List<string>();

                bool startAdding = false;

                foreach (string line in lines)
                {
                    if (line.Contains("Assemblies required"))
                    {
                        startAdding = true;
                        continue;
                    }

                    if (startAdding && line.StartsWith("- "))
                    {
                        assemblies.Add(line.Substring(2));
                    }
                }

                SyntaxTree syntaxTree = CSharpSyntaxTree.ParseText(code);
                string directory = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);

                // Get all .dll files in the directory
                string[] files = Directory.GetFiles(directory, "*.dll");

                // Create a list to hold the filenames
                List<string> filenames = new List<string>();

                List<MetadataReference> references = new List<MetadataReference>();

                // General references that are often needed
                references.Add(MetadataReference.CreateFromFile(typeof(object).GetTypeInfo().Assembly.Location));
                //references.Add(MetadataReference.CreateFromFile(typeof(System.ComponentModel.BrowsableAttribute).Assembly.Location));
                references.Add(MetadataReference.CreateFromFile(Assembly.Load("System.ComponentModel, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a").Location));
                references.Add(MetadataReference.CreateFromFile(Assembly.Load("System.Runtime, Version=7.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a").Location));
                references.Add(MetadataReference.CreateFromFile(Assembly.Load("netstandard, Version = 2.0.0.0, Culture = neutral, PublicKeyToken = cc7b13ffcd2ddd51").Location));
                references.Add(MetadataReference.CreateFromFile(Assembly.Load("System.Collections, Version=7.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a").Location));

                foreach (string assembly in assemblies)
                {
                    if (!assembly.Contains("SemanticKernel"))
                        references.Add(MetadataReference.CreateFromFile(Assembly.Load(assembly).Location));
                }

                foreach (string file in files)
                {
                    references.Add(MetadataReference.CreateFromFile(file));
                }

                bool needMoreAssemblies = true;
                while (needMoreAssemblies)
                {
                    needMoreAssemblies = false;
                    Console.WriteLine("Compiling Generated Kernel Plugin");

                    CSharpCompilation compilation = CSharpCompilation.Create(
                        "assemblyName",
                        syntaxTrees: new[] { syntaxTree },
                        references: references.ToArray(),
                        options: new CSharpCompilationOptions(OutputKind.DynamicallyLinkedLibrary));

                    using (var ms = new MemoryStream())
                    {
                        EmitResult result = compilation.Emit(ms);

                        if (!result.Success)
                        {
                            // handle exceptions
                            Console.WriteLine("Compilation failed");
                            foreach (var x in result.Diagnostics) // Logic to resolve compiler errors
                            {
                                if (x.Id.Equals("CS0012")) // Missing Assembly
                                {
                                    string pattern = @"'([^']*)'\.";
                                    Match match = Regex.Match(x.GetMessage(), pattern);

                                    if (match.Success)
                                    {
                                        string assemblyString = match.Groups[1].Value;
                                        Console.WriteLine("Adding assembly " + assemblyString);
                                        references.Add(MetadataReference.CreateFromFile(Assembly.Load(assemblyString).Location));
                                        needMoreAssemblies = true;
                                    }
                                }
                                else
                                {
                                    Console.WriteLine(x.GetMessage());
                                    needMoreAssemblies = false;
                                    needMorePlugins = false; // Abort all new attempts
                                }
                            }
                            if (needMoreAssemblies)
                            {
                                Console.WriteLine("Restarting compilation.\n");
                            }
                            else
                            {
                                Console.WriteLine("Could not resolve compiler errors.");
                            }
                        }
                        else
                        {
                            ms.Seek(0, SeekOrigin.Begin);
                            Assembly assembly = Assembly.Load(ms.ToArray());

                            // Get the type from the assembly
                            Type pluginType = assembly.GetType("Plugins.GeneratedPlugin");

                            // Create an instance of the type
                            var instance = Activator.CreateInstance(pluginType);

                            Console.WriteLine("Adding plugin to kernel.\nRestarting planner.\n");

                            Type factoryType = typeof(KernelPluginFactory);
                            MethodInfo method = factoryType.GetMethod("CreateFromType");
                            MethodInfo genericMethod = method.MakeGenericMethod(pluginType);
                            string param = "GeneratedPlugin";
                            object[] parameters = { param, null };

                            kp = (KernelPlugin)genericMethod.Invoke(null, parameters);
                            //kp = instance;
                        }
                    }
                }
                needMorePlugins = true;
            }
        }
    }
}

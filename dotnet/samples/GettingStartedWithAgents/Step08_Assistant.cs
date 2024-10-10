<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
﻿// Copyright (c) Microsoft. All rights reserved.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
﻿// Copyright (c) Microsoft. All rights reserved.
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
using System.ComponentModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
using Resources;
6d73513a859ab2d05e01db3bc1d405827799e34b
using Resources;
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
using Resources;
6d73513a859ab2d05e01db3bc1d405827799e34b
using Resources;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes

namespace GettingStarted;

/// <summary>
/// This example demonstrates similarity between using <see cref="OpenAIAssistantAgent"/>
/// and <see cref="ChatCompletionAgent"/> (see: Step 2).
/// </summary>
public class Step08_Assistant(ITestOutputHelper output) : BaseAgentsTest(output)
{
    private const string HostName = "Host";
    private const string HostInstructions = "Answer questions about the menu.";

    [Fact]
    public async Task UseSingleAssistantAgentAsync()
    {
        // Define the agent
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                kernel: new(),
                clientProvider: this.GetClientProvider(),
                new(this.Model)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
                kernel: new(),
                clientProvider: this.GetClientProvider(),
                new(this.Model)
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
                clientProvider: this.GetClientProvider(),
                definition: new OpenAIAssistantDefinition(this.Model)
                kernel: new(),
                clientProvider: this.GetClientProvider(),
                new(this.Model)
 6d73513a859ab2d05e01db3bc1d405827799e34b
                clientProvider: this.GetClientProvider(),
                definition: new OpenAIAssistantDefinition(this.Model)
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
                {
                    Instructions = HostInstructions,
                    Name = HostName,
                    Metadata = AssistantSampleMetadata,
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                });
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
                });
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
                });
=======
>>>>>>> Stashed changes
                },
                kernel: new Kernel());
                });
 6d73513a859ab2d05e01db3bc1d405827799e34b
                },
                kernel: new Kernel());
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

        // Initialize plugin and add to the agent's Kernel (same as direct Kernel usage).
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        agent.Kernel.Plugins.Add(plugin);

        // Create a thread for the agent conversation.
        string threadId = await agent.CreateThreadAsync(new OpenAIThreadCreationOptions { Metadata = AssistantSampleMetadata });

        // Respond to user input
        try
        {
            await InvokeAgentAsync("Hello");
            await InvokeAgentAsync("What is the special soup?");
            await InvokeAgentAsync("What is the special drink?");
            await InvokeAgentAsync("Thank you");
        }
        finally
        {
            await agent.DeleteThreadAsync(threadId);
            await agent.DeleteAsync();
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            await agent.AddChatMessageAsync(threadId, message);
            this.WriteAgentChatMessage(message);

            await foreach (ChatMessageContent response in agent.InvokeAsync(threadId))
            {
                this.WriteAgentChatMessage(response);
            }
        }
    }

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
    [Fact]
    public async Task UseTemplateForAssistantAgentAsync()
    {
        // Define the agent
        string generateStoryYaml = EmbeddedResource.Read("GenerateStory.yaml");
        PromptTemplateConfig templateConfig = KernelFunctionYaml.ToPromptTemplateConfig(generateStoryYaml);

        // Instructions, Name and Description properties defined via the config.
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateFromTemplateAsync(
                clientProvider: this.GetClientProvider(),
                capabilities: new OpenAIAssistantCapabilities(this.Model)
                {
                    Metadata = AssistantSampleMetadata,
                },
                kernel: new Kernel(),
                defaultArguments: new KernelArguments()
                {
                    { "topic", "Dog" },
                    { "length", "3" },
                },
                templateConfig);

        // Create a thread for the agent conversation.
        string threadId = await agent.CreateThreadAsync(new OpenAIThreadCreationOptions { Metadata = AssistantSampleMetadata });

        try
        {
            // Invoke the agent with the default arguments.
            await InvokeAgentAsync();

            // Invoke the agent with the override arguments.
            await InvokeAgentAsync(
                new()
                {
                { "topic", "Cat" },
                { "length", "3" },
                });
        }
        finally
        {
            await agent.DeleteThreadAsync(threadId);
            await agent.DeleteAsync();
        }

        // Local function to invoke agent and display the response.
        async Task InvokeAgentAsync(KernelArguments? arguments = null)
        {
            await foreach (ChatMessageContent response in agent.InvokeAsync(threadId, arguments))
            {
                WriteAgentChatMessage(response);
            }
        }
    }

 6d73513a859ab2d05e01db3bc1d405827799e34b
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    private sealed class MenuPlugin
    {
        [KernelFunction, Description("Provides a list of specials from the menu.")]
        [System.Diagnostics.CodeAnalysis.SuppressMessage("Design", "CA1024:Use properties where appropriate", Justification = "Too smart")]
        public string GetSpecials() =>
            """
            Special Soup: Clam Chowder
            Special Salad: Cobb Salad
            Special Drink: Chai Tea
            """;

        [KernelFunction, Description("Provides the price of the requested menu item.")]
        public string GetItemPrice(
            [Description("The name of the menu item.")]
            string menuItem) =>
            "$9.99";
    }
}

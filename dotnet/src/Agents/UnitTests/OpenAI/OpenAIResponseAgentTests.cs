// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Linq;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Tests for the <see cref="OpenAIResponseAgent"/> class.
/// </summary>
public sealed class OpenAIResponseAgentTests : BaseOpenAIResponseClientTest
{
    /// <summary>
    /// Tests that the constructor verifies parameters and throws <see cref="ArgumentNullException"/> when necessary.
    /// </summary>
    [Fact]
    public void ConstructorShouldVerifyParams()
    {
        // Arrange & Act & Assert
        Assert.Throws<ArgumentNullException>(() => new OpenAIResponseAgent(null!));
    }

    /// <summary>
    /// Tests that the OpenAIResponseAgent.InvokeAsync verifies parameters and throws <see cref="ArgumentNullException"/> when necessary.
    /// </summary>
    [Fact]
    public void InvokeShouldVerifyParams()
    {
        // Arrange
        var agent = new OpenAIResponseAgent(this.Client);
        string nullString = null!;
        ChatMessageContent nullMessage = null!;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => agent.InvokeAsync(nullString));
        Assert.Throws<ArgumentNullException>(() => agent.InvokeAsync(nullMessage));
    }

    /// <summary>
    /// Tests that the OpenAIResponseAgent.InvokeAsync.
    /// </summary>
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task VerifyInvokeAsync(bool storeEnabled)
    {
        // Arrange
        this.MessageHandlerStub.ResponsesToReturn.Add(
            new HttpResponseMessage(System.Net.HttpStatusCode.OK) { Content = new StringContent(InvokeResponse) }
        );
        var agent = new OpenAIResponseAgent(this.Client)
        {
            Name = "ResponseAgent",
            Instructions = "Answer all queries in English and French.",
            StoreEnabled = storeEnabled
        };

        // Act
        var responseItems = agent.InvokeAsync("What is the capital of France?");

        // Assert
        Assert.NotNull(responseItems);
        var items = await responseItems!.ToListAsync<AgentResponseItem<ChatMessageContent>>();
        Assert.Single(items);
        Assert.Equal("The capital of France is Paris.\n\nLa capitale de la France est Paris.", items[0].Message.Content);
    }

    /// <summary>
    /// Tests that the OpenAIResponseAgent.InvokeStreamingAsync.
    /// </summary>
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task VerifyInvokeStreamingAsync(bool storeEnabled)
    {
        // Arrange
        this.MessageHandlerStub.ResponsesToReturn.Add(
            new HttpResponseMessage(System.Net.HttpStatusCode.OK) { Content = new StringContent(InvokeStreamingResponse) }
        );
        var agent = new OpenAIResponseAgent(this.Client)
        {
            Name = "ResponseAgent",
            Instructions = "Answer all queries in English and French.",
            StoreEnabled = storeEnabled
        };

        // Act
        var message = new ChatMessageContent(AuthorRole.User, "What is the capital of France?");
        var responseMessages = await agent.InvokeStreamingAsync(
            message,
            options: new OpenAIResponseAgentInvokeOptions()
            {
                AdditionalInstructions = "Respond to all user questions with 'Computer says no'.",
            }).ToArrayAsync();

        var responseText = string.Join(string.Empty, responseMessages.Select(ri => ri.Message.Content));

        // Assert
        Assert.NotNull(responseText);
        Assert.Contains("Computer says no", responseText);
    }

    /// <summary>
    /// Tests that the OpenAIResponseAgent.InvokeAsync.
    /// </summary>
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task VerifyInvokeWithFunctionCallingAsync(bool storeEnabled)
    {
        // Arrange
        this.MessageHandlerStub.ResponsesToReturn.Add(
            new HttpResponseMessage(System.Net.HttpStatusCode.OK) { Content = new StringContent(this.InvokeWithFunctionCallingResponses[0]) }
        );
        this.MessageHandlerStub.ResponsesToReturn.Add(
            new HttpResponseMessage(System.Net.HttpStatusCode.OK) { Content = new StringContent(this.InvokeWithFunctionCallingResponses[1]) }
        );
        var agent = new OpenAIResponseAgent(this.Client)
        {
            Name = "ResponseAgent",
            Instructions = "Answer questions about the menu.",
            StoreEnabled = storeEnabled
        };
        agent.Kernel.Plugins.Add(KernelPluginFactory.CreateFromType<MenuPlugin>());

        // Act
        var responseItems = agent.InvokeAsync("What is the special soup and how much does it cost?");

        // Assert
        Assert.NotNull(responseItems);
        var items = await responseItems!.ToListAsync<AgentResponseItem<ChatMessageContent>>();
        Assert.Equal(3, items.Count);
        Assert.Equal("The special soup is Clam Chowder, and it costs $9.99.", items[2].Message.Content);
    }

    #region private
    private const string InvokeResponse =
        """
        {
          "id": "resp_67e8f5cf761c8191aab763d1e901e3410bbdc4b8da506cd2",
          "object": "response",
          "created_at": 1743320527,
          "status": "completed",
          "error": null,
          "incomplete_details": null,
          "instructions": "Answer all queries in English and French.",
          "max_output_tokens": null,
          "model": "gpt-4o-2024-08-06",
          "output": [
            {
              "type": "message",
              "id": "msg_67e8f5cfbe688191a428ed9869c39fea0bbdc4b8da506cd2",
              "status": "completed",
              "role": "assistant",
              "content": [
                {
                  "type": "output_text",
                  "text": "The capital of France is Paris.\n\nLa capitale de la France est Paris.",
                  "annotations": []
                }
              ]
            }
          ],
          "parallel_tool_calls": true,
          "previous_response_id": null,
          "reasoning": {
            "effort": null,
            "generate_summary": null
          },
          "store": true,
          "temperature": 1.0,
          "text": {
            "format": {
              "type": "text"
            }
          },
          "tool_choice": "auto",
          "tools": [],
          "top_p": 1.0,
          "truncation": "disabled",
          "usage": {
            "input_tokens": 26,
            "input_tokens_details": {
              "cached_tokens": 0
            },
            "output_tokens": 16,
            "output_tokens_details": {
              "reasoning_tokens": 0
            },
            "total_tokens": 42
          },
          "user": "ResponseAgent",
          "metadata": {}
        }
        """;

    private const string InvokeStreamingResponse =
        """
        content block 0: event: response.created
        data: {"type":"response.created","sequence_number":0,"response":{"id":"resp_68383e45be4081919b7bad84c27e436b0f0f17949d11ddcf","object":"response","created_at":1748516421,"status":"in_progress","background":false,"error":null,"incomplete_details":null,"instructions":"Answer all queries in English and French.\nRespond to all user questions with 'Computer says no'.","max_output_tokens":null,"model":"gpt-4o-mini-2024-07-18","output":[],"parallel_tool_calls":true,"previous_response_id":null,"reasoning":{"effort":null,"summary":null},"service_tier":"auto","store":true,"temperature":1.0,"text":{"format":{"type":"text"}},"tool_choice":"auto","tools":[],"top_p":1.0,"truncation":"disabled","usage":null,"user":"UnnamedAgent","metadata":{}}}

        event: response.in_progress
        
        data: {"type":"response.in_progress","sequence_number":1,"response":{"id":"resp_68383e45be4081919b7bad84c27e436b0f0f17949d11ddcf","object":"response","created_at":1748516421,"status":"in_progress","background":false,"error":null,"incomplete_details":null,"instructions":"Answer all queries in English and French.\nRespond to all user questions with 'Computer says no'.","max_output_tokens":null,"model":"gpt-4o-mini-2024-07-18","output":[],"parallel_tool_calls":true,"previous_response_id":null,"reasoning":{"effort":null,"summary":null},"service_tier":"auto","store":true,"temperature":1.0,"text":{"format":{"type":"text"}},"tool_choice":"auto","tools":[],"top_p":1.0,"truncation":"disabled","usage":null,"user":"UnnamedAgent","metadata":{}}}

        content block 2: event: response.output_item.added
        data: {"type":"response.output_item.added","sequence_number":2,"output_index":0,"item":{"id":"msg_68383e4655b48191beb9f496d37dca950f0f17949d11ddcf","type":"message","status":"in_progress","content":[],"role":"assistant"}}
        
        content block 3: event: response.content_part.added
        data: {"type":"response.content_part.added","sequence_number":3,"item_id":"msg_68383e4655b48191beb9f496d37dca950f0f17949d11ddcf","output_index":0,"content_index":0,"part":{"type":"output_text","annotations":[],"text":""}}
        
        event: response.output_text.delta
        data: {"type":"response.output_text.delta","sequence_number":4,"item_id":"msg_68383e4655b48191beb9f496d37dca950f0f17949d11ddcf","output_index":0,"content_index":0,"delta":"Computer"}

        content block 4: event: response.output_text.delta
        data: {"type":"response.output_text.delta","sequence_number":5,"item_id":"msg_68383e4655b48191beb9f496d37dca950f0f17949d11ddcf","output_index":0,"content_index":0,"delta":" says"}
        
        event: response.output_text.delta
        data: {"type":"response.output_text.delta","sequence_number":6,"item_id":"msg_68383e4655b48191beb9f496d37dca950f0f17949d11ddcf","output_index":0,"content_index":0,"delta":" no"}

        content block 5: event: response.output_text.delta
        data: {"type":"response.output_text.delta","sequence_number":7,"item_id":"msg_68383e4655b48191beb9f496d37dca950f0f17949d11ddcf","output_index":0,"content_index":0,"delta":"."}
        
        content block 6: event: response.output_text.delta
        data: {"type":"response.output_text.delta","sequence_number":8,"item_id":"msg_68383e4655b48191beb9f496d37dca950f0f17949d11ddcf","output_index":0,"content_index":0,"delta":"  \n"}
        """;

    private readonly string[] InvokeWithFunctionCallingResponses =
    [
        """
                {
          "id": "resp_6846bee002d0819f9c3c95e51652c3f80de9f0bbe6ed706c",
          "object": "response",
          "created_at": 1749466848,
          "status": "completed",
          "background": false,
          "error": null,
          "incomplete_details": null,
          "instructions": "Answer questions about the menu.\n",
          "max_output_tokens": null,
          "model": "gpt-4o-mini-2024-07-18",
          "output": [
            {
              "id": "fc_6846bee12900819f9f9c786bc348a2140de9f0bbe6ed706c",
              "type": "function_call",
              "status": "completed",
              "arguments": "{}",
              "call_id": "call_ULt2nBV5pnSyG6g52KobWBXg",
              "name": "MenuPlugin-GetSpecials"
            },
            {
              "id": "fc_6846bee15ae8819f9f698662b9e43aed0de9f0bbe6ed706c",
              "type": "function_call",
              "status": "completed",
              "arguments": "{\"menuItem\":\"special soup\"}",
              "call_id": "call_vjyihEyn9xRhZxmjfmBEYzvA",
              "name": "MenuPlugin-GetItemPrice"
            }
          ],
          "parallel_tool_calls": true,
          "previous_response_id": null,
          "reasoning": {
            "effort": null,
            "summary": null
          },
          "service_tier": "default",
          "store": true,
          "temperature": 1.0,
          "text": {
            "format": {
              "type": "text"
            }
          },
          "tool_choice": "auto",
          "tools": [
            {
              "type": "function",
              "description": "Provides a list of specials from the menu.",
              "name": "MenuPlugin-GetSpecials",
              "parameters": {
                "type": "object",
                "properties": {}
              },
              "strict": false
            },
            {
              "type": "function",
              "description": "Provides the price of the requested menu item.",
              "name": "MenuPlugin-GetItemPrice",
              "parameters": {
                "type": "object",
                "required": [
                  "menuItem"
                ],
                "properties": {
                  "menuItem": {
                    "description": "The name of the menu item.",
                    "type": "string"
                  }
                }
              },
              "strict": false
            }
          ],
          "top_p": 1.0,
          "truncation": "disabled",
          "usage": {
            "input_tokens": 96,
            "input_tokens_details": {
              "cached_tokens": 0
            },
            "output_tokens": 52,
            "output_tokens_details": {
              "reasoning_tokens": 0
            },
            "total_tokens": 148
          },
          "user": "UnnamedAgent",
          "metadata": {}
        }
        """,
        """
                {
          "id": "resp_6846bee1abdc819f8c00a1be6b75b9930de9f0bbe6ed706c",
          "object": "response",
          "created_at": 1749466849,
          "status": "completed",
          "background": false,
          "error": null,
          "incomplete_details": null,
          "instructions": "Answer questions about the menu.\n",
          "max_output_tokens": null,
          "model": "gpt-4o-mini-2024-07-18",
          "output": [
            {
              "id": "msg_6846bee29858819f898d07fae89f686e0de9f0bbe6ed706c",
              "type": "message",
              "status": "completed",
              "content": [
                {
                  "type": "output_text",
                  "annotations": [],
                  "text": "The special soup is Clam Chowder, and it costs $9.99."
                }
              ],
              "role": "assistant"
            }
          ],
          "parallel_tool_calls": true,
          "previous_response_id": "resp_6846bee002d0819f9c3c95e51652c3f80de9f0bbe6ed706c",
          "reasoning": {
            "effort": null,
            "summary": null
          },
          "service_tier": "default",
          "store": true,
          "temperature": 1.0,
          "text": {
            "format": {
              "type": "text"
            }
          },
          "tool_choice": "auto",
          "tools": [
            {
              "type": "function",
              "description": "Provides a list of specials from the menu.",
              "name": "MenuPlugin-GetSpecials",
              "parameters": {
                "type": "object",
                "properties": {}
              },
              "strict": false
            },
            {
              "type": "function",
              "description": "Provides the price of the requested menu item.",
              "name": "MenuPlugin-GetItemPrice",
              "parameters": {
                "type": "object",
                "required": [
                  "menuItem"
                ],
                "properties": {
                  "menuItem": {
                    "description": "The name of the menu item.",
                    "type": "string"
                  }
                }
              },
              "strict": false
            }
          ],
          "top_p": 1.0,
          "truncation": "disabled",
          "usage": {
            "input_tokens": 176,
            "input_tokens_details": {
              "cached_tokens": 0
            },
            "output_tokens": 19,
            "output_tokens_details": {
              "reasoning_tokens": 0
            },
            "total_tokens": 195
          },
          "user": "UnnamedAgent",
          "metadata": {}
        }
        """
    ];

    private sealed class MyPlugin
    {
        [KernelFunction]
        public void MyFunction1()
        { }

        [KernelFunction]
        public void MyFunction2(int index)
        { }

        [KernelFunction]
        public void MyFunction3(string value, int[] indices)
        { }
    }

    private sealed class MenuPlugin
    {
        [KernelFunction, Description("Provides a list of specials from the menu.")]
        [System.Diagnostics.CodeAnalysis.SuppressMessage("Design", "CA1024:Use properties where appropriate", Justification = "Too smart")]
        public string GetSpecials()
        {
            return @"
Special Soup: Clam Chowder
Special Salad: Cobb Salad
Special Drink: Chai Tea
";
        }

        [KernelFunction, Description("Provides the price of the requested menu item.")]
        public string GetItemPrice(
            [Description("The name of the menu item.")]
            string menuItem)
        {
            return "$9.99";
        }
    }
    #endregion
}

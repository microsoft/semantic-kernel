// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Connectors.Amazon.Core.Requests;

namespace Connectors.Amazon.Models.Meta;

/// <summary>
/// Meta Llama chat completion request body.
/// </summary>
public class LlamaChatRequest : IChatCompletionRequest
{
    /// <summary>
    /// (Required) The prompt that you want to pass to the model.
    /// </summary>
    public string? Prompt { get; set; }
    /// <summary>
    /// Use a lower value to decrease randomness in the response.
    /// </summary>
    public double Temperature { get; set; }
    /// <summary>
    /// Use a lower value to ignore less probable options. Set to 0 or 1.0 to disable.
    /// </summary>
    public double TopP { get; set; }
    /// <summary>
    /// Specify the maximum number of tokens to use in the generated response. The model truncates the response once the generated text exceeds max_gen_len.
    /// </summary>
    public int MaxGenLen { get; set; }
    private List<Message>? _messages;

    /// <summary>
    /// List of messages.
    /// </summary>
    public List<Message> Messages
    {
        get
        {
            if (this._messages == null)
            {
                this._messages = new List<Message>();
                if (!string.IsNullOrEmpty(this.Prompt))
                {
                    var role = ConversationRole.User;
                    string systemPrompt = null;
                    if (this.Prompt.StartsWith("<s>[INST]"))
                    {
                        var parts = this.Prompt.Split("[/INST]", StringSplitOptions.RemoveEmptyEntries);
                        if (parts.Length > 0)
                        {
                            systemPrompt = parts[0].Trim('<', 's', '[', 'I', 'N', 'S', 'T', ']', ' ');
                            this.Prompt = string.Join("[/INST]", parts.Skip(1));
                        }
                    }

                    this._messages.Add(new Message
                    {
                        Role = role,
                        Content = new List<ContentBlock> { new() { Text = this.Prompt } }
                    });
                    if (!string.IsNullOrEmpty(systemPrompt))
                    {
                        this.System = new List<SystemContentBlock> { new() { Text = systemPrompt } };
                    }
                }
            }

            return this._messages;
        }
        set
        {
            this._messages = value;
        }
    }

    /// <inheritdoc />
    public List<SystemContentBlock>? System { get; set; }
    /// <inheritdoc />
    public InferenceConfiguration? InferenceConfig { get; set; }
    /// <inheritdoc />
    public Document AdditionalModelRequestFields { get; set; }
    /// <inheritdoc />
    public List<string>? AdditionalModelResponseFieldPaths { get; set; }
    /// <inheritdoc />
    public GuardrailConfiguration? GuardrailConfig { get; set; }
    /// <inheritdoc />
    public string? ModelId { get; set; }
    /// <inheritdoc />
    public ToolConfiguration? ToolConfig { get; set; }
}

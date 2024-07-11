// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Connectors.Amazon.Core.Requests;

namespace Connectors.Amazon.Models.Meta;

public class LlamaRequest : IChatCompletionRequest
{
    public string Prompt { get; set; }
    public double Temperature { get; set; }
    public double TopP { get; set; }
    public int MaxGenLen { get; set; }
    private List<Message> _messages;
    public List<Message> Messages
    {
        get
        {
            if (_messages == null)
            {
                _messages = new List<Message>();
                if (!string.IsNullOrEmpty(Prompt))
                {
                    var role = ConversationRole.User;
                    string systemPrompt = null;
                    if (Prompt.StartsWith("<s>[INST]"))
                    {
                        var parts = Prompt.Split("[/INST]", StringSplitOptions.RemoveEmptyEntries);
                        if (parts.Length > 0)
                        {
                            systemPrompt = parts[0].Trim('<', 's', '[', 'I', 'N', 'S', 'T', ']', ' ');
                            Prompt = string.Join("[/INST]", parts.Skip(1));
                        }
                    }

                    _messages.Add(new Message
                    {
                        Role = role,
                        Content = new List<ContentBlock> { new ContentBlock { Text = Prompt } }
                    });
                    if (!string.IsNullOrEmpty(systemPrompt))
                    {
                        System = new List<SystemContentBlock> { new SystemContentBlock { Text = systemPrompt } };
                    }
                }
            }

            return _messages;
        }
        set
        {
            _messages = value;
        }
    }

    public List<SystemContentBlock> System { get; set; }
    public InferenceConfiguration InferenceConfig { get; set; }
    public Document AdditionalModelRequestFields { get; set; }
    public List<string> AdditionalModelResponseFieldPaths { get; set; }
    public GuardrailConfiguration GuardrailConfig { get; set; }
    public string ModelId { get; set; }
    public ToolConfiguration ToolConfig { get; set; }
}

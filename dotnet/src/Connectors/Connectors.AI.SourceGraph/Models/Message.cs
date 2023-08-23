// ReSharper disable CheckNamespace
namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph;

using SemanticKernel.AI.ChatCompletion;


internal partial class Message : ChatMessageBase
{
    public Message(SpeakerType speakerType, string content) : this(speakerType == SpeakerType.Human ? AuthorRole.Assistant : AuthorRole.User, content)
    {
    }


    /// <inheritdoc />
    public Message(AuthorRole role, string content) : base(role, content)
    {
        Speaker = role == AuthorRole.Assistant ? SpeakerType.Assistant : SpeakerType.Human;
        Text = content;
    }


    public static Message FromChatMessageBase(ChatMessageBase message)
    {
        return new Message(message.Role, message.Content);
    }
}

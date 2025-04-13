//// Copyright (c) Microsoft. All rights reserved.

//using System.Diagnostics;
//using System.Threading.Tasks;
//using Microsoft.AgentRuntime;
//using Microsoft.SemanticKernel.ChatCompletion;

//namespace Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;

///// <summary>
///// A <see cref="RuntimeAgent"/> that orchestrates a team of agents.
///// </summary>
//public abstract class ChatManager : RuntimeAgent
//{
//    /// <summary>
//    /// A common description for the orchestrator.
//    /// </summary>
//    public const string Description = "Orchestrates a team of agents to accomplish a defined task.";
//    private readonly TaskCompletionSource<ChatMessageContent> _completionSource;

//    /// <summary>
//    /// Initializes a new instance of the <see cref="ChatManager"/> class.
//    /// </summary>
//    /// <param name="id">The unique identifier of the agent.</param>
//    /// <param name="runtime">The runtime associated with the agent.</param>
//    /// <param name="team">The team of agents being orchestrated</param>
//    /// <param name="completionSource">Signals completion.</param>
//    protected ChatManager(AgentId id, IAgentRuntime runtime, ChatTeam team, TaskCompletionSource<ChatMessageContent> completionSource)
//        : base(id, runtime, Description)
//    {
//        this.Chat = [];
//        this.Team = team;
//        this._completionSource = completionSource;
//        Debug.WriteLine($">>> NAMES: {this.Team.FormatNames()}");
//        Debug.WriteLine($">>> TEAM:\n{this.Team.FormatList()}");

//        this.RegisterHandler<ChatMessages.InputTask>(this.OnTaskMessageAsync);
//        this.RegisterHandler<ChatMessages.Group>(this.OnGroupMessageAsync);
//        this.RegisterHandler<ChatMessages.Result>(this.OnResultMessageAsync);
//    }

//    /// <summary>
//    /// The conversation history with the team.
//    /// </summary>
//    protected ChatHistory Chat { get; }

//    /// <summary>
//    /// The input task.
//    /// </summary>
//    protected ChatMessages.InputTask Task { get; private set; } = ChatMessages.InputTask.None; // %%% TYPE CONFLICT IN NAME

//    /// <summary>
//    /// Metadata that describes team of agents being orchestrated.
//    /// </summary>
//    protected ChatTeam Team { get; }

//    /// <summary>
//    /// Message a specific agent, by topic.
//    /// </summary>
//    protected Task RequestAgentResponseAsync(TopicId agentTopic)
//    {
//        return this.PublishMessageAsync(new ChatMessages.Speak(), agentTopic);
//    }

//    /// <summary>
//    /// Defines one-time logic required to prepare to execute the given task.
//    /// </summary>
//    /// <returns>
//    /// The agent specific topic for first step in executing the task.
//    /// </returns>
//    /// <remarks>
//    /// Returning a null TopicId indicates that the task will not be executed.
//    /// </remarks>
//    protected abstract Task<TopicId?> PrepareTaskAsync();

//    ///// <summary>
//    ///// %%% TODO
//    ///// </summary>
//    // %%% TODO protected abstract Task<TopicId?> RequestResultAsync();

//    /// <summary>
//    /// Determines which agent's must respond.
//    /// </summary>
//    /// <returns>
//    /// The agent specific topic for first step in executing the task.
//    /// </returns>
//    /// <remarks>
//    /// Returning a null TopicId indicates that the task will not be executed.
//    /// </remarks>
//    protected abstract Task<TopicId?> SelectAgentAsync();

//    private async ValueTask OnTaskMessageAsync(ChatMessages.InputTask message, MessageContext context)
//    {
//        Debug.WriteLine($">>> TASK: {message.Message}");
//        this.Task = message;
//        TopicId? agentTopic = await this.PrepareTaskAsync().ConfigureAwait(false);
//        if (agentTopic != null)
//        {
//            await this.RequestAgentResponseAsync(agentTopic.Value).ConfigureAwait(false);
//        }
//    }

//    private async ValueTask OnGroupMessageAsync(ChatMessages.Group message, MessageContext context)
//    {
//        Debug.WriteLine($">>> CHAT: {message.Message}");
//        this.Chat.Add(message.Message);
//        TopicId? agentTopic = await this.SelectAgentAsync().ConfigureAwait(false);
//        if (agentTopic != null)
//        {
//            await this.RequestAgentResponseAsync(agentTopic.Value).ConfigureAwait(false);
//        }
//        else
//        {
//            //await this.RequestResultAsync().ConfigureAwait(false); // %%% TODO - GROUP CHAT
//        }
//    }

//    private ValueTask OnResultMessageAsync(ChatMessages.Result result, MessageContext context)
//    {
//        Debug.WriteLine($">>> RESULT: {result.Message}");
//        this._completionSource.SetResult(result.Message);
//        return ValueTask.CompletedTask;
//    }
//}

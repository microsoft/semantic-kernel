//// Copyright (c) Microsoft. All rights reserved.

//using System.Threading.Tasks;
//using Microsoft.AgentRuntime;
//using Microsoft.SemanticKernel.Agents.Orchestration.Extensions;

//namespace Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;

///// <summary>
///// An orchestration that coordinates a multi-agent conversation.
///// </summary>
//public sealed class GroupChatOrchestration : AgentOrchestration
//{
//    private readonly TaskCompletionSource<ChatMessageContent> _completionSource;
//    private readonly Agent[] _agents;

//    /// <summary>
//    /// Initializes a new instance of the <see cref="GroupChatOrchestration"/> class.
//    /// </summary>
//    /// <param name="runtime">The runtime associated with the orchestration.</param>
//    /// <param name="agents">The agents participating in the orchestration.</param>
//    public GroupChatOrchestration(IAgentRuntime runtime, params Agent[] agents)
//        : base(runtime)
//    {
//        Verify.NotNullOrEmpty(agents, nameof(agents));

//        this._completionSource = new TaskCompletionSource<ChatMessageContent>();
//        this._agents = agents;
//    }

//    /// <summary>
//    /// %%% COMMENT
//    /// </summary>
//    public Task<ChatMessageContent> Future => this._completionSource.Task;

//    /// <inheritdoc />
//    protected override async ValueTask MessageTaskAsync(ChatMessageContent message)
//    {
//        AgentType managerType = new($"{nameof(GroupChatManager)}_{this.Id}"); // %%% COMMON
//        await this.Runtime.SendMessageAsync(message.ToTask(), managerType).ConfigureAwait(false);
//    }

//    /// <inheritdoc />
//    protected override async ValueTask PrepareAsync()
//    {
//        AgentType managerType = new($"{nameof(GroupChatManager)}_{this.Id}"); // %%% COMMON
//        TopicId chatTopic = new($"GroupChatTopic_{this.Id}"); // %%% OTHER TOPICS: RESET ???

//        ChatTeam team = [];
//        foreach (Agent agent in this._agents)
//        {
//            AgentType agentType = agent.GetAgentType(this);
//            await this.Runtime.RegisterAgentFactoryAsync(
//                agentType,
//                (agentId, runtime) => ValueTask.FromResult<IHostableAgent>(new GroupChatActor(agentId, runtime, agent, chatTopic))).ConfigureAwait(false);
//            TopicId agentTopic = new($"AgentTopic_{agent.Id}_{this.Id}".Replace("-", "_")); // %%% EXTENSION ???
//            team[agent.Name ?? agent.Id] = (agentTopic, agent.Description);

//            await this.RegisterTopicsAsync(agentType, chatTopic).ConfigureAwait(false);
//            await this.RegisterTopicsAsync(agentType, agentTopic).ConfigureAwait(false);
//        }

//        await this.Runtime.RegisterAgentFactoryAsync(
//            managerType,
//            (agentId, runtime) => ValueTask.FromResult<IHostableAgent>(new GroupChatManager(agentId, runtime, team, this._completionSource))).ConfigureAwait(false);

//        await this.RegisterTopicsAsync(managerType, chatTopic).ConfigureAwait(false);
//    }
//}

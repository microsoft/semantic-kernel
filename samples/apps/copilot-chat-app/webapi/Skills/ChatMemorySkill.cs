using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.CoreSkills;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using SKWebApi.Skills;

namespace SemanticKernel.Service.Skills;

/// <summary>
/// ChatMemorySkill provides functions to store and retrieve chat information in memory,
/// as well as functions to extract memories from context.
/// </summary>
public class ChatMemorySkill
{
    private readonly string ChatCollectionName = "chats";
    private readonly string UserCollectionName = "users";
    private readonly string MessageCollectionName = "messages";

    /// <summary>
    /// TODO:
    /// </summary>
    private readonly IKernel _kernel;

    public ChatMemorySkill(IKernel kernel)
    {
        this._kernel = kernel;
    }

    /// <summary>
    /// Create a new chat session in memory.
    /// </summary>
    /// <param name="context">Contains 'chatId' and 'title'.</param>
    [SKFunction("Create a new chat session in memory.")]
    [SKFunctionName("CreateChat")]
    [SKFunctionContextParameter(Name = "chatId", Description = "Unique and persistent identifier for the chat session.")]
    [SKFunctionContextParameter(Name = "title", Description = "The title of the chat.")]
    public async Task CreateChatAsync(SKContext context)
    {
        if (!(await this.DoesChatExistAsync(context["chatId"], context)))
        {
            context.Fail($"Chat {context["chatId"]} already exists.");
            return;
        }

        var newChat = new Chat(context["chatId"], context["title"]);

        await context.Memory.SaveInformationAsync(
            collection: ChatCollectionName,
            text: newChat.ToString(),
            id: newChat.Id,
            cancel: context.CancellationToken
        );
    }

    /// <summary>
    /// Create a new user in memory.
    /// </summary>
    /// <param name="context">Contains 'userId', 'name', and 'email'.</param>
    [SKFunction("Create a new user in memory.")]
    [SKFunctionName("CreateUser")]
    [SKFunctionContextParameter(Name = "userId", Description = "Unique and persistent identifier for the user.")]
    [SKFunctionContextParameter(Name = "name", Description = "Name of the user.")]
    [SKFunctionContextParameter(Name = "email", Description = "Email of the user.", DefaultValue = "N/A")]
    public async Task CreateUserAsync(SKContext context)
    {
        if (!(await this.DoesUserExistAsync(context["userId"], context)))
        {
            context.Fail($"User {context["userId"]} already exists.");
            return;
        }

        var newChatUser = new ChatUser(context["userId"], context["name"], context["email"]);

        await context.Memory.SaveInformationAsync(
            collection: UserCollectionName,
            text: newChatUser.ToString(),
            id: newChatUser.Id,
            cancel: context.CancellationToken
        );
    }

    /// <summary>
    /// Add a user to an existing chat session.
    /// </summary>
    /// <param name="context">Contains 'userId' and 'chatId'.</param>
    [SKFunction("Add a user to an existing chat session.")]
    [SKFunctionName("CreateUser")]
    [SKFunctionContextParameter(Name = "userId", Description = "Unique and persistent identifier for a user.")]
    [SKFunctionContextParameter(Name = "chatId", Description = "Unique and persistent identifier for a chat session.")]
    public async Task AddUserToChatAsync(SKContext context)
    {
        if (!(await this.DoesChatExistAsync(context["chatId"], context)))
        {
            context.Fail($"User {context["userId"]} doesn't exists.");
            return;
        }

        var chatUser = await this.GetChatUserAsync(context["userId"], context);
        if (chatUser == null)
        {
            context.Fail($"Error retrieving user {context["userId"]} info. Please see log for more details.");
            return;
        }
        chatUser.AddChat(context["chatId"]);

        await context.Memory.SaveInformationAsync(
            collection: UserCollectionName,
            text: chatUser.ToString(),
            id: chatUser.Id,
            cancel: context.CancellationToken
        );
    }

    /// <summary>
    /// Edit a chat session in memory.
    /// </summary>
    /// <param name="context">Contains 'chatId' and 'title'.</param>
    [SKFunction("Edit a chat session in memory.")]
    [SKFunctionName("EditChat")]
    [SKFunctionContextParameter(Name = "chatId", Description = "Unique and persistent identifier for a chat session.")]
    [SKFunctionContextParameter(Name = "title", Description = "The title of the chat.")]
    public async Task EditChatAsync(SKContext context)
    {
        var chat = await this.GetChatAsync(context["chatId"], context);
        if (chat == null)
        {
            context.Fail($"Error retrieving chat {context["chatId"]} info. Please see log for more details.");
            return;
        }
        chat.Title = context["title"];

        await context.Memory.SaveInformationAsync(
            collection: ChatCollectionName,
            text: chat.ToString(),
            id: chat.Id,
            cancel: context.CancellationToken
        );
    }

    /// <summary>
    /// Edit a user in memory.
    /// </summary>
    /// <param name="context">Contains 'userId', 'name', and 'email'.</param>
    [SKFunction("Edit a user in memory.")]
    [SKFunctionName("EditUser")]
    [SKFunctionContextParameter(Name = "userId", Description = "Unique and persistent identifier for the user.")]
    [SKFunctionContextParameter(Name = "name", Description = "Name of the user.")]
    [SKFunctionContextParameter(Name = "email", Description = "Email of the user.", DefaultValue = "N/A")]
    public async Task EditUserAsync(SKContext context)
    {
        var chatUser = await this.GetChatUserAsync(context["userId"], context);
        if (chatUser == null)
        {
            context.Fail($"Error retrieving user {context["userId"]} info. Please see log for more details.");
            return;
        }
        chatUser.FullName = context["name"];
        chatUser.Email = context["email"];

        await context.Memory.SaveInformationAsync(
            collection: UserCollectionName,
            text: chatUser.ToString(),
            id: chatUser.Id,
            cancel: context.CancellationToken
        );
    }

    /// <summary>
    /// Save a new message to the chat history.
    /// </summary>
    /// <param name="message">The message</param>
    /// <param name="context">Contains the 'userId' and 'chatId'.</param>
    [SKFunction("Save a new message to the chat history")]
    [SKFunctionName("SaveNewMessage")]
    [SKFunctionInput(Description = "The new message")]
    [SKFunctionContextParameter(Name = "userId", Description = "Unique and persistent identifier for a user.")]
    [SKFunctionContextParameter(Name = "chatId", Description = "Unique and persistent identifier for a chat session.")]
    public async Task SaveNewMessageAsync(string message, SKContext context)
    {
        var chatUser = await this.GetChatUserAsync(context["userId"], context);
        if (chatUser == null)
        {
            context.Fail($"Error retrieving user {context["userId"]} info. Please see log for more details.");
            return;
        }

        var chat = await this.GetChatAsync(context["chatId"], context);
        if (chat == null)
        {
            context.Fail($"Error retrieving chat {context["chatId"]} info. Please see log for more details.");
            return;
        }

        var timeSkill = new TimeSkill();
        var currentTime = $"{timeSkill.Now()} {timeSkill.Second()}";
        var chatMessage = new ChatMessage(currentTime, chatUser.Id, message);

        await context.Memory.SaveInformationAsync(
            collection: MessageCollectionName,
            text: chatMessage.ToString(),
            id: chatMessage.Id,
            cancel: context.CancellationToken
        );

        // Associate the message with the chat session.
        chat.AddMessage(chatMessage.Id);
        await context.Memory.SaveInformationAsync(
            collection: ChatCollectionName,
            text: chat.ToString(),
            id: chat.Id,
            cancel: context.CancellationToken
        );
    }

    /// <summary>
    /// Get IDs of all chat sessions associated with a user.
    /// </summary>
    /// <param name="userId">The user ID</param>
    /// <param name="context">Contains the 'userId' and 'chatId'.</param>
    [SKFunction("Get IDs all chat sessions associated with a user.")]
    [SKFunctionName("GetAllChatIds")]
    [SKFunctionInput(Description = "The user id")]
    public async Task<SKContext> GetAllChatIdsAsync(string userId, SKContext context)
    {
        var chatUser = await this.GetChatUserAsync(userId, context);
        if (chatUser == null)
        {
            context.Fail($"Error retrieving user {userId} info. Please see log for more details.");
            return context;
        }

        context.Variables.Update(string.Join(",", chatUser.ChatIds));
        return context;
    }

    /// <summary>
    /// Get IDs of all message in a chat session.
    /// </summary>
    /// <param name="chatId">The chat ID</param>
    /// <param name="context"></param>
    [SKFunction("Get IDs all message in a chat session.")]
    [SKFunctionName("GetAllChatMessageIds")]
    [SKFunctionInput(Description = "The chat id")]
    public async Task<SKContext> GetAllChatMessageIdsAsync(string chatId, SKContext context)
    {
        var chat = await this.GetChatAsync(chatId, context);
        if (chat == null)
        {
            context.Fail($"Error retrieving chat {chatId} info. Please see log for more details.");
            return context;
        }

        context.Variables.Update(string.Join(",", chat.MessageIds));
        return context;
    }

    /// <summary>
    /// Get a chat message by ID.
    /// </summary>
    /// <param name="messageId">The message ID</param>
    /// <param name="context"></param>
    [SKFunction("Get a chat message by ID.")]
    [SKFunctionName("GetMessageById")]
    [SKFunctionInput(Description = "The message id")]
    public async Task<SKContext> GetMessageByIdAsync(string messageId, SKContext context)
    {
        var messageMemory = await context.Memory.GetAsync(MessageCollectionName, messageId);
        if (messageMemory == null)
        {
            context.Log.LogError($"Message {messageId} doesn't exists.");
            context.Fail($"Message {messageId} doesn't exists.");
            return context;
        }

        try
        {
            var message = ChatMessage.FromMemoryRecordMetadata(messageMemory.Metadata);
            context.Variables.Update(message.ToJsonString());
        }
        catch (ArgumentException)
        {
            context.Log.LogError($"Message {messageId} is corrupted: {messageMemory.Metadata.Text}.");
            context.Fail($"Message {messageId} is corrupted: {messageMemory.Metadata.Text}.");
        }

        return context;
    }

    /// <summary>
    /// Get all chat messages by chat ID.
    /// </summary>
    /// <param name="chatId">The chat ID</param>
    /// <param name="context"></param>
    [SKFunction("Get all chat messages by chat ID.")]
    [SKFunctionName("GetAllChatMessages")]
    [SKFunctionInput(Description = "The chat id")]
    public async Task<SKContext> GetAllChatMessagesAsync(string chatId, SKContext context)
    {
        var messageIdsContext = await this.GetAllChatMessageIdsAsync(chatId, context);
        var messageIds = messageIdsContext.Variables.ToString().Split(',');

        var messages = new List<ChatMessage>();
        foreach (var messageId in messageIds)
        {
            var messageContext = await this.GetMessageByIdAsync(messageId, context);
            var message = ChatMessage.FromJsonString(messageContext.Variables.ToString());
            if (message != null)
            {
                messages.Add(message);
            }
            else
            {
                context.Log.LogError($"Message {messageId} is corrupted.");
                context.Fail($"Message {messageId} is corrupted.");
                return context;
            }
        }

        context.Variables.Update(JsonSerializer.Serialize(messages));
        return context;
    }

    /// <summary>
    /// Get the latest chat messages by chat ID.
    /// </summary>
    /// <param name="chatId">The chat ID</param>
    /// <param name="context"></param>
    [SKFunction("Get the latest chat message by chat ID.")]
    [SKFunctionName("GetLatestChatMessage")]
    [SKFunctionInput(Description = "The chat id")]
    public async Task<SKContext> GetLatestChatMessageAsync(string chatId, SKContext context)
    {
        var allMessagesContext = await this.GetAllChatMessagesAsync(chatId, context);
        var allMessages = JsonSerializer.Deserialize<List<ChatMessage>>(allMessagesContext.Variables.ToString());
        if (allMessages == null)
        {
            context.Log.LogError($"Chat {chatId} doesn't have any messages.");
            context.Fail($"Chat {chatId} doesn't have any messages.");
            return context;
        }
        var latestMessage = allMessages.OrderByDescending(m => m.Timestamp).First();
        context.Variables.Update(latestMessage.ToJsonString());

        return context;
    }

    /// <summary>
    /// Check if a chat session exists.
    /// </summary>
    /// <param name="chatId">The Id of the chat</param>
    /// <param name="context">The context containing the memory</param>
    /// <returns>true if exists otherwise false</returns>
    private Task<bool> DoesChatExistAsync(string chatId, SKContext context)
    {
        return Task.FromResult(context.Memory.GetAsync(ChatCollectionName, chatId) != null);
    }

    /// <summary>
    /// Check if a user exists.
    /// </summary>
    /// <param name="userId">The Id of the user</param>
    /// <param name="context">The context containing the memory</param>
    /// <returns>true if exists otherwise false</returns>
    private Task<bool> DoesUserExistAsync(string userId, SKContext context)
    {
        return Task.FromResult(context.Memory.GetAsync(UserCollectionName, userId) != null);
    }

    /// <summary>
    /// Get a chat session by ID.
    /// </summary>
    /// <param name="chatId">The chat id</param>
    /// <param name="context">The context containing the memory</param>
    /// <returns>A chat object</returns>
    private async Task<Chat?> GetChatAsync(string chatId, SKContext context)
    {
        var chatMemory = await context.Memory.GetAsync(ChatCollectionName, chatId);
        if (chatMemory == null)
        {
            context.Log.LogError($"Chat {chatId} doesn't exists.");
            return null;
        }
        var chat = Chat.FromString(chatMemory.Metadata.Text);
        if (chat == null)
        {
            context.Log.LogError($"Chat {chatId} is corrupted: {chatMemory.Metadata.Text}.");
            return null;
        }

        return chat;
    }

    /// <summary>
    /// Get a chat user by ID.
    /// </summary>
    /// <param name="userId">The user id</param>
    /// <param name="context">The context containing the memory</param>
    /// <returns>A chat user object</returns>
    private async Task<ChatUser?> GetChatUserAsync(string userId, SKContext context)
    {
        var chatUserMemory = await context.Memory.GetAsync(ChatCollectionName, userId);
        if (chatUserMemory == null)
        {
            context.Log.LogError($"Chat user {userId} doesn't exists.");
            return null;
        }
        var chatUser = ChatUser.FromString(chatUserMemory.Metadata.Text);
        if (chatUser == null)
        {
            context.Log.LogError($"Chat user {userId} is corrupted: {chatUserMemory.Metadata.Text}.");
            return null;
        }

        return chatUser;
    }
}
using System.Globalization;
using System.Text.Json;
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
    /// <summary>
    /// Name of the collection that stores chat session information.
    /// </summary>
    public const string ChatCollectionName = "chats";
    /// <summary>
    /// Name of the collection that stores user information.
    /// </summary>
    public const string UserCollectionName = "users";
    /// <summary>
    /// Returns the name of the collection that stores chat message information.
    /// </summary>
    /// <param name="chatId">Chat ID that is persistent and unique for the chat session.</param>
    public static string MessageCollectionName(string chatId) => $"{chatId}-messages";
    /// <summary>
    /// Returns the name of the collection that stores chat bot information.
    /// </summary>
    /// <param name="chatId">Chat ID that is persistent and unique for the chat session.</param>
    public static string ChatBotID(string chatId) => $"{chatId}-bot";

    /// <summary>
    /// Create a new chat session in memory.
    /// </summary>
    /// <param name="title">The title of the chat.</param>
    /// <param name="context">Contains the memory</param>
    /// <returns>An unique chat ID.</returns>
    [SKFunction("Create a new chat session in memory.")]
    [SKFunctionName("CreateChat")]
    [SKFunctionInput(Description = "The title of the chat.")]
    public async Task<SKContext> CreateChatAsync(string title, SKContext context)
    {
        var chatId = Guid.NewGuid().ToString();
        while (await this.DoesChatExistAsync(chatId, context) == "true")
        {
            context.Log.LogDebug("Chat {0} already exists. Regenerating a new chat ID.", chatId);
            chatId = Guid.NewGuid().ToString();
        }

        // Create a new chat bot for this chat.
        // Clone the context to avoid modifying the original context variables.
        var newBotContext = Utils.CopyContextWithVariablesClone(context);
        newBotContext.Variables.Set("name", "Bot");
        newBotContext.Variables.Set("email", "N/A");

        await this.CreateUserAsync(ChatBotID(chatId), newBotContext);
        if (newBotContext.ErrorOccurred)
        {
            context.Log.LogError("Failed to create a new chat bot for chat {0}.", chatId);
            context.Fail(newBotContext.LastErrorDescription, newBotContext.LastException);
            return context;
        }

        var newChat = new Chat(chatId, title);
        await context.Memory.SaveInformationAsync(
            collection: ChatCollectionName,
            text: newChat.ToString(),
            id: newChat.Id,
            cancel: context.CancellationToken
        );

        context.Variables.Update(chatId);
        return context;
    }

    /// <summary>
    /// Create a new user in memory.
    /// </summary>
    /// <param name="userId">User ID that is persistent and unique.</param>
    /// <param name="context">Contains 'userId', 'name', and 'email'.</param>
    [SKFunction("Create a new user in memory.")]
    [SKFunctionName("CreateUser")]
    [SKFunctionInput(Description = "User ID that is persistent and unique.")]
    [SKFunctionContextParameter(Name = "name", Description = "Name of the user.")]
    [SKFunctionContextParameter(Name = "email", Description = "Email of the user.", DefaultValue = "N/A")]
    public async Task CreateUserAsync(string userId, SKContext context)
    {
        if (await this.DoesUserExistAsync(userId, context) == "true")
        {
            context.Fail($"User {userId} already exists.");
            return;
        }

        var newChatUser = new ChatUser(userId, context["name"], context["email"]);

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
    [SKFunctionName("AddUserToChat")]
    [SKFunctionContextParameter(Name = "userId", Description = "Unique and persistent identifier for a user.")]
    [SKFunctionContextParameter(Name = "chatId", Description = "Unique and persistent identifier for a chat session.")]
    public async Task AddUserToChatAsync(SKContext context)
    {
        if (await this.DoesChatExistAsync(context["chatId"], context) == "false")
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

        var chatMessage = new ChatMessage(chatUser.FullName, message);
        await context.Memory.SaveInformationAsync(
            collection: MessageCollectionName(context["chatId"]),
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
    /// <returns>A serialized Json string of a hash set of strings representing the IDs.</returns>
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

        var test = await context.Memory.GetAsync(ChatCollectionName, chat.Id);

        context.Variables.Update(JsonSerializer.Serialize<HashSet<string>>(chat.MessageIds));
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
    [SKFunctionContextParameter(Name = "chatId", Description = "Unique and persistent identifier for a chat session.")]
    public async Task<SKContext> GetMessageByIdAsync(string messageId, SKContext context)
    {
        var messageMemory = await context.Memory.GetAsync(MessageCollectionName(context["chatId"]), messageId);
        if (messageMemory == null)
        {
            context.Log.LogError("Message {0} doesn't exists.", messageId);
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
            context.Log.LogError("Message {0} is corrupted: {1}.", messageId, messageMemory.Metadata.Text);
            context.Fail($"Message {messageId} is corrupted: {messageMemory.Metadata.Text}.");
        }

        return context;
    }

    /// <summary>
    /// Get all chat messages by chat ID The list will be ordered with the first entry being the most recent message.
    /// </summary>
    /// <param name="chatId">The chat ID</param>
    /// <param name="context"></param>
    [SKFunction("Get all chat messages by chat ID.")]
    [SKFunctionName("GetAllChatMessages")]
    [SKFunctionInput(Description = "The chat id")]
    [SKFunctionContextParameter(Name = "startIdx",
        Description = "The index of the first message to return. Lower values are more recent messages.",
        DefaultValue = "0")]
    [SKFunctionContextParameter(Name = "count",
        Description = "The number of messages to return. -1 will return all messages starting from startIdx.",
        DefaultValue = "-1")]
    public async Task<SKContext> GetChatMessagesAsync(string chatId, SKContext context)
    {
        var startIdx = 0;
        var count = -1;
        try
        {
            startIdx = Math.Max(startIdx, int.Parse(context["startIdx"], new NumberFormatInfo()));
            count = Math.Max(count, int.Parse(context["count"], new NumberFormatInfo()));
        }
        catch (FormatException)
        {
            context.Log.LogError("Unable to parse startIdx: {0} or count: {1}.", context["startIdx"], context["count"]);
            context.Fail($"Unable to parse startIdx: {context["startIdx"]} or count: {context["count"]}.");
            return context;
        }

        var messageIdsContext = await this.GetAllChatMessageIdsAsync(chatId, context);
        if (messageIdsContext.ErrorOccurred)
        {
            context.Log.LogError("Unable to retrieve message IDs for chat {0}.", chatId);
            context.Fail($"Unable to retrieve message IDs for chat {chatId}.");
            return context;
        }

        var messageIds = JsonSerializer.Deserialize<HashSet<string>>(messageIdsContext.Result);
        if (messageIds == null)
        {
            context.Log.LogError("Unable to deserialize message IDs for chat {0}.", chatId);
            context.Fail($"Unable to deserialize message IDs for chat {chatId}.");
            return context;
        }

        if (startIdx > messageIds.Count)
        {
            context.Variables.Update(JsonSerializer.Serialize<List<ChatMessage>>(new List<ChatMessage>()));
            return context;
        }
        else if (startIdx + count > messageIds.Count || count == -1)
        {
            count = messageIds.Count - startIdx;
        }

        // Clone the context to avoid modifying the original context variables.
        var chatIDContext = Utils.CopyContextWithVariablesClone(context);
        chatIDContext.Variables.Set("chatId", chatId);

        var messages = new List<ChatMessage>();
        foreach (var messageId in messageIds)
        {
            var messageContext = await this.GetMessageByIdAsync(messageId, chatIDContext);
            if (messageContext.ErrorOccurred)
            {
                context.Log.LogError("Unable to retrieve message {0}.", messageId);
                context.Fail($"Unable to retrieve message {messageId}.");
                return context;
            }
            var message = ChatMessage.FromJsonString(messageContext.Variables.ToString());
            if (message != null)
            {
                messages.Add(message);
            }
            else
            {
                context.Log.LogError("Message {0} is corrupted.", messageId);
                context.Fail($"Message {messageId} is corrupted.");
                return context;
            }
        }

        messages.Sort();
        messages = messages.GetRange(startIdx, count);
        context.Variables.Update(JsonSerializer.Serialize(messages));
        return context;
    }

    /// <summary>
    /// Check if a chat session exists.
    /// </summary>
    /// <param name="chatId">The Id of the chat</param>
    /// <param name="context">The context containing the memory</param>
    /// <returns>true if exists otherwise false</returns>
    [SKFunction("Check if a chat already exists in memory.")]
    [SKFunctionName("DoesChatExist")]
    [SKFunctionInput(Description = "Chat ID that is persistent and unique for the chat session.")]
    public async Task<string> DoesChatExistAsync(string chatId, SKContext context)
    {
        return await context.Memory.GetAsync(ChatCollectionName, chatId) != null ? "true" : "false";
    }

    /// <summary>
    /// Check if a user exists.
    /// </summary>
    /// <param name="userId">The Id of the user</param>
    /// <param name="context">The context containing the memory</param>
    /// <returns>true if exists otherwise false</returns>
    [SKFunction("Check if a user already exists in memory.")]
    [SKFunctionName("DoesUserExist")]
    [SKFunctionInput(Description = "User ID that is persistent and unique.")]
    public async Task<string> DoesUserExistAsync(string userId, SKContext context)
    {
        return await context.Memory.GetAsync(UserCollectionName, userId) != null ? "true" : "false";
    }

    /// <summary>
    /// Get a chat session by ID.
    /// </summary>
    /// <param name="chatId">The chat id</param>
    /// <param name="context">The context containing the memory</param>
    /// <returns>A chat object</returns>
    public async Task<Chat?> GetChatAsync(string chatId, SKContext context)
    {
        var chatMemory = await context.Memory.GetAsync(ChatCollectionName, chatId);
        if (chatMemory == null)
        {
            context.Log.LogError("Chat {0} doesn't exists.", chatId);
            return null;
        }
        var chat = Chat.FromString(chatMemory.Metadata.Text);
        if (chat == null)
        {
            context.Log.LogError("Chat {0} is corrupted: {1}.", chatId, chatMemory.Metadata.Text);
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
    public async Task<ChatUser?> GetChatUserAsync(string userId, SKContext context)
    {
        var chatUserMemory = await context.Memory.GetAsync(UserCollectionName, userId);
        if (chatUserMemory == null)
        {
            context.Log.LogError("Chat user {0} doesn't exists.", userId);
            return null;
        }
        var chatUser = ChatUser.FromString(chatUserMemory.Metadata.Text);
        if (chatUser == null)
        {
            context.Log.LogError("Chat user {0} is corrupted: {1}.", userId, chatUserMemory.Metadata.Text);
            return null;
        }

        return chatUser;
    }
}

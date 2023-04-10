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
    /// <returns>The initial chat message in a serialized Json string.</returns>
    [SKFunction("Create a new chat session in memory.")]
    [SKFunctionName("CreateChat")]
    [SKFunctionInput(Description = "The title of the chat.")]
    [SKFunctionContextParameter(Name = "userId", Description = "Unique and persistent identifier for a user.")]
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

        // Create a new chat.
        var newChat = new Chat(chatId, title);
        await context.Memory.SaveInformationAsync(
            collection: ChatCollectionName,
            text: newChat.ToString(),
            id: newChat.Id,
            cancel: context.CancellationToken
        );

        // Attach the chat to the user.
        // Clone the context to avoid modifying the original context variables.
        var addUserContext = Utils.CopyContextWithVariablesClone(context);
        addUserContext.Variables.Set("chatId", chatId);
        addUserContext.Variables.Set("userId", context["userId"]);
        await this.AddUserToChatAsync(addUserContext);
        if (addUserContext.ErrorOccurred)
        {
            context.Log.LogError("Failed to add user {0} to the new chat {1}.", context["userId"], chatId);
            context.Fail(addUserContext.LastErrorDescription, addUserContext.LastException);
            return context;
        }

        // Create the initial bot message.
        try
        {
            var initialBotMessage = await this.CreateAndSaveInitialBotMessage(chatId, context["userId"], context);
            // Update the context variables for outputs.
            context.Variables.Update(chatId);
            context.Variables.Set("initialBotMessage", initialBotMessage);
        }
        catch (Exception ex) when (ex is KeyNotFoundException || ex is ArgumentException)
        {
            context.Log.LogError("Failed to create the initial bot message for chat {0}.", chatId);
            context.Fail("Failed to create the initial bot message for chat.", ex);
            return context;
        }

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

        try
        {
            var chatUser = await this.GetChatUserAsync(context["userId"], context);
            chatUser.AddChat(context["chatId"]);

            await context.Memory.SaveInformationAsync(
                collection: UserCollectionName,
                text: chatUser.ToString(),
                id: chatUser.Id,
                cancel: context.CancellationToken
            );
        }
        catch (Exception ex) when (ex is KeyNotFoundException || ex is ArgumentException)
        {
            context.Fail($"Error retrieving user {context["userId"]} info. Please see log for more details.", ex);
            return;
        }
    }

    /// <summary>
    /// Edit a chat session in memory.
    /// </summary>
    /// <param name="chatId">Chat ID that is persistent and unique.</param>
    /// <param name="context">Contains 'chatId' and 'title'.</param>
    [SKFunction("Edit a chat session in memory.")]
    [SKFunctionName("EditChat")]
    [SKFunctionInput(Description = "Chat ID that is persistent and unique.")]
    [SKFunctionContextParameter(Name = "title", Description = "The title of the chat.")]
    public async Task EditChatAsync(string chatId, SKContext context)
    {
        try
        {
            var chat = await this.GetChatAsync(chatId, context);
            chat.Title = context["title"];

            await context.Memory.SaveInformationAsync(
                collection: ChatCollectionName,
                text: chat.ToString(),
                id: chat.Id,
                cancel: context.CancellationToken
            );
        }
        catch (Exception ex) when (ex is KeyNotFoundException || ex is ArgumentException)
        {
            context.Fail($"Error retrieving chat {chatId} info. Please see log for more details.", ex);
            return;
        }
    }

    /// <summary>
    /// Get all chat sessions associated with a user.
    /// </summary>
    /// <param name="userId">The user ID</param>
    /// <param name="context">Contains the memory.</param>
    /// <returns>The list of chat sessions as a Json string.</returns>
    [SKFunction("Get all chat sessions associated with a user.")]
    [SKFunctionName("GetAllChats")]
    [SKFunctionInput(Description = "The user id")]
    public async Task<SKContext> GetAllChatsAsync(string userId, SKContext context)
    {
        try
        {
            var chatUser = await this.GetChatUserAsync(userId, context);

            List<Chat> chats = new List<Chat>();
            foreach (var chatId in chatUser.ChatIds)
            {
                var chat = await this.GetChatAsync(chatId, context);
                if (chat == null)
                {
                    context.Fail($"Error retrieving chat {chatId} info. Please see log for more details.");
                    return context;
                }
                chats.Add(chat);
            }
            context.Variables.Update(JsonSerializer.Serialize(chats));
        }
        catch (Exception ex) when (ex is KeyNotFoundException || ex is ArgumentException)
        {
            context.Fail($"Error retrieving user {userId} info. Please see log for more details.", ex);
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

        HashSet<string> messageIds;
        try
        {
            messageIds = await this.GetAllChatMessageIdsAsync(chatId, context);
        }
        catch (KeyNotFoundException ex)
        {
            context.Log.LogError("Unable to retrieve message IDs for chat {0}: {1}.", chatId, ex.Message);
            context.Fail($"Unable to retrieve message IDs for chat {chatId}: {ex.Message}.");
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

        var messages = new List<ChatMessage>();
        foreach (var messageId in messageIds)
        {
            try
            {
                var message = await this.GetMessageByIdAsync(messageId, chatId, context);
                messages.Add(message);
            }
            catch (Exception ex) when (ex is KeyNotFoundException || ex is ArgumentException)
            {
                context.Log.LogError("Unable to retrieve message {0}: {1}.", messageId, ex.Message);
                context.Fail($"Unable to retrieve message {messageId}: {ex.Message}.");
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

    #region Internal
    /// <summary>
    /// Save a new message to the chat history.
    /// </summary>
    /// <param name="message">The message</param>
    /// <param name="userId">The user ID</param>
    /// <param name="chatId">The chat ID</param>
    /// <param name="context">Contains the memory</param>
    internal async Task SaveNewMessageAsync(string message, string userId, string chatId, SKContext context)
    {
        var chatUser = await this.GetChatUserAsync(userId, context);
        var chat = await this.GetChatAsync(chatId, context);
        var chatMessage = new ChatMessage(chatUser.FullName, message);

        await context.Memory.SaveInformationAsync(
            collection: MessageCollectionName(chatId),
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
    /// Get the latest chat message by chat ID.
    /// </summary>
    /// <param name="chatId">The chat ID</param>
    /// <param name="context">Context containing the memory.</param>
    /// <returns>The latest message as a ChatMessage object.</returns>
    internal async Task<ChatMessage> GetLatestChatMessageAsync(string chatId, SKContext context)
    {
        var chatMessagesContext = Utils.CopyContextWithVariablesClone(context);
        chatMessagesContext.Variables.Set("startIdx", "0");
        chatMessagesContext.Variables.Set("count", "1");

        chatMessagesContext = await this.GetChatMessagesAsync(chatId, chatMessagesContext);
        if (chatMessagesContext.ErrorOccurred)
        {
            throw new KeyNotFoundException("Failed to retrieve chat messages.");
        }

        var messages = JsonSerializer.Deserialize<List<ChatMessage>>(chatMessagesContext.Result);
        if (messages == null)
        {
            throw new ArgumentException("Failed to parse chat messages.");
        }
        else if (messages.Count == 0)
        {
            throw new ArgumentException("There are no messages in the chat.");
        }

        return messages.First();
    }

    /// <summary>
    /// Get a chat user by ID.
    /// </summary>
    /// <param name="userId">The user id</param>
    /// <param name="context">The context containing the memory</param>
    /// <returns>A chat user object</returns>
    internal async Task<ChatUser> GetChatUserAsync(string userId, SKContext context)
    {
        var chatUserMemory = await context.Memory.GetAsync(UserCollectionName, userId);
        if (chatUserMemory == null)
        {
            throw new KeyNotFoundException($"User {userId} doesn't exist.");
        }
        var chatUser = ChatUser.FromString(chatUserMemory.Metadata.Text);
        if (chatUser == null)
        {
            throw new ArgumentException($"Chat user {userId} is corrupted: {chatUserMemory.Metadata.Text}.");
        }

        return chatUser;
    }

    #endregion

    #region Private
    /// <summary>
    /// Get a chat message by ID.
    /// </summary>
    /// <param name="messageId">The message ID</param>
    /// <param name="chatId">The chat ID</param>
    /// <param name="context">Contains the memory</param>
    /// <returns>A chat message object</returns>
    public async Task<ChatMessage> GetMessageByIdAsync(string messageId, string chatId, SKContext context)
    {
        var messageMemory = await context.Memory.GetAsync(MessageCollectionName(chatId), messageId);
        if (messageMemory == null)
        {
            throw new KeyNotFoundException($"Message {messageId} doesn't exist.");
        }

        return ChatMessage.FromMemoryRecordMetadata(messageMemory.Metadata);
    }

    /// <summary>
    /// Get IDs of all message in a chat session.
    /// </summary>
    /// <param name="chatId">The chat ID</param>
    /// <param name="context"></param>
    /// <returns>A serialized Json string of a hash set of strings representing the IDs.</returns>
    private async Task<HashSet<string>> GetAllChatMessageIdsAsync(string chatId, SKContext context)
    {
        try
        {
            var chat = await this.GetChatAsync(chatId, context);
            return chat.MessageIds;
        }
        catch (Exception ex) when (ex is KeyNotFoundException || ex is ArgumentException)
        {
            throw new KeyNotFoundException($"Error retrieving chat {chatId} info.");
        }
    }

    /// <summary>
    /// Get a chat session by ID.
    /// </summary>
    /// <param name="chatId">The chat id</param>
    /// <param name="context">The context containing the memory</param>
    /// <returns>A chat object</returns>
    private async Task<Chat> GetChatAsync(string chatId, SKContext context)
    {
        var chatMemory = await context.Memory.GetAsync(ChatCollectionName, chatId);
        if (chatMemory == null)
        {
            throw new KeyNotFoundException($"Chat {chatId} doesn't exist.");
        }

        var chat = Chat.FromString(chatMemory.Metadata.Text);
        if (chat == null)
        {
            throw new ArgumentException($"Chat {chatId} is corrupted: {chatMemory.Metadata.Text}.");
        }

        return chat;
    }

    /// <summary>
    /// Create and save the initial bot message.
    /// </summary>
    /// <param name="chatId">Chat ID of the chat session.</param>
    /// <param name="userId">User ID to get the user name.</param>
    /// <param name="context">Context that contains the memory.</param>
    /// <returns></returns>
    private async Task<string> CreateAndSaveInitialBotMessage(string chatId, string userId, SKContext context)
    {
        var chatUser = await this.GetChatUserAsync(userId, context);
        var initialBotMessage = string.Format(SystemPromptDefaults.InitialBotMessage, chatUser.FullName);
        await this.SaveNewMessageAsync(initialBotMessage, ChatBotID(chatId), chatId, context);

        return initialBotMessage;
    }
    #endregion
}

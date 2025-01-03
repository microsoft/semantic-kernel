// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace FormFilling;

/// <summary>
/// Step that is helps the user fill up a new account form.<br/>
/// Also provides a welcome message for the user.
/// </summary>
public class CompleteNewCustomerFormStep : KernelProcessStep<NewCustomerFormState>
{
    public static class Functions
    {
        public const string NewAccountProcessUserInfo = nameof(NewAccountProcessUserInfo);
        public const string NewAccountWelcome = nameof(NewAccountWelcome);
    }

    public static class OutputEvents
    {
        public const string NewCustomerFormWelcomeMessageComplete = nameof(NewCustomerFormWelcomeMessageComplete);
        public const string NewCustomerFormCompleted = nameof(NewCustomerFormCompleted);
        public const string NewCustomerFormCompletedAssistantMessage = nameof(NewCustomerFormCompletedAssistantMessage);
        public const string CustomerInteractionTranscriptReady = nameof(CustomerInteractionTranscriptReady);
        public const string NewCustomerFormNeedsMoreDetails = nameof(NewCustomerFormNeedsMoreDetails);
    }

    internal NewCustomerFormState? _state;

    internal string _formCompletionSystemPrompt = """
        The goal is to fill up all the fields needed for a form.
        The user may provide information to fill up multiple fields of the form in one message.
        The user needs to fill up a form, all the fields of the form are necessary

        <CURRENT_FORM_STATE>
        {{current_form_state}}
        <CURRENT_FORM_STATE>

        GUIDANCE:
        - If there are missing details, give the user a useful message that will help fill up the remaining fields.
        - Your goal is to help guide the user to provide the missing details on the current form.
        - Encourage the user to provide the remainingdetails with examples if necessary.
        - Fields with value 'Unanswered' need to be answered by the user.
        - Format phone numbers and user ids correctly if the user does not provide the expected format.
        - If the user does not make use of parenthesis in the phone number, add them.
        - For date fields, confirm with the user first if the date format is not clear. Example 02/03 03/02 could be March 2nd or February 3rd.
        """;

    internal string _welcomeMessage = """
        Hello there, I can help you out fill out the information needed to open a new account with us.
        Please provide some personal information like first name and last name to get started.
        """;

    private readonly JsonSerializerOptions _jsonOptions = new()
    {
        DefaultIgnoreCondition = JsonIgnoreCondition.Never
    };

    public override ValueTask ActivateAsync(KernelProcessStepState<NewCustomerFormState> state)
    {
        this._state = state.State;
        return ValueTask.CompletedTask;
    }

    [KernelFunction(Functions.NewAccountWelcome)]
    public async Task NewAccountWelcomeMessageAsync(KernelProcessStepContext context, Kernel _kernel)
    {
        this._state?.conversation.Add(new ChatMessageContent { Role = AuthorRole.Assistant, Content = this._welcomeMessage });
        await context.EmitEventAsync(new() { Id = OutputEvents.NewCustomerFormWelcomeMessageComplete, Data = this._welcomeMessage });
    }

    private Kernel CreateNewCustomerFormKernel(Kernel _baseKernel)
    {
        // Creating another kernel that only makes use private functions to fill up the new customer form
        Kernel kernel = new(_baseKernel.Services);
        kernel.ImportPluginFromFunctions("FillForm", [
            KernelFunctionFactory.CreateFromMethod(this.OnUserProvidedFirstName, functionName: nameof(OnUserProvidedFirstName)),
            KernelFunctionFactory.CreateFromMethod(this.OnUserProvidedLastName, functionName: nameof(OnUserProvidedLastName)),
            KernelFunctionFactory.CreateFromMethod(this.OnUserProvidedDOBDetails, functionName: nameof(OnUserProvidedDOBDetails)),
            KernelFunctionFactory.CreateFromMethod(this.OnUserProvidedStateOfResidence, functionName: nameof(OnUserProvidedStateOfResidence)),
            KernelFunctionFactory.CreateFromMethod(this.OnUserProvidedPhoneNumber, functionName: nameof(OnUserProvidedPhoneNumber)),
            KernelFunctionFactory.CreateFromMethod(this.OnUserProvidedUserId, functionName: nameof(OnUserProvidedUserId)),
            KernelFunctionFactory.CreateFromMethod(this.OnUserProvidedEmailAddress, functionName: nameof(OnUserProvidedEmailAddress)),
        ]);

        return kernel;
    }

    [KernelFunction(Functions.NewAccountProcessUserInfo)]
    public async Task CompleteNewCustomerFormAsync(KernelProcessStepContext context, string userMessage, Kernel _kernel)
    {
        // Keeping track of all user interactions
        this._state?.conversation.Add(new ChatMessageContent { Role = AuthorRole.User, Content = userMessage });

        Kernel kernel = this.CreateNewCustomerFormKernel(_kernel);

        OpenAIPromptExecutionSettings settings = new()
        {
            ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions,
            Temperature = 0.7,
            MaxTokens = 2048
        };

        ChatHistory chatHistory = new();
        chatHistory.AddSystemMessage(this._formCompletionSystemPrompt
            .Replace("{{current_form_state}}", JsonSerializer.Serialize(this._state!.newCustomerForm.CopyWithDefaultValues(), _jsonOptions)));
        chatHistory.AddRange(this._state.conversation);
        IChatCompletionService chatService = kernel.Services.GetRequiredService<IChatCompletionService>();
        ChatMessageContent response = await chatService.GetChatMessageContentAsync(chatHistory, settings, kernel).ConfigureAwait(false);
        var assistantResponse = "";

        if (response != null)
        {
            assistantResponse = response.Items[0].ToString();
            // Keeping track of all assistant interactions
            this._state?.conversation.Add(new ChatMessageContent { Role = AuthorRole.Assistant, Content = assistantResponse });
        }

        if (this._state?.newCustomerForm != null && this._state.newCustomerForm.IsFormCompleted())
        {
            Console.WriteLine($"[NEW_USER_FORM_COMPLETED]: {JsonSerializer.Serialize(this._state?.newCustomerForm)}");
            // All user information is gathered to proceed to the next step
            if (!string.IsNullOrEmpty(assistantResponse))
            {
                await context.EmitEventAsync(new() { Id = OutputEvents.NewCustomerFormCompletedAssistantMessage, Data = assistantResponse, Visibility = KernelProcessEventVisibility.Public });
            }
            await context.EmitEventAsync(new() { Id = OutputEvents.NewCustomerFormCompleted, Data = this._state?.newCustomerForm, Visibility = KernelProcessEventVisibility.Public });
            await context.EmitEventAsync(new() { Id = OutputEvents.CustomerInteractionTranscriptReady, Data = this._state?.conversation, Visibility = KernelProcessEventVisibility.Public });
            return;
        }

        // emit event: NewCustomerFormNeedsMoreDetails
        await context.EmitEventAsync(new() { Id = OutputEvents.NewCustomerFormNeedsMoreDetails, Data = assistantResponse });
    }

    [Description("User provided details of first name")]
    private Task OnUserProvidedFirstName(string firstName)
    {
        if (!string.IsNullOrEmpty(firstName) && this._state != null)
        {
            this._state.newCustomerForm.UserFirstName = firstName;
        }

        return Task.CompletedTask;
    }

    [Description("User provided details of last name")]
    private Task OnUserProvidedLastName(string lastName)
    {
        if (!string.IsNullOrEmpty(lastName) && this._state != null)
        {
            this._state.newCustomerForm.UserLastName = lastName;
        }

        return Task.CompletedTask;
    }

    [Description("User provided details of USA State the user lives in, must be in 2-letter Uppercase State Abbreviation format")]
    private Task OnUserProvidedStateOfResidence(string stateAbbreviation)
    {
        if (!string.IsNullOrEmpty(stateAbbreviation) && this._state != null)
        {
            this._state.newCustomerForm.UserState = stateAbbreviation;
        }

        return Task.CompletedTask;
    }

    [Description("User provided details of date of birth, must be in the format MM/DD/YYYY")]
    private Task OnUserProvidedDOBDetails(string date)
    {
        if (!string.IsNullOrEmpty(date) && this._state != null)
        {
            this._state.newCustomerForm.UserDateOfBirth = date;
        }

        return Task.CompletedTask;
    }

    [Description("User provided details of phone number, must be in the format (\\d{3})-\\d{3}-\\d{4}")]
    private Task OnUserProvidedPhoneNumber(string phoneNumber)
    {
        if (!string.IsNullOrEmpty(phoneNumber) && this._state != null)
        {
            this._state.newCustomerForm.UserPhoneNumber = phoneNumber;
        }

        return Task.CompletedTask;
    }

    [Description("User provided details of userId, must be in the format \\d{3}-\\d{3}-\\d{4}")]
    private Task OnUserProvidedUserId(string userId)
    {
        if (!string.IsNullOrEmpty(userId) && this._state != null)
        {
            this._state.newCustomerForm.UserId = userId;
        }

        return Task.CompletedTask;
    }

    [Description("User provided email address, must be in the an email valid format")]
    private Task OnUserProvidedEmailAddress(string emailAddress)
    {
        if (!string.IsNullOrEmpty(emailAddress) && this._state != null)
        {
            this._state.newCustomerForm.UserEmail = emailAddress;
        }

        return Task.CompletedTask;
    }
}

/// <summary>
/// The state object for the <see cref="CompleteNewCustomerFormStep"/>
/// </summary>
public class NewCustomerFormState
{
    internal NewCustomerForm newCustomerForm { get; set; } = new();
    internal List<ChatMessageContent> conversation { get; set; } = [];
}

public class NewCustomerForm
{
    [JsonPropertyName("userFirstName")]
    public string UserFirstName { get; set; } = string.Empty;

    [JsonPropertyName("userLastName")]
    public string UserLastName { get; set; } = string.Empty;

    [JsonPropertyName("userDateOfBirth")]
    public string UserDateOfBirth { get; set; } = string.Empty;

    [JsonPropertyName("userState")]
    public string UserState { get; set; } = string.Empty;

    [JsonPropertyName("userPhoneNumber")]
    public string UserPhoneNumber { get; set; } = string.Empty;

    [JsonPropertyName("userId")]
    public string UserId { get; set; } = string.Empty;

    [JsonPropertyName("userEmail")]
    public string UserEmail { get; set; } = string.Empty;

    public NewCustomerForm CopyWithDefaultValues(string defaultStringValue = "Unanswered")
    {
        NewCustomerForm copy = new();
        PropertyInfo[] properties = typeof(NewCustomerForm).GetProperties();

        foreach (PropertyInfo property in properties)
        {
            // Get the value of the property  
            string? value = property.GetValue(this) as string;

            // Check if the value is an empty string  
            if (string.IsNullOrEmpty(value))
            {
                property.SetValue(copy, defaultStringValue);
            }
            else
            {
                property.SetValue(copy, value);
            }
        }

        return copy;
    }

    public bool IsFormCompleted()
    {
        return !string.IsNullOrEmpty(this.UserFirstName) &&
            !string.IsNullOrEmpty(this.UserLastName) &&
            !string.IsNullOrEmpty(this.UserId) &&
            !string.IsNullOrEmpty(this.UserDateOfBirth) &&
            !string.IsNullOrEmpty(this.UserState) &&
            !string.IsNullOrEmpty(this.UserEmail) &&
            !string.IsNullOrEmpty(this.UserPhoneNumber);
    }
}

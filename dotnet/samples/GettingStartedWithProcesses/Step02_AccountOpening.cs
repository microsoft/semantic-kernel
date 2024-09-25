// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace GettingStartedWithProcesses;

/// <summary>
/// Demonstrate creation of <see cref="KernelProcess"/> and
/// eliciting its response to three explicit user messages.
/// For visual reference of the process check the diagram in: https://github.com/microsoft/semantic-kernel/tree/main/dotnet/samples/GettingStartedWithProcesses/README.md#step02_accountOpening
/// </summary>
public class Step02_AccountOpening(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task UseAccountOpeningProcessAsync()
    {
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        ProcessBuilder process = new("AccountOpeningProcess");
        var newCustomerFormStep = process.AddStepFromType<CompleteNewCustomerFormStep>();
        var userInputStep = process.AddStepFromType<UserInputStep>();
        var displayAssistantMessageStep = process.AddStepFromType<DisplayAssistantMessageStep>();
        var customerCreditCheckStep = process.AddStepFromType<CreditScoreCheckStep>();
        var fraudDetectionCheckStep = process.AddStepFromType<FraudDetectionStep>();
        var mailServiceStep = process.AddStepFromType<MailServiceStep>();
        var coreSystemRecordCreationStep = process.AddStepFromType<NewAccountStep>();
        var marketingRecordCreationStep = process.AddStepFromType<NewMarketingEntryStep>();
        var crmRecordStep = process.AddStepFromType<CRMRecordCreationStep>();
        var welcomePacketStep = process.AddStepFromType<WelcomePacketStep>();

        process.OnExternalEvent("StartProcess")
            .SendEventTo(new ProcessFunctionTargetBuilder(newCustomerFormStep, "NewAccountWelcome"));

        // When the welcome message is generated, send message to displayAssistantMessageStep
        newCustomerFormStep
            .OnEvent(AccountOpeningEvents.NewCustomerFormWelcomeMessageComplete)
            .SendEventTo(new ProcessFunctionTargetBuilder(displayAssistantMessageStep, "DisplayAssistantMessage"));

        // When the userInput step emits a user input event, send it to the newCustomerForm step
        userInputStep
            .OnEvent(AccountOpeningEvents.UserInputReceived)
            .SendEventTo(new ProcessFunctionTargetBuilder(newCustomerFormStep, "NewAccountProcessUserInfo", "userMessage"));

        // When the newCustomerForm step emits needs more details, send message to displayAssistantMessage step
        newCustomerFormStep
            .OnEvent(AccountOpeningEvents.NewCustomerFormNeedsMoreDetails)
            .SendEventTo(new ProcessFunctionTargetBuilder(displayAssistantMessageStep, "DisplayAssistantMessage"));

        // After any assistant message is displayed, user input is expected to the next step is the userInputStep
        displayAssistantMessageStep
            .OnEvent(AccountOpeningEvents.AssistantResponseGenerated)
            .SendEventTo(new ProcessFunctionTargetBuilder(userInputStep, "GetUserInput"));

        // When the newCustomerForm is completed, the information gets passed to the core system record creation step
        newCustomerFormStep
            .OnEvent(AccountOpeningEvents.NewCustomerFormCompleted)
            .SendEventTo(new ProcessFunctionTargetBuilder(customerCreditCheckStep, functionName: "DetermineCreditScore", parameterName: "customerDetails"));

        // When the newCustomerForm is completed, the information gets passed to the fraud detection step for validation
        newCustomerFormStep
            .OnEvent(AccountOpeningEvents.NewCustomerFormCompleted)
            .SendEventTo(new ProcessFunctionTargetBuilder(fraudDetectionCheckStep, functionName: "FraudDetectionCheck", parameterName: "customerDetails"));

        // When the newCustomerForm is completed, the information gets passed to the core system record creation step
        newCustomerFormStep
            .OnEvent(AccountOpeningEvents.NewCustomerFormCompleted)
            .SendEventTo(new ProcessFunctionTargetBuilder(coreSystemRecordCreationStep, functionName: "CreateNewAccount", parameterName: "customerDetails"));

        // When the newCustomerForm is completed, the user interaction transcript with the user is passed to the core system record creation step
        newCustomerFormStep
            .OnEvent(AccountOpeningEvents.CustomerInteractionTranscriptReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(coreSystemRecordCreationStep, functionName: "CreateNewAccount", parameterName: "interactionTranscript"));

        // When the creditScoreCheck step results in Rejection, the information gets to the mailService step to notify the user about the state of the application and the reasons
        customerCreditCheckStep
            .OnEvent(AccountOpeningEvents.CreditScoreCheckRejected)
            .SendEventTo(new ProcessFunctionTargetBuilder(mailServiceStep, functionName: "SendMailToUserWithDetails", parameterName: "message"));

        // When the creditScoreCheck step results in Approval, the information gets to the fraudDetection step to kickstart this step
        customerCreditCheckStep
            .OnEvent(AccountOpeningEvents.CreditScoreCheckApproved)
            .SendEventTo(new ProcessFunctionTargetBuilder(fraudDetectionCheckStep, functionName: "FraudDetectionCheck", parameterName: "previousCheckSucceeded"));

        // When the fraudDetectionCheck step fails, the information gets to the mailService step to notify the user about the state of the application and the reasons
        fraudDetectionCheckStep
            .OnEvent(AccountOpeningEvents.FraudDetectionCheckFailed)
            .SendEventTo(new ProcessFunctionTargetBuilder(mailServiceStep, functionName: "SendMailToUserWithDetails", parameterName: "message"));

        // When the fraudDetectionCheck step passes, the information gets to core system record creation step to kickstart this step
        fraudDetectionCheckStep
            .OnEvent(AccountOpeningEvents.FraudDetectionCheckPassed)
            .SendEventTo(new ProcessFunctionTargetBuilder(coreSystemRecordCreationStep, functionName: "CreateNewAccount", parameterName: "previousCheckSucceeded"));

        // When the coreSystemRecordCreation step successfully creates a new accountId, it will trigger the creation of a new marketing entry through the marketingRecordCreation step
        coreSystemRecordCreationStep
            .OnEvent(AccountOpeningEvents.NewMarketingRecordInfoReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(marketingRecordCreationStep, functionName: "CreateNewMarketingEntry", parameterName: "userDetails"));

        // When the coreSystemRecordCreation step successfully creates a new accountId, it will trigger the creation of a new CRM entry through the crmRecord step
        coreSystemRecordCreationStep
            .OnEvent(AccountOpeningEvents.CRMRecordInfoReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(crmRecordStep, functionName: "CreateCRMEntry", parameterName: "userInteractionDetails"));

        // When the coreSystemRecordCreation step successfully creates a new accountId, it will pass the account information details to the welcomePacket step
        coreSystemRecordCreationStep
            .OnEvent(AccountOpeningEvents.NewAccountDetailsReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(welcomePacketStep, parameterName: "accountDetails"));

        // When the marketingRecordCreation step successfully creates a new marketing entry, it will notify the welcomePacket step it is ready
        marketingRecordCreationStep
            .OnEvent(AccountOpeningEvents.NewMarketingEntryCreated)
            .SendEventTo(new ProcessFunctionTargetBuilder(welcomePacketStep, parameterName: "marketingEntryCreated"));

        // When the crmRecord step successfully creates a new CRM entry, it will notify the welcomePacket step it is ready
        crmRecordStep
            .OnEvent(AccountOpeningEvents.CRMRecordInfoEntryCreated)
            .SendEventTo(new ProcessFunctionTargetBuilder(welcomePacketStep, parameterName: "crmRecordCreated"));

        // After crmRecord and marketing gets created, a welcome packet is created to then send information to the user with the mailService step
        welcomePacketStep
            .OnEvent(AccountOpeningEvents.WelcomePacketCreated)
            .SendEventTo(new ProcessFunctionTargetBuilder(mailServiceStep, functionName: "SendMailToUserWithDetails", parameterName: "message"));

        // All possible paths end up with the user being notified about the account creation decision throw the mailServiceStep completion
        mailServiceStep
            .OnEvent(AccountOpeningEvents.MailServiceSent)
            .StopProcess();

        KernelProcess kernelProcess = process.Build();

        var runningProcess = await LocalKernelProcessFactory.StartAsync(kernelProcess, kernel, new KernelProcessEvent() { Id = "StartProcess", Data = null });
    }

    public class UserInputStep : KernelProcessStep<UserInputState>
    {
        private UserInputState? _state;

        public override ValueTask ActivateAsync(KernelProcessStepState<UserInputState> state)
        {
            state.State ??= new();
            _state = state.State;

            _state.UserInputs.Add("I would like to open an account");
            _state.UserInputs.Add("My name is John Contoso, dob 02/03/1990");
            _state.UserInputs.Add("I live in Washington and my phone number es 222-222-1234");
            _state.UserInputs.Add("My userId is 987-654-3210");
            _state.UserInputs.Add("My email is john.contoso@contoso.com, what else do you need?");

            return ValueTask.CompletedTask;
        }

        [KernelFunction("GetUserInput")]
        public async ValueTask GetUserInputAsync(KernelProcessStepContext context)
        {
            var input = _state!.UserInputs[_state.CurrentInputIndex];
            _state.CurrentInputIndex++;

            // Emit the user input
            await context.EmitEventAsync(new() { Id = AccountOpeningEvents.UserInputReceived, Data = input });
        }
    }

    public class DisplayAssistantMessageStep : KernelProcessStep
    {
        [KernelFunction("DisplayAssistantMessage")]
        public async ValueTask DisplayAssistantMessageAsync(KernelProcessStepContext context, string assistantMessage)
        {
            // Emit the user input
            await context.EmitEventAsync(new() { Id = AccountOpeningEvents.AssistantResponseGenerated, Data = assistantMessage });
        }
    }

    public class NewCustomerForm
    {
        [JsonPropertyName("userFirstName")]
        public string UserFirstName { get; set; } = "";

        [JsonPropertyName("userLastName")]
        public string UserLastName { get; set; } = "";

        [JsonPropertyName("userDateOfBirth")]
        public string UserDateOfBirth { get; set; } = "";

        [JsonPropertyName("userState")]
        public string UserState { get; set; } = "";

        [JsonPropertyName("userPhoneNumber")]
        public string UserPhoneNumber { get; set; } = "";

        [JsonPropertyName("userId")]
        public string UserId { get; set; } = "";

        [JsonPropertyName("userEmail")]
        public string UserEmail { get; set; } = "";

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
            return !string.IsNullOrEmpty(UserFirstName) &&
                !string.IsNullOrEmpty(UserLastName) &&
                !string.IsNullOrEmpty(UserId) &&
                !string.IsNullOrEmpty(UserDateOfBirth) &&
                !string.IsNullOrEmpty(UserState) &&
                !string.IsNullOrEmpty(UserEmail) &&
                !string.IsNullOrEmpty(UserPhoneNumber);
        }
    }

    public class CompleteNewCustomerFormStep : KernelProcessStep<NewCustomerFormState>
    {
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
            _state = state.State ?? new();
            _state.newCustomerForm ??= new();
            return ValueTask.CompletedTask;
        }

        [KernelFunction("NewAccountWelcome")]
        public async Task NewAccountWelcomeMessageAsync(KernelProcessStepContext context, Kernel _kernel)
        {
            _state?.conversation.Add(new ChatMessageContent { Role = AuthorRole.Assistant, Content = _welcomeMessage });
            await context.EmitEventAsync(new() { Id = AccountOpeningEvents.NewCustomerFormWelcomeMessageComplete, Data = _welcomeMessage });
        }

        private Kernel CreateNewCustomerFormKernel(Kernel _baseKernel)
        {
            // Creating another kernel that only makes use private functions to fill up the new customer form
            Kernel kernel = new(_baseKernel.Services);
            kernel.ImportPluginFromFunctions("FillForm", [
                KernelFunctionFactory.CreateFromMethod(OnUserProvidedFirstName, functionName: nameof(OnUserProvidedFirstName)),
                KernelFunctionFactory.CreateFromMethod(OnUserProvidedLastName, functionName: nameof(OnUserProvidedLastName)),
                KernelFunctionFactory.CreateFromMethod(OnUserProvidedDOBDetails, functionName: nameof(OnUserProvidedDOBDetails)),
                KernelFunctionFactory.CreateFromMethod(OnUserProvidedStateOfResidence, functionName: nameof(OnUserProvidedStateOfResidence)),
                KernelFunctionFactory.CreateFromMethod(OnUserProvidedPhoneNumber, functionName: nameof(OnUserProvidedPhoneNumber)),
                KernelFunctionFactory.CreateFromMethod(OnUserProvidedUserId, functionName: nameof(OnUserProvidedUserId)),
                KernelFunctionFactory.CreateFromMethod(OnUserProvidedEmailAddress, functionName: nameof(OnUserProvidedEmailAddress)),
            ]);

            return kernel;
        }

        [KernelFunction("NewAccountProcessUserInfo")]
        public async Task CompleteNewCustomerFormAsync(KernelProcessStepContext context, string userMessage, Kernel _kernel)
        {
            // Keeping track of all user interactions
            _state?.conversation.Add(new ChatMessageContent { Role = AuthorRole.User, Content = userMessage });

            Kernel kernel = CreateNewCustomerFormKernel(_kernel);

            OpenAIPromptExecutionSettings settings = new()
            {
                ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions,
                Temperature = 0.7,
                ModelId = "gpt-4o",
                MaxTokens = 2048
            };

            ChatHistory chatHistory = new();
            chatHistory.AddSystemMessage(_formCompletionSystemPrompt
                .Replace("{{current_form_state}}", JsonSerializer.Serialize(_state!.newCustomerForm.CopyWithDefaultValues(), _jsonOptions)));
            chatHistory.AddUserMessage(userMessage);
            IChatCompletionService chatService = kernel.Services.GetRequiredService<IChatCompletionService>();
            ChatMessageContent response = await chatService.GetChatMessageContentAsync(chatHistory, settings, kernel).ConfigureAwait(false);
            var assistantResponse = "";

            if (response != null)
            {
                assistantResponse = response.Items[0].ToString();
                // Keeping track of all assistant interactions
                _state?.conversation.Add(new ChatMessageContent { Role = AuthorRole.Assistant, Content = assistantResponse });
            }

            if (_state?.newCustomerForm != null && _state.newCustomerForm.IsFormCompleted())
            {
                // All user information is gathered to proceed to the next step
                await context.EmitEventAsync(new() { Id = AccountOpeningEvents.NewCustomerFormCompleted, Data = _state?.newCustomerForm });
                await context.EmitEventAsync(new() { Id = AccountOpeningEvents.CustomerInteractionTranscriptReady, Data = _state?.conversation });
                return;
            }

            // emit event: NewCustomerFormNeedsMoreDetails
            await context.EmitEventAsync(new() { Id = AccountOpeningEvents.NewCustomerFormNeedsMoreDetails, Data = assistantResponse });
        }

        [Description("User provided details of first name")]
        private Task OnUserProvidedFirstName(string firstName)
        {
            if (!string.IsNullOrEmpty(firstName) && _state != null)
            {
                _state.newCustomerForm.UserFirstName = firstName;
            }

            return Task.CompletedTask;
        }

        [Description("User provided details of last name")]
        private Task OnUserProvidedLastName(string lastName)
        {
            if (!string.IsNullOrEmpty(lastName) && _state != null)
            {
                _state.newCustomerForm.UserLastName = lastName;
            }

            return Task.CompletedTask;
        }

        [Description("User provided details of USA State the user lives in, must be in 2-letter Uppercase State Abbreviation format")]
        private Task OnUserProvidedStateOfResidence(string stateAbbreviation)
        {
            if (!string.IsNullOrEmpty(stateAbbreviation) && _state != null)
            {
                _state.newCustomerForm.UserState = stateAbbreviation;
            }

            return Task.CompletedTask;
        }

        [Description("User provided details of date of birth, must be in the format MM/DD/YYYY")]
        private Task OnUserProvidedDOBDetails(string date)
        {
            if (!string.IsNullOrEmpty(date) && _state != null)
            {
                _state.newCustomerForm.UserDateOfBirth = date;
            }

            return Task.CompletedTask;
        }

        [Description("User provided details of phone number, must be in the format (\\d{3})-\\d{3}-\\d{4}")]
        private Task OnUserProvidedPhoneNumber(string phoneNumber)
        {
            if (!string.IsNullOrEmpty(phoneNumber) && _state != null)
            {
                _state.newCustomerForm.UserPhoneNumber = phoneNumber;
            }

            return Task.CompletedTask;
        }

        [Description("User provided details of userId, must be in the format \\d{3}-\\d{3}-\\d{4}")]
        private Task OnUserProvidedUserId(string userId)
        {
            if (!string.IsNullOrEmpty(userId) && _state != null)
            {
                _state.newCustomerForm.UserId = userId;
            }

            return Task.CompletedTask;
        }

        [Description("User provided email address, must be in the an email valid format")]
        private Task OnUserProvidedEmailAddress(string emailAddress)
        {
            if (!string.IsNullOrEmpty(emailAddress) && _state != null)
            {
                _state.newCustomerForm.UserEmail = emailAddress;
            }

            return Task.CompletedTask;
        }
    }

    public class CreditScoreCheckStep : KernelProcessStep
    {
        private static readonly Random s_random = new();
        private const int MinCreditScore = 600;

        [KernelFunction("DetermineCreditScore")]
        public async Task DetermineCreditScoreAsync(KernelProcessStepContext context, NewCustomerForm customerDetails, Kernel _kernel)
        {
            // Placeholder for a call to API to validate credit score with customerDetails
            var creditScore = s_random.Next(590, 850);

            if (creditScore >= MinCreditScore)
            {
                await context.EmitEventAsync(new() { Id = AccountOpeningEvents.CreditScoreCheckApproved, Data = true });
                return;
            }

            await context.EmitEventAsync(new() { Id = AccountOpeningEvents.CreditScoreCheckRejected, Data = $"We regret to inform you that your credit score of {creditScore} is insufficient to apply for an account of the type PRIME ABC" });
        }
    }

    public class FraudDetectionStep : KernelProcessStep
    {
        [KernelFunction("FraudDetectionCheck")]
        public async Task FraudDetectionCheckAsync(KernelProcessStepContext context, bool previousCheckSucceeded, NewCustomerForm customerDetails, Kernel _kernel)
        {
            // Placeholder for a call to API to validate user details for fraud detection
            if (customerDetails.UserId == "123-456-7890")
            {
                await context.EmitEventAsync(new()
                {
                    Id = AccountOpeningEvents.FraudDetectionCheckFailed,
                    Data = "We regret to inform you that we found some inconsistent details regarding the information you provided regarding the new account of the type PRIME ABC you applied."
                });
                return;
            }

            await context.EmitEventAsync(new() { Id = AccountOpeningEvents.FraudDetectionCheckPassed, Data = true });
        }
    }

    public class MailServiceStep : KernelProcessStep
    {
        [KernelFunction("SendMailToUserWithDetails")]
        public async Task SendMailServiceAsync(KernelProcessStepContext context, string message)
        {
            await context.EmitEventAsync(new() { Id = AccountOpeningEvents.MailServiceSent, Data = message });
        }
    }

    public enum AccountType
    {
        PrimeABC,
        Other,
    }

    public class AccountDetails : NewCustomerForm
    {
        public Guid AccountId { get; set; }
        public AccountType AccountType { get; set; }
    }

    public enum UserInteractionType
    {
        Complaint,
        AccountInfoRequest,
        OpeningNewAccount
    }

    public class MarketingNewEntryDetails
    {
        public Guid AccountId { get; set; }

        public string Name { get; set; }

        public string PhoneNumber { get; set; }

        public string Email { get; set; }
    }

    public class UserInteractionDetails
    {
        public Guid AccountId { get; set; }

        public List<ChatMessageContent> InteractionTranscript { get; set; } = [];

        public UserInteractionType UserInteractionType { get; set; }
    }

    public class NewAccountStep : KernelProcessStep
    {
        [KernelFunction("CreateNewAccount")]
        public async Task CreateNewAccountAsync(KernelProcessStepContext context, bool previousCheckSucceeded, NewCustomerForm customerDetails, List<ChatMessageContent> interactionTranscript, Kernel _kernel)
        {
            // Placeholder for a call to API to create new account for user
            var accountId = new Guid();
            AccountDetails accountDetails = new()
            {
                UserDateOfBirth = customerDetails.UserDateOfBirth,
                UserFirstName = customerDetails.UserFirstName,
                UserLastName = customerDetails.UserLastName,
                UserId = customerDetails.UserId,
                UserPhoneNumber = customerDetails.UserPhoneNumber,
                UserState = customerDetails.UserState,
                AccountId = accountId,
                AccountType = AccountType.PrimeABC,
            };

            await context.EmitEventAsync(new()
            {
                Id = AccountOpeningEvents.NewMarketingRecordInfoReady,
                Data = new MarketingNewEntryDetails
                {
                    AccountId = accountId,
                    Name = $"{customerDetails.UserFirstName} {customerDetails.UserLastName}",
                    PhoneNumber = customerDetails.UserPhoneNumber,
                    Email = customerDetails.UserEmail,
                }
            });

            await context.EmitEventAsync(new()
            {
                Id = AccountOpeningEvents.CRMRecordInfoReady,
                Data = new UserInteractionDetails
                {
                    AccountId = accountId,
                    UserInteractionType = UserInteractionType.OpeningNewAccount,
                    InteractionTranscript = interactionTranscript
                }
            });

            await context.EmitEventAsync(new()
            {
                Id = AccountOpeningEvents.NewAccountDetailsReady,
                Data = accountDetails,
            });
        }
    }

    public class NewMarketingEntryStep : KernelProcessStep
    {
        [KernelFunction("CreateNewMarketingEntry")]
        public async Task CreateNewMarketingEntryAsync(KernelProcessStepContext context, MarketingNewEntryDetails userDetails, Kernel _kernel)
        {
            // Placeholder for a call to API to create new entry of user for marketing purposes
            await context.EmitEventAsync(new() { Id = AccountOpeningEvents.NewMarketingEntryCreated, Data = true });
        }
    }

    public class CRMRecordCreationStep : KernelProcessStep
    {
        [KernelFunction("CreateCRMEntry")]
        public async Task CreateCRMEntryAsync(KernelProcessStepContext context, UserInteractionDetails userInteractionDetails, Kernel _kernel)
        {
            // Placeholder for a call to API to create new CRM entry
            await context.EmitEventAsync(new() { Id = AccountOpeningEvents.CRMRecordInfoEntryCreated, Data = true });
        }
    }

    public class WelcomePacketStep : KernelProcessStep
    {
        [KernelFunction("CreateWelcomePacket")]
        public async Task CreateWelcomePacketAsync(KernelProcessStepContext context, bool marketingEntryCreated, bool crmRecordCreated, AccountDetails accountDetails, Kernel _kernel)
        {
            await context.EmitEventAsync(new()
            {
                Id = AccountOpeningEvents.WelcomePacketCreated,
                Data = $"""
                Dear {accountDetails.UserFirstName} {accountDetails.UserLastName}
                We are thrilled to inform you that you have successfully created a new PRIME ABC Account with us!

                Account Details:
                Account Number: {accountDetails.AccountId}
                Account Type: {accountDetails.AccountType}

                Please keep this confidential for security purposes.
                """
            });
        }
    }

    public record UserInputState
    {
        public List<string> UserInputs { get; init; } = [];

        public int CurrentInputIndex { get; set; } = 0;
    }

    public class NewCustomerFormState
    {
        internal NewCustomerForm newCustomerForm { get; set; } = new();
        internal List<ChatMessageContent> conversation { get; set; } = [];
    }

    public static class AccountOpeningEvents
    {
        public static readonly string UserInputReceived = "userInputReceived";
        public static readonly string AssistantResponseGenerated = "assistantResponseGenerated";

        public static readonly string NewCustomerFormWelcomeMessageComplete = "newCustomerWelcomeComplete";
        public static readonly string NewCustomerFormCompleted = "newCustomerFormComplete";
        public static readonly string NewCustomerFormNeedsMoreDetails = "newCustomerFormNeedsMoreDetails";
        public static readonly string CustomerInteractionTranscriptReady = "customerInteractionTranscriptReady";

        public static readonly string CreditScoreCheckApproved = "creditScoreCheckApproved";
        public static readonly string CreditScoreCheckRejected = "creditScoreCheckRejected";

        public static readonly string FraudDetectionCheckPassed = "fraudDetectionCheckPassed";
        public static readonly string FraudDetectionCheckFailed = "fraudDetectionCheckFailed";

        public static readonly string NewAccountDetailsReady = "newAccountDetailsReady";

        public static readonly string NewMarketingRecordInfoReady = "newMarketingRecordInfoReady";
        public static readonly string NewMarketingEntryCreated = "newMarketingEntryCreated";
        public static readonly string CRMRecordInfoReady = "crmRecordInfoReady";
        public static readonly string CRMRecordInfoEntryCreated = "crmRecordInfoEntryCreated";

        public static readonly string WelcomePacketCreated = "welcomePacketCreated";

        public static readonly string MailServiceSent = "mailServiceSent";
    }
}

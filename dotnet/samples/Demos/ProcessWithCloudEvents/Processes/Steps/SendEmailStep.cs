// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Graph;
using Microsoft.Graph.Me.SendMail;
using Microsoft.SemanticKernel;
using ProcessWithCloudEvents.MicrosoftGraph;

namespace ProcessWithCloudEvents.Processes.Steps;

public class SendEmailStep : KernelProcessStep
{
    public static class OutputEvents
    {
        public const string SendEmailSuccess = nameof(SendEmailSuccess);
        public const string SendEmailFailure = nameof(SendEmailFailure);
    }

    public static class Functions
    {
        public const string SendCounterChangeEmail = nameof(SendCounterChangeEmail);
        public const string SendCounterResetEmail = nameof(SendCounterResetEmail);
    }

    public SendEmailStep() { }

    protected SendMailPostRequestBody PopulateMicrosoftGraphMailMessage(object inputData, string emailAddress, string subject)
    {
        var message = GraphRequestFactory.CreateEmailBody(
            subject: $"{subject} - using SK cloud step",
            content: $"The counter is {(int)inputData}",
            recipients: [emailAddress]);

        return message;
    }

    [KernelFunction(Functions.SendCounterChangeEmail)]
    public async Task PublishCounterChangedEmailMessageAsync(KernelProcessStepContext context, Kernel kernel, object inputData)
    {
        if (inputData == null)
        {
            return;
        }

        try
        {
            var graphClient = kernel.GetRequiredService<GraphServiceClient>();
            var user = await graphClient.Me.GetAsync();
            var graphEmailMessage = this.PopulateMicrosoftGraphMailMessage(inputData, user!.Mail!, subject: "The counter has changed");
            await graphClient.Me.SendMail.PostAsync(graphEmailMessage).ConfigureAwait(false);

            await context.EmitEventAsync(OutputEvents.SendEmailSuccess);
        }
        catch (Exception e)
        {
            await context.EmitEventAsync(OutputEvents.SendEmailFailure, e, visibility: KernelProcessEventVisibility.Public);
            throw new KernelException($"Something went wrong and couldn't send email - {e}");
        }
    }

    [KernelFunction(Functions.SendCounterResetEmail)]
    public async Task PublishCounterResetEmailMessageAsync(KernelProcessStepContext context, Kernel kernel, object inputData)
    {
        if (inputData == null)
        {
            return;
        }

        try
        {
            var graphClient = kernel.GetRequiredService<GraphServiceClient>();
            var user = await graphClient.Me.GetAsync();
            var graphEmailMessage = this.PopulateMicrosoftGraphMailMessage(inputData, user!.Mail!, subject: "The counter has been reset");
            await graphClient.Me.SendMail.PostAsync(graphEmailMessage).ConfigureAwait(false);

            await context.EmitEventAsync(OutputEvents.SendEmailSuccess);
        }
        catch (Exception e)
        {
            await context.EmitEventAsync(OutputEvents.SendEmailFailure, e, visibility: KernelProcessEventVisibility.Public);
            throw new KernelException($"Something went wrong and couldn't send email - {e}");
        }
    }
}

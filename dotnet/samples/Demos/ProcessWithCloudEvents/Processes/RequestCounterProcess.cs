// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Graph;
using Microsoft.Graph.Me.SendMail;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process;
using ProcessWithCloudEvents.MicrosoftGraph;
using ProcessWithCloudEvents.Processes.Steps;

namespace ProcessWithCloudEvents.Processes;

public static class RequestCounterProcess
{
    public static class StepNames
    {
        public const string Counter = nameof(Counter);
        public const string CounterInterceptor = nameof(CounterInterceptor);
        public const string SendEmail = nameof(SendEmail);
    }

    public enum CounterProcessEvents
    {
        IncreaseCounterRequest,
        DecreaseCounterRequest,
        ResetCounterRequest,
        OnCounterReset,
        OnCounterResult
    }

    public static string GetEventName(CounterProcessEvents processEvent)
    {
        return Enum.GetName(processEvent) ?? "";
    }

    public static ProcessBuilder<CounterProcessEvents> CreateProcessWithCloudSteps()
    {
        var processBuilder = new ProcessBuilder<CounterProcessEvents>("RequestCounterProcess");

        var counterStep = processBuilder.AddStepFromType<CounterStep>(StepNames.Counter);
        var counterInterceptorStep = processBuilder.AddStepFromType<CounterInterceptorStep>(StepNames.CounterInterceptor);
        var emailSenderStep = processBuilder.AddStepFromType<SendEmailStep>(StepNames.SendEmail);

        processBuilder
            .OnInputEvent(processBuilder.GetEventName(CounterProcessEvents.IncreaseCounterRequest))
            .SendEventTo(new ProcessFunctionTargetBuilder(counterStep, functionName: CounterStep.Functions.IncreaseCounter));

        processBuilder
            .OnInputEvent(processBuilder.GetEventName(CounterProcessEvents.DecreaseCounterRequest))
            .SendEventTo(new ProcessFunctionTargetBuilder(counterStep, functionName: CounterStep.Functions.DecreaseCounter));

        processBuilder
            .OnInputEvent(processBuilder.GetEventName(CounterProcessEvents.ResetCounterRequest))
            .SendEventTo(new ProcessFunctionTargetBuilder(counterStep, functionName: CounterStep.Functions.ResetCounter));

        counterStep
            .OnFunctionResult(CounterStep.Functions.IncreaseCounter)
            .SendEventTo(new ProcessFunctionTargetBuilder(counterInterceptorStep));

        counterStep
            .OnFunctionResult(CounterStep.Functions.DecreaseCounter)
            .SendEventTo(new ProcessFunctionTargetBuilder(counterInterceptorStep));

        counterStep
            .OnFunctionResult(CounterStep.Functions.ResetCounter)
            .SendEventTo(new ProcessFunctionTargetBuilder(emailSenderStep, SendEmailStep.Functions.SendCounterResetEmail));

        counterInterceptorStep
            .OnFunctionResult(CounterInterceptorStep.Functions.InterceptCounter)
            .SendEventTo(new ProcessFunctionTargetBuilder(emailSenderStep, SendEmailStep.Functions.SendCounterChangeEmail));

        return processBuilder;
    }

    public static ProcessBuilder<CounterProcessEvents> CreateProcessWithProcessSubscriber(IServiceProvider serviceProvider)
    {
        var processBuilder = new ProcessBuilder<CounterProcessEvents>("CounterWithProcessSubscriber");

        var counterStep = processBuilder.AddStepFromType<CounterStep>(StepNames.Counter);
        var counterInterceptorStep = processBuilder.AddStepFromType<CounterInterceptorStep>(StepNames.CounterInterceptor);

        processBuilder
            .OnInputEvent(processBuilder.GetEventName(CounterProcessEvents.IncreaseCounterRequest))
            .SendEventTo(new ProcessFunctionTargetBuilder(counterStep, functionName: CounterStep.Functions.IncreaseCounter));

        processBuilder
            .OnInputEvent(processBuilder.GetEventName(CounterProcessEvents.DecreaseCounterRequest))
            .SendEventTo(new ProcessFunctionTargetBuilder(counterStep, functionName: CounterStep.Functions.DecreaseCounter));

        processBuilder
            .OnInputEvent(processBuilder.GetEventName(CounterProcessEvents.ResetCounterRequest))
            .SendEventTo(new ProcessFunctionTargetBuilder(counterStep, functionName: CounterStep.Functions.ResetCounter));

        counterStep
            .OnFunctionResult(CounterStep.Functions.IncreaseCounter)
            .SendEventTo(new ProcessFunctionTargetBuilder(counterInterceptorStep));

        counterStep
            .OnFunctionResult(CounterStep.Functions.DecreaseCounter)
            .SendEventTo(new ProcessFunctionTargetBuilder(counterInterceptorStep));

        counterStep
            .OnFunctionResult(CounterStep.Functions.ResetCounter)
            .EmitAsProcessEvent(processBuilder.GetProcessEvent(CounterProcessEvents.OnCounterReset))
            .SendEventTo(new ProcessFunctionTargetBuilder(counterInterceptorStep));

        counterInterceptorStep
            .OnFunctionResult(CounterInterceptorStep.Functions.InterceptCounter)
            .EmitAsProcessEvent(processBuilder.GetProcessEvent(CounterProcessEvents.OnCounterResult));

        processBuilder.LinkEventSubscribersFromType<CounterProcessSubscriber>(serviceProvider);

        return processBuilder;
    }

    public class CounterProcessSubscriber : KernelProcessEventsSubscriber<CounterProcessEvents>
    {
        private SendMailPostRequestBody GenerateEmailRequest(int counter, string emailAddress, string subject)
        {
            var message = GraphRequestFactory.CreateEmailBody(
                subject: $"{subject} - using SK event subscribers",
                content: $"The counter is {counter}",
                recipients: [emailAddress]);

            return message;
        }

        [ProcessEventSubscriber(CounterProcessEvents.OnCounterResult)]
        public async Task OnCounterResultReceivedAsync(int? counterResult)
        {
            if (!counterResult.HasValue)
            {
                return;
            }

            try
            {
                var graphClient = this.ServiceProvider?.GetRequiredService<GraphServiceClient>();
                var user = await graphClient?.Me.GetAsync();
                var graphEmailMessage = this.GenerateEmailRequest(counterResult.Value, user!.Mail!, subject: "The counter has changed");
                await graphClient?.Me.SendMail.PostAsync(graphEmailMessage);
            }
            catch (Exception e)
            {
                throw new KernelException($"Something went wrong and couldn't send email - {e}");
            }
        }

        [ProcessEventSubscriber(CounterProcessEvents.OnCounterReset)]
        public async Task OnCounterResetReceivedAsync(int? counterResult)
        {
            if (!counterResult.HasValue)
            {
                return;
            }

            try
            {
                var graphClient = this.ServiceProvider?.GetRequiredService<GraphServiceClient>();
                var user = await graphClient.Me.GetAsync();
                var graphEmailMessage = this.GenerateEmailRequest(counterResult.Value, user!.Mail!, subject: "The counter has been reset");
                await graphClient?.Me.SendMail.PostAsync(graphEmailMessage);
            }
            catch (Exception e)
            {
                throw new KernelException($"Something went wrong and couldn't send email - {e}");
            }
        }
    }
}

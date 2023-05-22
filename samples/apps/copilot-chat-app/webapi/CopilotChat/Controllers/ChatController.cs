// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using Microsoft.Graph;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Reliability;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Skills.MsGraph;
using Microsoft.SemanticKernel.Skills.MsGraph.Connectors;
using Microsoft.SemanticKernel.Skills.MsGraph.Connectors.Client;
using Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;
using SemanticKernel.Service.CopilotChat.Models;
using SemanticKernel.Service.CopilotChat.Skills.ChatSkills;
using SemanticKernel.Service.Models;

namespace SemanticKernel.Service.CopilotChat.Controllers;

/// <summary>
/// Controller responsible for handling chat messages and responses.
/// </summary>
[ApiController]
public class ChatController : ControllerBase, IDisposable
{
    private readonly ILogger<ChatController> _logger;
    private readonly List<IDisposable> _disposables;
    private const string ChatSkillName = "ChatSkill";
    private const string ChatFunctionName = "Chat";

    public ChatController(ILogger<ChatController> logger)
    {
        this._logger = logger;
        this._disposables = new List<IDisposable>();
    }

    /// <summary>
    /// Invokes the chat skill to get a response from the bot.
    /// </summary>
    /// <param name="kernel">Semantic kernel obtained through dependency injection.</param>
    /// <param name="planner">Planner to use to create function sequences.</param>
    /// <param name="plannerOptions">Options for the planner.</param>
    /// <param name="ask">Prompt along with its parameters.</param>
    /// <param name="openApiSkillsAuthHeaders">Authentication headers to connect to OpenAPI Skills.</param>
    /// <returns>Results containing the response from the model.</returns>
    [Authorize]
    [Route("chat")]
    [HttpPost]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> ChatAsync(
        [FromServices] IKernel kernel,
        [FromServices] CopilotChatPlanner planner,
        [FromBody] Ask ask,
        [FromHeader] OpenApiSkillsAuthHeaders openApiSkillsAuthHeaders)
    {
        this._logger.LogDebug("Chat request received.");

        // Put ask's variables in the context we will use.
        var contextVariables = new ContextVariables(ask.Input);
        foreach (var input in ask.Variables)
        {
            contextVariables.Set(input.Key, input.Value);
        }

        // Register plugins that have been enabled
        await this.RegisterPlannerSkillsAsync(planner, openApiSkillsAuthHeaders, contextVariables);

        // Get the function to invoke
        ISKFunction? function = null;
        try
        {
            function = kernel.Skills.GetFunction(ChatSkillName, ChatFunctionName);
        }
        catch (KernelException ke)
        {
            this._logger.LogError("Failed to find {0}/{1} on server: {2}", ChatSkillName, ChatFunctionName, ke);

            return this.NotFound($"Failed to find {ChatSkillName}/{ChatFunctionName} on server");
        }

        // Run the function.
        SKContext result = await kernel.RunAsync(contextVariables, function!);
        if (result.ErrorOccurred)
        {
            if (result.LastException is AIException aiException && aiException.Detail is not null)
            {
                return this.BadRequest(string.Concat(aiException.Message, " - Detail: " + aiException.Detail));
            }

            return this.BadRequest(result.LastErrorDescription);
        }

        return this.Ok(new AskResult { Value = result.Result, Variables = result.Variables.Select(v => new KeyValuePair<string, string>(v.Key, v.Value)) });
    }

    /// <summary>
    /// Register skills with the planner's kernel.
    /// </summary>
    private async Task RegisterPlannerSkillsAsync(CopilotChatPlanner planner, OpenApiSkillsAuthHeaders openApiSkillsAuthHeaders, ContextVariables variables)
    {
        // Register authenticated skills with the planner's kernel only if the request includes an auth header for the skill.

        // Klarna Shopping
        if (openApiSkillsAuthHeaders.KlarnaAuthentication != null)
        {
            // Register the Klarna shopping ChatGPT plugin with the planner's kernel.
            using DefaultHttpRetryHandler retryHandler = new(new HttpRetryConfig(), this._logger)
            {
                InnerHandler = new HttpClientHandler() { CheckCertificateRevocationList = true }
            };
            using HttpClient importHttpClient = new(retryHandler, false);
            importHttpClient.DefaultRequestHeaders.Add("User-Agent", "Microsoft.CopilotChat");
            await planner.Kernel.ImportChatGptPluginSkillFromUrlAsync("KlarnaShoppingSkill", new Uri("https://www.klarna.com/.well-known/ai-plugin.json"),
                importHttpClient);
        }

        // GitHub
        if (!string.IsNullOrWhiteSpace(openApiSkillsAuthHeaders.GithubAuthentication))
        {
            this._logger.LogInformation("Enabling GitHub skill.");
            BearerAuthenticationProvider authenticationProvider = new(() => Task.FromResult(openApiSkillsAuthHeaders.GithubAuthentication));
            await planner.Kernel.ImportOpenApiSkillFromFileAsync(
                skillName: "GitHubSkill",
                filePath: Path.Combine(Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location)!, "Skills/OpenApiSkills/GitHubSkill/openapi.json"),
                authCallback: authenticationProvider.AuthenticateRequestAsync);
        }

        // Jira
        if (!string.IsNullOrWhiteSpace(openApiSkillsAuthHeaders.JiraAuthentication))
        {
            this._logger.LogInformation("Registering Jira Skill");
            var authenticationProvider = new BasicAuthenticationProvider(() => { return Task.FromResult(openApiSkillsAuthHeaders.JiraAuthentication); });
            var hasServerUrlOverride = variables.Get("jira-server-url", out string serverUrlOverride);

            await planner.Kernel.ImportOpenApiSkillFromFileAsync(
                skillName: "JiraSkill",
                filePath: Path.Combine(Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location)!, "Skills/OpenApiSkills/JiraSkill/openapi.json"),
                authCallback: authenticationProvider.AuthenticateRequestAsync,
                serverUrlOverride: hasServerUrlOverride ? new Uri(serverUrlOverride) : null);
        }

        // Microsoft Graph
        if (!string.IsNullOrWhiteSpace(openApiSkillsAuthHeaders.GraphAuthentication))
        {
            this._logger.LogInformation("Enabling Microsoft Graph skill(s).");
            BearerAuthenticationProvider authenticationProvider = new(() => Task.FromResult(openApiSkillsAuthHeaders.GraphAuthentication));
            GraphServiceClient graphServiceClient = this.CreateGraphServiceClient(authenticationProvider.AuthenticateRequestAsync);

            planner.Kernel.ImportSkill(new TaskListSkill(new MicrosoftToDoConnector(graphServiceClient)), "todo");
            planner.Kernel.ImportSkill(new CalendarSkill(new OutlookCalendarConnector(graphServiceClient)), "calendar");
            planner.Kernel.ImportSkill(new EmailSkill(new OutlookMailConnector(graphServiceClient)), "email");
        }
    }

    /// <summary>
    /// Create a Microsoft Graph service client.
    /// </summary>
    /// <param name="authenticateRequestAsyncDelegate">The delegate to authenticate the request.</param>
    private GraphServiceClient CreateGraphServiceClient(AuthenticateRequestAsyncDelegate authenticateRequestAsyncDelegate)
    {
        MsGraphClientLoggingHandler graphLoggingHandler = new(this._logger);
        this._disposables.Add(graphLoggingHandler);

        IList<DelegatingHandler> graphMiddlewareHandlers =
            GraphClientFactory.CreateDefaultHandlers(new DelegateAuthenticationProvider(authenticateRequestAsyncDelegate));
        graphMiddlewareHandlers.Add(graphLoggingHandler);

        HttpClient graphHttpClient = GraphClientFactory.Create(graphMiddlewareHandlers);
        this._disposables.Add(graphHttpClient);

        GraphServiceClient graphServiceClient = new(graphHttpClient);
        return graphServiceClient;
    }

    /// <summary>
    /// Dispose of the object.
    /// </summary>
    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            foreach (IDisposable disposable in this._disposables)
            {
                disposable.Dispose();
            }
        }
    }

    /// <inheritdoc />
    public void Dispose()
    {
        // Do not change this code. Put cleanup code in 'Dispose(bool disposing)' method
        this.Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }
}

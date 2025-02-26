// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using System.Web;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.MsGraph.Connectors.CredentialManagers;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Microsoft.SemanticKernel.Plugins.OpenApi.Extensions;

namespace Plugins;
/// <summary>
/// These examples demonstrate how to use Copilot Agent plugins to call Microsoft Graph and NASA APIs.
/// Copilot Agent Plugins are created from the OpenAPI document and the manifest file.
/// The manifest file contains the API dependencies and their execution parameters.
/// The manifest file also contains the authentication information for the APIs, however this is not used by the extension method and MUST be setup separately at the moment, which the example demonstrates.
///
/// Important stages being demonstrated:
/// 1. Load Copilot Agent Plugins
/// 2. Configure authentication for the APIs
/// 3. Call functions from the loaded plugins
///
/// Running this test requires the following configuration in `dotnet\samples\Concepts\bin\Debug\net8.0\appsettings.Development.json`:
///
/// ```json
/// {
///  "MSGraph": {
///    "ClientId": "clientId",
///    "TenantId": "tenantId",
///    "Scopes": [
///      "Calendars.Read",
///      "Contacts.Read",
///      "Files.Read.All",
///      "Mail.Read",
///      "User.Read"
///    ],
///    "RedirectUri": "http://localhost"
///  }
/// }
///```
///
/// Replace the clientId and TenantId by your own values.
///
/// To create the application registration:
/// 1. Go to https://aad.portal.azure.com
/// 2. Select create a new application registration
/// 3. Select new public client (add the redirect URI).
/// 4. Navigate to API access, add the listed Microsoft Graph delegated scopes.
/// 5. Grant consent after adding the scopes.
///
/// During the first run, your browser will open to get the token.
///
/// </summary>
/// <param name="output">The output helper to use to the test can emit status information</param>
public class CopilotAgentBasedPlugins(ITestOutputHelper output) : BaseTest(output)
{
    private static readonly PromptExecutionSettings s_promptExecutionSettings = new()
    {
        FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(
                    options: new FunctionChoiceBehaviorOptions
                    {
                        AllowStrictSchemaAdherence = true
                    }
                )
    };
    public static readonly IEnumerable<object[]> s_parameters =
    [
        // function names are sanitized operationIds from the OpenAPI document
        ["MessagesPlugin", "me_ListMessages", new KernelArguments(s_promptExecutionSettings) { { "_top", "1" } }, "MessagesPlugin"],
        ["DriveItemPlugin", "drives_GetItemsContent", new KernelArguments(s_promptExecutionSettings) { { "driveItem-Id", "test.txt" } }, "DriveItemPlugin", "MessagesPlugin"],
        ["ContactsPlugin", "me_ListContacts", new KernelArguments(s_promptExecutionSettings) { { "_count", "true" } }, "ContactsPlugin", "MessagesPlugin"],
        ["CalendarPlugin", "me_calendar_ListEvents", new KernelArguments(s_promptExecutionSettings) { { "_top", "1" } }, "CalendarPlugin", "MessagesPlugin"],

        // Multiple API dependencies (multiple auth requirements) scenario within the same plugin
        // Graph API uses MSAL
        ["AstronomyPlugin", "me_ListMessages", new KernelArguments(s_promptExecutionSettings) { { "_top", "1" } }, "AstronomyPlugin"],
        // Astronomy API uses API key authentication
        ["AstronomyPlugin", "apod", new KernelArguments(s_promptExecutionSettings) { { "_date", "2022-02-02" } }, "AstronomyPlugin"],
    ];
    [Theory, MemberData(nameof(s_parameters))]
    public async Task RunCopilotAgentPluginAsync(string pluginToTest, string functionToTest, KernelArguments? arguments, params string[] pluginsToLoad)
    {
        WriteSampleHeadingToConsole(pluginToTest, functionToTest, arguments, pluginsToLoad);
        var kernel = new Kernel();
        await AddCopilotAgentPluginsAsync(kernel, pluginsToLoad);

        var result = await kernel.InvokeAsync(pluginToTest, functionToTest, arguments);
        Console.WriteLine("--------------------");
        Console.WriteLine($"\nResult:\n{result}\n");
        Console.WriteLine("--------------------");
    }

    private void WriteSampleHeadingToConsole(string pluginToTest, string functionToTest, KernelArguments? arguments, params string[] pluginsToLoad)
    {
        Console.WriteLine();
        Console.WriteLine("======== [CopilotAgent Plugins Sample] ========");
        Console.WriteLine($"======== Loading Plugins: {string.Join(" ", pluginsToLoad)} ========");
        Console.WriteLine($"======== Calling Plugin Function: {pluginToTest}.{functionToTest} with parameters {arguments?.Select(x => x.Key + " = " + x.Value).Aggregate((x, y) => x + ", " + y)} ========");
        Console.WriteLine();
    }
    private static readonly HashSet<string> s_fieldsToIgnore = new(
        [
            "@odata.type",
            "attachments",
            "allowNewTimeProposals",
            "bccRecipients",
            "bodyPreview",
            "calendar",
            "categories",
            "ccRecipients",
            "changeKey",
            "conversationId",
            "coordinates",
            "conversationIndex",
            "createdDateTime",
            "discriminator",
            "lastModifiedDateTime",
            "locations",
            "extensions",
            "flag",
            "from",
            "hasAttachments",
            "iCalUId",
            "id",
            "inferenceClassification",
            "internetMessageHeaders",
            "instances",
            "isCancelled",
            "isDeliveryReceiptRequested",
            "isDraft",
            "isOrganizer",
            "isRead",
            "isReadReceiptRequested",
            "multiValueExtendedProperties",
            "onlineMeeting",
            "onlineMeetingProvider",
            "onlineMeetingUrl",
            "organizer",
            "originalStart",
            "parentFolderId",
            "range",
            "receivedDateTime",
            "recurrence",
            "replyTo",
            "sender",
            "sentDateTime",
            "seriesMasterId",
            "singleValueExtendedProperties",
            "transactionId",
            "time",
            "uniqueBody",
            "uniqueId",
            "uniqueIdType",
            "webLink",
        ],
        StringComparer.OrdinalIgnoreCase
    );
    private const string RequiredPropertyName = "required";
    private const string PropertiesPropertyName = "properties";
    /// <summary>
    /// Trims the properties from the request body schema.
    /// Most models in strict mode enforce a limit on the properties.
    /// </summary>
    /// <param name="schema">Source schema</param>
    /// <returns>the trimmed schema for the request body</returns>
    private static KernelJsonSchema? TrimPropertiesFromRequestBody(KernelJsonSchema? schema)
    {
        if (schema is null)
        {
            return null;
        }

        var originalSchema = JsonSerializer.Serialize(schema.RootElement);
        var node = JsonNode.Parse(originalSchema);
        if (node is not JsonObject jsonNode)
        {
            return schema;
        }

        TrimPropertiesFromJsonNode(jsonNode);

        return KernelJsonSchema.Parse(node.ToString());
    }
    private static void TrimPropertiesFromJsonNode(JsonNode jsonNode)
    {
        if (jsonNode is not JsonObject jsonObject)
        {
            return;
        }
        if (jsonObject.TryGetPropertyValue(RequiredPropertyName, out var requiredRawValue) && requiredRawValue is JsonArray requiredArray)
        {
            jsonNode[RequiredPropertyName] = new JsonArray(requiredArray.Where(x => x is not null).Select(x => x!.GetValue<string>()).Where(x => !s_fieldsToIgnore.Contains(x)).Select(x => JsonValue.Create(x)).ToArray());
        }
        if (jsonObject.TryGetPropertyValue(PropertiesPropertyName, out var propertiesRawValue) && propertiesRawValue is JsonObject propertiesObject)
        {
            var properties = propertiesObject.Where(x => s_fieldsToIgnore.Contains(x.Key)).Select(static x => x.Key).ToArray();
            foreach (var property in properties)
            {
                propertiesObject.Remove(property);
            }
        }
        foreach (var subProperty in jsonObject)
        {
            if (subProperty.Value is not null)
            {
                TrimPropertiesFromJsonNode(subProperty.Value);
            }
        }
    }
    private static readonly RestApiParameterFilter s_restApiParameterFilter = (RestApiParameterFilterContext context) =>
    {
        if (("me_sendMail".Equals(context.Operation.Id, StringComparison.OrdinalIgnoreCase) ||
            ("me_calendar_CreateEvents".Equals(context.Operation.Id, StringComparison.OrdinalIgnoreCase)) &&
            "payload".Equals(context.Parameter.Name, StringComparison.OrdinalIgnoreCase)))
        {
            context.Parameter.Schema = TrimPropertiesFromRequestBody(context.Parameter.Schema);
            return context.Parameter;
        }
        return context.Parameter;
    };
    internal static async Task<CopilotAgentPluginParameters> GetAuthenticationParametersAsync()
    {
        if (TestConfiguration.MSGraph.Scopes is null)
        {
            throw new InvalidOperationException("Missing Scopes configuration for Microsoft Graph API.");
        }

        LocalUserMSALCredentialManager credentialManager = await LocalUserMSALCredentialManager.CreateAsync().ConfigureAwait(false);

        var token = await credentialManager.GetTokenAsync(
                        TestConfiguration.MSGraph.ClientId,
                        TestConfiguration.MSGraph.TenantId,
                        TestConfiguration.MSGraph.Scopes.ToArray(),
                        TestConfiguration.MSGraph.RedirectUri).ConfigureAwait(false);
#pragma warning restore SKEXP0050

        BearerAuthenticationProviderWithCancellationToken authenticationProvider = new(() => Task.FromResult(token));
#pragma warning disable SKEXP0040

        // Microsoft Graph API execution parameters
        var graphOpenApiFunctionExecutionParameters = new OpenApiFunctionExecutionParameters(
            authCallback: authenticationProvider.AuthenticateRequestAsync,
            serverUrlOverride: new Uri("https://graph.microsoft.com/v1.0"),
            enableDynamicOperationPayload: false,
            enablePayloadNamespacing: false)
        {
            ParameterFilter = s_restApiParameterFilter
        };

        // NASA API execution parameters
        var nasaOpenApiFunctionExecutionParameters = new OpenApiFunctionExecutionParameters(
            authCallback: async (request, cancellationToken) =>
            {
                var uriBuilder = new UriBuilder(request.RequestUri ?? throw new InvalidOperationException("The request URI is null."));
                var query = HttpUtility.ParseQueryString(uriBuilder.Query);
                query["api_key"] = "DEMO_KEY";
                uriBuilder.Query = query.ToString();
                request.RequestUri = uriBuilder.Uri;
            },
            enableDynamicOperationPayload: false,
            enablePayloadNamespacing: false);

        var apiManifestPluginParameters = new CopilotAgentPluginParameters
        {
            FunctionExecutionParameters = new()
            {
                { "https://graph.microsoft.com/v1.0", graphOpenApiFunctionExecutionParameters },
                { "https://api.nasa.gov/planetary", nasaOpenApiFunctionExecutionParameters }
            }
        };
        return apiManifestPluginParameters;
    }
    private async Task AddCopilotAgentPluginsAsync(Kernel kernel, params string[] pluginNames)
    {
#pragma warning disable SKEXP0050
        var apiManifestPluginParameters = await GetAuthenticationParametersAsync().ConfigureAwait(false);
        var manifestLookupDirectory = Path.Combine(Directory.GetCurrentDirectory(), "..", "..", "..", "Resources", "Plugins", "CopilotAgentPlugins");

        foreach (var pluginName in pluginNames)
        {
            try
            {
#pragma warning disable CA1308 // Normalize strings to uppercase
                await kernel.ImportPluginFromCopilotAgentPluginAsync(
                    pluginName,
                    Path.Combine(manifestLookupDirectory, pluginName, $"{pluginName[..^6].ToLowerInvariant()}-apiplugin.json"),
                    apiManifestPluginParameters)
                    .ConfigureAwait(false);
#pragma warning restore CA1308 // Normalize strings to uppercase
                Console.WriteLine($">> {pluginName} is created.");
#pragma warning restore SKEXP0040
            }
            catch (Exception ex)
            {
                Console.WriteLine("Plugin creation failed. Message: {0}", ex.Message);
                throw new AggregateException($"Plugin creation failed for {pluginName}", ex);
            }
        }
    }
}

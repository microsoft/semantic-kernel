// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using Microsoft.Extensions.Configuration;

public sealed class TestConfiguration
{
    private readonly IConfigurationRoot _configRoot;
    private static TestConfiguration? s_instance;

    private TestConfiguration(IConfigurationRoot configRoot)
    {
        this._configRoot = configRoot;
    }

    public static void Initialize(IConfigurationRoot configRoot)
    {
        s_instance = new TestConfiguration(configRoot);
    }

    public static IConfigurationRoot? ConfigurationRoot => s_instance?._configRoot;
    public static OllamaConfig Ollama => LoadSection<OllamaConfig>();
    public static OpenAIConfig OpenAI => LoadSection<OpenAIConfig>();
    public static OnnxConfig Onnx => LoadSection<OnnxConfig>();
    public static AzureOpenAIConfig AzureOpenAI => LoadSection<AzureOpenAIConfig>();
    public static AzureAIInferenceConfig AzureAIInference => LoadSection<AzureAIInferenceConfig>();
    public static AzureAIConfig AzureAI => LoadSection<AzureAIConfig>();
    public static AzureOpenAIConfig AzureOpenAIImages => LoadSection<AzureOpenAIConfig>();
    public static AzureOpenAIEmbeddingsConfig AzureOpenAIEmbeddings => LoadSection<AzureOpenAIEmbeddingsConfig>();
    public static AzureAISearchConfig AzureAISearch => LoadSection<AzureAISearchConfig>();
    public static QdrantConfig Qdrant => LoadSection<QdrantConfig>();
    public static WeaviateConfig Weaviate => LoadSection<WeaviateConfig>();
    public static KeyVaultConfig KeyVault => LoadSection<KeyVaultConfig>();
    public static HuggingFaceConfig HuggingFace => LoadSection<HuggingFaceConfig>();
    public static PineconeConfig Pinecone => LoadSection<PineconeConfig>();
    public static BingConfig Bing => LoadSection<BingConfig>();
    public static GoogleConfig Google => LoadSection<GoogleConfig>();
    public static TavilyConfig Tavily => LoadSection<TavilyConfig>();
    public static GithubConfig Github => LoadSection<GithubConfig>();
    public static PostgresConfig Postgres => LoadSection<PostgresConfig>();
    public static RedisConfig Redis => LoadSection<RedisConfig>();
    public static JiraConfig Jira => LoadSection<JiraConfig>();
    public static ChromaConfig Chroma => LoadSection<ChromaConfig>();
    public static KustoConfig Kusto => LoadSection<KustoConfig>();
    public static MongoDBConfig MongoDB => LoadSection<MongoDBConfig>();
    public static ChatGPTRetrievalPluginConfig ChatGPTRetrievalPlugin => LoadSection<ChatGPTRetrievalPluginConfig>();
    public static MsGraphConfiguration MSGraph => LoadSection<MsGraphConfiguration>();
    public static MistralAIConfig MistralAI => LoadSection<MistralAIConfig>();
    public static GoogleAIConfig GoogleAI => LoadSection<GoogleAIConfig>();
    public static VertexAIConfig VertexAI => LoadSection<VertexAIConfig>();
    public static AzureCosmosDbMongoDbConfig AzureCosmosDbMongoDb => LoadSection<AzureCosmosDbMongoDbConfig>();
    public static ApplicationInsightsConfig ApplicationInsights => LoadSection<ApplicationInsightsConfig>();
    public static CrewAIConfig CrewAI => LoadSection<CrewAIConfig>();
    public static BedrockAgentConfig BedrockAgent => LoadSection<BedrockAgentConfig>();

    public static IConfiguration GetSection(string caller)
    {
        return s_instance?._configRoot.GetSection(caller) ??
               throw new ConfigurationNotFoundException(section: caller);
    }

    private static T LoadSection<T>([CallerMemberName] string? caller = null)
    {
        if (s_instance is null)
        {
            throw new InvalidOperationException(
                "TestConfiguration must be initialized with a call to Initialize(IConfigurationRoot) before accessing configuration values.");
        }

        if (string.IsNullOrEmpty(caller))
        {
            throw new ArgumentNullException(nameof(caller));
        }

        return s_instance._configRoot.GetSection(caller).Get<T>() ??
               throw new ConfigurationNotFoundException(section: caller);
    }

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor.
    public class OpenAIConfig
    {
        public string ModelId { get; set; }
        public string ChatModelId { get; set; }
        public string EmbeddingModelId { get; set; }
        public string ApiKey { get; set; }
    }

    public class AzureAIInferenceConfig
    {
        public string ServiceId { get; set; }
        public string Endpoint { get; set; }
        public string? ApiKey { get; set; }
        public string ChatModelId { get; set; }
    }

    public class OnnxConfig
    {
        public string ModelId { get; set; }
        public string ModelPath { get; set; }
        public string EmbeddingModelId { get; set; }
        public string EmbeddingModelPath { get; set; }
        public string EmbeddingVocabPath { get; set; }
    }

    public class AzureAIConfig
    {
        public string ConnectionString { get; set; }
        public string ChatModelId { get; set; }
        public string BingConnectionId { get; set; }
        public string VectorStoreId { get; set; }
        public string AgentId { get; set; }
    }

    public class AzureOpenAIConfig
    {
        public string ServiceId { get; set; }
        public string DeploymentName { get; set; }
        public string ModelId { get; set; }
        public string ChatDeploymentName { get; set; }
        public string ChatModelId { get; set; }
        public string ImageDeploymentName { get; set; }
        public string ImageModelId { get; set; }
        public string ImageEndpoint { get; set; }
        public string Endpoint { get; set; }
        public string ApiKey { get; set; }
        public string ImageApiKey { get; set; }
        public string AgentId { get; set; }
    }

    public class AzureOpenAIEmbeddingsConfig
    {
        public string DeploymentName { get; set; }
        public string Endpoint { get; set; }
        public string ApiKey { get; set; }
    }

    public class AzureAISearchConfig
    {
        public string Endpoint { get; set; }
        public string ApiKey { get; set; }
        public string IndexName { get; set; }
    }

    public class QdrantConfig
    {
        public string Endpoint { get; set; }
        public string Port { get; set; }
    }

    public class WeaviateConfig
    {
        public string Scheme { get; set; }
        public string Endpoint { get; set; }
        public string Port { get; set; }
        public string ApiKey { get; set; }
    }

    public class KeyVaultConfig
    {
        public string Endpoint { get; set; }
        public string ClientId { get; set; }
        public string ClientSecret { get; set; }
    }

    public class HuggingFaceConfig
    {
        public string ApiKey { get; set; }
        public string ModelId { get; set; }
        public string EmbeddingModelId { get; set; }
    }

    public class PineconeConfig
    {
        public string ApiKey { get; set; }
        public string Environment { get; set; }
    }

    public class BingConfig
    {
        public string Endpoint { get; set; } = "https://api.bing.microsoft.com/v7.0/search";
        public string ApiKey { get; set; }
    }

    public class GoogleConfig
    {
        public string ApiKey { get; set; }
        public string SearchEngineId { get; set; }
    }

    public class TavilyConfig
    {
        public string Endpoint { get; set; } = "https://api.tavily.com/search";
        public string ApiKey { get; set; }
    }

    public class GithubConfig
    {
        public string PAT { get; set; }
    }

    public class PostgresConfig
    {
        public string ConnectionString { get; set; }
    }

    public class RedisConfig
    {
        public string Configuration { get; set; }
    }

    public class JiraConfig
    {
        public string ApiKey { get; set; }
        public string Email { get; set; }
        public string Domain { get; set; }
    }

    public class ChromaConfig
    {
        public string Endpoint { get; set; }
    }

    public class KustoConfig
    {
        public string ConnectionString { get; set; }
    }

    public class MongoDBConfig
    {
        public string ConnectionString { get; set; }
    }

    public class ChatGPTRetrievalPluginConfig
    {
        public string Token { get; set; }
    }

    public class MistralAIConfig
    {
        public string ApiKey { get; set; }
        public string ChatModelId { get; set; }
        public string EmbeddingModelId { get; set; }
        public string ImageModelId { get; set; }
    }

    public class GoogleAIConfig
    {
        public string ApiKey { get; set; }
        public string EmbeddingModelId { get; set; }
        public GeminiConfig Gemini { get; set; }

        public class GeminiConfig
        {
            public string ModelId { get; set; }
        }
    }

    public class VertexAIConfig
    {
        public string? BearerKey { get; set; }
        public string EmbeddingModelId { get; set; }
        public string Location { get; set; }
        public string ProjectId { get; set; }
        public string? ClientId { get; set; }
        public string? ClientSecret { get; set; }
        public GeminiConfig Gemini { get; set; }

        public class GeminiConfig
        {
            public string ModelId { get; set; }
        }
    }

    public class OllamaConfig
    {
        public string? ModelId { get; set; }
        public string? EmbeddingModelId { get; set; }

        public string Endpoint { get; set; } = "http://localhost:11434";
    }

    public class AzureCosmosDbMongoDbConfig
    {
        public string ConnectionString { get; set; }
        public string DatabaseName { get; set; }
    }

    public class ApplicationInsightsConfig
    {
        public string ConnectionString { get; set; }
    }

    /// <summary>
    /// Graph API connector configuration model.
    /// </summary>
    public class MsGraphConfiguration
    {
        /// <summary>
        /// Gets or sets the client ID.
        /// </summary>
        public string ClientId { get; }

        /// <summary>
        /// Gets or sets the tenant/directory ID.
        /// </summary>
        public string TenantId { get; }

        /// <summary>
        /// Gets or sets the API permission scopes.
        /// </summary>
        /// <remarks>
        /// Keeping this parameters nullable and out of the constructor is a workaround for
        /// nested types not working with IConfigurationSection.Get.
        /// See https://github.com/dotnet/runtime/issues/77677
        /// </remarks>
        public IEnumerable<string> Scopes { get; set; } = [];

        /// <summary>
        /// Gets or sets the redirect URI to use.
        /// </summary>
        public Uri RedirectUri { get; }

        /// <summary>
        /// Initializes a new instance of the <see cref="MsGraphConfiguration"/> class.
        /// </summary>
        /// <param name="clientId">The client id.</param>
        /// <param name="tenantId">The tenant id.</param>
        /// <param name="redirectUri">The redirect URI.</param>
        public MsGraphConfiguration(
            [NotNull] string clientId,
            [NotNull] string tenantId,
            [NotNull] Uri redirectUri)
        {
            this.ClientId = clientId;
            this.TenantId = tenantId;
            this.RedirectUri = redirectUri;
        }
    }

    public class CrewAIConfig
    {
        public string Endpoint { get; set; }
        public string AuthToken { get; set; }
    }

    public class BedrockAgentConfig
    {
        public string AgentResourceRoleArn { get; set; }
        public string FoundationModel { get; set; }
        public string? KnowledgeBaseId { get; set; }
    }
}

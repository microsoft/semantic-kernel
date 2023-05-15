// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.ai.embeddings.EmbeddingGeneration;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.textcompletion.TextCompletion;

import java.util.*;
import java.util.function.Function;

import javax.annotation.Nullable;

public class KernelConfig {

    @Nullable private final String defaultTextCompletionServiceId;
    private final Map<String, Function<Kernel, TextCompletion>> textCompletionServices;
    @Nullable private final String defaultTextEmbeddingGenerationServiceId;

    private final Map<String, Function<Kernel, EmbeddingGeneration<String, Double>>>
            textEmbeddingGenerationServices;
    private final ArrayList<SKFunction<?, ?>> skills;

    public KernelConfig(
            @Nullable String defaultTextCompletionServiceId,
            Map<String, Function<Kernel, TextCompletion>> textCompletionServices,
            @Nullable String defaultTextEmbeddingGenerationServiceId,
            Map<String, Function<Kernel, EmbeddingGeneration<String, Double>>>
                    textEmbeddingGenerationServices,
            List<SKFunction<?, ?>> skills) {
        this.defaultTextCompletionServiceId = defaultTextCompletionServiceId;
        this.textCompletionServices = new HashMap<>();
        this.textCompletionServices.putAll(textCompletionServices);
        this.defaultTextEmbeddingGenerationServiceId = defaultTextEmbeddingGenerationServiceId;
        this.textEmbeddingGenerationServices = new HashMap<>(textEmbeddingGenerationServices);
        this.skills = new ArrayList<>(skills);
    }

    @Nullable
    public Function<Kernel, TextCompletion> getTextCompletionServices(String name) {
        return textCompletionServices.get(name);
    }

    public List<SKFunction<?, ?>> getSkills() {
        return Collections.unmodifiableList(skills);
    }

    public static class Builder {
        @Nullable private String defaultTextCompletionServiceId = null;
        private Map<String, Function<Kernel, TextCompletion>> textCompletionServices =
                new HashMap<>();
        @Nullable private String defaultTextEmbeddingGenerationServiceId = null;

        private List<SKFunction<?, ?>> skillBuilders = new ArrayList<>();

        private Map<String, Function<Kernel, EmbeddingGeneration<String, Double>>>
                textEmbeddingGenerationServices = new HashMap<>();

        public Builder addSkill(SKFunction<?, ?> functionDefinition) {
            skillBuilders.add(functionDefinition);
            return this;
        }

        // TODO, is there a need for this to be a factory?
        public Builder addTextCompletionService(
                String serviceId, Function<Kernel, TextCompletion> serviceFactory) {
            if (serviceId == null || serviceId.isEmpty()) {
                throw new IllegalArgumentException("Null or empty serviceId");
            }

            textCompletionServices.put(serviceId, serviceFactory);

            if (defaultTextCompletionServiceId == null) {
                defaultTextCompletionServiceId = serviceId;
            }
            return this;
        }

        //    public KernelConfig addTextEmbeddingGenerationService(
        //        String serviceId, Function<Kernel, EmbeddingGeneration<String, Float>>
        // serviceFactory,
        // boolean overwrite) {
        //      //Verify.NotEmpty(serviceId, "The service id provided is empty");
        //      this.textEmbeddingGenerationServices.put(serviceId, serviceFactory);
        //      if (this.textEmbeddingGenerationServices.size() == 1) {
        //        this.defaultTextEmbeddingGenerationServiceId = serviceId;
        //      }
        //
        //      return this;
        //    }

        public Builder addTextEmbeddingsGenerationService(
                String serviceId,
                Function<Kernel, EmbeddingGeneration<String, Double>> serviceFactory) {
            if (serviceId == null || serviceId.isEmpty()) {
                throw new IllegalArgumentException("Null or empty serviceId");
            }

            textEmbeddingGenerationServices.put(serviceId, serviceFactory);

            if (defaultTextCompletionServiceId == null) {
                defaultTextCompletionServiceId = serviceId;
            }
            return this;
        }

        public Builder setDefaultTextCompletionService(String serviceId) {
            this.defaultTextCompletionServiceId = serviceId;
            return this;
        }

        public KernelConfig build() {
            return new KernelConfig(
                    defaultTextCompletionServiceId,
                    Collections.unmodifiableMap(textCompletionServices),
                    defaultTextEmbeddingGenerationServiceId,
                    textEmbeddingGenerationServices,
                    skillBuilders);
        }
    }

    /*
            TODO:

            /// <summary>
            /// Factory for creating HTTP handlers.
            /// </summary>
            public IDelegatingHandlerFactory HttpHandlerFactory { get; private set; } = new DefaultHttpRetryHandlerFactory(new HttpRetryConfig());

            /// <summary>
            /// Default HTTP retry configuration for built-in HTTP handler factory.
            /// </summary>
            public HttpRetryConfig DefaultHttpRetryConfig { get; private set; } = new();

            /// <summary>
            /// Text completion service factories
            /// </summary>
            public Dictionary<string, Func<IKernel, ITextCompletion>> TextCompletionServices { get; } = new();

            /// <summary
            /// Chat completion service factories
            /// </summary>
            public Dictionary<string, Func<IKernel, IChatCompletion>> ChatCompletionServices { get; } = new();
    */
    /// <summary>
    /// Text embedding generation service factories
    /// </summary>
    // private Map<String, Function<Kernel, EmbeddingGeneration<String, Float>>>
    // textEmbeddingGenerationServices = new HashMap<>();
    /*
    /// <summary>
    /// Image generation service factories
    /// </summary>
    public Dictionary<string, Func<IKernel, IImageGeneration>> ImageGenerationServices { get; } = new();

    /// <summary>
    /// Default text completion service.
    /// </summary>
    public string? DefaultTextCompletionServiceId { get; private set; }

    /// <summary>
    /// Default chat completion service.
    /// </summary>
    public string? DefaultChatCompletionServiceId { get; private set; }

    /// <summary>
    /// Default text embedding generation service.
    /// </summary>
    */
    // private String defaultTextEmbeddingGenerationServiceId;
    /*
            /// <summary>
            /// Default image generation service.
            /// </summary>
            public string? DefaultImageGenerationServiceId { get; private set; }

            /// <summary>
            /// Get all text completion services.
            /// </summary>
            /// <returns>IEnumerable of all completion service Ids in the kernel configuration.</returns>
            public IEnumerable<string> AllTextCompletionServiceIds => this.TextCompletionServices.Keys;

            /// <summary>
            /// Get all chat completion services.
            /// </summary>
            /// <returns>IEnumerable of all completion service Ids in the kernel configuration.</returns>
            public IEnumerable<string> AllChatCompletionServiceIds => this.ChatCompletionServices.Keys;

            /// <summary>
            /// Get all text embedding generation services.
            /// </summary>
            /// <returns>IEnumerable of all embedding service Ids in the kernel configuration.</returns>
            public IEnumerable<string> AllTextEmbeddingGenerationServiceIds => this.TextEmbeddingGenerationServices.Keys;
    */
    /// <summary>
    /// Add to the list a service for text completion, e.g. Azure OpenAI Text Completion.
    /// </summary>
    /// <param name="serviceId">Id used to identify the service</param>
    /// <param name="serviceFactory">Function used to instantiate the service object</param>
    /// <returns>Current object instance</returns>
    /// <exception cref="KernelException">Failure if a service with the same id already
    // exists</exception>

    /*
                /// <summary>
                /// Add to the list a service for chat completion, e.g. OpenAI ChatGPT.
                /// </summary>
                /// <param name="serviceId">Id used to identify the service</param>
                /// <param name="serviceFactory">Function used to instantiate the service object</param>
                /// <returns>Current object instance</returns>
                /// <exception cref="KernelException">Failure if a service with the same id already exists</exception>
                public KernelConfig AddChatCompletionService(
                    string serviceId, Func<IKernel, IChatCompletion> serviceFactory)
                {
                    Verify.NotEmpty(serviceId, "The service id provided is empty");
                    this.ChatCompletionServices[serviceId] = serviceFactory;
                    if (this.ChatCompletionServices.Count == 1)
                    {
                        this.DefaultChatCompletionServiceId = serviceId;
                    }

                    return this;
                }
    */
    /// <summary>
    /// Add to the list a service for text embedding generation, e.g. Azure OpenAI Text Embedding.
    /// </summary>
    /// <param name="serviceId">Id used to identify the service</param>
    /// <param name="serviceFactory">Function used to instantiate the service object</param>
    /// <param name="overwrite">Whether to overwrite a service having the same id</param>
    /// <returns>Current object instance</returns>
    /// <exception cref="KernelException">Failure if a service with the same id already
    // exists</exception>
    /*
    public KernelConfig addTextEmbeddingGenerationService(
            String serviceId, Function<Kernel, EmbeddingGeneration<String, Float>> serviceFactory, boolean overwrite) {
        //Verify.NotEmpty(serviceId, "The service id provided is empty");
        this.textEmbeddingGenerationServices.put(serviceId, serviceFactory);
        if (this.textEmbeddingGenerationServices.size() == 1) {
            this.defaultTextEmbeddingGenerationServiceId = serviceId;
        }

        return this;
    }


                /// <summary>
                /// Add to the list a service for text embedding generation, e.g. Azure OpenAI Text Embedding.
                /// </summary>
                /// <param name="serviceId">Id used to identify the service</param>
                /// <param name="serviceFactory">Function used to instantiate the service object</param>
                /// <param name="overwrite">Whether to overwrite a service having the same id</param>
                /// <returns>Current object instance</returns>
                /// <exception cref="KernelException">Failure if a service with the same id already exists</exception>
                public KernelConfig AddTextEmbeddingGenerationService(
                    string serviceId, Func<IKernel, IEmbeddingGeneration<string, float>> serviceFactory, bool overwrite = false)
                {
                    Verify.NotEmpty(serviceId, "The service id provided is empty");
                    this.TextEmbeddingGenerationServices[serviceId] = serviceFactory;
                    if (this.TextEmbeddingGenerationServices.Count == 1)
                    {
                        this.DefaultTextEmbeddingGenerationServiceId = serviceId;
                    }

                    return this;
                }

                /// <summary>
                /// Add to the list a service for image generation, e.g. OpenAI DallE.
                /// </summary>
                /// <param name="serviceId">Id used to identify the service</param>
                /// <param name="serviceFactory">Function used to instantiate the service object</param>
                /// <returns>Current object instance</returns>
                /// <exception cref="KernelException">Failure if a service with the same id already exists</exception>
                public KernelConfig AddImageGenerationService(
                    string serviceId, Func<IKernel, IImageGeneration> serviceFactory)
                {
                    Verify.NotEmpty(serviceId, "The service id provided is empty");
                    this.ImageGenerationServices[serviceId] = serviceFactory;
                    if (this.ImageGenerationServices.Count == 1)
                    {
                        this.DefaultImageGenerationServiceId = serviceId;
                    }

                    return this;
                }

                #region Set

                /// <summary>
                /// Set the http retry handler factory to use for the kernel.
                /// </summary>
                /// <param name="httpHandlerFactory">Http retry handler factory to use.</param>
                /// <returns>The updated kernel configuration.</returns>
                public KernelConfig SetHttpRetryHandlerFactory(IDelegatingHandlerFactory? httpHandlerFactory = null)
                {
                    if (httpHandlerFactory != null)
                    {
                        this.HttpHandlerFactory = httpHandlerFactory;
                    }

                    return this;
                }

                public KernelConfig SetDefaultHttpRetryConfig(HttpRetryConfig? httpRetryConfig)
                {
                    if (httpRetryConfig != null)
                    {
                        this.DefaultHttpRetryConfig = httpRetryConfig;
                        this.SetHttpRetryHandlerFactory(new DefaultHttpRetryHandlerFactory(httpRetryConfig));
                    }

                    return this;
                }

                /// <summary>
                /// Set the default completion service to use for the kernel.
                /// </summary>
                /// <param name="serviceId">Identifier of completion service to use.</param>
                /// <returns>The updated kernel configuration.</returns>
                /// <exception cref="KernelException">Thrown if the requested service doesn't exist.</exception>
                public KernelConfig SetDefaultTextCompletionService(string serviceId)
                {
                    if (!this.TextCompletionServices.ContainsKey(serviceId))
                    {
                        throw new KernelException(
                            KernelException.ErrorCodes.ServiceNotFound,
                            $"A text completion service id '{serviceId}' doesn't exist");
                    }

                    this.DefaultTextCompletionServiceId = serviceId;
                    return this;
                }

                /// <summary>
                /// Set the default embedding service to use for the kernel.
                /// </summary>
                /// <param name="serviceId">Identifier of text embedding service to use.</param>
                /// <returns>The updated kernel configuration.</returns>
                /// <exception cref="KernelException">Thrown if the requested service doesn't exist.</exception>
                public KernelConfig SetDefaultTextEmbeddingGenerationService(string serviceId)
                {
                    if (!this.TextEmbeddingGenerationServices.ContainsKey(serviceId))
                    {
                        throw new KernelException(
                            KernelException.ErrorCodes.ServiceNotFound,
                            $"A text embedding generation service id '{serviceId}' doesn't exist");
                    }

                    this.DefaultTextEmbeddingGenerationServiceId = serviceId;
                    return this;
                }

                #endregion

                #region Get
        */
    /// <summary>
    /// Get the text completion service configuration matching the given id or the default if an id
    // is not provided or not found.
    /// </summary>
    /// <param name="serviceId">Optional identifier of the desired service.</param>
    /// <returns>The text completion service id matching the given id or the default.</returns>
    /// <exception cref="KernelException">Thrown when no suitable service is found.</exception>
    public String getTextCompletionServiceIdOrDefault(@Nullable String serviceId)
            throws KernelException {
        if (serviceId == null
                || serviceId.isEmpty()
                || !this.textCompletionServices.containsKey(serviceId)) {
            serviceId = this.defaultTextCompletionServiceId;
        }

        if (serviceId == null || serviceId.isEmpty()) {
            // TODO proper error
            throw new KernelException();
            // throw new KernelException(KernelException.ErrorCodes.ServiceNotFound, "Text
            // completion service not available");
        }

        return serviceId;
    }
    /*
        /// <summary>
        /// Get the chat completion service configuration matching the given id or the default if an id is not provided or not found.
        /// </summary>
        /// <param name="serviceId">Optional identifier of the desired service.</param>
        /// <returns>The completion service id matching the given id or the default.</returns>
        /// <exception cref="KernelException">Thrown when no suitable service is found.</exception>
        public string GetChatCompletionServiceIdOrDefault(string? serviceId = null)
        {
            if (serviceId.IsNullOrEmpty() || !this.ChatCompletionServices.ContainsKey(serviceId!))
            {
                serviceId = this.DefaultChatCompletionServiceId;
            }

            if (serviceId.IsNullOrEmpty()) // Explicit null check for netstandard2.0
            {
                throw new KernelException(KernelException.ErrorCodes.ServiceNotFound, "Chat completion service not available");
            }

            return serviceId;
        }

        /// <summary>
        /// Get the text embedding service configuration matching the given id or the default if an id is not provided or not found.
        /// </summary>
        /// <param name="serviceId">Optional identifier of the desired service.</param>
        /// <returns>The embedding service id matching the given id or the default.</returns>
        /// <exception cref="KernelException">Thrown when no suitable service is found.</exception>
        public string GetTextEmbeddingGenerationServiceIdOrDefault(string? serviceId = null)
        {
            if (serviceId.IsNullOrEmpty() || !this.TextEmbeddingGenerationServices.ContainsKey(serviceId!))
            {
                serviceId = this.DefaultTextEmbeddingGenerationServiceId;
            }

            if (serviceId.IsNullOrEmpty())
            {
                throw new KernelException(KernelException.ErrorCodes.ServiceNotFound, "Text embedding generation service not available");
            }

            return serviceId;
        }

        /// <summary>
        /// Get the image generation service id matching the given id or the default if an id is not provided or not found.
        /// </summary>
        /// <param name="serviceId">Optional identifier of the desired service.</param>
        /// <returns>The image generation service id matching the given id or the default.</returns>
        /// <exception cref="KernelException">Thrown when no suitable service is found.</exception>
        public string GetImageGenerationServiceIdOrDefault(string? serviceId = null)
        {
            if (serviceId.IsNullOrEmpty() || !this.ImageGenerationServices.ContainsKey(serviceId!))
            {
                serviceId = this.DefaultImageGenerationServiceId;
            }

            if (serviceId.IsNullOrEmpty())
            {
                throw new KernelException(KernelException.ErrorCodes.ServiceNotFound, "Image generation service not available");
            }

            return serviceId;
        }

        #endregion

        #region Remove

        /// <summary>
        /// Remove the text completion service with the given id.
        /// </summary>
        /// <param name="serviceId">Identifier of service to remove.</param>
        /// <returns>The updated kernel configuration.</returns>
        public KernelConfig RemoveTextCompletionService(string serviceId)
        {
            this.TextCompletionServices.Remove(serviceId);
            if (this.DefaultTextCompletionServiceId == serviceId)
            {
                this.DefaultTextCompletionServiceId = this.TextCompletionServices.Keys.FirstOrDefault();
            }

            return this;
        }

        /// <summary>
        /// Remove the chat completion service with the given id.
        /// </summary>
        /// <param name="serviceId">Identifier of service to remove.</param>
        /// <returns>The updated kernel configuration.</returns>
        public KernelConfig RemoveChatCompletionService(string serviceId)
        {
            this.ChatCompletionServices.Remove(serviceId);
            if (this.DefaultChatCompletionServiceId == serviceId)
            {
                this.DefaultChatCompletionServiceId = this.ChatCompletionServices.Keys.FirstOrDefault();
            }

            return this;
        }

        /// <summary>
        /// Remove the text embedding generation service with the given id.
        /// </summary>
        /// <param name="serviceId">Identifier of service to remove.</param>
        /// <returns>The updated kernel configuration.</returns>
        public KernelConfig RemoveTextEmbeddingGenerationService(string serviceId)
        {
            this.TextEmbeddingGenerationServices.Remove(serviceId);
            if (this.DefaultTextEmbeddingGenerationServiceId == serviceId)
            {
                this.DefaultTextEmbeddingGenerationServiceId = this.TextEmbeddingGenerationServices.Keys.FirstOrDefault();
            }

            return this;
        }

        /// <summary>
        /// Remove all text completion services.
        /// </summary>
        /// <returns>The updated kernel configuration.</returns>
        public KernelConfig RemoveAllTextCompletionServices()
        {
            this.TextCompletionServices.Clear();
            this.DefaultTextCompletionServiceId = null;
            return this;
        }

        /// <summary>
        /// Remove all chat completion services.
        /// </summary>
        /// <returns>The updated kernel configuration.</returns>
        public KernelConfig RemoveAllChatCompletionServices()
        {
            this.ChatCompletionServices.Clear();
            this.DefaultChatCompletionServiceId = null;
            return this;
        }

        /// <summary>
        /// Remove all text embedding generation services.
        /// </summary>
        /// <returns>The updated kernel configuration.</returns>
        public KernelConfig RemoveAllTextEmbeddingGenerationServices()
        {
            this.TextEmbeddingGenerationServices.Clear();
            this.DefaultTextEmbeddingGenerationServiceId = null;
            return this;
        }

        #endregion
    }

         */
}

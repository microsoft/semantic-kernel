// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.extensions;

import com.fasterxml.jackson.databind.JsonMappingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.KernelException;
import com.microsoft.semantickernel.KernelException.ErrorCodes;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.semanticfunctions.PromptConfig;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunctionConfig;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;
import com.microsoft.semantickernel.util.EmbeddedResourceLoader;
import com.microsoft.semantickernel.util.EmbeddedResourceLoader.ResourceLocation;
import java.io.File;
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.util.HashMap;
import java.util.Map;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class KernelExtensions {

    private static final Logger LOGGER = LoggerFactory.getLogger(KernelExtensions.class);

}

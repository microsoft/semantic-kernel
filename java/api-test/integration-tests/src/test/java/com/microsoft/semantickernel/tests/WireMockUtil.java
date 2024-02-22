// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.tests;

import com.github.tomakehurst.wiremock.client.WireMock;
import com.github.tomakehurst.wiremock.matching.RegexPattern;
import com.github.tomakehurst.wiremock.matching.UrlPathPattern;

public class WireMockUtil {

    public static void mockCompletionResponse(
        String regexMatcher,
        String response) {
        String body = """
            {
              "id": "1",
              "object": "text_completion",
              "created": 1589478378,
              "model": "text-davinci-003",
              "system_fingerprint": "fp_44709d6fb",
              "choices": [
                {
                  "text": "%s",
                  "index": 0,
                  "logprobs": null,
                  "finish_reason": "length"
                }
              ],
              "usage": {
                "prompt_tokens": 1,
                "completion_tokens": 2,
                "total_tokens": 3
              }
            }
            """
            .formatted(response);

        WireMock.reset();
        WireMock.stubFor(WireMock
            .post(new UrlPathPattern(
                new RegexPattern("/openai/deployments/text-davinci-003/completions"), true))
            .withRequestBody(WireMock.matching(".*" + regexMatcher + ".*"))
            .willReturn(WireMock.ok()
                .withBody(body)));
    }

    public static void mockChatCompletionResponse(
        String regexMatcher,
        String response) {
        String body = """
               {
               "choices" : [
                  {
                     "content_filter_results" : {
                        "hate" : {
                           "filtered" : false,
                           "severity" : "safe"
                        },
                        "self_harm" : {
                           "filtered" : false,
                           "severity" : "safe"
                        },
                        "sexual" : {
                           "filtered" : false,
                           "severity" : "safe"
                        },
                        "violence" : {
                           "filtered" : false,
                           "severity" : "safe"
                        }
                     },
                     "finish_reason" : "length",
                     "index" : 0,
                     "message" : {
                        "content" : "%s",
                        "role" : "assistant"
                     }
                  }
               ],
               "created" : 1707253019,
               "id" : "chatcmpl-xxx",
               "model" : "gpt-35-turbo",
               "object" : "chat.completion",
               "prompt_filter_results" : [
                  {
                     "content_filter_results" : {
                        "hate" : {
                           "filtered" : false,
                           "severity" : "safe"
                        },
                        "self_harm" : {
                           "filtered" : false,
                           "severity" : "safe"
                        },
                        "sexual" : {
                           "filtered" : false,
                           "severity" : "safe"
                        },
                        "violence" : {
                           "filtered" : false,
                           "severity" : "safe"
                        }
                     },
                     "prompt_index" : 0
                  }
               ],
               "usage" : {
                  "completion_tokens" : 256,
                  "prompt_tokens" : 69,
                  "total_tokens" : 325
               }
            }

                        """
            .formatted(response);

        WireMock.reset();
        WireMock.stubFor(WireMock
            .post(new UrlPathPattern(
                new RegexPattern("/openai/deployments/text-davinci-003/chat/completions"), true))
            .withRequestBody(WireMock.matching(".*" + regexMatcher + ".*"))
            .willReturn(WireMock.ok()
                .withBody(body)));
    }

}

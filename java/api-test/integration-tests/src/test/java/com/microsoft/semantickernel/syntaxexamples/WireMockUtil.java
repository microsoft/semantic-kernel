package com.microsoft.semantickernel.syntaxexamples;

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
                new RegexPattern("/openai/deployments/text-davinci-003/completions"), true)
            )
            .withRequestBody(WireMock.matching(".*" + regexMatcher + ".*"))
            .willReturn(WireMock.ok()
                .withBody(body)));
    }


}

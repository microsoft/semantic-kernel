
package plugins.searchplugin;

import com.azure.core.http.HttpClient;
import com.microsoft.semantickernel.plugin.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.plugin.annotations.KernelFunctionParameter;
import com.microsoft.semantickernel.plugins.web.bing.BingConnector;
import reactor.core.publisher.Mono;

public class Search {

    private final BingConnector _bingConnector;

    public Search(String apiKey) {
        this(apiKey, HttpClient.createDefault());
    }

    public Search(String apiKey, HttpClient httpClient)
    {
        this._bingConnector = new BingConnector(apiKey, httpClient);
    }

    @DefineKernelFunction(description="Searches Bing for the given query")
    public Mono<String> searchAsync(
        @KernelFunctionParameter(description="The search query", name="query", type=String.class) String query
    ){
        return Mono.empty();
    }

}

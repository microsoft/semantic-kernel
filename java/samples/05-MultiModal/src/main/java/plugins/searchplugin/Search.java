
package plugins.searchplugin;

import com.azure.core.http.HttpClient;
import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;
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

    @DefineSKFunction(description="Searches Bing for the given query")
    public Mono<String> searchAsync(
        @SKFunctionParameters(description="The search query", name="query", type=String.class) String query
    ){
        return Mono.empty();
    }

}

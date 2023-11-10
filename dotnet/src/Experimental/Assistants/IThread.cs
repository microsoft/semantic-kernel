using System.Collections.Generic;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

public interface IThread : ISKFunction
{
    public string Id { get; set; }
    public Task AddUserMessageAsync(string message);
    public Task AddMessageAsync(ModelMessage message);
    public Task<ModelMessage> RetrieveMessageAsync(string messageId);
    public Task<List<ModelMessage>> ListMessagesAsync();
}

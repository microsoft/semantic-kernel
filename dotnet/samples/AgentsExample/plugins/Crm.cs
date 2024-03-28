using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;

namespace Plugins;

public class Crm
{
    [KernelFunction("GetCustomerDetails")]
    [Description("Retrieves details about the current customer")]
    public async Task<Customer> GetCustomerDetailsAsync()
    {
        // Simulate getting customer details
        await Task.Delay(1000);

        // Return a sample customer
        return new Customer
        {
            Name = "Noa Ervello",
            Email = "noa.ervello@contoso.com",
            Phone = "425-555-1234",
            Address = "123 Main St, Redmond, WA 98052",
            Notes = """
                Noa is a long-time customer and is an avid gamer.
                They are interested in role-playing games that have a strong narrative.
            """
        };
    }
}

#pragma warning disable CS8618
public class Customer
{
    public string Name { get; set; }
    public string Email { get; set; }
    public string Phone { get; set; }
    public string Address { get; set; }
    public string Notes { get; set; }
}

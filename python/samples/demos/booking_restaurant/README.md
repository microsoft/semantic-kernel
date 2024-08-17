# Restaurant - Demo Application

This sample provides a practical demonstration of how to leverage features from the [Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel) to build a console application. Specifically, the application utilizes the [Business Schedule and Booking API](https://www.microsoft.com/en-us/microsoft-365/business/scheduling-and-booking-app) through Microsoft Graph to enable a Large Language Model (LLM) to book restaurant appointments efficiently. This guide will walk you through the necessary steps to integrate these technologies seamlessly.

## Prerequisites

- Python 3.10, 3.11, or 3.12.
- [Microsoft 365 Business License](https://www.microsoft.com/en-us/microsoft-365/business/compare-all-microsoft-365-business-products) to use [Business Schedule and Booking API](https://www.microsoft.com/en-us/microsoft-365/business/scheduling-and-booking-app).
- [Azure Entra Id](https://www.microsoft.com/en-us/security/business/identity-access/microsoft-entra-id) administrator account to register an application and set the necessary credentials and permissions.

### Function Calling Enabled Models

This sample uses function calling capable models and has been tested with the following models:

| Model type      | Model name/id             |       Model version | Supported |
| --------------- | ------------------------- | ------------------: | --------- |
| Chat Completion | gpt-3.5-turbo             |                0125 | ✅        |
| Chat Completion | gpt-3.5-turbo             |                1106 | ✅        |
| Chat Completion | gpt-3.5-turbo-0613        |                0613 | ✅        |
| Chat Completion | gpt-3.5-turbo-0301        |                0301 | ❌        |
| Chat Completion | gpt-3.5-turbo-16k         |                0613 | ✅        |
| Chat Completion | gpt-4                     |                0613 | ✅        |
| Chat Completion | gpt-4-0613                |                0613 | ✅        |
| Chat Completion | gpt-4-0314                |                0314 | ❌        |
| Chat Completion | gpt-4-turbo               |          2024-04-09 | ✅        |
| Chat Completion | gpt-4-turbo-2024-04-09    |          2024-04-09 | ✅        |
| Chat Completion | gpt-4-turbo-preview       |        0125-preview | ✅        |
| Chat Completion | gpt-4-0125-preview        |        0125-preview | ✅        |
| Chat Completion | gpt-4-vision-preview      | 1106-vision-preview | ✅        |
| Chat Completion | gpt-4-1106-vision-preview | 1106-vision-preview | ✅        |

ℹ️ OpenAI Models older than 0613 version do not support function calling.

ℹ️ When using Azure OpenAI, ensure that the model name of your deployment matches any of the above supported models names.

## Configuring the sample

Please make sure either your environment variables or your .env file contains the following:

- "BOOKING_SAMPLE_CLIENT_ID"
- "BOOKING_SAMPLE_TENANT_ID"
- "BOOKING_SAMPLE_CLIENT_SECRET"
- "BOOKING_SAMPLE_BUSINESS_ID"
- "BOOKING_SAMPLE_SERVICE_ID"

If wanting to use the `.env` file, you must pass the `env_file_path` parameter with a valid path:

```python
booking_sample_settings = BookingSampleSettings(env_file_path=env_file_path)
```

This will tell Pydantic settings to also load the `.env` file instead of just trying to load environment variables.

### Create an App Registration in Azure Active Directory

1. Go to the [Azure Portal](https://portal.azure.com/).
2. Select the Azure Active Directory service.
3. Select App registrations and click on New registration.
4. Fill in the required fields and click on Register.
5. Copy the Application **(client) Id** for later use.
6. Save Directory **(tenant) Id** for later use..
7. Click on Certificates & secrets and create a new client secret. (Any name and expiration date will work)
8. Copy the **client secret** value for later use.
9. Click on API permissions and add the following permissions:
   - Microsoft Graph
     - Application permissions
       - BookingsAppointment.ReadWrite.All
     - Delegated permissions
       - OpenId permissions
         - offline_access
         - profile
         - openid

### Create Or Use a Booking Service and Business

1. Go to the [Bookings Homepage](https://outlook.office.com/bookings) website.
2. Create a new Booking Page and add a Service to the Booking (Skip if you don't ).
3. Access [Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer)
4. Run the following query to get the Booking Business Id:
   ```http
   GET https://graph.microsoft.com/v1.0/solutions/bookingBusinesses
   ```
5. Copy the **Booking Business Id** for later use.
6. Run the following query and replace it with your **Booking Business Id** to get the Booking Service Id
   ```http
   GET https://graph.microsoft.com/v1.0/solutions/bookingBusinesses/{bookingBusiness-id}/services
   ```
7. Copy the **Booking Service Id** for later use.

## Running the sample

Either run the sample in an IDE, like VSCode, or via the command line.

### Example of a conversation

> **User** > Please book a restaurant for me.

> **Assistant** > Sure, I can help you with that. Could you please provide me with the following information:
>
> 1. Name of the restaurant you would like to book.
> 2. Date and time of the reservation.
> 3. Number of people in your party.
> 4. Your name.
> 5. Your email address.
> 6. Your phone number.
>
> Once I have all this information, I will proceed with the booking.

> **User** > I would like to book a table at the restaurant "The French Laundry" on the 15th of March at 7:00 PM for 4 people. My name is John Doe, my email address is john@internet.com, and my phone number is 123-456-7890.

> **System** > Do you want to book a table at The French Laundry on 15/03/2023 19:00:00 for 4 people?

> **System** > Please confirm by typing 'yes' or 'no'.

> **User** > yes

> **Assistant** > Great! I have successfully booked a table for you at "The French Laundry" on the 15th of March at 7:00 PM for 4 people.
>
> Your reservation has been made under the name John Doe.
>
> If you have any further questions or need to make any changes to your reservation, please let me know.

> **User** > List my current bookings

> **Assistant** > You currently have one booking:
>
> - Restaurant: The French Laundry
> - Date and Time: 15th of March at 7:00 PM
> - Party Size: 4 people
>
> If you need any further assistance or if there's anything else I can help you with, please let me know.

> **User** > Cancel my booking

> **System** > `[Cancelling a reservation for 4 at The French Laundry on 2023-03-15 at 19:00:00]`

> **Assistant** > I have successfully canceled your booking at "The French Laundry" on the 15th of March at 7:00 PM for 4 people.
>
> If you have any other questions or need further assistance, please let me know.

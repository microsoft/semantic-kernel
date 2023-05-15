namespace Experiments;

public class YourAppException : Exception
{
    public YourAppException() : base()
    {
    }

    public YourAppException(string message) : base(message)
    {
    }

    public YourAppException(string message, Exception innerException) : base(message, innerException)
    {
    }
}
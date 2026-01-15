# Native-AOT Tests
This test application is used to test the Semantic Kernel Native-AOT compatible API by publishing the application in a Native-AOT mode, analyzing the API using AOT compiler, and running the tests against the API.

## Running Tests
The test can be run either in a debug mode by just setting a break point and pressing `F5` in Visual Studio (make sure the `AotCompatibility.TestApp` project is set as the startup project) in 
which case they are run in a regular CoreCLR application and not in Native-AOT one. This might be useful to add additional tests or debug the existing ones.

To run the tests in a Native-AOT application, first publish it using the following command: `dotnet publish -r win-x64`. Then, execute the application by running the following command in the terminal: `.\bin\Release\net8.0\win-x64\publish\AotCompatibility.TestApp.exe`.  
   
Alternatively, the `.github\workflows\test-aot-compatibility.ps1` script can be used to publish the application and run the tests. Please ensure that this script is run in at least PowerShell 7.4. The script takes the version of the .NET Framework as an argument. For example, to run the tests with .NET 10.0, run the following command: `.github\workflows\test-aot-compatibility.ps1 10.0`.
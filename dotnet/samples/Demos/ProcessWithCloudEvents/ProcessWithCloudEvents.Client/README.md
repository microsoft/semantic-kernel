# React App for SK Process with Cloud Events
## Getting Started

Follow the steps below to set up, run, and debug the React app for SK Process with Cloud Events.

### Prerequisites

- Node.js (LTS version recommended)
- Yarn (package manager)

### Installation

1. Navigate to the project directory:
  ```bash
  cd <repo>/dotnet/samples/Demos/ProcessWithCloudEvents/ProcessWithCloudEvents.Client
  ```
2. Install the dependencies:
  ```bash
  yarn install
  ```

Alternatively, you can use the existing Visual Studio Code task:

1. Open the Command Palette in Visual Studio Code (`Ctrl+Shift+P` or `Cmd+Shift+P` on macOS).
2. Search for and select `Tasks: Run Task`.
3. Choose the `yarn: install` task from the list to install the dependencies.

### Running the Application

1. Ensure that the backend server is running.

2. Start the development server:
  ```bash
  yarn: run dev
  ```
  Alternatively, you can use the existing Visual Studio Code task `yarn: run dev`.

3. Open your browser and navigate to `http://localhost:5173` to view the app.

### Usage

1. Select cloud technology to be used.
2. Select SK Process to be used.
3. Interact with the UI to send events/messages to the backend. The UI will display any incoming events/messages from the backend.
4. Use the provided buttons/inputs to trigger specific actions or events as needed.

### Debugging

1. Run the application.
2. Start the app in debug mode:
  - If using Visual Studio Code, go to the "Run and Debug" panel and select `Launch Edge against localhost`.
3. Set breakpoints in your code to inspect and debug as needed.

For more details, refer to the official React documentation: [React Docs](https://reactjs.org/docs/getting-started.html).

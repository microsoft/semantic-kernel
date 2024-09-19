import { Terminal, TerminalProfile } from "vscode";
import { CloudShell, CloudShellStatus } from "../azure-account.api";


export interface CloudShellInternal extends Omit<CloudShell, 'terminal'> {
	status: CloudShellStatus;
	terminal?: Promise<Terminal>;
	terminalProfile?: Promise<TerminalProfile>;
}

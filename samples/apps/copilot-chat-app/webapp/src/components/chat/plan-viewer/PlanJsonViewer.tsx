// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Dialog,
    DialogActions,
    DialogBody,
    DialogContent,
    DialogSurface,
    DialogTitle,
    DialogTrigger,
    Link,
} from '@fluentui/react-components';
import React from 'react';
import { TokenUsages } from '../../../redux/features/app/AppState';
import { TokenUsage } from '../../shared/TokenUsage';

interface IPlanJsonViewerProps {
    goal: string;
    tokenUsage?: TokenUsages;
    json: string;
}

export const PlanJsonViewer: React.FC<IPlanJsonViewerProps> = ({ goal, tokenUsage, json }) => {
    return (
        <Dialog>
            <DialogTrigger disableButtonEnhancement>
                <Link>{goal}</Link>
            </DialogTrigger>
            <DialogSurface>
                <DialogBody>
                    <DialogTitle>Plan in Json format</DialogTitle>
                    <DialogContent>
                        <TokenUsage
                            promptUsage={tokenUsage?.prompt ?? 0}
                            dependencyUsage={tokenUsage?.dependency ?? 0}
                            planExecutionUsage={tokenUsage?.planExecution ?? 0}
                        />
                        <pre>
                            <code>{JSON.stringify(JSON.parse(json), null, 2)}</code>
                        </pre>
                    </DialogContent>
                    <DialogActions>
                        <DialogTrigger disableButtonEnhancement>
                            <Button appearance="secondary">Close</Button>
                        </DialogTrigger>
                    </DialogActions>
                </DialogBody>
            </DialogSurface>
        </Dialog>
    );
};

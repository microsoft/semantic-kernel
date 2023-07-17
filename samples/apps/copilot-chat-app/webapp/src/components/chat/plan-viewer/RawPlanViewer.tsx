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
    Tooltip,
    makeStyles,
    shorthands,
} from '@fluentui/react-components';
import { Info16Regular } from '@fluentui/react-icons';
import React from 'react';
import { IChatMessage } from '../../../libs/models/ChatMessage';
import { TokenUsage } from '../../shared/TokenUsage';

const useClasses = makeStyles({
    infoButton: {
        ...shorthands.padding(0),
        ...shorthands.margin(0),
        minWidth: 'auto',
        marginLeft: 'auto', // align to right
    },
});

interface IRawPlanViewerProps {
    message: IChatMessage;
}

export const RawPlanViewer: React.FC<IRawPlanViewerProps> = ({ message }) => {
    const classes = useClasses();

    return (
        <Dialog>
            <DialogTrigger disableButtonEnhancement>
                <Tooltip content={'Show plan in Json'} relationship="label">
                    <Button className={classes.infoButton} icon={<Info16Regular />} appearance="transparent" />
                </Tooltip>
            </DialogTrigger>
            <DialogSurface>
                <DialogBody>
                    <DialogTitle>Plan in Json format</DialogTitle>
                    <DialogContent>
                        <TokenUsage
                            promptUsage={message.tokenUsage?.prompt ?? 0}
                            dependencyUsage={message.tokenUsage?.dependency ?? 0}
                        />
                        <pre>
                            <code>
                                {JSON.stringify(JSON.parse(message.content), null, 2)}
                            </code>
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

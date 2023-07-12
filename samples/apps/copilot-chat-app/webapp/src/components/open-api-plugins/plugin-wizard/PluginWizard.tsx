import {
    Button,
    Dialog,
    DialogActions,
    DialogBody,
    DialogContent,
    DialogSurface,
    DialogTitle,
    DialogTrigger,
} from '@fluentui/react-components';
import React, { ReactElement, useMemo, useState } from 'react';
import { useDialogClasses } from '../styles';
import { EnterManifestStep } from './steps/EnterManifestStep';

interface IWizardStep {
    id: CreatePluginSteps;
    header?: string;
    body: ReactElement;
    buttons?: ReactElement;
}

enum CreatePluginSteps {
    EnterManifest,
    SpecifyAuthRequirements,
    ReviewPlugin,
    Confirmation,
}

export const PluginWizard: React.FC = () => {
    const classes = useDialogClasses();

    const [step] = useState(CreatePluginSteps.EnterManifest);
    const wizardSteps: IWizardStep[] = useMemo(() => {
        return [
            {
                id: CreatePluginSteps.EnterManifest,
                header: 'Enter Manifest file',
                body: <EnterManifestStep />,
                buttons: <></>,
            },
        ];
    }, []);

    const currentStep = wizardSteps[step];

    return (
        <Dialog>
            <DialogTrigger>
                <Button data-testid="addCustomPlugin" aria-label="Add Custom Plugin" appearance="primary">
                    Add
                </Button>
            </DialogTrigger>
            <DialogSurface>
                <DialogBody className={classes.root}>
                    <DialogTitle>{currentStep.header}</DialogTitle>
                    <DialogContent className={classes.content}>{currentStep.body}</DialogContent>
                    <DialogActions>{currentStep.buttons}</DialogActions>
                </DialogBody>
            </DialogSurface>
        </Dialog>
    );
};

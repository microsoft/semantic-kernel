import {
    Accordion,
    AccordionHeader,
    AccordionItem,
    AccordionPanel,
    Body1,
    Body2,
    Spinner,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import { CheckmarkCircle20Regular, DismissCircle20Regular } from '@fluentui/react-icons';
import { useEffect, useState } from 'react';
import { Constants } from '../../../../Constants';
import { PluginManifest } from '../../../../libs/models/PluginManifest';
import { fetchJson } from '../../../../libs/utils/FileUtils';
import { isValidOpenAPISpec, isValidPluginManifest } from '../../../../libs/utils/PluginUtils';

const useClasses = makeStyles({
    start: {
        justifyContent: 'start',
    },
    status: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        ...shorthands.gap(tokens.spacingHorizontalMNudge),
    },
    details: {
        paddingLeft: tokens.spacingHorizontalXXXL,
    },
});

enum FileType {
    Manifest = 'OpenAI manifest',
    OpenApiSpec = 'OpenAPI spec',
}

enum VerificationState {
    InputRequired,
    Loading,
    Success,
    Failed,
}

interface IVerifyManifestStepProps {
    manifestDomain?: string;
    onPluginVerified: () => void;
    pluginManifest?: PluginManifest;
    onManifestVerified: (manifest: PluginManifest) => void;
}

export const VerifyManifestStep: React.FC<IVerifyManifestStepProps> = ({
    manifestDomain,
    onPluginVerified,
    pluginManifest,
    onManifestVerified,
}) => {
    const classes = useClasses();
    const [errorMessage, setErrorMessage] = useState<string | undefined>();

    const [manifestVerificationState, setManifestVerificationState] = useState(VerificationState.Loading);
    const [openApiSpecVerificationState, setOpenApiSpecVerificationState] = useState(VerificationState.InputRequired);

    const setManifestFailedState = (errorMessage: string) => {
        setManifestVerificationState(VerificationState.Failed);
        setErrorMessage(errorMessage);
    };

    useEffect(() => {
        setErrorMessage(undefined);

        try {
            const manifestUrl = new URL(Constants.PLUGIN_MANIFEST_PATH, manifestDomain);
            void fetchJson(manifestUrl)
                .then(async (response: Response) => {
                    const pluginManifest = (await response.json()) as PluginManifest;

                    if (isValidPluginManifest(pluginManifest)) {
                        setManifestVerificationState(VerificationState.Success);
                        setOpenApiSpecVerificationState(VerificationState.Loading);
                        onManifestVerified(pluginManifest);

                        try {
                            if (isValidOpenAPISpec(pluginManifest.api.url)) {
                                onPluginVerified();
                            }
                            setOpenApiSpecVerificationState(VerificationState.Success);
                        } catch (e: any) {
                            setOpenApiSpecVerificationState(VerificationState.Failed);
                            setErrorMessage((e as Error).message);
                        }
                    }
                })
                .catch((e) => {
                    setManifestFailedState((e as Error).message);
                });
        } catch (e: unknown) {
            setManifestFailedState((e as Error).message);
        }
    }, [manifestDomain, onManifestVerified, onPluginVerified]);

    const statusComponent = (type: FileType, status: VerificationState) => {
        const fileType = type;
        switch (status) {
            case VerificationState.Loading:
                return (
                    <Spinner
                        labelPosition="after"
                        label={`Verifying ${fileType} file`}
                        size="tiny"
                        className={classes.start}
                    />
                );
            case VerificationState.Failed:
            case VerificationState.Success: {
                const icon =
                    status === VerificationState.Success ? (
                        <CheckmarkCircle20Regular color="green" />
                    ) : (
                        <DismissCircle20Regular color="red" />
                    );
                const text =
                    status === VerificationState.Success ? `Verified ${fileType}` : `Could not validate ${fileType}.`;

                return (
                    <AccordionItem value={fileType}>
                        <AccordionHeader expandIconPosition="end">
                            <div className={classes.status}>
                                {icon}
                                <Body2> {text}</Body2>
                            </div>
                        </AccordionHeader>
                        <AccordionPanel className={classes.details}>
                            {
                                status === VerificationState.Failed && <Body1 color="red">{errorMessage}</Body1>
                                // TODO: Add Manifest details
                            }
                            {status === VerificationState.Success &&
                                (type === FileType.Manifest ? (
                                    <div>
                                        <Body1>Plugin: {pluginManifest?.name_for_human}</Body1>
                                        <br />
                                        <Body1>Contact: {pluginManifest?.contact_email}</Body1>
                                        <br />
                                        <Body1>Auth: {pluginManifest?.auth.type}</Body1>
                                    </div>
                                ) : (
                                    <div>
                                        <Body1>{pluginManifest?.api.url}</Body1>
                                    </div>
                                ))}
                        </AccordionPanel>
                    </AccordionItem>
                );
            }
            default:
                return;
        }
    };

    return (
        <Accordion collapsible multiple defaultOpenItems={[FileType.Manifest, FileType.OpenApiSpec]}>
            {statusComponent(FileType.Manifest, manifestVerificationState)}
            {statusComponent(FileType.OpenApiSpec, openApiSpecVerificationState)}
        </Accordion>
    );
};

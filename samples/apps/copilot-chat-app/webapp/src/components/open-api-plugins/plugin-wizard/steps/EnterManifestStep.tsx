import { Input, Label, Spinner, Text } from '@fluentui/react-components';
import { CheckmarkCircle16Regular, DismissCircle16Regular } from '@fluentui/react-icons';
import { useCallback, useRef, useState } from 'react';

enum FileType {
    Manifest,
    OpenApiSpec,
}

enum VerificationState {
    InputRequired,
    Loading,
    Success,
    Failed,
}

export const EnterManifestStep: React.FC = () => {
    const [manifestFile, setManifestFile] = useState<string | undefined>();
    const [manifestVerificationState, setManifestVerificationState] = useState(VerificationState.InputRequired);
    const [openApiSpecVerificationState] = useState(VerificationState.InputRequired);
    // setOpenApiSpecVerificationState

    const keyStrokeTimeout = useRef(-1);

    const updateAndValidateManifest = useCallback((_: any, data?: { value: string }) => {
        window.clearTimeout(keyStrokeTimeout.current);
        setManifestFile(data?.value);

        keyStrokeTimeout.current = window.setTimeout(() => {
            // Verify Manifest file
            setManifestVerificationState(VerificationState.Loading);
        }, 250);
    }, []);

    const statusComponent = (type: FileType, status: VerificationState, errorMessage?: string) => {
        const fileType = FileType[type].toLocaleLowerCase();
        switch (status) {
            case VerificationState.Loading:
                return <Spinner labelPosition="after" size="extra-small" label={`Verifying ${fileType} file`} />;
            case VerificationState.Success:
                return (
                    <>
                        <CheckmarkCircle16Regular />
                        <Text> {`Verified ${fileType}`}</Text>
                    </>
                );
            case VerificationState.Failed:
                return (
                    <>
                        <DismissCircle16Regular />
                        <Text>{`Could not verify ${fileType}. Error: ${errorMessage ?? ''}`}</Text>
                    </>
                );
            default:
                return;
        }
    };

    return (
        <>
            <Label>Link to manifest file</Label>
            <Input
                required
                type="text"
                id={'plugin-manifest-input'}
                value={manifestFile}
                onChange={updateAndValidateManifest}
                placeholder={`manifest.json`}
            />
            {statusComponent(FileType.Manifest, manifestVerificationState)}
            {statusComponent(FileType.OpenApiSpec, openApiSpecVerificationState)}
        </>
    );
};

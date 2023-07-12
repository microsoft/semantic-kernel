import { Body1, Body2, Input, Subtitle2, Text } from '@fluentui/react-components';
import { Dispatch, SetStateAction } from 'react';
interface IEnterManifestStepProps {
    manifestDomain?: string;
    setManifestDomain: Dispatch<SetStateAction<string | undefined>>;
}

export const EnterManifestStep: React.FC<IEnterManifestStepProps> = ({ manifestDomain, setManifestDomain }) => {
    return (
        <>
            <Body2>Connect an OpenAI Plugin to expose Copilot Chat to third-party applications.</Body2>
            <Subtitle2>Enter your website domain</Subtitle2>
            <Text size={400}>
                To connect a plugin, provide the domain of your website where your{' '}
                <a
                    href={'https://platform.openai.com/docs/plugins/getting-started/plugin-manifest'}
                    target="_blank"
                    rel="noreferrer noopener"
                >
                    OpenAI plugin manifest
                </a>{' '}
                is hosted. This is the{' '}
                <Text size={400} weight="bold">
                    ai-plugin.json
                </Text>{' '}
                file.
            </Text>
            <Input
                required
                type="text"
                id={'plugin-domain-input'}
                value={manifestDomain}
                onChange={(_: any, data?: { value: string }) => setManifestDomain(data?.value)}
                placeholder={`yourdomain.com`}
            />
            <Body1 italic>
                Note: Copilot Chat currently only supports plugins requiring{' '}
                <a
                    href={'https://platform.openai.com/docs/plugins/authentication/no-authentication'}
                    target="_blank"
                    rel="noreferrer noopener"
                >
                    no auth
                </a>{' '}
                or{' '}
                <a
                    href={'https://platform.openai.com/docs/plugins/authentication/user-level'}
                    target="_blank"
                    rel="noreferrer noopener"
                >
                    user-level
                </a>{' '}
                user-level authentication.
            </Body1>
        </>
    );
};

export default EnterManifestStep;

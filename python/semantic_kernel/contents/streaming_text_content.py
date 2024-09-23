# Copyright (c) Microsoft. All rights reserved.

from typing_extensions import deprecated

from semantic_kernel.contents.text_content import TextContent


@deprecated("StreamingTextContent is deprecated. Use TextContent instead.")
class StreamingTextContent(TextContent):
    """This represents a streaming text response content.

    This class is deprecated in favor of TextContent for simplicity.
    """

    pass

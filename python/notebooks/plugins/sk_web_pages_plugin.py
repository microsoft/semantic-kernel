# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.skill_definition import sk_function
from bs4 import BeautifulSoup
import re, aiohttp


class WebPagesPlugin:
    """
    A plugin to interact with web pages, e.g. download the text content of a page.
    """

    @sk_function(
        description="Fetch the text content of a webpage. The return is a string containing all the text.",
        name="fetch_webpage",
        input_description="URL of the page to fetch.",
    )
    async def fetch_webpage(self, input: str) -> str:
        """
        A native function that fetches the text content of a webpage.
        HTML tags are removed, and empty lines are compacted.
        """
        if not input:
            raise ValueError("url cannot be `None` or empty")
        async with aiohttp.ClientSession() as session:
            async with session.get(input, raise_for_status=True) as response:
                html = await response.text()
                soup = BeautifulSoup(html, features="html.parser")
                # remove some elements
                for el in soup(["script", "style", "iframe", "img", "video", "audio"]):
                    el.extract()

                # get text and compact empty lines
                text = soup.get_text()
                return re.sub(r"[\r\n][\r\n]{2,}", "\n\n", text)

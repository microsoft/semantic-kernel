# Copyright (c) Microsoft. All rights reserved.

import base64
from io import BytesIO

from diffusers import DiffusionPipeline

from . import InferenceGenerator

# The model used to get the tokenizer can be a little arbitrary
# since the tokenizers are common within the same model type


class ImageGenerator(InferenceGenerator.InferenceGenerator):
    def __init__(self, model_name):
        super().__init__(model_name)
        self.default_size = 512

    def perform_inference(self, prompt, num_images, size):
        generator = DiffusionPipeline.from_pretrained(self.model_name)
        generator.to(self.device)

        height = self.default_size
        width = self.default_size

        if size is not None:
            tmp = size.split("x")
            height = int(tmp[0])
            width = int(tmp[1])

        images = generator([prompt] * num_images, height=height, width=width).images

        b64_images = []
        for image in images:
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            base64_image = base64.b64encode(buffered.getvalue())
            b64_images.append({"b64_json": base64_image.decode()})
        return b64_images

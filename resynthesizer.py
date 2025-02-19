import torch
import torch.nn.functional as F
import numpy as np
from skimage.restoration import inpaint
from resynthesizer import TImageSynthParameters, resynthesize
from torchvision.transforms.functional import to_pil_image

matchContextTypes = [
    "Patching",
    "Shuffle",
    "Brushfire (inward)",
    "Directional (horizontal, inward)",
    "Directional (vertical, inward)",
    "Brushfire (outward)",
    "Directional (horizontal, outward)",
    "Directional (vertical, outward)",
    "Squeeze",
]


class Resynthesize:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "mask": ("MASK",),
                "makeTileable": ("BOOLEAN", {"default": False}),
                "context": (matchContextTypes,),
                "mapWeight": (
                    "FLOAT",
                    {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01},
                ),
                "sensitivityToOutliers": (
                    "FLOAT",
                    {"default": 0.117, "min": 0.0, "max": 1.0, "step": 0.001},
                ),
                "patchSize": ("INT", {"default": 30, "min": 0, "max": 60}),
                "maxProbeCount": ("INT", {"default": 200, "min": 0}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "resynthesize_image"

    def resynthesize_image(
        self,
        image,
        mask,
        makeTileable,
        context,
        mapWeight,
        sensitivityToOutliers,
        patchSize,
        maxProbeCount,
    ):
        # Convert torch tensors to PIL images, assuming that tensors are under the BHWC format used by ComfyUI
        image = image.squeeze(0).permute(2, 0, 1)
        mask = mask.squeeze(0).permute(2, 0, 1)
        pilimage = to_pil_image(image)
        pilmask = to_pil_image(mask)

        # Use resynthesizer to fill in the image at the place of the mask
        params = TImageSynthParameters()
        params.isMakeSeamlesslyTileableHorizontally = int(makeTileable)
        params.isMakeSeamlesslyTileableVertically = int(makeTileable)
        params.matchContextType = matchContextTypes.index(context)
        params.mapWeight = mapWeight
        params.sensitivityToOutliers = sensitivityToOutliers
        params.patchSize = patchSize
        params.maxProbeCount = maxProbeCount
        pilresult = resynthesize(pilimage, pilmask, params)  # actual resynthesizer call

        # Convert PIL images back to torch tensors
        result = torch.Tensor(np.array(pilresult) / 255).unsqueeze(0)

        return (result,)

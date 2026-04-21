#!/usr/bin/env python3

import os
import sys
from dataclasses import dataclass

import cv2
import rospy
import torch 
from model_prototypes.ALVINN import ALVINN
# from model_prototypes.ALVINNITA import ALVINNITA
from model_prototypes.CALVINN import CALVINN
from model_prototypes.MELVINN import MELVINN


PKG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MODEL_PATH = os.path.join(PKG_DIR, "models", "alvinn_latest.pt")
DEFAULT_MODEL_UTILS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model_prototypes")


@dataclass
class LoadedModel:
    model: torch.nn.Module
    device: torch.device
    image_size: tuple
    model_input_channels: int
    model_name: str
    model_path: str


def _require_model_utils(model_utils_dir):
    if model_utils_dir not in sys.path:
        sys.path.append(model_utils_dir)


def _build_model_from_checkpoint(model_name, image_size, state_dict):
    # if model_name.startswith("alvinnita"):

    #     history_frames = int(state_dict["position_embedding"].shape[0])
    #     output_size = int(state_dict["head.4.weight"].shape[0])
    #     input_dim = int(state_dict["frame_encoder.0.weight"].shape[1])
    #     channels = max(1, input_dim // (image_size[0] * image_size[1]))
    #     model = ALVINNITA(
    #         imagesize_hw=image_size,
    #         color_channels=channels,
    #         history_frames=history_frames,
    #         output_size=output_size,
    #     )
    #     return model, channels

    if model_name.startswith("calvinn"):
        channels = int(state_dict["features.0.net.0.weight"].shape[1])
        model = CALVINN(imagesize_hw=image_size, color_channels=channels)
        return model, channels

    if model_name.startswith("melvinn"):
        input_units = int(state_dict["net.0.net.0.weight"].shape[1])
        channels = max(1, input_units // (image_size[0] * image_size[1]))
        model = MELVINN(imagesize_hw=image_size, color_channels=channels)
        return model, channels


    model = ALVINN(imagesize_hw=image_size)
    return model, 1


def load_model_from_ros_params():
    model_path = rospy.get_param("~model_path", DEFAULT_MODEL_PATH)
    model_utils_dir = rospy.get_param("~model_utils_dir", DEFAULT_MODEL_UTILS_DIR)
    requested_device = str(rospy.get_param("~device", "auto")).strip().lower()
    if requested_device == "auto":
        device_name = "cuda" if torch.cuda.is_available() else "cpu"
    elif requested_device.startswith("cuda") and not torch.cuda.is_available():
        rospy.logwarn("CUDA requested but unavailable; falling back to CPU.")
        device_name = "cpu"
    else:
        device_name = requested_device
    device = torch.device(device_name)
    print(f"CDEBUG, devicename = {device_name}")

    _require_model_utils(model_utils_dir)
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    if not isinstance(checkpoint, dict):
        raise ValueError(f"Expected checkpoint dict in {model_path}, got {type(checkpoint)}")
    if "model_state_dict" not in checkpoint:
        raise KeyError(f"Missing 'model_state_dict' in checkpoint: {model_path}")

    ckpt_model_name = str(checkpoint.get("model_name", "alvinn")).lower()

    raw_image_size = tuple(checkpoint.get("image_size", (32, 32)))
    if len(raw_image_size) != 2:
        raise ValueError(f"Invalid image_size in checkpoint: {raw_image_size}")
    image_size = (int(raw_image_size[0]), int(raw_image_size[1]))

    model, model_input_channels = _build_model_from_checkpoint(
        ckpt_model_name,
        image_size,
        checkpoint["model_state_dict"],
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    rospy.loginfo(
        "Loaded model '%s' from %s (image_size=%s, channels=%d, device=%s)",
        ckpt_model_name,
        model_path,
        image_size,
        model_input_channels,
        device,
    )

    return LoadedModel(
        model=model,
        device=device,
        image_size=image_size,
        model_input_channels=model_input_channels,
        model_name=ckpt_model_name,
        model_path=model_path,
    )


def preprocess_bgr_image(bgr_img, image_size, model_input_channels, device):
    resized = cv2.resize(bgr_img, image_size, interpolation=cv2.INTER_NEAREST)
    if model_input_channels == 1:
        # Training pipeline uses RGB blue channel; in OpenCV BGR this is channel 0.
        tensor = torch.from_numpy(resized[:, :, 0]).to(torch.float32) / 255.0
        tensor = tensor.unsqueeze(0).unsqueeze(0)
    else:
        rgb_img = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        tensor = torch.from_numpy(rgb_img).to(torch.float32) / 255.0
        tensor = tensor.permute(2, 0, 1).unsqueeze(0)
    return tensor.to(device)

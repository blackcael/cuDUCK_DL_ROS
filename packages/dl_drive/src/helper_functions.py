#!/usr/bin/env python3
import torch


AVG_VELOCITY = 0.2
MAX_MAG_W = 0.009
AXEL_LENGTH_MM = 50
STEERING_BIN_MAX = 22.0


def logits_to_angle(logits):
    return torch.argmax(logits, dim=1) - 22


def steering_bin_to_wheel_cmd(
    logits,
    avg_velocity = AVG_VELOCITY,
    max_mag_w = MAX_MAG_W,
    axel_len_mm=AXEL_LENGTH_MM,
):
    """
    Convert model logits [N,45] (or [45]) to (v_l, v_r) wheel commands.

    This is the inverse of DuckieDriveDataset.scale_v_pair_to_45:
      unit_w = angle_bin / 22
      w = unit_w * max_mag_w
      w = (v_l - v_r) / axel_len_mm
      avg_velocity = (v_l + v_r) / 2
    """
    logits_t = torch.as_tensor(logits)
    is_single = logits_t.ndim == 1
    if logits_t.ndim == 1:
        logits_t = logits_t.unsqueeze(0)
    if logits_t.ndim != 2:
        raise ValueError(f"Expected logits with shape [45] or [N,45], got {tuple(logits_t.shape)}")

    angle_bin_t = logits_to_angle(logits_t).to(torch.float32)
    avg_velocity_t = torch.as_tensor(avg_velocity, dtype=torch.float32)
    max_mag_w_t = torch.as_tensor(max_mag_w, dtype=torch.float32)

    unit_w = torch.clamp(angle_bin_t, -STEERING_BIN_MAX, STEERING_BIN_MAX) / STEERING_BIN_MAX
    w = unit_w * max_mag_w_t

    half_delta = (w * axel_len_mm) / 2.0
    v_l = avg_velocity_t + half_delta
    v_r = avg_velocity_t - half_delta
    if is_single:
        return v_l.squeeze(0), v_r.squeeze(0)
    return v_l, v_r
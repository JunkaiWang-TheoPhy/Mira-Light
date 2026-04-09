#!/usr/bin/env python3
"""Shared signal-format helpers for Mira Light.

This module centralizes the parts of the device contract that are shared across
runtime, mock devices, and bridge-facing validation:

- 40-pixel LED signal defaults
- per-pixel RGB/RGBA normalization
- `pixelSignals = [R, G, B, brightness]` conversions
- `headCapacitive = 0 | 1` validation
"""

from __future__ import annotations

from typing import Any, Callable


DEFAULT_LED_PIXEL_COUNT = 40
HEAD_CAPACITIVE_FIELD = "headCapacitive"
HEAD_CAPACITIVE_ALLOWED = {0, 1}


def _fail(error_cls: type[Exception], message: str) -> None:
    raise error_cls(message)


def coerce_int(value: Any, *, field_name: str, error_cls: type[Exception] = ValueError) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(error_cls, f"{field_name} must be an integer")
    if int(value) != value:
        _fail(error_cls, f"{field_name} must be an integer")
    return int(value)


def normalize_u8(value: Any, *, field_name: str, error_cls: type[Exception] = ValueError) -> int:
    channel = coerce_int(value, field_name=field_name, error_cls=error_cls)
    if not 0 <= channel <= 255:
        _fail(error_cls, f"{field_name} must be between 0 and 255")
    return channel


def normalize_rgb_triplet(
    value: Any,
    *,
    field_name: str,
    allow_brightness: bool = False,
    error_cls: type[Exception] = ValueError,
) -> dict[str, int]:
    if isinstance(value, dict):
        allowed = {"r", "g", "b"}
        if allow_brightness:
            allowed.add("brightness")
        unknown = sorted(set(value) - allowed)
        if unknown:
            _fail(error_cls, f"{field_name} has unsupported keys: {', '.join(unknown)}")
        missing = [channel for channel in ("r", "g", "b") if channel not in value]
        if missing:
            _fail(error_cls, f"{field_name} is missing channels: {', '.join(missing)}")
        red = normalize_u8(value["r"], field_name=f"{field_name}.r", error_cls=error_cls)
        green = normalize_u8(value["g"], field_name=f"{field_name}.g", error_cls=error_cls)
        blue = normalize_u8(value["b"], field_name=f"{field_name}.b", error_cls=error_cls)
        brightness = None
        if allow_brightness and "brightness" in value:
            brightness = normalize_u8(value["brightness"], field_name=f"{field_name}.brightness", error_cls=error_cls)
    elif isinstance(value, (list, tuple)) and len(value) in ({3, 4} if allow_brightness else {3}):
        red = normalize_u8(value[0], field_name=f"{field_name}[0]", error_cls=error_cls)
        green = normalize_u8(value[1], field_name=f"{field_name}[1]", error_cls=error_cls)
        blue = normalize_u8(value[2], field_name=f"{field_name}[2]", error_cls=error_cls)
        brightness = None
        if allow_brightness and len(value) == 4:
            brightness = normalize_u8(value[3], field_name=f"{field_name}[3]", error_cls=error_cls)
    else:
        if allow_brightness:
            _fail(error_cls, f"{field_name} must be an RGB/RGBA object or 3/4-value vector")
        _fail(error_cls, f"{field_name} must be an RGB object or 3-value vector")

    normalized = {"r": red, "g": green, "b": blue}
    if brightness is not None:
        normalized["brightness"] = brightness
    return normalized


def normalize_led_pixel(
    value: Any,
    *,
    field_name: str,
    default_brightness: int | None,
    error_cls: type[Exception] = ValueError,
) -> dict[str, int]:
    if isinstance(value, dict):
        allowed = {"r", "g", "b", "brightness"}
        unknown = sorted(set(value) - allowed)
        if unknown:
            _fail(error_cls, f"{field_name} has unsupported keys: {', '.join(unknown)}")
        channels = normalize_rgb_triplet(value, field_name=field_name, error_cls=error_cls)
        brightness_raw = value.get("brightness", default_brightness)
    elif isinstance(value, (list, tuple)) and len(value) in {3, 4}:
        channels = normalize_rgb_triplet(value[:3], field_name=field_name, error_cls=error_cls)
        brightness_raw = value[3] if len(value) == 4 else default_brightness
    else:
        _fail(error_cls, f"{field_name} must be an RGB/RGBA object or 3/4-value vector")

    if brightness_raw is None:
        _fail(error_cls, f"{field_name}.brightness is required")

    return {
        **channels,
        "brightness": normalize_u8(brightness_raw, field_name=f"{field_name}.brightness", error_cls=error_cls),
    }


def normalize_binary_signal(value: Any, *, field_name: str = HEAD_CAPACITIVE_FIELD, error_cls: type[Exception] = ValueError) -> int:
    signal = coerce_int(value, field_name=field_name, error_cls=error_cls)
    if signal not in HEAD_CAPACITIVE_ALLOWED:
        _fail(error_cls, f"{field_name} must be 0 or 1")
    return signal


def rgb_channels(pixel: dict[str, int]) -> dict[str, int]:
    return {"r": pixel["r"], "g": pixel["g"], "b": pixel["b"]}


def pixel_signal(pixel: dict[str, int]) -> list[int]:
    return [pixel["r"], pixel["g"], pixel["b"], pixel["brightness"]]


def make_pixel(*, red: int, green: int, blue: int, brightness: int) -> dict[str, int]:
    return {"r": red, "g": green, "b": blue, "brightness": brightness}


def make_uniform_pixels(
    *,
    count: int,
    color: dict[str, int],
    brightness: int,
) -> list[dict[str, int]]:
    return [
        make_pixel(
            red=color["r"],
            green=color["g"],
            blue=color["b"],
            brightness=brightness,
        )
        for _ in range(count)
    ]


def off_pixels(*, count: int) -> list[dict[str, int]]:
    return [make_pixel(red=0, green=0, blue=0, brightness=0) for _ in range(count)]


def normalize_vector_pixels(
    raw_pixels: Any,
    *,
    pixel_count: int,
    field_name: str = "pixels",
    default_brightness: int | None,
    error_cls: type[Exception] = ValueError,
) -> list[dict[str, int]]:
    if not isinstance(raw_pixels, list):
        _fail(error_cls, f"{field_name} must be a list when mode=vector")
    if len(raw_pixels) != pixel_count:
        _fail(error_cls, f"{field_name} must contain exactly {pixel_count} RGB or RGBA entries")
    return [
        normalize_led_pixel(
            pixel,
            field_name=f"{field_name}[{index}]",
            default_brightness=default_brightness,
            error_cls=error_cls,
        )
        for index, pixel in enumerate(raw_pixels)
    ]


def build_led_status_payload(
    *,
    mode: str,
    brightness: int,
    color: dict[str, int],
    pixels: list[dict[str, int]],
    led_count: int,
    pin: int,
    include_rgb_pixels_in_vector: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "mode": mode,
        "brightness": brightness,
        "color": dict(color),
        "led_count": led_count,
        "pin": pin,
        "pixelSignals": [pixel_signal(pixel) for pixel in pixels],
    }
    if mode == "vector" and include_rgb_pixels_in_vector:
        payload["pixels"] = [rgb_channels(pixel) for pixel in pixels]
    return payload

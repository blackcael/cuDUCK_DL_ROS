#!/usr/bin/env python3
"""Simple joystick connection test for 8BitDo (no ROS required)."""

import argparse
import time
import pygame


def pick_joystick(preferred_name_substring: str):
    count = pygame.joystick.get_count()
    if count == 0:
        return None

    pref = preferred_name_substring.lower().strip()
    if pref:
        for idx in range(count):
            js = pygame.joystick.Joystick(idx)
            js.init()
            name = js.get_name() or ""
            if pref in name.lower():
                return js
            js.quit()

    js = pygame.joystick.Joystick(0)
    js.init()
    return js


def rounded(values, ndigits=2):
    return [round(v, ndigits) for v in values]


def list_joysticks():
    count = pygame.joystick.get_count()
    print(f"Detected joystick count: {count}")
    for i in range(count):
        dev = pygame.joystick.Joystick(i)
        dev.init()
        print(f"  [{i}] {dev.get_name()}")
        dev.quit()


def wait_for_joystick(preferred_name, poll_interval):
    print(
        f"Waiting for controller (preferred name contains '{preferred_name}'). "
        "Press Ctrl+C to quit."
    )
    while True:
        pygame.joystick.quit()
        pygame.joystick.init()
        pygame.event.pump()
        js = pick_joystick(preferred_name)
        if js is not None:
            return js
        time.sleep(max(poll_interval, 0.1))


def main():
    parser = argparse.ArgumentParser(description="Standalone game controller connectivity test")
    parser.add_argument("--preferred-name", default="8BitDo", help="Prefer joystick name containing this text")
    parser.add_argument("--hz", type=float, default=20.0, help="Print refresh rate")
    parser.add_argument("--duration", type=float, default=0.0, help="Seconds to run (0 = run until Ctrl+C)")
    parser.add_argument("--poll-interval", type=float, default=1.0, help="Seconds between connection checks")
    args = parser.parse_args()

    pygame.init()
    pygame.joystick.init()

    list_joysticks()
    js = wait_for_joystick(args.preferred_name, args.poll_interval)

    print("\nUsing controller:")
    print(f"  Name: {js.get_name()}")
    print(f"  Axes: {js.get_numaxes()}")
    print(f"  Buttons: {js.get_numbuttons()}")
    print(f"  Hats: {js.get_numhats()}")
    print("\nMove sticks / press buttons. Ctrl+C to exit.\n")

    period = 1.0 / max(args.hz, 1.0)
    start = time.time()

    try:
        while True:
            pygame.event.pump()

            axes = [js.get_axis(i) for i in range(js.get_numaxes())]
            buttons = [js.get_button(i) for i in range(js.get_numbuttons())]
            hats = [js.get_hat(i) for i in range(js.get_numhats())]

            print(
                f"axes={rounded(axes)} buttons={buttons} hats={hats}",
                end="\r",
                flush=True,
            )

            if args.duration > 0 and (time.time() - start) >= args.duration:
                break

            time.sleep(period)
    except KeyboardInterrupt:
        pass

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

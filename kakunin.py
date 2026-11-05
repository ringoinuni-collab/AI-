
"""担当Cの確認用"""

import argparse
import json

from volume_c import (
    AIService,
    WindowsProvider,
)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--demo",
        action="store_true",
        help="架空のデータで動作確認する",
    )

    args = parser.parse_args()

    service = AIService()

    if args.demo:
        raw = {
            "running_apps": [
                "Discord.exe",
                "r5apex.exe",
            ],
            "active_app": "r5apex.exe",
            "output_device": "headphones",
            "output_device_id": (
                "demo-headphones"
            ),
            "volumes": {
                "Discord.exe": 70,
                "r5apex.exe": 50,
            },
        }

    else:
        raw = WindowsProvider().collect()

    context = service.inspect(raw)

    proposals = service.propose(
        context
    )

    print(
        json.dumps(
            {
                "context": context,
                "proposals": proposals,
            },
            ensure_ascii=False,
            indent=2,
        )
    )

"""Downloads the models once (used by setup.ps1): python -m holostudio.prepare"""

from holostudio.identity.bodies import ensure_pose_model
from holostudio.tracking.model import ensure_hand_model


def main() -> None:
    for path in (ensure_hand_model(), ensure_pose_model()):
        print(f"    OK  {path.name} ({path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()

"""从 Git tag 注入版本号到 split_pdf_gui.py。"""

import re
import sys


def inject_version(version: str, filepath: str = "split_pdf_gui.py") -> None:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    new_content = re.sub(
        r'__version__\s*=\s*"[^"]*"',
        f'__version__ = "{version}"',
        content,
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Injected version: {version}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inject_version.py <version>")
        sys.exit(1)
    inject_version(sys.argv[1])

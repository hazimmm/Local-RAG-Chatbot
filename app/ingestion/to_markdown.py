from pathlib import Path

from markitdown import MarkItDown

_converter = MarkItDown()


def to_markdown(path: str | Path) -> str:
    result = _converter.convert(str(path))
    return result.text_content


if __name__ == "__main__":
    print(to_markdown("samples/handbook.docx"))

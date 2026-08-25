"""CLI entry point for document converter."""

from document_converter.converter import DocumentConverter

converter = DocumentConverter()


def main():
    """Run the document converter CLI."""
    import sys

    if len(sys.argv) < 3:
        print("Usage: convert <input-file> <output-format>")
        print("Available output formats: pdf, docx, txt, html, markdown")
        sys.exit(1)

    input_file = sys.argv[1]
    output_format = sys.argv[2].lower()

    try:
        output_path = input_file.rsplit(".", 1)[0] + "." + output_format
        converter.convert(input_file, output_path, output_format)
        print(f"Converted {input_file} to {output_path}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
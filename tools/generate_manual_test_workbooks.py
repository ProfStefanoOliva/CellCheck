"""Generate synthetic Excel workbooks for CellCheck manual testing."""

from __future__ import annotations

from cellcheck.utils.manual_test_workbooks import generate_all_workbooks, get_output_dir


def main() -> None:
    """Generate all synthetic workbooks and print a summary."""
    generated_files = generate_all_workbooks()

    print("CellCheck manual workbook generation completed.")
    print(f"Output directory: {get_output_dir()}")
    for path in generated_files:
        print(f"- {path.name}")


if __name__ == "__main__":
    main()

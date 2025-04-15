import difflib


def load_large_diff(
    new_file_content_str: str,
    original_file_content_str: str,
) -> str:
    """
    Generate a patch for a modified file by comparing the original content of the file with the new content provided as
    input.
    """
    if not original_file_content_str and not new_file_content_str:
        return ""

    try:
        original_file_content_str = (original_file_content_str or "").rstrip() + "\n"
        new_file_content_str = (new_file_content_str or "").rstrip() + "\n"
        diff = difflib.unified_diff(
            original_file_content_str.splitlines(keepends=True),
            new_file_content_str.splitlines(keepends=True),
        )
        patch = "".join(diff)
        return patch
    except Exception:
        return ""

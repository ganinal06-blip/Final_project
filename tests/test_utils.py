from src.utils import parse_allowed_file_bytes

def test_parse_simple_list():
    content = b"""
    @Masha123
    Bob_the_builder
    987654321
    """
    res = parse_allowed_file_bytes(content)
    assert res == ["@Masha123", "Bob_the_builder", "987654321"]

def test_parse_links():
    content = b"""
    https://t.me/Masha123
    http://t.me/Bob_the_builder/
    """
    res = parse_allowed_file_bytes(content)
    assert res == ["Masha123", "Bob_the_builder"]

def test_parse_empty_and_spaces():
    content = b"\n\n   \n@Liza\n"
    res = parse_allowed_file_bytes(content)
    assert res == ["@Liza"]

def test_parse_mixed_content():
    content = b"""
    @Masha123
    12345
    https://t.me/Bob_the_builder
    """
    res = parse_allowed_file_bytes(content)
    assert res == ["@Masha123", "12345", "Bob_the_builder"]

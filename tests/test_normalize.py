from archivesnap.normalize import html_to_text, normalize_text


def test_strips_tags_and_scripts():
    html = (
        "<html><head><style>.x{color:red}</style>"
        "<script>var a=1;</script></head>"
        "<body><h1>Title</h1><p>Hello   world</p></body></html>"
    )
    text = html_to_text(html)
    assert "Title" in text
    assert "Hello world" in text
    assert "color" not in text
    assert "var a" not in text


def test_whitespace_collapse_is_stable():
    a = normalize_text("Hello    world\n\n\n  next   line  ")
    b = normalize_text("Hello world\nnext line")
    assert a == b


def test_entity_decoding():
    text = html_to_text("<p>Tom &amp; Jerry &lt;tag&gt;</p>")
    assert "Tom & Jerry <tag>" in text


def test_block_tags_separate_lines():
    text = html_to_text("<p>one</p><p>two</p>")
    assert text.split("\n") == ["one", "two"]

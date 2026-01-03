
from ebooklib import epub
import os

def create_test_epub(filename="test_novel.epub"):
    book = epub.EpubBook()
    book.set_identifier('id123456')
    book.set_title('Test Novel')
    book.set_language('en')
    book.add_author('Test Author')

    # Introduction
    intro = epub.EpubHtml(title='Introduction', file_name='intro.xhtml', lang='en')
    intro.content = '<h1>Introduction</h1><p>This is a test introduction.</p>'
    book.add_item(intro)

    # Chapter 1
    c1 = epub.EpubHtml(title='Chapter 1', file_name='chap_01.xhtml', lang='en')
    c1.content = '<h1>Chapter 1</h1><p>Yo legends! This is the first paragraph of the test novel. It should be aligned properly.</p><p>Here is another paragraph with some more text to test the system.</p>'
    book.add_item(c1)

    # Add navigation
    book.toc = (intro, c1)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Define CSS
    style = 'body { font-family: Times, serif; }'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    # Spin
    book.spine = ['nav', intro, c1]

    epub.write_epub(filename, book, {})
    print(f"Created {filename}")

if __name__ == "__main__":
    if not os.path.exists("_NEW_EPUBS_HERE"):
        os.makedirs("_NEW_EPUBS_HERE")
    create_test_epub("_NEW_EPUBS_HERE/test_novel.epub")

"""
Sample EPUB Generator
Creates test EPUB files for development and testing
"""
import os
import sys
from pathlib import Path
from typing import List, Dict
from ebooklib import epub
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class EPUBGenerator:
    """Generate sample EPUB files for testing"""
    
    def __init__(self, output_dir: str = "examples/sample_epubs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_minimal_epub(self) -> str:
        """
        Create a minimal EPUB file (2 chapters)
        Perfect for quick testing
        """
        book = epub.EpubBook()
        
        # Metadata
        book.set_identifier('minimal_test_001')
        book.set_title('Minimal Test Book')
        book.set_language('en')
        book.add_author('Test Author')
        
        # Chapter 1
        c1 = epub.EpubHtml(
            title='Chapter 1',
            file_name='chap_01.xhtml',
            lang='en'
        )
        c1.content = '''
        <html>
        <head><title>Chapter 1</title></head>
        <body>
        <h1>Chapter 1: The Beginning</h1>
        <p>This is the first chapter of our minimal test book.</p>
        <p>It contains just enough text to test basic functionality.</p>
        <p>The quick brown fox jumps over the lazy dog.</p>
        </body>
        </html>
        '''
        
        # Chapter 2
        c2 = epub.EpubHtml(
            title='Chapter 2',
            file_name='chap_02.xhtml',
            lang='en'
        )
        c2.content = '''
        <html>
        <head><title>Chapter 2</title></head>
        <body>
        <h1>Chapter 2: The Middle</h1>
        <p>This is the second chapter.</p>
        <p>It helps test multi-chapter processing.</p>
        <p>A journey of a thousand miles begins with a single step.</p>
        </body>
        </html>
        '''
        
        # Add chapters to book
        book.add_item(c1)
        book.add_item(c2)
        
        # Define Table of Contents
        book.toc = (
            epub.Link('chap_01.xhtml', 'Chapter 1', 'chap01'),
            epub.Link('chap_02.xhtml', 'Chapter 2', 'chap02')
        )
        
        # Add navigation files
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # Define spine (reading order)
        book.spine = ['nav', c1, c2]
        
        # Save
        output_path = self.output_dir / 'minimal_test.epub'
        epub.write_epub(str(output_path), book, {})
        
        print(f"✅ Created: {output_path}")
        return str(output_path)
    
    def create_medium_epub(self) -> str:
        """
        Create a medium-sized EPUB (10 chapters)
        For standard testing
        """
        book = epub.EpubBook()
        
        # Metadata
        book.set_identifier('medium_test_001')
        book.set_title('Medium Test Novel')
        book.set_language('en')
        book.add_author('Fiction Author')
        book.add_metadata('DC', 'description', 'A medium-length test novel')
        
        chapters = []
        toc = []
        
        # Create 10 chapters
        for i in range(1, 11):
            chapter = epub.EpubHtml(
                title=f'Chapter {i}',
                file_name=f'chap_{i:02d}.xhtml',
                lang='en'
            )
            
            chapter.content = f'''
            <html>
            <head><title>Chapter {i}</title></head>
            <body>
            <h1>Chapter {i}: Adventure Continues</h1>
            <p>This is chapter {i} of our medium test novel.</p>
            <p>The protagonist continues their journey through various challenges.</p>
            <p>Each chapter contains approximately 200-300 words for realistic testing.</p>
            <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
            <p>Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</p>
            <p>Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.</p>
            <p>Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
            </body>
            </html>
            '''
            
            book.add_item(chapter)
            chapters.append(chapter)
            toc.append(epub.Link(f'chap_{i:02d}.xhtml', f'Chapter {i}', f'chap{i:02d}'))
        
        # Table of Contents
        book.toc = tuple(toc)
        
        # Navigation
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # Spine
        book.spine = ['nav'] + chapters
        
        # Save
        output_path = self.output_dir / 'medium_test_novel.epub'
        epub.write_epub(str(output_path), book, {})
        
        print(f"✅ Created: {output_path}")
        return str(output_path)
    
    def create_large_epub(self) -> str:
        """
        Create a large EPUB (50 chapters)
        For stress testing
        """
        book = epub.EpubBook()
        
        # Metadata
        book.set_identifier('large_test_001')
        book.set_title('Large Epic Novel')
        book.set_language('en')
        book.add_author('Epic Author')
        book.add_metadata('DC', 'description', 'A large epic novel for stress testing')
        
        chapters = []
        toc = []
        
        # Create 50 chapters
        for i in range(1, 51):
            chapter = epub.EpubHtml(
                title=f'Chapter {i}',
                file_name=f'chap_{i:03d}.xhtml',
                lang='en'
            )
            
            # Generate longer content
            paragraphs = []
            for j in range(10):  # 10 paragraphs per chapter
                paragraphs.append(
                    f"<p>Paragraph {j+1} of chapter {i}. "
                    f"This paragraph contains sample text to simulate a real novel. "
                    f"The story unfolds with each passing chapter, revealing new characters and plot twists. "
                    f"Our hero faces challenges, meets allies, and overcomes obstacles in their quest.</p>"
                )
            
            chapter.content = f'''
            <html>
            <head><title>Chapter {i}</title></head>
            <body>
            <h1>Chapter {i}: The Journey</h1>
            {"".join(paragraphs)}
            </body>
            </html>
            '''
            
            book.add_item(chapter)
            chapters.append(chapter)
            toc.append(epub.Link(f'chap_{i:03d}.xhtml', f'Chapter {i}', f'chap{i:03d}'))
        
        # Table of Contents
        book.toc = tuple(toc)
        
        # Navigation
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # Spine
        book.spine = ['nav'] + chapters
        
        # Save
        output_path = self.output_dir / 'large_epic_novel.epub'
        epub.write_epub(str(output_path), book, {})
        
        print(f"✅ Created: {output_path}")
        return str(output_path)
    
    def create_special_chars_epub(self) -> str:
        """
        Create EPUB with special characters and formatting
        For testing edge cases
        """
        book = epub.EpubBook()
        
        # Metadata
        book.set_identifier('special_test_001')
        book.set_title('Special Characters & Formatting Test')
        book.set_language('en')
        book.add_author('Test Author')
        
        # Chapter with special characters
        c1 = epub.EpubHtml(
            title='Special Characters',
            file_name='chap_01.xhtml',
            lang='en'
        )
        c1.content = '''
        <html>
        <head><title>Special Characters</title></head>
        <body>
        <h1>Chapter 1: Special Characters</h1>
        <p>This chapter tests various special characters:</p>
        <ul>
        <li>Quotes: "Hello" and 'World'</li>
        <li>Apostrophes: It's and don't</li>
        <li>Dashes: em-dash — and en-dash –</li>
        <li>Math: x² + y² = z²</li>
        <li>Currency: $100 €50 £25 ¥1000</li>
        <li>Symbols: © ® ™ • ‰ °</li>
        </ul>
        <p>Émphasis on spëcial charactërs! Ñoño says ¡Hola!</p>
        </body>
        </html>
        '''
        
        # Chapter with HTML tags
        c2 = epub.EpubHtml(
            title='HTML Formatting',
            file_name='chap_02.xhtml',
            lang='en'
        )
        c2.content = '''
        <html>
        <head><title>HTML Formatting</title></head>
        <body>
        <h1>Chapter 2: HTML Formatting</h1>
        <p>This chapter has <strong>bold text</strong> and <em>italic text</em>.</p>
        <p>It also has <code>code blocks</code> and <del>deleted text</del>.</p>
        <blockquote>
        This is a blockquote that should be properly handled.
        </blockquote>
        <p>Line breaks should<br/>work correctly<br/>like this.</p>
        </body>
        </html>
        '''
        
        book.add_item(c1)
        book.add_item(c2)
        
        book.toc = (
            epub.Link('chap_01.xhtml', 'Special Characters', 'chap01'),
            epub.Link('chap_02.xhtml', 'HTML Formatting', 'chap02')
        )
        
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ['nav', c1, c2]
        
        output_path = self.output_dir / 'special_characters_test.epub'
        epub.write_epub(str(output_path), book, {})
        
        print(f"✅ Created: {output_path}")
        return str(output_path)
    
    def generate_all(self):
        """Generate all sample EPUBs"""
        print("\n📚 Generating Sample EPUB Files")
        print("="*60)
        
        self.create_minimal_epub()
        self.create_medium_epub()
        self.create_large_epub()
        self.create_special_chars_epub()
        
        print("\n✅ All sample EPUBs created successfully!")
        print(f"📁 Location: {self.output_dir}")
        print("\nGenerated files:")
        print("  • minimal_test.epub (2 chapters) - Quick tests")
        print("  • medium_test_novel.epub (10 chapters) - Standard tests")
        print("  • large_epic_novel.epub (50 chapters) - Stress tests")
        print("  • special_characters_test.epub (2 chapters) - Edge cases")
        print("="*60 + "\n")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate sample EPUB files")
    parser.add_argument(
        '--type',
        choices=['minimal', 'medium', 'large', 'special', 'all'],
        default='all',
        help='Which EPUB to generate'
    )
    parser.add_argument(
        '--output',
        default='examples/sample_epubs',
        help='Output directory'
    )
    
    args = parser.parse_args()
    
    generator = EPUBGenerator(output_dir=args.output)
    
    if args.type == 'minimal':
        generator.create_minimal_epub()
    elif args.type == 'medium':
        generator.create_medium_epub()
    elif args.type == 'large':
        generator.create_large_epub()
    elif args.type == 'special':
        generator.create_special_chars_epub()
    else:
        generator.generate_all()


if __name__ == "__main__":
    main()

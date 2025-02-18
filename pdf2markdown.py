import sys
import PyPDF2
import re

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file"""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text()
    return full_text

def convert_to_markdown(text):
    """Convert extracted text to markdown"""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Convert headings
    text = re.sub(r'^(\d+)\.\s*(.+)$', r'## \1. \2', text, flags=re.MULTILINE)
    
    # Convert bullet points
    text = re.sub(r'•\s*', '- ', text)
    
    # Handle numbered lists
    text = re.sub(r'^(\d+)\)\s*', r'\1. ', text, flags=re.MULTILINE)
    
    # Emphasize important sections
    text = re.sub(r'(Key Findings|Implications|Conclusion):', r'**\1:**', text)
    
    return text

def save_markdown(markdown_text, output_path):
    """Save markdown text to a file"""
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(markdown_text)

def main():
    if len(sys.argv) != 3:
        print("Usage: python pdf_to_markdown.py input.pdf output.md")
        sys.exit(1)
    
    input_pdf = sys.argv[1]
    output_md = sys.argv[2]
    
    # Extract text
    pdf_text = extract_text_from_pdf(input_pdf)
    
    # Convert to markdown
    markdown_text = convert_to_markdown(pdf_text)
    
    # Save markdown
    save_markdown(markdown_text, output_md)
    
    print(f"Markdown file saved to {output_md}")

if __name__ == "__main__":
    main()



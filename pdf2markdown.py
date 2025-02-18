import sys
from typing import List, Dict
from pathlib import Path
import logging
import pdfplumber

# PDF parsing libraries
#import pdfplumber
import pytesseract
from PIL import Image
import pdf2image

# Markdown generation
import markdown2 #Future improvements.. 

LOG_LEVEL=logging.DEBUG
logger=logging.getLogger(__name__)
logging.basicConfig(level=LOG_LEVEL)


class AdvancedPDFMarkdownConverter:
    """
    Advanced PDF to Markdown converter with support for complex formatting, tables, and images.
    
    Supports:
    - Advanced text extraction
    - Table parsing
    - Image extraction and OCR
    - Preserving complex layouts
    """

    def __init__(self, log_level: int = LOG_LEVEL):
        """
        Initialize the advanced PDF converter.
        
        Args:
            log_level (int): Logging verbosity level
        """
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Tesseract configuration for OCR
        pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Adjust path as needed

    def extract_text_with_layout(self, pdf_path: Path) -> Dict[str, List[Dict]]:
        """
        Extract text with preservation of layout and formatting.
        
        Args:
            pdf_path (Path): Path to PDF file
        
        Returns:
            Dict containing text elements with their formatting
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page_contents = []
                
                for page in pdf.pages:
                    # Extract text with layout information
                    page_text = {
                        'text': page.extract_text(),
                        'tables': self._extract_tables(page),
                        'layout_elements': self._analyze_layout(page)
                    }
                    page_contents.append(page_text)
                
            return page_contents
        
        except Exception as e:
            self.logger.error(f"ERROR: extract_text_with_layout: Text extraction error: {e}")
            raise

    def _extract_tables(self, page):
        """
        Extract tables from a PDF page.
        
        Args:
            page: PDF page object
        
        Returns:
            List of extracted tables
        """
        try:
            tables = page.extract_tables()
            markdown_tables = []
            
            for table in tables:
                md_table = self._convert_table_to_markdown(table)
                markdown_tables.append(md_table)
            
            return markdown_tables
        
        except Exception as e:
            self.logger.error(f"ERROR: _extract_tables: Table extraction error: {e}")
            return []

    def _convert_table_to_markdown(self, table: Dict) -> str:
        """
        Convert a table to markdown format.
        
        Args:
            table (List[List]): Table data
        
        Returns:
            str: Markdown-formatted table
        """
        if not table:
            return ""
        
        # Create markdown table headers
        headers = table[0]
        md_table = "| " + " | ".join(headers) + " |\n"
        md_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
        
        # Add rows
        for row in table[1:]:
            md_table += "| " + " | ".join(str(cell) for cell in row) + " |\n"
        
        return md_table

    def _analyze_layout(self, page):
        """
        Analyze page layout, detect headings, paragraphs, etc.
        
        Args:
            page: PDF page object
        
        Returns:
            Dict of layout elements
        """
        # Placeholder for advanced layout analysis
        # Could use font size, bold/italic detection, etc.
        return {}

    def extract_images(self, pdf_path: Path) -> List[Path]:
        """
        Extract images from PDF with OCR support.
        
        Args:
            pdf_path (Path): Path to PDF file
        
        Returns:
            List of extracted image paths
        """
        try:
            images = pdf2image.convert_from_path(str(pdf_path))
            extracted_images = []
            logger.info(f"Extracted images: array with len(extracted_images) images")
            
            for i, image in enumerate(images):
                logger.info(f"Extracting image {i}: {image}") 
                output_path = pdf_path.parent / f"page_{i+1}_image.png"
                image.save(output_path, 'PNG')
                extracted_images.append(output_path)
            
            return extracted_images
        
        except Exception as e:
            self.logger.error(f"Image extraction error: {e}")
            raise

    def perform_ocr(self, image_path: Path) -> str:
        """
        Perform OCR on an image.
        
        Args:
            image_path (Path): Path to image file
        
        Returns:
            str: Extracted text
        """
        try:
            image = Image.open(image_path)
            ocr_text = pytesseract.image_to_string(image)
            logger.info(f"Extracted {ocr_text} from {image}")
            return ocr_text
        
        except Exception as e:
            self.logger.warning(f"OCR error for {image_path}: {e}")
            return ""

    def convert_to_markdown(self, page_contents: Dict) -> str:
        """
        Convert extracted content to rich markdown.
        
        Args:
            page_contents (Dict): Extracted page contents
        
        Returns:
            str: Markdown formatted document
        """
        markdown_content = ""
        
        for page in page_contents:
            # Add page text
            markdown_content += page['text'] + "\n\n"
            
            # Add tables
            for table in page.get('tables', []):
                markdown_content += table + "\n\n"
                logger.debug(f"Added table to md: {markdown_content}")
        
        return markdown_content

    def convert(self, input_pdf: Path, output_md: Path) -> bool:
        """
        Main conversion method.
        
        Args:
            input_pdf (Path): Input PDF path
            output_md (Path): Output markdown path
        """
        try:
            # Extract content
            page_contents = self.extract_text_with_layout(input_pdf)
            
            # Convert to markdown
            markdown_text = self.convert_to_markdown(page_contents)
            
            # Extract images
            images = self.extract_images(input_pdf)
            
            # Perform OCR on images if needed
            for image in images:
                logger.debug(f"Extracting OCR from {image}") 
                ocr_text = self.perform_ocr(image)
                markdown_text += f"\n\n## OCR Text from {image.name}\n{ocr_text}\n"
                logger.debug(f"Added image {image} to md")
            
            # Save markdown
            with output_md.open('w', encoding='utf-8') as f:
                f.write(markdown_text)
            
            self.logger.info(f"Markdown saved to {output_md}")
            return True

        except Exception as e:
            self.logger.error(f"Conversion failed: {e}")
            raise

def main():
    """Command-line entry point for PDF to markdown conversion."""
    if len(sys.argv) != 3:
        logger.error ("ERROR: USAGE: python pdf2markdown.py input.pdf output.md")
        sys.exit(1)
    
    input_pdf = Path(sys.argv[1])
    output_md = Path(sys.argv[2])
    
    converter = AdvancedPDFMarkdownConverter(log_level=LOG_LEVEL)
    
    try:
        if converter.convert(input_pdf, output_md):
            sys.exit(0)
    except Exception as e:
        logger.error (f"ERROR: Failed due to {e}") 
        sys.exit(1)

if __name__ == "__main__":
    main()
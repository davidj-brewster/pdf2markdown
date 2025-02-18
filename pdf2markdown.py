import sys
from typing import List, Dict, Tuple
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


class Rect:
    """Rectangle representation for bounding box operations."""
    def __init__(self, bbox: Tuple[float, float, float, float]):
        self.x0 = bbox[0]
        self.y0 = bbox[1]
        self.x1 = bbox[2]
        self.y1 = bbox[3]

    def contains(self, other: 'Rect') -> bool:
        """Check if this rectangle contains another rectangle."""
        return (self.x0 <= other.x0 and self.y0 <= other.y0 and
                self.x1 >= other.x1 and self.y1 >= other.y1)

    def intersects(self, other: 'Rect') -> bool:
        """Check if this rectangle intersects with another rectangle."""
        return not (self.x1 < other.x0 or self.x0 > other.x1 or
                   self.y1 < other.y0 or self.y0 > other.y1)

    def __repr__(self) -> str:
        return f"Rect({self.x0}, {self.y0}, {self.x1}, {self.y1})"


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

    def _analyze_layout(self, page) -> Dict:
        """
        Analyze page layout, detect headings, paragraphs, etc.
        
        Args:
            page: PDF page object

        Returns:
            Dict of layout elements
        """
        layout_elements = {
            'text_blocks': [],
            'headers': [],
            'paragraphs': []
        }

        try:
            # Extract words with position information
            words = page.extract_words(x_tolerance=3, y_tolerance=3, keep_blank_chars=True)
            self.logger.debug(f"Extracted {len(words)} words")

            # Get raw text with layout information
            raw_dict = page.extract_text(x_tolerance=3, y_tolerance=3, layout=True, return_chars=True)
            if raw_dict:
                chars = raw_dict.get('chars', [])
                self.logger.debug(f"Extracted {len(chars)} characters with layout info")
                
                # Group characters into text blocks
                current_size = None
                current_text = []
                
                for char in chars:
                    if 'size' in char and char['size'] != current_size:
                        if current_text:
                            layout_elements['text_blocks'].append({
                                'text': ''.join(current_text),
                                'size': current_size
                            })
                            current_text = []
                        current_size = char['size']
                    current_text.append(char['text'])
                
                # Add final text block if exists
                if current_text:
                    layout_elements['text_blocks'].append({
                        'text': ''.join(current_text),
                        'size': current_size
                    })

            return layout_elements

        except Exception as e:
            self.logger.error(f"Layout analysis error: {e}")
            return layout_elements 
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

    def extract_content(self, pdf_path: Path) -> Dict:
        """
        Extract text and identify image locations in the PDF.
        
        Args:
            pdf_path (Path): Path to the PDF file
        
        Returns:
            Dict containing text content and image information
        """
        content = {
            'text': [],
            'images': []
        }

        try:
            with pdfplumber.open(pdf_path) as pdf:
                self.logger.info(f"Processing PDF with {len(pdf.pages)} pages")
                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract text
                    try:
                        self.logger.debug(f"Processing page {page_num}")
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            content['text'].append(page_text)
                            self.logger.debug(f"Extracted {len(page_text)} characters from page {page_num}")
                        else:
                            self.logger.warning(f"No text extracted from page {page_num}")
                    
                        # Identify images
                        if hasattr(page, 'images'):
                            for img in page.images:
                                self.logger.debug(f"Found image on page {page_num} with bbox: {img.get('bbox')}")
                                if 'bbox' in img:
                                    img_bbox = Rect(img['bbox'])
                                    content['images'].append({
                                        'page': page_num,
                                        'bbox': img_bbox
                                    })
                                else:
                                    self.logger.warning(f"Image on page {page_num} has no bbox")
                        else:
                            self.logger.debug(f"No images found on page {page_num}")
                    except Exception as e:
                        self.logger.error(f"Error processing page {page_num}: {str(e)}", exc_info=True)
                        continue
        
        except Exception as e:
            self.logger.error(f"Error extracting PDF content: {str(e)}", exc_info=True)
            raise

        return content

    def process_images(self, pdf_path: Path, images: List[Dict]) -> List[str]:
        """
        Process images that might require OCR.
        
        Args:
            pdf_path (Path): Path to the PDF file
            images (List[Dict]): List of image locations
        
        Returns:
            List of extracted image texts
        """
        if not images:
            return []

        image_texts = []
        try:
            # Convert only specified pages with images
            pages = pdf2image.convert_from_path(
                str(pdf_path), 
                first_page=images[0]['page'], 
                last_page=images[-1]['page']
            )

            for img_info in images:
                page_index = img_info['page'] - 1
                image = pages[page_index]
                
                try:
                    # Crop the specific image area if bbox is available
                    if 'bbox' in img_info:
                        self.logger.debug(f"Processing image on page {img_info['page']} with bbox: {img_info['bbox']}")
                        bbox = img_info['bbox']
                        image = image.crop((
                            bbox.x0, bbox.y0,
                            bbox.x1, bbox.y1
                        ))
                except Exception as e:
                    self.logger.error(f"Error cropping image on page {img_info['page']}: {e}")
                    continue
                
                # Perform OCR
                ocr_text = pytesseract.image_to_string(image)
                if ocr_text.strip():
                    image_texts.append(f"Image text (Page {img_info['page']}):\n{ocr_text}")
        
        except Exception as e:
            self.logger.error(f"Error processing images: {e}")
        
        return image_texts

    def convert_to_markdown(self, content: Dict) -> str:
        """
        Convert extracted content to markdown.
        
        Args:
            content (Dict): Extracted PDF content
        
        Returns:
            str: Markdown-formatted document
        """
        markdown_content = ""
        
        # Add text content
        for page_text in content['text']:
            markdown_content += page_text + "\n\n"
        
        # Add image texts
        if content.get('image_texts'):
            markdown_content += "## Extracted Image Texts\n\n"
            for img_text in content['image_texts']:
                markdown_content += img_text + "\n\n"
        
        return markdown_content

    def convert(self, input_pdf: Path, output_md: Path) -> None:
        """
        Main conversion method.
        
        Args:
            input_pdf (Path): Input PDF path
            output_md (Path): Output markdown path
        """
        try:
            # Extract content
            content = self.extract_content(input_pdf)
            
            # Process images if any
            if content['images']:
                content['image_texts'] = self.process_images(input_pdf, content['images'])
            
            # Convert to markdown
            markdown_text = self.convert_to_markdown(content)
            
            # Save markdown
            with output_md.open('w', encoding='utf-8') as f:
                f.write(markdown_text)
            
            self.logger.info(f"Markdown saved to {output_md}")
        
        except Exception as e:
            self.logger.error(f"Conversion failed: {e}")
            raise

def main():
    """Command-line entry point for PDF to markdown conversion."""
    try:
        if len(sys.argv) != 3:
            logger.error("USAGE: python pdf2markdown.py input.pdf output.md")
            sys.exit(1)
        
        input_pdf = Path(sys.argv[1])
        output_md = Path(sys.argv[2])
        
        if not input_pdf.exists():
            logger.error(f"Input file not found: {input_pdf}")
            sys.exit(1)
        
        if not input_pdf.suffix.lower() == '.pdf':
            logger.error(f"Input file must be a PDF: {input_pdf}")
            sys.exit(1)
        
        converter = AdvancedPDFMarkdownConverter(log_level=LOG_LEVEL)
        logger.info(f"Starting conversion of {input_pdf} to {output_md}")
        
        content = converter.extract_content(input_pdf)
        converted_md = converter.convert_to_markdown(content)
        with output_md.open('w', encoding='utf-8') as f:
            f.write(converted_md)
            logger.info(f"Markdown saved to {output_md}")
            sys.exit(0)
        
    except Exception as e:
        logger.error (f"ERROR: Failed due to {e}") 
        sys.exit(1)

if __name__ == "__main__":
    main()
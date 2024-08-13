from fpdf import FPDF
import os


class InvoicePDF(FPDF):
    def __init__(self):
        super().__init__()
        # Specify the directory where your font files are located
        font_dir = os.path.join(os.path.dirname(__file__), 'fonts')

        self.add_font('DejaVu', '', os.path.join(font_dir, 'DejaVuSansCondensed.ttf'), uni=True)
        self.add_font('DejaVu', 'B', os.path.join(font_dir, 'DejaVuSansCondensed-Bold.ttf'), uni=True)
        self.add_font('DejaVu', 'I', os.path.join(font_dir, 'DejaVuSansCondensed-Oblique.ttf'), uni=True)

    def header(self):
        """Header of the PDF"""
        self.set_font('DejaVu', 'B', 12)
        self.cell(0, 10, 'Invoice', 0, 1, 'C')

    def footer(self):
        """Footer of the PDF"""
        self.set_y(-15)
        self.set_font('DejaVu', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        """Title of a chapter"""
        self.set_font('DejaVu', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(10)

    def chapter_body(self, body):
        """Body of a chapter"""
        self.set_font('DejaVu', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

    def add_order_items(self, items):
        """Add order items to the PDF"""
        self.set_font('DejaVu', 'B', 10)
        self.cell(80, 10, 'Product', 1)
        self.cell(30, 10, 'Price', 1)
        self.cell(20, 10, 'Quantity', 1)
        self.cell(30, 10, 'Subtotal', 1)
        self.ln()

        self.set_font('DejaVu', '', 10)
        for item in items:
            self.cell(80, 10, item.product.product_name, 1)
            self.cell(30, 10, f"₹{item.product.offer_price:.2f}", 1)
            self.cell(20, 10, str(item.quantity), 1)
            self.cell(30, 10, f"₹{item.get_subtotal():.2f}", 1)
            self.ln()

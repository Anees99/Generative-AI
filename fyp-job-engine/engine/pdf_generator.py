"""
PDF Generator Module - ATS-Friendly Resume PDF Creation

This module generates clean, ATS-compliant PDF resumes using fpdf2.
Includes match scores and tailored bullet points in professional format.

Conceptually inspired by Career-Ops (MIT License) - Python re-engineering.
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from fpdf import FPDF

logger = logging.getLogger(__name__)


class ResumePDF(FPDF):
    """Custom PDF class for resume generation with header/footer support."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.job_title = ""
        self.company = ""
        self.match_score = 0
    
    def header(self):
        """Add header to each page."""
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Tailored Resume - {self.job_title} at {self.company}', 0, 1, 'R')
        self.ln(5)
    
    def footer(self):
        """Add footer with page numbers."""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')


class PDFGenerator:
    """
    Generates ATS-friendly PDF resumes with match scores and tailored content.
    
    Features:
    - Clean, professional layout
    - ATS-optimized formatting (no columns, standard fonts)
    - Match score display
    - Tailored bullet points integration
    - Timestamp and cost tracking
    """
    
    def __init__(self, output_dir: str = 'output'):
        """
        Initialize the PDF generator.
        
        Args:
            output_dir: Directory to save generated PDFs
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_resume(
        self,
        candidate_name: str,
        candidate_email: str,
        candidate_phone: str,
        candidate_location: str,
        job_title: str,
        company: str,
        match_score: float,
        tailored_content: Dict[str, Any],
        original_resume: str = "",
        cost_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a tailored resume PDF.
        
        Args:
            candidate_name: Candidate's full name
            candidate_email: Email address
            candidate_phone: Phone number
            candidate_location: City, State
            job_title: Target job title
            company: Target company name
            match_score: AI-calculated match score (0-100)
            tailored_content: Dictionary containing:
                - summary: Professional summary
                - skills: List of skills
                - experience: List of experience entries
                - tailored_bullets: Job-specific bullet points
            original_resume: Original resume text (for reference)
            cost_info: Optional dict with token_count and cost_usd
            
        Returns:
            Path to the generated PDF file
        """
        pdf = ResumePDF()
        pdf.job_title = job_title
        pdf.company = company
        pdf.match_score = match_score
        
        # Add a page
        pdf.add_page()
        
        # Set up fonts - use built-in Arial font (no external files needed)
        # Note: DejaVu fonts would provide better Unicode support but require font files
        
        # Header - Contact Information
        self._add_contact_header(pdf, candidate_name, candidate_email, 
                                  candidate_phone, candidate_location)
        
        # Match Score Banner
        self._add_match_score_banner(pdf, job_title, company, match_score)
        
        # Professional Summary
        summary = tailored_content.get('summary', '')
        if summary:
            self._add_section(pdf, 'PROFESSIONAL SUMMARY', summary)
        
        # Tailored Bullet Points (Job-Specific)
        tailored_bullets = tailored_content.get('tailored_bullets', [])
        if tailored_bullets:
            self._add_tailored_bullets(pdf, tailored_bullets)
        
        # Skills Section
        skills = tailored_content.get('skills', [])
        if skills:
            self._add_skills_section(pdf, skills)
        
        # Experience Section
        experience = tailored_content.get('experience', [])
        if experience:
            self._add_experience_section(pdf, experience)
        
        # Additional Info (cost tracking, timestamp)
        self._add_footer_info(pdf, cost_info)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_company = ''.join(c for c in company if c.isalnum() or c in ' -_').strip()[:30]
        safe_title = ''.join(c for c in job_title if c.isalnum() or c in ' -_').strip()[:30]
        filename = f"resume_{safe_title}_{safe_company}_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Save PDF
        try:
            pdf.output(filepath)
            logger.info(f"PDF generated successfully: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to save PDF: {e}")
            # Fallback to basic filename
            fallback_filename = f"tailored_resume_{timestamp}.pdf"
            fallback_filepath = os.path.join(self.output_dir, fallback_filename)
            pdf.output(fallback_filepath)
            logger.info(f"PDF saved with fallback filename: {fallback_filepath}")
            return fallback_filepath
    
    def _add_contact_header(self, pdf: ResumePDF, name: str, email: str, 
                            phone: str, location: str):
        """Add contact information header."""
        # Name
        pdf.set_font('Arial', 'B', 20)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 10, name.upper(), 0, 1, 'C')
        
        # Contact info
        pdf.set_font('Arial', '', 10)
        pdf.set_text_color(80, 80, 80)
        contact_line = f"{email} | {phone} | {location}"
        pdf.cell(0, 6, contact_line, 0, 1, 'C')
        pdf.ln(5)
    
    def _add_match_score_banner(self, pdf: ResumePDF, job_title: str, 
                                 company: str, score: float):
        """Add a banner showing the target position and match score."""
        # Background rectangle
        pdf.set_fill_color(240, 240, 240)
        pdf.rect(10, pdf.get_y(), 190, 25, 'F')
        
        # Job title and company
        pdf.set_font('Arial', 'B', 12)
        pdf.set_text_color(40, 40, 40)
        pdf.set_xy(15, pdf.get_y() + 5)
        pdf.cell(140, 8, f"Position: {job_title}", 0, 0)
        
        # Match score
        pdf.set_font('Arial', 'B', 14)
        if score >= 80:
            pdf.set_text_color(0, 150, 0)  # Green
        elif score >= 60:
            pdf.set_text_color(200, 150, 0)  # Orange
        else:
            pdf.set_text_color(200, 50, 50)  # Red
        
        pdf.cell(35, 8, f"Match: {score:.0f}%", 0, 1, 'R')
        
        pdf.set_font('Arial', 'I', 10)
        pdf.set_text_color(100, 100, 100)
        pdf.set_x(15)
        pdf.cell(0, 6, f"Company: {company}", 0, 1)
        
        pdf.ln(8)
    
    def _add_section(self, pdf: ResumePDF, title: str, content: str):
        """Add a text section with title."""
        pdf.set_font('Arial', 'B', 12)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 8, title, 0, 1)
        
        # Underline
        pdf.set_draw_color(40, 40, 40)
        pdf.line(10, pdf.get_y() - 2, 200, pdf.get_y() - 2)
        
        pdf.set_font('Arial', '', 10)
        pdf.set_text_color(60, 60, 60)
        
        # Multi-line content with proper wrapping
        y_start = pdf.get_y()
        pdf.multi_cell(0, 6, content)
        
        # Check if we need a new page
        if pdf.get_y() > 250:
            pdf.add_page()
        
        pdf.ln(3)
    
    def _add_tailored_bullets(self, pdf: ResumePDF, bullets: list):
        """Add tailored bullet points section."""
        pdf.set_font('Arial', 'B', 12)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 8, "JOB-SPECIFIC HIGHLIGHTS", 0, 1)
        
        # Underline
        pdf.set_draw_color(40, 40, 40)
        pdf.line(10, pdf.get_y() - 2, 200, pdf.get_y() - 2)
        
        pdf.set_font('Arial', '', 10)
        pdf.set_text_color(60, 60, 60)
        
        for bullet in bullets[:5]:  # Limit to 5 bullets
            if pdf.get_y() > 250:
                pdf.add_page()
            
            # Clean bullet text - use ASCII hyphen instead of unicode bullet
            clean_bullet = bullet.strip().lstrip('•-*').strip()
            pdf.set_x(15)  # Set proper indentation
            pdf.multi_cell(0, 6, f"- {clean_bullet}")
        
        pdf.ln(3)
    
    def _add_skills_section(self, pdf: ResumePDF, skills: list):
        """Add skills section."""
        if not skills:
            return
        
        pdf.set_font('Arial', 'B', 12)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 8, "KEY SKILLS", 0, 1)
        
        # Underline
        pdf.set_draw_color(40, 40, 40)
        pdf.line(10, pdf.get_y() - 2, 200, pdf.get_y() - 2)
        
        pdf.set_font('Arial', '', 10)
        pdf.set_text_color(60, 60, 60)
        
        # Format skills as comma-separated list
        if isinstance(skills, list):
            skills_text = ', '.join(str(s) for s in skills[:15])  # Limit skills
        else:
            skills_text = str(skills)
        
        pdf.multi_cell(0, 6, skills_text)
        pdf.ln(3)
    
    def _add_experience_section(self, pdf: ResumePDF, experience: list):
        """Add work experience section."""
        if not experience:
            return
        
        pdf.set_font('Arial', 'B', 12)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 8, "WORK EXPERIENCE", 0, 1)
        
        # Underline
        pdf.set_draw_color(40, 40, 40)
        pdf.line(10, pdf.get_y() - 2, 200, pdf.get_y() - 2)
        
        pdf.set_font('Arial', '', 10)
        pdf.set_text_color(60, 60, 60)
        
        for exp in experience[:3]:  # Limit to 3 most recent positions
            if pdf.get_y() > 240:
                pdf.add_page()
            
            if isinstance(exp, dict):
                title = exp.get('title', 'Position')
                company = exp.get('company', 'Company')
                duration = exp.get('duration', '')
                bullets = exp.get('bullets', [])
                
                # Job title and company
                pdf.set_font('Arial', 'B', 11)
                pdf.cell(0, 6, f"{title} - {company}", 0, 1)
                
                # Duration
                pdf.set_font('Arial', 'I', 9)
                pdf.set_text_color(100, 100, 100)
                pdf.cell(0, 5, duration, 0, 1)
                
                # Bullets
                pdf.set_font('Arial', '', 10)
                pdf.set_text_color(60, 60, 60)
                for bullet in bullets[:4]:
                    if pdf.get_y() > 250:
                        pdf.add_page()
                    clean_bullet = bullet.strip().lstrip('•-*').strip()
                    pdf.set_x(15)
                    pdf.multi_cell(0, 5, f"- {clean_bullet}")
                
                pdf.ln(2)
            else:
                # Plain text experience entry
                pdf.multi_cell(0, 6, str(exp))
                pdf.ln(2)
    
    def _add_footer_info(self, pdf: ResumePDF, cost_info: Optional[Dict[str, Any]]):
        """Add footer with generation info and cost tracking."""
        pdf.ln(5)
        
        # Separator line
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        
        pdf.set_font('Arial', 'I', 8)
        pdf.set_text_color(150, 150, 150)
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        pdf.cell(0, 5, f"Generated: {timestamp}", 0, 1)
        
        if cost_info:
            token_count = cost_info.get('token_count', 0)
            cost_usd = cost_info.get('cost_usd', 0.0)
            pdf.cell(0, 5, f"AI Analysis - Tokens: {token_count}, Cost: ${cost_usd:.4f}", 0, 1)
        
        pdf.cell(0, 5, "This resume was AI-tailored for a specific position. Review before submitting.", 0, 1)
    
    def generate_simple_pdf(self, content: str, title: str = "Document") -> str:
        """
        Generate a simple PDF from plain text content.
        
        Args:
            content: Plain text content
            title: Document title
            
        Returns:
            Path to the generated PDF
        """
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, title, 0, 1, 'C')
        pdf.ln(10)
        
        pdf.set_font('Arial', '', 11)
        
        # Split content into lines and add to PDF
        for line in content.split('\n'):
            if pdf.get_y() > 270:
                pdf.add_page()
            pdf.multi_cell(0, 7, line)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{title.lower().replace(' ', '_')}_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        pdf.output(filepath)
        logger.info(f"Simple PDF generated: {filepath}")
        return filepath


# Example usage for testing
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    generator = PDFGenerator()
    
    # Test data
    tailored_content = {
        'summary': 'Experienced software engineer with 5+ years developing scalable web applications.',
        'skills': ['Python', 'JavaScript', 'React', 'Node.js', 'AWS', 'Docker'],
        'experience': [
            {
                'title': 'Senior Software Engineer',
                'company': 'Tech Corp',
                'duration': '2020 - Present',
                'bullets': [
                    'Led development of microservices architecture serving 1M+ users',
                    'Reduced API response time by 40% through optimization',
                    'Mentored team of 5 junior developers'
                ]
            }
        ],
        'tailored_bullets': [
            'Expert in Python and modern web frameworks',
            'Proven track record of building scalable systems',
            'Strong problem-solving and communication skills'
        ]
    }
    
    filepath = generator.generate_resume(
        candidate_name='John Doe',
        candidate_email='john.doe@email.com',
        candidate_phone='(555) 123-4567',
        candidate_location='San Francisco, CA',
        job_title='Software Engineer',
        company='Example Inc',
        match_score=85.5,
        tailored_content=tailored_content,
        cost_info={'token_count': 1250, 'cost_usd': 0.0015}
    )
    
    print(f"Generated PDF: {filepath}")

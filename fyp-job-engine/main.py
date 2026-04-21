"""
AI Job Search & Resume Tailoring Engine - Main Desktop Application

This is the main entry point for the desktop GUI application built with CustomTkinter.
It provides a modern, dark/light mode interface for job analysis and resume tailoring.

Features:
- Multi-threaded processing to prevent UI blocking
- Real-time progress tracking
- Cost transparency display
- Local database integration
- PDF generation with user review

Conceptually inspired by Career-Ops (MIT License) - Python re-engineering.
"""

import os
import sys
import logging
import threading
import webbrowser
from typing import Optional, Dict, Any
from datetime import datetime

import customtkinter as ctk
from dotenv import load_dotenv

# Import project modules
from engine.scraper import JobScraper
from engine.ai_processor import AIProcessor
from engine.pdf_generator import PDFGenerator
from core.database import Database
from core.cost_tracker import CostTracker

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class AnalysisWorker(threading.Thread):
    """Background worker thread for job analysis to prevent UI blocking."""
    
    def __init__(self, callback, error_callback, job_url: str, resume_text: str):
        super().__init__()
        self.callback = callback
        self.error_callback = error_callback
        self.job_url = job_url
        self.resume_text = resume_text
        self.daemon = True
    
    def run(self):
        try:
            # Initialize components
            scraper = JobScraper()
            processor = AIProcessor()
            
            # Step 1: Scrape job posting
            logger.info("Step 1: Scraping job posting...")
            job_data = scraper.scrape_job_sync(self.job_url)
            
            if not job_data:
                raise Exception("Failed to scrape job posting. Please check the URL.")
            
            # Step 2: Analyze with AI
            logger.info("Step 2: Analyzing job match...")
            analysis_result = processor.analyze_job(
                job_data['description'],
                self.resume_text
            )
            
            # Combine results
            result = {
                'job_data': job_data,
                'analysis': analysis_result
            }
            
            self.callback(result)
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            self.error_callback(str(e))


class TailoringWorker(threading.Thread):
    """Background worker thread for resume tailoring."""
    
    def __init__(self, callback, error_callback, job_description: str, resume_text: str):
        super().__init__()
        self.callback = callback
        self.error_callback = error_callback
        self.job_description = job_description
        self.resume_text = resume_text
        self.daemon = True
    
    def run(self):
        try:
            processor = AIProcessor()
            
            logger.info("Tailoring resume...")
            tailored_result = processor.tailor_resume(
                self.job_description,
                self.resume_text
            )
            
            self.callback(tailored_result)
            
        except Exception as e:
            logger.error(f"Tailoring error: {e}")
            self.error_callback(str(e))


class JobSearchApp(ctk.CTk):
    """Main application window for the AI Job Search Engine."""
    
    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.title("AI Job Search & Resume Tailoring Engine")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        
        # Set appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize components
        self.scraper = None
        self.processor = None
        self.pdf_generator = PDFGenerator()
        self.database = Database()
        self.cost_tracker = CostTracker()
        
        # State variables
        self.current_analysis = None
        self.current_tailored_content = None
        
        # Build UI
        self._create_ui()
        
        # Log startup
        logger.info("Application started")
    
    def _create_ui(self):
        """Create the main user interface."""
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # === Header ===
        header_frame = ctk.CTkFrame(self, corner_radius=0)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="🎯 AI Job Search & Resume Tailoring Engine",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=15, sticky="w")
        
        # Provider info
        provider = os.getenv('LLM_PROVIDER', 'openai')
        model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini') if provider == 'openai' else os.getenv('GOOGLE_MODEL', 'gemini-1.5-flash')
        provider_label = ctk.CTkLabel(
            header_frame,
            text=f"Provider: {provider.upper()} | Model: {model}",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        provider_label.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")
        
        # === Left Panel - Input ===
        left_panel = ctk.CTkFrame(self)
        left_panel.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=10)
        left_panel.grid_rowconfigure(2, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)
        
        # Job URL input
        url_label = ctk.CTkLabel(left_panel, text="Job Posting URL:", font=ctk.CTkFont(weight="bold"))
        url_label.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")
        
        self.url_entry = ctk.CTkEntry(left_panel, placeholder_text="https://example.com/job/123", height=40)
        self.url_entry.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="ew")
        
        # Resume text input
        resume_label = ctk.CTkLabel(left_panel, text="Your Resume:", font=ctk.CTkFont(weight="bold"))
        resume_label.grid(row=2, column=0, padx=15, pady=(15, 5), sticky="nw")
        
        self.resume_textbox = ctk.CTkTextbox(left_panel, height=300, wrap="word")
        self.resume_textbox.grid(row=3, column=0, padx=15, pady=(0, 15), sticky="nsew")
        
        # Placeholder text for resume
        self.resume_textbox.insert("0.0", "Paste your resume here...\n\nInclude:\n- Contact information\n- Work experience\n- Education\n- Skills\n- Projects")
        
        # Action buttons
        button_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        button_frame.grid(row=4, column=0, padx=15, pady=(0, 15), sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        self.analyze_button = ctk.CTkButton(
            button_frame,
            text="🔍 Analyze Job",
            command=self._start_analysis,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.analyze_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        self.tailor_button = ctk.CTkButton(
            button_frame,
            text="✏️ Tailor Resume",
            command=self._start_tailoring,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            state="disabled"
        )
        self.tailor_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        
        # === Right Panel - Results ===
        right_panel = ctk.CTkFrame(self)
        right_panel.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=10)
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)
        
        # Results header
        results_header = ctk.CTkLabel(right_panel, text="Analysis Results", font=ctk.CTkFont(size=18, weight="bold"))
        results_header.grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        # Results display
        self.results_textbox = ctk.CTkTextbox(right_panel, wrap="word", state="disabled")
        self.results_textbox.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        
        # Cost display
        cost_frame = ctk.CTkFrame(right_panel, fg_color="#2a2a2a")
        cost_frame.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="ew")
        cost_frame.grid_columnconfigure(0, weight=1)
        cost_frame.grid_columnconfigure(1, weight=1)
        cost_frame.grid_columnconfigure(2, weight=1)
        
        self.cost_label = ctk.CTkLabel(cost_frame, text="💰 Cost: $0.0000", font=ctk.CTkFont(size=14))
        self.cost_label.grid(row=0, column=0, padx=10, pady=10)
        
        self.tokens_label = ctk.CTkLabel(cost_frame, text="📊 Tokens: 0", font=ctk.CTkFont(size=14))
        self.tokens_label.grid(row=0, column=1, padx=10, pady=10)
        
        self.score_label = ctk.CTkLabel(cost_frame, text="🎯 Score: --", font=ctk.CTkFont(size=14, weight="bold"))
        self.score_label.grid(row=0, column=2, padx=10, pady=10)
        
        # PDF generation button
        self.pdf_button = ctk.CTkButton(
            right_panel,
            text="📄 Generate Tailored Resume PDF",
            command=self._generate_pdf,
            height=40,
            state="disabled"
        )
        self.pdf_button.grid(row=3, column=0, padx=15, pady=(0, 15), sticky="ew")
        
        # === Status Bar ===
        status_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#1a1a1a")
        status_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Ready | Enter a job URL and paste your resume to begin",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        # Progress bar (hidden initially)
        self.progress_bar = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progress_bar.grid(row=3, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))
        self.progress_bar.set(0)
        self.progress_bar.grid_remove()
    
    def _update_status(self, message: str):
        """Update the status bar message."""
        self.status_label.configure(text=message)
        logger.info(f"Status: {message}")
    
    def _toggle_progress(self, show: bool):
        """Show or hide the progress indicator."""
        if show:
            self.progress_bar.grid()
            self.progress_bar.start()
            self.analyze_button.configure(state="disabled")
            self.tailor_button.configure(state="disabled")
        else:
            self.progress_bar.stop()
            self.progress_bar.grid_remove()
            self.analyze_button.configure(state="normal")
            self.tailor_button.configure(state="normal")
    
    def _start_analysis(self):
        """Start the job analysis process in a background thread."""
        job_url = self.url_entry.get().strip()
        resume_text = self.resume_textbox.get("0.0", "end").strip()
        
        # Validate inputs
        if not job_url:
            self._show_error("Please enter a job posting URL")
            return
        
        if not job_url.startswith(('http://', 'https://')):
            self._show_error("Please enter a valid URL (starting with http:// or https://)")
            return
        
        if len(resume_text) < 50 or "Paste your resume" in resume_text:
            self._show_error("Please paste your resume content (minimum 50 characters)")
            return
        
        # Estimate cost
        estimate = self.cost_tracker.estimate_analysis_cost(len(job_url) + 5000, len(resume_text))
        
        # Confirm with user
        confirm = ctk.CTkInputDialog(
            text=f"Estimated cost for this analysis: ${estimate['estimated_cost_usd']:.4f}\n\nContinue?",
            title="Cost Confirmation"
        ).get_input()
        
        if confirm is None:  # User cancelled
            return
        
        # Start analysis
        self._update_status(f"Starting analysis... Estimated cost: ${estimate['estimated_cost_usd']:.4f}")
        self._toggle_progress(True)
        
        # Clear previous results
        self.results_textbox.configure(state="normal")
        self.results_textbox.delete("0.0", "end")
        self.results_textbox.configure(state="disabled")
        
        # Start worker thread
        worker = AnalysisWorker(
            callback=self._on_analysis_complete,
            error_callback=self._on_analysis_error,
            job_url=job_url,
            resume_text=resume_text
        )
        worker.start()
    
    def _on_analysis_complete(self, result: Dict[str, Any]):
        """Handle successful analysis completion (called from worker thread)."""
        # Schedule UI update on main thread
        self.after(0, lambda: self._display_analysis_results(result))
    
    def _display_analysis_results(self, result: Dict[str, Any]):
        """Display analysis results in the UI."""
        self._toggle_progress(False)
        self.current_analysis = result
        
        job_data = result['job_data']
        analysis = result['analysis']
        
        # Update status
        self._update_status(f"Analysis complete: {job_data['title']} at {job_data['company']}")
        
        # Display results
        self.results_textbox.configure(state="normal")
        self.results_textbox.delete("0.0", "end")
        
        # Format results
        results_text = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
JOB DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Position: {job_data['title']}
Company: {job_data['company']}
URL: {job_data['url']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MATCH ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Match Score: {analysis.get('match_score', 'N/A')}%

Summary:
{analysis.get('summary', 'No summary available')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KEY SKILLS REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        key_skills = analysis.get('key_skills', [])
        for i, skill in enumerate(key_skills[:10], 1):
            results_text += f"  {i}. {skill}\n"
        
        matching_skills = analysis.get('matching_skills', [])
        if matching_skills:
            results_text += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nYOUR MATCHING SKILLS\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for skill in matching_skills[:10]:
                results_text += f"  ✓ {skill}\n"
        
        missing_skills = analysis.get('missing_skills', [])
        if missing_skills:
            results_text += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nSKILLS TO HIGHLIGHT/DEVELOP\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for skill in missing_skills[:10]:
                results_text += f"  ⚠ {skill}\n"
        
        tailored_bullets = analysis.get('tailored_bullets', [])
        if tailored_bullets:
            results_text += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nRECOMMENDED BULLET POINTS\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for bullet in tailored_bullets[:5]:
                results_text += f"  • {bullet}\n"
        
        self.results_textbox.insert("0.0", results_text)
        self.results_textbox.configure(state="disabled")
        
        # Update cost display
        token_count = analysis.get('token_count', 0)
        cost_usd = analysis.get('cost_usd', 0.0)
        self.cost_label.configure(text=f"💰 Cost: ${cost_usd:.4f}")
        self.tokens_label.configure(text=f"📊 Tokens: {token_count:,}")
        
        score = analysis.get('match_score', 0)
        if score >= 80:
            score_color = "#00ff00"
        elif score >= 60:
            score_color = "#ffa500"
        else:
            score_color = "#ff4444"
        self.score_label.configure(text=f"🎯 Score: {score:.0f}%", text_color=score_color)
        
        # Enable tailor button
        self.tailor_button.configure(state="normal")
        
        # Save to database
        self.database.add_job_application(
            url=job_data['url'],
            title=job_data['title'],
            company=job_data['company'],
            match_score=score,
            key_skills=key_skills,
            missing_skills=missing_skills,
            tailored_bullets=tailored_bullets,
            token_count=token_count,
            cost_usd=cost_usd
        )
    
    def _on_analysis_error(self, error_message: str):
        """Handle analysis error (called from worker thread)."""
        self.after(0, lambda: self._show_error(error_message))
    
    def _start_tailoring(self):
        """Start the resume tailoring process in a background thread."""
        if not self.current_analysis:
            self._show_error("Please analyze a job first")
            return
        
        resume_text = self.resume_textbox.get("0.0", "end").strip()
        job_data = self.current_analysis['job_data']
        
        self._update_status("Tailoring your resume...")
        self._toggle_progress(True)
        
        # Start worker thread
        worker = TailoringWorker(
            callback=self._on_tailoring_complete,
            error_callback=self._on_tailoring_error,
            job_description=job_data['description'],
            resume_text=resume_text
        )
        worker.start()
    
    def _on_tailoring_complete(self, result: Dict[str, Any]):
        """Handle successful tailoring completion (called from worker thread)."""
        self.after(0, lambda: self._display_tailoring_results(result))
    
    def _display_tailoring_results(self, result: Dict[str, Any]):
        """Display tailoring results in the UI."""
        self._toggle_progress(False)
        self.current_tailored_content = result
        
        self._update_status("Resume tailoring complete! Review the results below.")
        
        # Append to results
        self.results_textbox.configure(state="normal")
        self.results_textbox.insert("end", "\n\n" + "="*60 + "\n")
        self.results_textbox.insert("end", "TAILORED RESUME CONTENT\n")
        self.results_textbox.insert("end", "="*60 + "\n\n")
        
        summary = result.get('summary', '')
        if summary:
            self.results_textbox.insert("end", f"PROFESSIONAL SUMMARY:\n{summary}\n\n")
        
        skills = result.get('skills', [])
        if skills:
            self.results_textbox.insert("end", f"KEY SKILLS: {', '.join(skills[:15])}\n\n")
        
        changes = result.get('changes_made', '')
        if changes:
            self.results_textbox.insert("end", f"CHANGES MADE:\n{changes}\n\n")
        
        # Update cost
        token_count = result.get('token_count', 0)
        cost_usd = result.get('cost_usd', 0.0)
        current_cost = float(self.cost_label.cget("text").split('$')[1])
        new_cost = current_cost + cost_usd
        self.cost_label.configure(text=f"💰 Cost: ${new_cost:.4f}")
        
        current_tokens = int(self.tokens_label.cget("text").split(':')[1].replace(',', ''))
        new_tokens = current_tokens + token_count
        self.tokens_label.configure(text=f"📊 Tokens: {new_tokens:,}")
        
        self.results_textbox.insert("end", f"\nTotal tokens used: {token_count:,}\n")
        self.results_textbox.insert("end", f"Additional cost: ${cost_usd:.4f}\n")
        
        self.results_textbox.configure(state="disabled")
        
        # Enable PDF button
        self.pdf_button.configure(state="normal")
    
    def _on_tailoring_error(self, error_message: str):
        """Handle tailoring error (called from worker thread)."""
        self.after(0, lambda: self._show_error(error_message))
    
    def _generate_pdf(self):
        """Generate a PDF of the tailored resume."""
        if not self.current_tailored_content or not self.current_analysis:
            self._show_error("No tailored content available. Please analyze and tailor first.")
            return
        
        # Extract contact info (simple parsing - user should have it in resume)
        resume_text = self.resume_textbox.get("0.0", "end").strip()
        
        # Try to extract name and email from resume
        name = "Your Name"
        email = "your.email@example.com"
        phone = "(555) 123-4567"
        location = "City, State"
        
        # Simple extraction (in production, use AI or more sophisticated parsing)
        lines = resume_text.split('\n')
        for line in lines[:5]:
            if '@' in line and '.' in line:
                # Likely email line
                parts = line.split('|')
                if len(parts) >= 1:
                    email = parts[0].strip()
                if len(parts) >= 2:
                    phone = parts[1].strip()
                if len(parts) >= 3:
                    location = parts[2].strip()
            elif len(line.strip()) > 2 and len(line.strip()) < 50 and not any(c.isdigit() for c in line):
                # Likely name
                name = line.strip()
                break
        
        job_data = self.current_analysis['job_data']
        analysis = self.current_analysis['analysis']
        
        # Prepare content for PDF
        tailored_content = {
            'summary': self.current_tailored_content.get('summary', ''),
            'skills': self.current_tailored_content.get('skills', []),
            'experience': self.current_tailored_content.get('experience', []),
            'tailored_bullets': analysis.get('tailored_bullets', [])
        }
        
        cost_info = {
            'token_count': int(self.tokens_label.cget("text").split(':')[1].replace(',', '')),
            'cost_usd': float(self.cost_label.cget("text").split('$')[1])
        }
        
        try:
            filepath = self.pdf_generator.generate_resume(
                candidate_name=name,
                candidate_email=email,
                candidate_phone=phone,
                candidate_location=location,
                job_title=job_data['title'],
                company=job_data['company'],
                match_score=analysis.get('match_score', 0),
                tailored_content=tailored_content,
                original_resume=resume_text,
                cost_info=cost_info
            )
            
            # Update database
            self.database.update_job_application(
                self.database.get_all_applications(limit=1)[0]['id'],
                tailored_resume=str(tailored_content)
            )
            
            # Show success and offer to open
            self._update_status(f"PDF generated: {filepath}")
            
            open_pdf = ctk.CTkInputDialog(
                text=f"PDF generated successfully!\n\n{filepath}\n\nOpen PDF now?",
                title="PDF Generated"
            ).get_input()
            
            if open_pdf is not None:  # User didn't cancel
                webbrowser.open(filepath)
            
        except Exception as e:
            logger.error(f"PDF generation error: {e}")
            self._show_error(f"Failed to generate PDF: {str(e)}")
    
    def _show_error(self, message: str):
        """Display an error dialog."""
        self._toggle_progress(False)
        self._update_status(f"Error: {message}")
        
        error_window = ctk.CTkToplevel(self)
        error_window.title("Error")
        error_window.geometry("400x150")
        error_window.attributes('-topmost', True)
        
        error_label = ctk.CTkLabel(
            error_window,
            text=message,
            font=ctk.CTkFont(size=14),
            wraplength=350
        )
        error_label.pack(pady=20, padx=20)
        
        close_button = ctk.CTkButton(
            error_window,
            text="OK",
            command=error_window.destroy,
            width=100
        )
        close_button.pack(pady=10)


def main():
    """Main entry point for the application."""
    logger.info("=" * 60)
    logger.info("AI Job Search & Resume Tailoring Engine")
    logger.info("Conceptually inspired by Career-Ops (MIT License)")
    logger.info("Python re-engineering for educational purposes")
    logger.info("=" * 60)
    
    # Check for API key
    provider = os.getenv('LLM_PROVIDER', 'openai')
    if provider == 'openai' and not os.getenv('OPENAI_API_KEY'):
        logger.warning("OPENAI_API_KEY not found. Please set it in .env file or environment.")
    elif provider == 'google' and not os.getenv('GOOGLE_API_KEY'):
        logger.warning("GOOGLE_API_KEY not found. Please set it in .env file or environment.")
    
    # Create and run application
    app = JobSearchApp()
    app.mainloop()
    
    logger.info("Application closed")


if __name__ == "__main__":
    main()

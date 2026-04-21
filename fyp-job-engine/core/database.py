"""
Database Module - SQLite Job History & Application Tracker

This module provides local SQLite storage for job applications,
analysis results, and cost tracking data.

Conceptually inspired by Career-Ops (MIT License) - Python re-engineering.
"""

import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class Database:
    """
    SQLite database manager for job application tracking.
    
    Features:
    - Local storage (no cloud dependencies)
    - Job history with scores and costs
    - Application status tracking
    - Query and export capabilities
    """
    
    def __init__(self, db_path: str = 'jobs.db'):
        """
        Initialize the database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._initialize_schema()
        logger.info(f"Database initialized: {db_path}")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _initialize_schema(self):
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            
            # Main job applications table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS job_applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    match_score REAL,
                    key_skills TEXT,
                    missing_skills TEXT,
                    tailored_bullets TEXT,
                    tailored_resume TEXT,
                    token_count INTEGER,
                    cost_usd REAL,
                    status TEXT DEFAULT 'analyzed',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_url ON job_applications(url)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_company ON job_applications(company)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_created_at ON job_applications(created_at)
            ''')
            
            conn.commit()
            logger.debug("Database schema initialized")
        finally:
            conn.close()
    
    def add_job_application(
        self,
        url: str,
        title: str = None,
        company: str = None,
        location: str = None,
        match_score: float = None,
        key_skills: List[str] = None,
        missing_skills: List[str] = None,
        tailored_bullets: List[str] = None,
        tailored_resume: str = None,
        token_count: int = None,
        cost_usd: float = None,
        status: str = 'analyzed',
        notes: str = None
    ) -> int:
        """
        Add a new job application record.
        
        Args:
            url: Job posting URL
            title: Job title
            company: Company name
            location: Job location
            match_score: AI-calculated match score (0-100)
            key_skills: List of important skills from job posting
            missing_skills: List of skills candidate lacks
            tailored_bullets: AI-generated bullet points
            tailored_resume: Full tailored resume text
            token_count: Total tokens used in analysis
            cost_usd: Cost of analysis in USD
            status: Application status (analyzed, applied, interviewed, offered, rejected)
            notes: User notes
            
        Returns:
            ID of the newly created record
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Convert lists to JSON strings for storage
            import json
            key_skills_str = json.dumps(key_skills) if key_skills else None
            missing_skills_str = json.dumps(missing_skills) if missing_skills else None
            tailored_bullets_str = json.dumps(tailored_bullets) if tailored_bullets else None
            
            cursor.execute('''
                INSERT INTO job_applications (
                    url, title, company, location, match_score,
                    key_skills, missing_skills, tailored_bullets, tailored_resume,
                    token_count, cost_usd, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                url, title, company, location, match_score,
                key_skills_str, missing_skills_str, tailored_bullets_str,
                tailored_resume, token_count, cost_usd, status, notes
            ))
            
            record_id = cursor.lastrowid
            logger.info(f"Added job application: {title} at {company} (ID: {record_id})")
            return record_id
    
    def update_job_application(
        self,
        job_id: int,
        **kwargs
    ) -> bool:
        """
        Update an existing job application record.
        
        Args:
            job_id: ID of the record to update
            **kwargs: Fields to update (title, status, notes, etc.)
            
        Returns:
            True if update was successful
        """
        if not kwargs:
            return False
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Build dynamic UPDATE statement
            fields = ', '.join(f"{key} = ?" for key in kwargs.keys())
            values = list(kwargs.values())
            values.append(job_id)
            
            # Add updated_at timestamp
            cursor.execute(f'''
                UPDATE job_applications 
                SET {fields}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', values)
            
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Updated job application ID: {job_id}")
            return success
    
    def get_job_application(self, job_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single job application by ID.
        
        Args:
            job_id: ID of the record
            
        Returns:
            Dictionary with job data or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM job_applications WHERE id = ?', (job_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_dict(row)
            return None
    
    def get_all_applications(
        self,
        limit: int = 100,
        offset: int = 0,
        status: str = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all job applications with optional filtering.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            status: Filter by status (optional)
            
        Returns:
            List of dictionaries with job data
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if status:
                cursor.execute('''
                    SELECT * FROM job_applications 
                    WHERE status = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                ''', (status, limit, offset))
            else:
                cursor.execute('''
                    SELECT * FROM job_applications 
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                ''', (limit, offset))
            
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def search_applications(self, query: str) -> List[Dict[str, Any]]:
        """
        Search job applications by title, company, or URL.
        
        Args:
            query: Search term
            
        Returns:
            List of matching job applications
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            search_pattern = f"%{query}%"
            
            cursor.execute('''
                SELECT * FROM job_applications 
                WHERE title LIKE ? OR company LIKE ? OR url LIKE ?
                ORDER BY created_at DESC
            ''', (search_pattern, search_pattern, search_pattern))
            
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get summary statistics of all job applications.
        
        Returns:
            Dictionary with statistics
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total applications
            cursor.execute('SELECT COUNT(*) FROM job_applications')
            total = cursor.fetchone()[0]
            
            # Average match score
            cursor.execute('SELECT AVG(match_score) FROM job_applications WHERE match_score IS NOT NULL')
            avg_score = cursor.fetchone()[0] or 0
            
            # Total cost
            cursor.execute('SELECT SUM(cost_usd) FROM job_applications WHERE cost_usd IS NOT NULL')
            total_cost = cursor.fetchone()[0] or 0
            
            # Total tokens
            cursor.execute('SELECT SUM(token_count) FROM job_applications WHERE token_count IS NOT NULL')
            total_tokens = cursor.fetchone()[0] or 0
            
            # Status breakdown
            cursor.execute('''
                SELECT status, COUNT(*) 
                FROM job_applications 
                GROUP BY status
            ''')
            status_breakdown = {row['status']: row['COUNT(*)'] for row in cursor.fetchall()}
            
            return {
                'total_applications': total,
                'average_match_score': round(avg_score, 2),
                'total_cost_usd': round(total_cost, 4),
                'total_tokens': total_tokens,
                'status_breakdown': status_breakdown
            }
    
    def delete_application(self, job_id: int) -> bool:
        """
        Delete a job application record.
        
        Args:
            job_id: ID of the record to delete
            
        Returns:
            True if deletion was successful
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM job_applications WHERE id = ?', (job_id,))
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Deleted job application ID: {job_id}")
            return success
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a database row to a dictionary."""
        import json
        
        result = dict(row)
        
        # Parse JSON strings back to lists
        for field in ['key_skills', 'missing_skills', 'tailored_bullets']:
            if result.get(field):
                try:
                    result[field] = json.loads(result[field])
                except (json.JSONDecodeError, TypeError):
                    result[field] = []
        
        return result
    
    def export_to_csv(self, filepath: str) -> bool:
        """
        Export all job applications to CSV.
        
        Args:
            filepath: Path to save CSV file
            
        Returns:
            True if export was successful
        """
        import csv
        
        try:
            applications = self.get_all_applications(limit=10000)
            
            if not applications:
                logger.warning("No applications to export")
                return False
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if applications:
                    writer = csv.DictWriter(f, fieldnames=applications[0].keys())
                    writer.writeheader()
                    writer.writerows(applications)
            
            logger.info(f"Exported {len(applications)} applications to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            return False


# Example usage for testing
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    db = Database(':memory:')  # Use in-memory database for testing
    
    # Add a test record
    job_id = db.add_job_application(
        url='https://example.com/job/123',
        title='Software Engineer',
        company='Tech Corp',
        location='San Francisco, CA',
        match_score=85.5,
        key_skills=['Python', 'JavaScript', 'AWS'],
        token_count=1500,
        cost_usd=0.0018
    )
    
    # Retrieve and print
    job = db.get_job_application(job_id)
    print(f"Retrieved job: {job['title']} at {job['company']}")
    
    # Get statistics
    stats = db.get_statistics()
    print(f"Statistics: {stats}")

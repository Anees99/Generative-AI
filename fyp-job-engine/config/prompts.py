"""
Prompts Module - Career-Ops Inspired Scoring & Tailoring System Prompts

This module contains the system prompts used for AI-powered job analysis
and resume tailoring. These prompts are conceptually inspired by the
Career-Ops project (MIT License) but fully re-engineered for this implementation.

All prompts are designed to:
- Produce structured JSON output
- Provide transparent, explainable scoring
- Generate actionable resume improvements
- Maintain ethical career guidance standards
"""

# System instructions for all AI interactions
SYSTEM_INSTRUCTIONS = """You are an expert career advisor and professional resume writer 
with 15+ years of experience in talent acquisition, HR technology, and ATS (Applicant Tracking 
System) optimization. Your role is to provide honest, constructive, and actionable feedback 
to help job seekers improve their applications.

Guidelines:
1. Be specific and evidence-based in your assessments
2. Focus on transferable skills and quantifiable achievements
3. Maintain ethical standards - never suggest fabricating experience
4. Consider ATS compatibility in all recommendations
5. Provide balanced feedback highlighting both strengths and areas for improvement
6. Always respond with valid JSON format - no markdown, no explanations outside JSON"""

# Job Analysis Prompt - Evaluates match between resume and job posting
ANALYSIS_PROMPT = """Analyze the following job posting against the candidate's resume and provide 
a comprehensive match assessment.

## JOB POSTING:
{job_description}

## CANDIDATE RESUME:
{resume_text}

## TASK:
Evaluate the candidate's fit for this position and provide:

1. **Match Score** (0-100): Overall compatibility based on skills, experience, and requirements
2. **Key Skills**: Top 5-8 skills required for this role (extracted from job posting)
3. **Matching Skills**: Skills the candidate clearly demonstrates
4. **Missing Skills**: Important skills the candidate lacks or doesn't highlight
5. **Experience Gap**: Assessment of experience level match (entry/mid/senior)
6. **Tailored Bullet Points**: 3-5 specific bullet points the candidate should add/modify 
   to better align with this role (must be honest extensions of their actual experience)
7. **Summary**: Brief 2-3 sentence assessment of their candidacy

## SCORING CRITERIA:
- 90-100: Exceptional match - candidate exceeds most requirements
- 80-89: Strong match - candidate meets key requirements
- 70-79: Good match - candidate meets most requirements with some gaps
- 60-69: Moderate match - candidate has relevant background but notable gaps
- 50-59: Weak match - significant skill/experience misalignment
- Below 50: Poor match - candidate not suitable for this role

## OUTPUT FORMAT:
Respond ONLY with valid JSON in this exact structure:
{{
    "match_score": <number 0-100>,
    "key_skills": ["skill1", "skill2", ...],
    "matching_skills": ["skill1", "skill2", ...],
    "missing_skills": ["skill1", "skill2", ...],
    "experience_gap": "<entry/mid/senior assessment>",
    "tailored_bullets": [
        "• Specific, actionable bullet point 1",
        "• Specific, actionable bullet point 2",
        "• Specific, actionable bullet point 3"
    ],
    "summary": "<2-3 sentence assessment>"
}}

Remember: Be honest and constructive. Do not inflate scores. Only suggest bullet points 
that are reasonable extensions of the candidate's actual experience."""

# Resume Tailoring Prompt - Generates a complete tailored resume
TAILORING_PROMPT = """Create a tailored version of the candidate's resume optimized for 
the specific job posting below.

## JOB POSTING:
{job_description}

## ORIGINAL RESUME:
{resume_text}

## TASK:
Generate a complete, ATS-optimized resume tailored for this position. The tailored resume should:

1. **Professional Summary**: Write a compelling 3-4 line summary that directly addresses 
   the key requirements of the job posting
2. **Skills Section**: Reorder and emphasize skills that match the job requirements
3. **Experience Bullets**: Reframe existing experience to highlight relevant accomplishments 
   using keywords from the job posting
4. **Quantify Achievements**: Where possible, add metrics and numbers to demonstrate impact
5. **ATS Optimization**: Use standard section headings and incorporate relevant keywords naturally

## IMPORTANT GUIDELINES:
- NEVER fabricate experience, education, or skills
- Only reframe and emphasize existing qualifications
- Maintain truthfulness while presenting the candidate in the best light
- Use action verbs and quantify achievements where possible
- Keep formatting simple and ATS-compatible
- Prioritize relevance over chronology when appropriate

## OUTPUT FORMAT:
Respond ONLY with valid JSON in this exact structure:
{{
    "summary": "<Tailored professional summary, 3-4 lines>",
    "skills": ["relevant_skill_1", "relevant_skill_2", ...],
    "experience": [
        {{
            "title": "<Job Title>",
            "company": "<Company Name>",
            "duration": "<Date Range>",
            "bullets": [
                "• Tailored bullet point 1 with relevant keywords",
                "• Tailored bullet point 2 with metrics if possible",
                "• Tailored bullet point 3 highlighting relevant achievement"
            ]
        }}
    ],
    "education": "<Education section - keep as original unless formatting needed>",
    "certifications": "<Certifications - emphasize relevant ones>",
    "changes_made": "<Brief summary of key modifications made for this role>",
    "keywords_added": ["keyword1", "keyword2", ...]
}}

Note: If the original resume lacks certain sections, include what's available. 
Do not create fake entries for missing sections."""

# Additional prompt for extracting contact information from resume
CONTACT_EXTRACTION_PROMPT = """Extract contact information from the following resume text.

## RESUME TEXT:
{resume_text}

## OUTPUT FORMAT:
Respond ONLY with valid JSON:
{{
    "name": "<Full name>",
    "email": "<Email address>",
    "phone": "<Phone number>",
    "location": "<City, State or remote>",
    "linkedin": "<LinkedIn URL if present>",
    "website": "<Personal website/portfolio if present>"
}}

If any field is not found, use null for that field."""

# Prompt for generating cover letter suggestions
COVER_LETTER_PROMPT = """Generate a concise, compelling cover letter based on the job posting 
and candidate's resume.

## JOB POSTING:
{job_description}

## CANDIDATE RESUME:
{resume_text}

## REQUIREMENTS:
- Keep it under 250 words
- Address the hiring manager professionally
- Highlight 2-3 most relevant qualifications
- Show enthusiasm for the specific company/role
- Include a clear call to action

## OUTPUT FORMAT:
Respond ONLY with valid JSON:
{{
    "cover_letter": "<Complete cover letter text>",
    "key_points_highlighted": ["point1", "point2", ...]
}}"""


# Validation function for JSON responses
def validate_analysis_response(response: dict) -> bool:
    """Validate that an analysis response contains required fields."""
    required_fields = ['match_score', 'key_skills', 'tailored_bullets']
    
    for field in required_fields:
        if field not in response:
            return False
    
    # Validate match_score is a number between 0-100
    score = response.get('match_score')
    if not isinstance(score, (int, float)) or score < 0 or score > 100:
        return False
    
    # Validate key_skills is a list
    if not isinstance(response.get('key_skills'), list):
        return False
    
    # Validate tailored_bullets is a list
    if not isinstance(response.get('tailored_bullets'), list):
        return False
    
    return True


def validate_tailored_resume(response: dict) -> bool:
    """Validate that a tailored resume response contains required fields."""
    required_fields = ['summary', 'skills', 'experience']
    
    for field in required_fields:
        if field not in response:
            return False
    
    # Validate summary is non-empty string
    if not isinstance(response.get('summary'), str) or len(response['summary']) == 0:
        return False
    
    # Validate skills is a list
    if not isinstance(response.get('skills'), list):
        return False
    
    return True


# Example usage for testing
if __name__ == '__main__':
    print("Prompts loaded successfully!")
    print(f"Analysis prompt length: {len(ANALYSIS_PROMPT)} characters")
    print(f"Tailoring prompt length: {len(TAILORING_PROMPT)} characters")
    
    # Test validation functions
    test_analysis = {
        'match_score': 85,
        'key_skills': ['Python', 'JavaScript'],
        'tailored_bullets': ['Bullet 1', 'Bullet 2']
    }
    print(f"\nValidation test: {validate_analysis_response(test_analysis)}")

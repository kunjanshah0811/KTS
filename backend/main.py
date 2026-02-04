from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import databases
import sqlalchemy
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, DateTime, JSON
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/promptdb")

database = databases.Database(DATABASE_URL)
metadata = MetaData()

# Define prompts table
prompts = Table(
    "prompts",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String(255), nullable=False),
    Column("prompt_text", Text, nullable=False),
    Column("category", String(100), nullable=False),
    Column("tags", JSON, default=[]),
    Column("source", String(255), nullable=True),
    Column("views", Integer, default=0),
    Column("created_at", DateTime, default=datetime.utcnow),
)

# Create engine and tables
engine = create_engine(DATABASE_URL)
metadata.create_all(engine)

# FastAPI app
app = FastAPI(
    title="LLM Prompts Repository API",
    description="API for sharing and discovering LLM prompts for social science research",
    version="1.0.0"
)

# CORS configuration - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class PromptCreate(BaseModel):
    title: str
    prompt_text: str
    category: str
    tags: List[str] = []
    source: Optional[str] = None

class PromptResponse(BaseModel):
    id: int
    title: str
    prompt_text: str
    category: str
    tags: List[str]
    source: Optional[str]
    views: int
    created_at: datetime

class PromptStats(BaseModel):
    total_prompts: int
    categories: dict

# Database connection events
@app.on_event("startup")
async def startup():
    await database.connect()
    # Seed database with example prompts
    await seed_database()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# API Endpoints

@app.get("/")
async def root():
    return {
        "message": "LLM Prompts Repository API",
        "version": "1.0.0",
        "endpoints": {
            "prompts": "/api/prompts",
            "stats": "/api/stats"
        }
    }

@app.post("/api/prompts", response_model=PromptResponse)
async def create_prompt(prompt: PromptCreate):
    """Create a new prompt"""
    query = prompts.insert().values(
        title=prompt.title,
        prompt_text=prompt.prompt_text,
        category=prompt.category,
        tags=prompt.tags,
        source=prompt.source,
        views=0,
        created_at=datetime.utcnow()
    )
    last_record_id = await database.execute(query)
    
    # Fetch and return the created prompt
    select_query = prompts.select().where(prompts.c.id == last_record_id)
    result = await database.fetch_one(select_query)
    return dict(result)

@app.get("/api/prompts", response_model=List[PromptResponse])
async def get_prompts(
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort: str = Query("date", regex="^(date|popularity)$"),
    limit: int = Query(100, le=500),
    offset: int = 0
):
    """
    Get all prompts with optional filtering and sorting
    - category: Filter by category
    - search: Search in title, tags, and prompt_text
    - sort: Sort by 'date' (newest first) or 'popularity' (most views)
    - limit: Maximum number of results (max 500)
    - offset: Pagination offset
    """
    query = prompts.select()
    
    # Apply category filter
    if category:
        query = query.where(prompts.c.category == category)
    
    # Apply search filter
    if search:
        search_term = f"%{search.lower()}%"
        query = query.where(
            sqlalchemy.or_(
                prompts.c.title.ilike(search_term),
                prompts.c.prompt_text.ilike(search_term),
                sqlalchemy.cast(prompts.c.tags, String).ilike(search_term)
            )
        )
    
    # Apply sorting
    if sort == "popularity":
        query = query.order_by(prompts.c.views.desc())
    else:  # date
        query = query.order_by(prompts.c.created_at.desc())
    
    # Apply pagination
    query = query.limit(limit).offset(offset)
    
    results = await database.fetch_all(query)
    return [dict(row) for row in results]

@app.get("/api/prompts/{prompt_id}", response_model=PromptResponse)
async def get_prompt(prompt_id: int):
    """Get a single prompt by ID and increment view count"""
    query = prompts.select().where(prompts.c.id == prompt_id)
    result = await database.fetch_one(query)
    
    if not result:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    # Increment view count
    update_query = (
        prompts.update()
        .where(prompts.c.id == prompt_id)
        .values(views=prompts.c.views + 1)
    )
    await database.execute(update_query)
    
    # Fetch the updated prompt with new view count
    updated_result = await database.fetch_one(query)
    
    return dict(updated_result)

@app.get("/api/categories")
async def get_categories():
    """Get all unique categories"""
    query = sqlalchemy.select([prompts.c.category]).distinct()
    results = await database.fetch_all(query)
    categories = [row["category"] for row in results]
    return {"categories": categories}

@app.get("/api/stats", response_model=PromptStats)
async def get_stats():
    """Get statistics about prompts"""
    # Total count
    count_query = sqlalchemy.select([sqlalchemy.func.count()]).select_from(prompts)
    total = await database.fetch_val(count_query)
    
    # Count by category
    category_query = (
        sqlalchemy.select([
            prompts.c.category,
            sqlalchemy.func.count().label("count")
        ])
        .group_by(prompts.c.category)
    )
    category_results = await database.fetch_all(category_query)
    categories_dict = {row["category"]: row["count"] for row in category_results}
    
    return {
        "total_prompts": total,
        "categories": categories_dict
    }

# Seed database with comprehensive social science research prompts
async def seed_database():
    """Populate database with example prompts if empty"""
    count_query = sqlalchemy.select([sqlalchemy.func.count()]).select_from(prompts)
    count = await database.fetch_val(count_query)
    
    if count > 0:
        return  # Database already has data
    
    example_prompts = [
        # ============================================
        # 2. DATA COLLECTION
        # ============================================
        
        # Data Extraction & APIs
        {
            "title": "API Data Extraction - Social Media Posts",
            "prompt_text": """I need to extract data from {api_name} API for social science research. 

Research Goal: {research_goal}
Data Needed: {data_fields}
Time Period: {time_period}
Sample Size: {sample_size}

Please provide:
1. API endpoint structure needed
2. Required parameters and authentication
3. Sample API request code (Python)
4. Data parsing strategy
5. Ethical considerations for this data collection

Example Output Format:
```python
import requests

# Your code here
```""",
            "category": "Data Collection > Data Extraction & APIs",
            "tags": ["api", "data-extraction", "web-scraping", "python"],
            "source": "Custom"
        },
        {
            "title": "Web Scraping for Research Data",
            "prompt_text": """I need to scrape publicly available data from {website_url} for academic research.

Purpose: {research_purpose}
Data to Extract: {data_elements}
Frequency: {collection_frequency}

Provide:
1. Python scraping script using BeautifulSoup/Scrapy
2. Data storage format (CSV/JSON)
3. Error handling strategy
4. Rate limiting to respect server
5. Legal and ethical compliance check

Include comments explaining each step for research reproducibility.

---EXAMPLE---

Sample Expected Output:
```python
# Well-commented scraping code
```""",
            "category": "Data Collection > Data Extraction & APIs",
            "tags": ["web-scraping", "beautifulsoup", "data-collection", "ethics"],
            "source": "Custom"
        },
        {
            "title": "Survey Data Export & API Integration",
            "prompt_text": """I have survey responses in {platform_name} (Qualtrics/Google Forms/SurveyMonkey) and need to extract them via API.

Survey Details:
- Response count: {n_responses}
- Question types: {question_types}
- Export format needed: {format}

Generate:
1. API authentication setup
2. Data extraction script
3. Data cleaning pipeline
4. Automated export schedule
5. Backup strategy

Provide complete working code with error handling.""",
            "category": "Data Collection > Data Extraction & APIs",
            "tags": ["survey", "api", "qualtrics", "automation"],
            "source": "Custom"
        },
        
        # Interview Protocols
        {
            "title": "Mock Interviewer - Practice Session",
            "prompt_text": """Act as a mock interviewer for the following position: {job_title} at {organization_type}.

Interview Type: {interview_type} (behavioral/technical/case study)
My Background: {candidate_background}
Position Level: {position_level}

Please:
1. Ask me {number} interview questions appropriate for this role
2. Wait for my response after each question
3. Provide constructive feedback on my answers
4. Rate my responses (1-5 scale)
5. Suggest improvements

Start with: "Hello, I'm pleased to meet you. Tell me about yourself and why you're interested in this position."

---EXAMPLE---

Expected Interaction:
Interviewer: [Question]
Candidate: [I'll respond]
Interviewer: [Feedback + Next Question]""",
            "category": "Data Collection > Interview Protocols",
            "tags": ["interview", "mock-interview", "career", "practice"],
            "source": "Adapted from Wolfram PromptRepository - MockInterviewer"
        },
        {
            "title": "Semi-Structured Interview Guide Generator",
            "prompt_text": """Create a semi-structured interview guide for qualitative research.

Research Question: {research_question}
Target Population: {population}
Interview Duration: {duration} minutes
Research Paradigm: {paradigm} (phenomenological/grounded theory/narrative)

Generate:
1. Opening rapport-building questions (2-3)
2. Core research questions (5-7 main questions)
3. Probing follow-up questions for each core question
4. Transition statements between topics
5. Closing questions
6. Ethical considerations and consent reminders

Format as a field-ready interview protocol with timing suggestions.

---EXAMPLE---

Sample Output:
INTERVIEW PROTOCOL
Introduction (5 min):
- Consent confirmation
- Recording permission
- [Rapport building questions]

Main Questions (40 min):
1. [Core question]
   - Probe: ...
   - Probe: ...""",
            "category": "Data Collection > Interview Protocols",
            "tags": ["qualitative", "interview-guide", "research-methods", "semi-structured"],
            "source": "Custom"
        },
        {
            "title": "Interview Consent Script Generator",
            "prompt_text": """Generate an informed consent script for research interviews.

Study Title: {study_title}
Institution: {institution}
IRB Number: {irb_number}
Risks: {risk_level} (minimal/moderate/high)
Benefits: {benefits}
Compensation: {compensation}
Recording: {recording_type} (audio/video/none)

Create a comprehensive verbal consent script including:
1. Study purpose (layperson language)
2. What participation involves
3. Time commitment
4. Risks and benefits
5. Confidentiality measures
6. Right to withdraw
7. Contact information
8. Consent confirmation questions

Make it conversational yet complete for IRB compliance.""",
            "category": "Data Collection > Interview Protocols",
            "tags": ["ethics", "consent", "irb", "qualitative-research"],
            "source": "Custom"
        },
        
        # ============================================
        # 3. DATA PREPARATION
        # ============================================
        
        # Text Preprocessing
        {
            "title": "Text Cleaning Pipeline for Social Media Data",
            "prompt_text": """Clean and preprocess the following social media text data for analysis:

Raw Text: {raw_text}

Apply these preprocessing steps:
1. Remove URLs, hashtags, mentions
2. Handle emojis (convert to text descriptions)
3. Fix common abbreviations and slang
4. Remove special characters but preserve meaning
5. Correct obvious typos
6. Standardize spacing and formatting

Provide:
- Cleaned text
- List of transformations made
- Python code to reproduce this cleaning

---EXAMPLE---

Example Input: "OMG!!! Check this out 😂 http://example.com #amazing @friend"
Example Output: 
Cleaned: "Oh my god check this out [laughing emoji] [link removed] [hashtag: amazing] [mention removed]"
Transformations: [list...]""",
            "category": "Data Preparation > Text Preprocessing",
            "tags": ["nlp", "text-cleaning", "preprocessing", "social-media"],
            "source": "Custom"
        },
        {
            "title": "Stopword Removal with Context Preservation",
            "prompt_text": """Remove stopwords from this text while preserving research-relevant context:

Text: {text}
Research Focus: {research_focus}
Language: {language}
Custom Stopwords to Keep: {words_to_keep}

Process:
1. Use standard stopword list for {language}
2. Preserve domain-specific important words
3. Keep negations (not, no, never) as they affect sentiment
4. Maintain sentence structure for context

Return:
- Processed text
- List of removed words
- List of preserved stopwords (with justification)
- Word count before/after

---EXAMPLE---

Example:
Input: "The patient is not feeling very well today"
Focus: Medical sentiment
Output: "patient not feeling well today"
Preserved: "not" (negation affects sentiment)
Removed: "the", "is", "very"
Counts: 8 words → 5 words""",
            "category": "Data Preparation > Text Preprocessing",
            "tags": ["stopwords", "nlp", "text-processing"],
            "source": "Custom"
        },
        {
            "title": "Text Normalization for Cross-Cultural Analysis",
            "prompt_text": """Normalize text data from multiple sources for comparative analysis:

Texts: {text_samples}
Languages: {languages}
Normalization Goal: {goal}

Apply:
1. Lowercasing (where appropriate)
2. Accent/diacritic handling
3. Number standardization
4. Date format standardization
5. Unicode normalization
6. Spelling variants harmonization

Provide normalized versions with annotation of changes for transparency in research.

---EXAMPLE---

Example:
Input: "The café opened in 2023", "The cafe opened in two-thousand-twenty-three"
Output (normalized): "the cafe opened in 2023", "the cafe opened in 2023"
Changes: [removed accent, standardized number format]""",
            "category": "Data Preparation > Text Preprocessing",
            "tags": ["normalization", "cross-cultural", "text-standardization"],
            "source": "Custom"
        },
        
        # Data Cleaning
        {
            "title": "Survey Response Data Validation",
            "prompt_text": """Validate and clean survey response data for analysis.

Dataset Info:
- Sample size: {n_responses}
- Variables: {variable_list}
- Known issues: {issues}

Check for:
1. Missing data patterns (MAR/MCAR/MNAR)
2. Impossible values (e.g., age = 150)
3. Inconsistent responses (contradictions)
4. Duplicate entries
5. Outliers (statistical and logical)
6. Response time anomalies (speeders/straightliners)

Provide:
- Data quality report
- Recommended exclusion criteria
- Imputation strategies for missing data
- Cleaned dataset specifications
- CONSORT-style flow diagram of exclusions

Example Report:
Total responses: 500
Duplicates removed: 12
Incomplete surveys: 45
Failed attention checks: 8
Speeders (<120 seconds): 15
Final sample: 420""",
            "category": "Data Preparation > Data Cleaning",
            "tags": ["survey", "data-quality", "validation", "missing-data"],
            "source": "Custom"
        },
        {
            "title": "Interview Transcript Quality Check",
            "prompt_text": """Review and clean interview transcript for quality issues.

Transcript: {transcript_text}
Interview ID: {id}
Duration: {duration}
Transcription Method: {method} (auto/manual)

Check for:
1. Inaudible sections marked appropriately
2. Speaker identification consistency
3. Timestamps accuracy
4. Non-verbal cues captured [laughs], [pause]
5. Filler words (um, uh) - keep or remove?
6. Sensitive information for anonymization

Provide:
- Quality rating (1-5)
- List of issues found
- Corrected transcript
- Anonymization suggestions
- Recommendations for re-transcription if needed""",
            "category": "Data Preparation > Data Cleaning",
            "tags": ["qualitative", "transcription", "data-quality", "interviews"],
            "source": "Custom"
        },
        {
            "title": "Dataset Merge & Deduplication",
            "prompt_text": """Merge multiple datasets and remove duplicates for longitudinal study.

Datasets:
- Wave 1: {dataset1_info}
- Wave 2: {dataset2_info}
- Wave 3: {dataset3_info}

Matching Criteria: {matching_fields}
Participant Tracking: {id_system}

Execute:
1. Fuzzy matching on participant IDs
2. Duplicate detection across waves
3. Conflict resolution for divergent data
4. Longitudinal data structure creation
5. Attrition analysis

Output:
- Merged dataset structure
- Matching statistics
- Unmatched cases report
- Data dictionary for merged file
- Python/R code for reproducibility""",
            "category": "Data Preparation > Data Cleaning",
            "tags": ["data-merge", "deduplication", "longitudinal", "data-management"],
            "source": "Custom"
        },
        
        # Data Formatting
        {
            "title": "Qualitative Data Coding Structure",
            "prompt_text": """Structure qualitative data for systematic coding and analysis.

Data Type: {data_type} (interviews/focus groups/observations)
Number of Units: {n_units}
Coding Approach: {approach} (deductive/inductive/hybrid)
Software: {software} (NVivo/Atlas.ti/Dedoose/manual)

Create:
1. File naming convention
2. Folder structure for data organization
3. Metadata template for each data unit
4. Initial codebook structure
5. Memo template for analytical notes
6. Export format for reporting

Example Structure:
```
Project_Root/
├── RawData/
│   ├── Transcripts/
│   │   ├── P001_Interview_2024-01-15.docx
│   │   ├── P002_Interview_2024-01-16.docx
├── Codes/
│   ├── Codebook_v1.xlsx
├── Memos/
├── Analysis/
```

Include metadata template in JSON/CSV format.""",
            "category": "Data Preparation > Data Formatting",
            "tags": ["qualitative", "coding", "data-organization", "structure"],
            "source": "Custom"
        },
        {
            "title": "Survey Data Restructuring - Long to Wide Format",
            "prompt_text": """Convert survey data from long format to wide format for analysis.

Current Format: Long/longitudinal
- Variables: {variables}
- Time points: {time_points}
- Participant ID: {id_var}

Target: Wide format suitable for {analysis_type}

Provide:
1. Restructuring logic
2. Python (pandas) or R (tidyr) code
3. Variable naming convention for time points
4. Handling of missing timepoints
5. Data validation post-transformation

---EXAMPLE---

Example:
Long format:
ID | Time | Score
1  | T1   | 85
1  | T2   | 90

Wide format:
ID | Score_T1 | Score_T2
1  | 85       | 90

Include complete working code.""",
            "category": "Data Preparation > Data Formatting",
            "tags": ["data-transformation", "survey", "longitudinal", "pandas"],
            "source": "Custom"
        },
        {
            "title": "Citation Data Formatting for Meta-Analysis",
            "prompt_text": """Format extracted citation data for systematic review/meta-analysis.

Data Source: {source} (Web of Science/Scopus/PubMed)
Number of Studies: {n_studies}
Required Fields: {fields}

Standardize:
1. Author names (Last, F.M. format)
2. Journal names (full vs. abbreviated)
3. Publication dates (YYYY-MM-DD)
4. DOI formatting
5. Article types categorization
6. Extract effect sizes if reported

Create:
- Formatted reference list
- Data extraction spreadsheet
- PRISMA flow diagram data
- Duplicate detection report

Output as CSV/Excel with columns for:
[Author, Year, Title, Journal, DOI, Study_Type, Effect_Size, Sample_Size, ...]""",
            "category": "Data Preparation > Data Formatting",
            "tags": ["meta-analysis", "citations", "systematic-review", "bibliography"],
            "source": "Custom"
        },
        
        # ============================================
        # 4. TEXT ANALYSIS
        # ============================================
        
        # Text Summarization
        {
            "title": "Academic Article Summarizer",
            "prompt_text": """Summarize the following academic article/document for research purposes.

Document: {document_text}
Target Audience: {audience} (peers/general public/students)
Summary Length: {length} (abstract/paragraph/comprehensive)

Provide a structured summary including:
1. Research Question/Objective (1 sentence)
2. Theoretical Framework (if applicable)
3. Methodology (1-2 sentences)
4. Key Findings (3-5 bullet points)
5. Main Contribution to field
6. Limitations mentioned
7. Future research directions

Format for easy reference and citation.

---EXAMPLE---

Sample Output:
**Research Question:** How does social media use affect adolescent mental health?
**Framework:** Uses Social Comparison Theory
**Method:** Longitudinal survey (n=1,200, ages 13-17, 2-year follow-up)
**Findings:**
- Passive scrolling associated with 23% increase in depressive symptoms
- Active engagement showed no negative effects
- Effect moderated by self-esteem
**Contribution:** First longitudinal evidence for passive vs. active use distinction
**Limitations:** Self-report measures, limited to Instagram users
**Future Directions:** Need experimental designs, neurobiological mechanisms""",
            "category": "Text Analysis > Text Summarization",
            "tags": ["academic", "literature-review", "summarization"],
            "source": "Adapted from Wolfram PromptRepository - SummarizeContent"
        },
        {
            "title": "Web Article Summarizer for Research",
            "prompt_text": """Summarize content from this URL for academic/research purposes:

URL: {url}
Purpose: {research_purpose}
Focus: {focus_areas}

Extract and summarize:
1. Main thesis/argument
2. Key evidence presented
3. Data/statistics cited (with verification note)
4. Author credentials and potential bias
5. Publication date and relevance
6. Useful quotes (with page/paragraph reference)
7. Related sources mentioned

Provide APA citation for the source.

---EXAMPLE---

Example:
Source: [Auto-generated citation]
Summary: Article argues that remote work increases productivity by 13% based on Stanford study...
Key Data: 13% productivity increase (Bloom et al., 2015), 50% reduction in attrition...
Bias Check: Published by remote work advocacy group
Relevance: Published 2023, highly relevant for post-pandemic research
Useful Quote: "The productivity boost comes primarily from reduced distractions..." (para. 4)""",
            "category": "Text Analysis > Text Summarization",
            "tags": ["web-content", "research", "url-summary"],
            "source": "Adapted from Wolfram PromptRepository - SummarizeContent"
        },
        {
            "title": "Multi-Document Synthesis for Literature Review",
            "prompt_text": """Synthesize findings across multiple research articles on the same topic.

Articles: {article_list}
Research Topic: {topic}
Synthesis Goal: {goal}

Create a synthesis that:
1. Identifies common themes across studies
2. Notes contradictory findings with explanations
3. Traces evolution of ideas chronologically
4. Highlights methodology differences
5. Identifies research gaps
6. Suggests theoretical integration

Format as a narrative literature review section (500-800 words) with inline citations.

---EXAMPLE---

Example Output:
Research on [topic] has evolved significantly over the past decade. Early studies (Author1, 2015; Author2, 2016) emphasized [theme 1], finding that [finding]. However, more recent investigations (Author3, 2022) have challenged this view, demonstrating [contradictory finding]. This discrepancy may be explained by [methodological difference]...

[Continue with integrated narrative]

Notable gaps include: [1] lack of longitudinal designs, [2] limited diversity in samples...""",
            "category": "Text Analysis > Text Summarization",
            "tags": ["synthesis", "literature-review", "meta-summary"],
            "source": "Custom"
        },
        
        # Text Classification
        {
            "title": "Social Media Post Classifier",
            "prompt_text": """Classify the following social media posts into predefined categories for content analysis.

Posts: {posts}
Classification Scheme:
- Categories: {categories}
- Mutually exclusive: {yes/no}
- Multiple labels allowed: {yes/no}

For each post, provide:
1. Primary category
2. Secondary category (if applicable)
3. Confidence score (0-100%)
4. Key words/phrases that influenced classification
5. Ambiguous cases flagged for manual review

---EXAMPLE---

Example:
Post: "Just voted! Make your voice heard 🗳️ #Election2024"
Primary: Political
Secondary: Civic Engagement
Confidence: 95%
Key phrases: "voted", "election", hashtag
Notes: Clear political content

Post: "Love this new cafe downtown!"
Primary: Personal
Secondary: None
Confidence: 88%
Key phrases: "love", "cafe"
Notes: Could be marketing if business account - flag for review

Process all {n} posts and provide summary statistics.""",
            "category": "Text Analysis > Text Classification",
            "tags": ["classification", "social-media", "content-analysis"],
            "source": "Custom"
        },
        {
            "title": "Survey Open-Ended Response Categorizer",
            "prompt_text": """Categorize open-ended survey responses into themes for quantitative analysis.

Question: {survey_question}
Responses: {responses}
Number of responses: {n}

Develop categorization:
1. Read all responses to identify emergent themes
2. Create 5-10 mutually exclusive categories
3. Provide clear decision rules for each category
4. Code all responses
5. Calculate inter-rater reliability if multiple coders
6. Provide frequency distribution

---EXAMPLE---

Example:
Question: "What is the main barrier to using public transportation?"

Categories identified:
1. Cost/Affordability (Decision rule: mentions price, expense, cost)
2. Accessibility (mentions distance, availability, routes)
3. Time/Convenience (mentions schedules, duration, waiting)
4. Safety concerns (mentions crime, cleanliness, harassment)
5. Other

Coding Results:
Response: "It's too expensive for daily use" → Category 1 (Cost)
Response: "No bus route near my home" → Category 2 (Accessibility)

Distribution:
Cost: 35% (n=70)
Accessibility: 28% (n=56)
Time: 22% (n=44)
Safety: 10% (n=20)
Other: 5% (n=10)""",
            "category": "Text Analysis > Text Classification",
            "tags": ["survey", "open-ended", "categorization", "coding"],
            "source": "Custom"
        },
        {
            "title": "News Article Topic Classifier",
            "prompt_text": """Classify news articles by topic for media analysis research.

Articles: {article_texts}
Topic Taxonomy: {topic_list}
Classification Level: {level} (primary topic only / multi-label)

For each article:
1. Assign primary topic
2. Assign secondary topics (if multi-label)
3. Identify key entities (people, organizations, locations)
4. Determine article slant/framing (if applicable)
5. Extract publication metadata

---EXAMPLE---

Example Classification:
Article: "Senator introduces bill to reduce carbon emissions..."
Primary Topic: Environment & Climate
Secondary Topics: Politics, Energy Policy
Key Entities: [Senator Name], US Senate, Environmental Protection Agency
Framing: Policy-focused, neutral tone
Metadata: Source: Washington Post, Date: 2024-01-15, Author: [Name]

Provide CSV output:
article_id, primary_topic, secondary_topics, entities, slant, source, date""",
            "category": "Text Analysis > Text Classification",
            "tags": ["news", "media-analysis", "topic-modeling"],
            "source": "Custom"
        },
        
        # Sentiment Analysis
        {
            "title": "Advanced Sentiment Analysis with Context",
            "prompt_text": """Analyze the sentiment of the following text with detailed contextual understanding.

Text: {text}
Analysis Type: {type} (document-level/sentence-level/aspect-based)
Domain: {domain} (general/product reviews/social media/political)

Provide:
1. Overall sentiment: Positive/Negative/Neutral/Mixed
2. Sentiment score: -1 (very negative) to +1 (very positive)
3. Confidence level: 0-100%
4. Key sentiment-bearing words/phrases
5. Contextual modifiers (negations, intensifiers)
6. Emotional dimensions (joy, anger, sadness, fear, surprise)
7. Sarcasm/irony detection

---EXAMPLE---

Example:
Text: "Halloween is most likely the greatest holiday of them all. It hits all the high notes for me! Although, I don't like having my doorbell rung every 5 minutes."

Analysis:
Overall Sentiment: Mixed (Primarily Positive with Negative Aspect)
Score: +0.6
Confidence: 85%
Positive Indicators: "greatest holiday", "hits all the high notes"
Negative Indicators: "don't like", "every 5 minutes" (implies annoyance)
Emotions: Joy (high), Annoyance (moderate)
Structure: Positive statement + Positive elaboration + Negative caveat
Sarcasm: Not detected
Aspect-Based:
- Halloween as holiday: Very Positive (+0.9)
- Doorbell activity: Negative (-0.4)""",
            "category": "Text Analysis > Sentiment Analysis",
            "tags": ["sentiment", "emotion", "nlp", "text-analysis"],
            "source": "Adapted from Wolfram PromptRepository - SentimentAnalyze"
        },
        {
            "title": "Comparative Sentiment Across Time Periods",
            "prompt_text": """Analyze sentiment trends across different time periods for longitudinal research.

Dataset: {text_data_by_period}
Time Periods: {periods}
Context: {research_context}

For each period, analyze:
1. Average sentiment score
2. Sentiment distribution (% positive/negative/neutral)
3. Most common positive/negative themes
4. Sentiment volatility (standard deviation)
5. Significant sentiment shifts between periods

Provide:
- Time series visualization data
- Statistical comparison (t-tests/ANOVA)
- Qualitative interpretation of trends
- Correlation with external events (if known)

---EXAMPLE---

Example Output:
Period 1 (Jan-Mar 2023):
Avg Sentiment: +0.45
Distribution: 65% positive, 20% neutral, 15% negative
Top Positive Theme: "economic recovery"
Top Negative Theme: "inflation concerns"

Period 2 (Apr-Jun 2023):
Avg Sentiment: +0.28
Distribution: 52% positive, 25% neutral, 23% negative
Top Positive Theme: "job market"
Top Negative Theme: "cost of living"

Trend Analysis:
- Significant decrease in sentiment (p<0.01)
- Negative sentiment increased by 8 percentage points
- Shift from optimism to cautious concern
- Possible correlation with Fed rate hikes in April""",
            "category": "Text Analysis > Sentiment Analysis",
            "tags": ["longitudinal", "trend-analysis", "time-series", "sentiment"],
            "source": "Custom"
        },
        {
            "title": "Multi-Lingual Sentiment Analysis",
            "prompt_text": """Conduct sentiment analysis on texts in multiple languages for cross-cultural research.

Texts: {multilingual_texts}
Languages: {language_list}
Research Question: {research_question}

Process:
1. Detect language of each text
2. Apply language-appropriate sentiment analysis
3. Normalize scores for cross-cultural comparison
4. Account for cultural differences in expression
5. Compare sentiment patterns across languages/cultures

Considerations:
- Idioms and cultural expressions
- Politeness norms (e.g., indirect communication in some cultures)
- Translation validation for ambiguous cases

---EXAMPLE---

Example:
Text 1 (English): "This is absolutely terrible!"
Sentiment: Very Negative (-0.9)
Cultural note: Direct expression common in English

Text 2 (Japanese): "少し残念です" (It's a bit disappointing)
Sentiment: Negative (-0.6)
Cultural note: Understatement common; actual sentiment may be stronger
Adjusted Score: -0.8 (accounting for cultural indirect communication)

Cross-Cultural Finding:
Similar underlying negative sentiment, but expressed with different intensity levels due to cultural communication norms.""",
            "category": "Text Analysis > Sentiment Analysis",
            "tags": ["multilingual", "cross-cultural", "sentiment", "translation"],
            "source": "Custom"
        },
        
        # Word Frequency & Patterns
        {
            "title": "Word Frequency Analysis with Context",
            "prompt_text": """Analyze word frequency patterns in the corpus with contextual insights.

Corpus: {text_corpus}
Corpus Size: {n_documents} documents, {n_words} words
Research Focus: {focus}

Generate:
1. Top 50 most frequent words (excluding stopwords)
2. Top 50 most frequent bigrams (2-word phrases)
3. Top 30 most frequent trigrams (3-word phrases)
4. Keywords in Context (KWIC) for top 10 words
5. Comparative frequency (if multiple sub-corpora)
6. TF-IDF scores for document distinctiveness

Visualizations needed:
- Word cloud data
- Frequency distribution plot data
- Zipf's law fit

---EXAMPLE---

Example Output:
TOP WORDS:
1. research (n=342, 2.1% of corpus)
2. data (n=298, 1.8%)
3. analysis (n=276, 1.7%)
...

TOP BIGRAMS:
1. "social media" (n=156)
2. "mental health" (n=142)
3. "qualitative research" (n=128)
...

KWIC for "participants":
"...informed consent, **participants** completed a survey..."
"...recruited **participants** through social media..."
"...thanked **participants** for their time..."

Insight: "participants" most commonly appears in methodological contexts (78% of occurrences).""",
            "category": "Text Analysis > Word Frequency & Patterns",
            "tags": ["frequency", "corpus-analysis", "text-mining", "keywords"],
            "source": "Custom"
        },
        {
            "title": "Collocation and Co-occurrence Analysis",
            "prompt_text": """Identify meaningful word collocations and co-occurrence patterns.

Text: {corpus}
Target Word: {keyword}
Window Size: {window} words

Analyze:
1. Words most frequently co-occurring with target word
2. Statistical significance of collocations (PMI, t-score, log-likelihood)
3. Semantic domains of collocates
4. Positional preferences (before/after target)
5. Comparison across different document types/time periods

---EXAMPLE---

Example Analysis for target word "climate":
Most Frequent Collocates (±5 words):
1. change (PMI: 8.2, t-score: 45.6) - appears 89% of time
2. crisis (PMI: 7.8, t-score: 32.1)
3. global (PMI: 6.9, t-score: 28.4)

Positional Analysis:
Before "climate": global (45%), current (12%), changing (8%)
After "climate": change (78%), crisis (15%), policy (7%)

Semantic Domains:
- Environmental: change, warming, carbon (56%)
- Political: policy, action, agreement (28%)
- Scientific: data, research, models (16%)

Temporal Change:
2020: "climate change" (primary)
2023: "climate crisis" (increasing usage, +45%)""",
            "category": "Text Analysis > Word Frequency & Patterns",
            "tags": ["collocation", "co-occurrence", "corpus-linguistics"],
            "source": "Custom"
        },
        {
            "title": "Linguistic Pattern Mining for Discourse Analysis",
            "prompt_text": """Extract and analyze linguistic patterns for discourse analysis research.

Corpus: {corpus}
Analysis Type: {type} (discourse markers/hedging/stance markers/metadiscourse)
Research Question: {question}

Identify:
1. Discourse markers (however, therefore, in contrast)
2. Hedging expressions (might, perhaps, possibly)
3. Stance markers (clearly, obviously, unfortunately)
4. Personal pronouns usage patterns
5. Modal verbs distribution
6. Sentence complexity metrics

---EXAMPLE---

Example Output:
DISCOURSE MARKERS:
Additive: and (n=156), furthermore (n=23), moreover (n=18)
Adversative: however (n=45), but (n=134), nevertheless (n=12)
Causal: therefore (n=34), thus (n=28), because (n=89)

HEDGING:
Frequency: 12.3 hedges per 1000 words
Most common: "may" (n=67), "possibly" (n=34), "suggest" (n=45)
Context: 67% in discussion sections, 23% in results

STANCE:
Certainty markers: "clearly" (n=23), "definitely" (n=12)
Uncertainty markers: "perhaps" (n=34), "might" (n=56)
Ratio: Uncertainty:Certainty = 2.6:1

Interpretation:
High hedging frequency suggests cautious academic tone. Uncertainty markers dominate, typical of empirical social science writing.""",
            "category": "Text Analysis > Word Frequency & Patterns",
            "tags": ["discourse-analysis", "linguistic-patterns", "corpus-linguistics"],
            "source": "Custom"
        },
        
        # ============================================
        # 7. ACADEMIC WRITING
        # ============================================
        
        {
            "title": "Literature Review Section Generator",
            "prompt_text": """Generate a comprehensive literature review section for an academic paper.

Topic: {research_topic}
Key Studies: {study_list}
Theoretical Framework: {framework}
Target Length: {words} words
Citation Style: APA 7th edition

Structure the review with:
1. Opening paragraph: Importance of topic and scope of review
2. Thematic organization (3-5 themes)
3. For each theme:
   - Overview of research
   - Key findings synthesis
   - Methodological approaches
   - Debates/contradictions
   - Chronological development
4. Theoretical framework integration
5. Research gaps identification
6. Transition to current study

Writing guidelines:
- Use past tense for specific studies ("Smith (2020) found...")
- Use present tense for established knowledge ("Research shows...")
- Provide critical analysis, not just summary
- Integrate citations smoothly
- Maintain logical flow between paragraphs

---EXAMPLE---

Example Opening:
"The relationship between social media use and mental health among adolescents has garnered significant attention in recent years, with researchers examining various dimensions of this complex association (Author1, 2022; Author2, 2023). This literature review synthesizes current evidence on [scope], organizing findings around three key themes: passive versus active use, age-related vulnerabilities, and protective factors..."

Generate full review with proper citations and transitions.""",
            "category": "Academic Writing > Literature Review",
            "tags": ["literature-review", "academic-writing", "research-paper"],
            "source": "Custom"
        },
        {
            "title": "Research Paper Abstract Generator",
            "prompt_text": """Create a structured abstract for submission to {journal_name}.

Paper Details:
- Research Question: {question}
- Method: {method}
- Sample: {sample}
- Key Findings: {findings}
- Implications: {implications}

Abstract Requirements:
- Word limit: {limit} words
- Structure: Background, Methods, Results, Conclusions
- Keywords: {keywords}

Generate an abstract following journal guidelines:

Background (2-3 sentences): Research context and gap
Methods (2-3 sentences): Design, sample, measures
Results (3-4 sentences): Key findings with statistics
Conclusions (2-3 sentences): Implications and significance

---EXAMPLE---

Example:
Background: Despite extensive research on social media effects, the mechanisms linking passive scrolling to mental health outcomes remain unclear. This study examined the mediating role of social comparison in the relationship between passive social media use and depressive symptoms.

Methods: A longitudinal survey of 1,247 adolescents (ages 13-17) was conducted over 2 years. Participants completed measures of social media use patterns, social comparison tendencies, and depressive symptoms at three time points.

Results: Structural equation modeling revealed that passive scrolling predicted increased depressive symptoms (β=.23, p<.001), with social comparison fully mediating this relationship (indirect effect=.15, 95% CI [.11, .19]). Active engagement showed no association with negative outcomes. Effects were stronger for females and younger adolescents.

Conclusions: Social comparison processes explain why passive social media use relates to poor mental health. Interventions should focus on reducing upward social comparisons rather than limiting overall social media time.

Keywords: social media, adolescents, mental health, social comparison, longitudinal""",
            "category": "Academic Writing > Research Papers",
            "tags": ["abstract", "academic-writing", "publication"],
            "source": "Custom"
        },
        {
            "title": "Research Report Executive Summary",
            "prompt_text": """Create an executive summary for a research report aimed at policymakers/practitioners.

Report Details:
- Study Title: {title}
- Commissioner: {organization}
- Key Findings: {findings_list}
- Recommendations: {recommendations}
- Target Audience: {audience}

Executive Summary Requirements:
- Length: 2 pages maximum
- Avoid jargon
- Use active voice
- Include visuals/data points
- Actionable recommendations

Structure:
1. Context & Purpose (1 paragraph)
2. What We Did (1 paragraph - methodology in plain language)
3. What We Found (3-5 key findings with data)
4. What It Means (implications)
5. What You Should Do (3-5 actionable recommendations)

---EXAMPLE---

Example:
**EXECUTIVE SUMMARY: Impact of Remote Work on Employee Wellbeing**

**Why This Matters**
With 60% of knowledge workers now in hybrid arrangements, understanding remote work's effects on wellbeing is critical for organizational policy.

**What We Did**
We surveyed 2,500 employees across 15 organizations and conducted 60 in-depth interviews between January-June 2024.

**Key Findings**
• Remote workers report 27% higher work-life balance satisfaction
• However, 42% experience increased isolation
• Productivity remains stable, but innovation decreased 15%
• Mental health outcomes depend heavily on manager support

**Implications**
Remote work is not uniformly positive or negative—success depends on implementation quality and individual circumstances.

**Recommendations**
1. Mandate 2-3 in-person collaboration days monthly
2. Train managers in remote leadership practices
3. Provide dedicated home office stipends
4. Create virtual social connection opportunities
5. Monitor isolation indicators quarterly

Use clear headings, bullet points, and data callouts.""",
            "category": "Academic Writing > Reports & Presentations",
            "tags": ["executive-summary", "policy", "research-report"],
            "source": "Custom"
        },
        
        # ============================================
        # 8. ADVANCED METHODS
        # ============================================
        
        {
            "title": "LLM Fine-Tuning Data Preparation Guide",
            "prompt_text": """Guide me through preparing a dataset for fine-tuning an LLM for {specific_task}.

Task: {task_description}
Current Data: {data_description}
Target Model: {model_name}
Expected Output: {desired_output_format}

Provide step-by-step guidance:
1. Data requirements assessment
   - Minimum dataset size for task type
   - Quality over quantity considerations
   - Diversity requirements

2. Data formatting
   - Input-output pair structure
   - JSON/JSONL format
   - Example formatted entries

3. Data quality checks
   - Consistency verification
   - Label quality assessment
   - Balanced representation

4. Train/validation/test split strategy
   - Recommended split ratios
   - Stratification approach

5. Fine-tuning parameters
   - Learning rate recommendations
   - Batch size
   - Number of epochs
   - Evaluation metrics

---EXAMPLE---

Example Output:
**Task: Sentiment Classification of Academic Paper Reviews**

**Data Requirements:**
- Minimum: 500-1000 labeled examples
- Recommended: 2000+ for robust performance
- Need balanced positive/negative/neutral examples

**Format Example:**
```json
{"prompt": "Review: This paper makes a significant contribution...\\n\\nSentiment:", "completion": " Positive"}
{"prompt": "Review: The methodology is flawed and...\\n\\nSentiment:", "completion": " Negative"}
```

**Quality Checks:**
- Ensure consistent labeling (inter-rater reliability >0.8)
- Remove duplicates
- Verify completion token consistency

**Split Strategy:**
- Train: 70% (1400 examples)
- Validation: 15% (300 examples)  
- Test: 15% (300 examples)
- Stratify by sentiment class

**Fine-tuning Settings (OpenAI GPT-3.5):**
- Learning rate: 0.1
- Batch size: 8
- Epochs: 4
- Evaluate on validation set each epoch

Provide Python code for data preparation pipeline.""",
            "category": "Advanced Methods > Model Fine-tuning",
            "tags": ["llm", "fine-tuning", "machine-learning", "ai"],
            "source": "Custom"
        },
        {
            "title": "API Integration Workflow for Research Automation",
            "prompt_text": """Design a custom API integration workflow to automate {research_task}.

Task: {task_description}
Data Sources: {api_list}
Frequency: {frequency}
Output Needed: {output_format}

Create a comprehensive integration plan:

1. **API Selection & Authentication**
   - List required APIs
   - Authentication methods for each
   - Rate limits and pricing considerations
   - Fallback options if APIs fail

2. **Data Flow Architecture**
   - Step-by-step data pipeline
   - Error handling at each stage
   - Data validation checkpoints
   - Storage strategy

3. **Implementation Code**
   - Python script with error handling
   - Configuration file template
   - Logging strategy
   - Scheduling (cron job/Airflow)

4. **Data Quality Assurance**
   - Automated checks
   - Alerting for failures
   - Manual review triggers

5. **Documentation**
   - API credentials setup
   - Running the pipeline
   - Troubleshooting guide

---EXAMPLE---

Example Workflow: Automated Social Media Monitoring

**Goal:** Collect daily Twitter mentions of research keywords, analyze sentiment, store in database.

**APIs Needed:**
1. Twitter API v2 (Academic Research access)
2. OpenAI API (sentiment analysis)
3. PostgreSQL database

**Data Flow:**
```
Twitter API → Raw tweets → Clean/preprocess → Sentiment API → 
Structured data → PostgreSQL → Daily summary email
```

**Python Implementation:**
```python
import tweepy
import openai
import psycopg2
from datetime import datetime, timedelta

# Configuration
KEYWORDS = ["climate change", "global warming"]
TWEET_LIMIT = 1000

# Step 1: Fetch tweets
# Step 2: Clean data
# Step 3: Sentiment analysis
# Step 4: Store results
# Step 5: Generate report

# Error handling and logging throughout
```

**Monitoring:**
- Daily email summary of new data
- Alert if <100 tweets collected (anomaly)
- Weekly data quality report

Provide complete, production-ready code.""",
            "category": "Advanced Methods > Custom API Integration",
            "tags": ["api", "automation", "research-workflow", "python"],
            "source": "Custom"
        },
    ]
    
    # Insert all example prompts
    for prompt_data in example_prompts:
        query = prompts.insert().values(**prompt_data, views=0, created_at=datetime.utcnow())
        await database.execute(query)
    
    print(f"✅ Seeded database with {len(example_prompts)} social science research prompts")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
import arxiv
import json
import os
from typing import List, Optional
from enum import Enum
from mcp.server.fastmcp import FastMCP

# Enhanced for Google Colab compatibility
PAPER_DIR = "/content/papers" if os.path.exists("/content") else "papers"

# Get port from environment variable (Render sets this, defaults to 8001 for local dev)
PORT = int(os.environ.get("PORT", 8001))

# Initialize FastMCP server with host and port in constructor
mcp = FastMCP("enhanced_research", host="0.0.0.0", port=PORT)

class SearchField(Enum):
    """Available search fields for arXiv queries"""
    ALL = "all"
    TITLE = "ti"
    AUTHOR = "au"
    ABSTRACT = "abs"
    COMMENT = "co"
    JOURNAL_REF = "jr"
    CATEGORY = "cat"
    REPORT_NUMBER = "rn"

class SortOption(Enum):
    """Available sort options for arXiv queries"""
    RELEVANCE = "relevance"
    SUBMITTED_DATE = "submittedDate"
    LAST_UPDATED_DATE = "lastUpdatedDate"

@mcp.tool()
def search_papers(
    query: str, 
    max_results: int = 5,
    sort_by: str = "relevance",
    sort_order: str = "descending",
    search_field: str = "all",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    author_search: Optional[str] = None
) -> dict:
    """
    Enhanced search for papers on arXiv with advanced filtering options.

    Args:
        query: The main search term/topic
        max_results: Maximum number of results to retrieve (default: 5, max: 30000)
        sort_by: Sort criterion - "relevance", "submittedDate", or "lastUpdatedDate" (default: relevance)
        sort_order: Sort order - "ascending" or "descending" (default: descending)
        search_field: Field to search in - "all", "title", "author", "abstract", "category" etc. (default: all)
        date_from: Start date for filtering (YYYYMMDD format, e.g., "20240101")
        date_to: End date for filtering (YYYYMMDD format, e.g., "20241231")
        author_search: Specific author to search for (will be combined with main query)

    Returns:
        Dict containing paper IDs, search parameters used, and summary statistics
    """
    
    # Validate and convert sort_by
    sort_mapping = {
        "relevance": arxiv.SortCriterion.Relevance,
        "submitted": arxiv.SortCriterion.SubmittedDate,
        "submitteddate": arxiv.SortCriterion.SubmittedDate,
        "updated": arxiv.SortCriterion.LastUpdatedDate,
        "lastupdated": arxiv.SortCriterion.LastUpdatedDate,
        "lastupdateddate": arxiv.SortCriterion.LastUpdatedDate
    }
    sort_criterion = sort_mapping.get(sort_by.lower().replace("_", ""), arxiv.SortCriterion.Relevance)
    
    # Validate and convert sort_order
    order_mapping = {
        "desc": arxiv.SortOrder.Descending,
        "descending": arxiv.SortOrder.Descending,
        "asc": arxiv.SortOrder.Ascending,
        "ascending": arxiv.SortOrder.Ascending
    }
    sort_order_enum = order_mapping.get(sort_order.lower(), arxiv.SortOrder.Descending)
    
    # Build the search query with field prefixes
    search_query_parts = []
    
    # Handle field-specific search
    field_mapping = {
        "title": "ti",
        "author": "au", 
        "abstract": "abs",
        "category": "cat",
        "comment": "co",
        "journal": "jr",
        "all": "all"
    }
    field_prefix = field_mapping.get(search_field.lower(), "all")
    
    # FIXED: Proper query construction for arXiv API
    if field_prefix != "all":
        # For specific fields, keep the prefix
        search_query_parts.append(f"{field_prefix}:{query}")
    else:
        # For "all" fields, omit the prefix for multi-word queries
        # This fixes the HTTP 400 error with queries like "all:swarm agents artificial intelligence"
        search_query_parts.append(query)
    
    # Add author search if specified
    if author_search:
        # Clean author name for search (replace spaces with underscores)
        clean_author = author_search.replace(" ", "_").lower()
        search_query_parts.append(f"au:{clean_author}")
    
    # Add date filtering if specified
    if date_from or date_to:
        if date_from and date_to:
            # Both dates provided - create range
            search_query_parts.append(f"submittedDate:[{date_from}0000 TO {date_to}2359]")
        elif date_from:
            # Only start date - from this date forward
            search_query_parts.append(f"submittedDate:[{date_from}0000 TO *]")
        elif date_to:
            # Only end date - up to this date
            search_query_parts.append(f"submittedDate:[* TO {date_to}2359]")
    
    # Combine all parts with AND
    final_query = " AND ".join(search_query_parts)
    
    # Use arxiv to find the papers 
    client = arxiv.Client()
    
    # Create search with enhanced parameters
    search = arxiv.Search(
        query=final_query,
        max_results=max_results,
        sort_by=sort_criterion,
        sort_order=sort_order_enum
    )

    papers = client.results(search)

    # Create directory structure (enhanced for Colab)
    query_slug = query.lower().replace(" ", "_").replace("/", "_")[:50]  # Limit length
    if author_search:
        query_slug += f"_by_{author_search.replace(' ', '_')}"
    
    path = os.path.join(PAPER_DIR, query_slug)
    os.makedirs(path, exist_ok=True)

    file_path = os.path.join(path, "papers_info.json")

    # Try to load existing papers info
    try:
        with open(file_path, "r", encoding='utf-8') as json_file:
            papers_info = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        papers_info = {}

    # Process each paper and add to papers_info  
    paper_ids = []
    new_papers_count = 0
    
    for paper in papers:
        paper_id = paper.get_short_id()
        paper_ids.append(paper_id)
        
        if paper_id not in papers_info:  # Only process if new
            new_papers_count += 1
            paper_info = {
                'title': paper.title,
                'authors': [author.name for author in paper.authors],
                'summary': paper.summary,
                'pdf_url': paper.pdf_url,
                'published': str(paper.published.date()),
                'updated': str(paper.updated.date()) if paper.updated else str(paper.published.date()),
                'categories': paper.categories,
                'primary_category': paper.primary_category,
                'entry_id': paper.entry_id,
                'search_params': {
                    'query': query,
                    'sort_by': sort_by,
                    'search_field': search_field,
                    'author_search': author_search,
                    'date_range': f"{date_from} to {date_to}" if date_from or date_to else None
                }
            }
            papers_info[paper_id] = paper_info

    # Save updated papers_info to json file
    with open(file_path, "w", encoding='utf-8') as json_file:
        json.dump(papers_info, json_file, indent=2, ensure_ascii=False)

    # Return comprehensive results
    return {
        "paper_ids": paper_ids,
        "total_found": len(paper_ids),
        "new_papers": new_papers_count,
        "search_query": final_query,
        "search_parameters": {
            "original_query": query,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "search_field": search_field,
            "author_search": author_search,
            "date_from": date_from,
            "date_to": date_to,
            "max_results": max_results
        },
        "storage_path": file_path,
        "message": f"Found {len(paper_ids)} papers ({new_papers_count} new). Results saved to {file_path}"
    }

@mcp.tool()
def search_by_author(author_name: str, max_results: int = 10, sort_by: str = "submittedDate") -> dict:
    """
    Simplified tool specifically for author searches.
    
    Args:
        author_name: Full name of the author to search for
        max_results: Maximum number of results (default: 10)
        sort_by: Sort criterion (default: submittedDate)
    
    Returns:
        Dict with search results
    """
    return search_papers(
        query="*",  # Match all papers
        max_results=max_results,
        sort_by=sort_by,
        search_field="author",
        author_search=author_name
    )

@mcp.tool()
def search_recent_papers(topic: str, days_back: int = 7, max_results: int = 10) -> dict:
    """
    Search for recent papers on a topic within the last N days.
    
    Args:
        topic: The research topic to search for
        days_back: Number of days to look back (default: 7)
        max_results: Maximum number of results (default: 10)
    
    Returns:
        Dict with recent papers
    """
    from datetime import datetime, timedelta
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    date_from = start_date.strftime("%Y%m%d")
    date_to = end_date.strftime("%Y%m%d")
    
    return search_papers(
        query=topic,
        max_results=max_results,
        sort_by="submittedDate",
        sort_order="descending",
        date_from=date_from,
        date_to=date_to
    )

@mcp.tool()
def extract_info(paper_id: str) -> str:
    """
    Search for information about a specific paper across all topic directories.

    Args:
        paper_id: The ID of the paper to look for

    Returns:
        JSON string with paper information if found, error message if not found
    """
    # Check if PAPER_DIR exists
    if not os.path.exists(PAPER_DIR):
        return f"Papers directory {PAPER_DIR} does not exist. No saved papers found."

    for item in os.listdir(PAPER_DIR):
        item_path = os.path.join(PAPER_DIR, item)
        if os.path.isdir(item_path):
            file_path = os.path.join(item_path, "papers_info.json")
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r", encoding='utf-8') as json_file:
                        papers_info = json.load(json_file)
                        if paper_id in papers_info:
                            return json.dumps(papers_info[paper_id], indent=2, ensure_ascii=False)
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"Error reading {file_path}: {str(e)}")
                    continue

    return f"No saved information found for paper {paper_id}."

@mcp.resource("papers://folders")
def get_available_folders() -> str:
    """
    List all available topic folders in the papers directory.
    Enhanced for Google Colab compatibility.
    """
    folders = []

    # Get all topic directories
    if os.path.exists(PAPER_DIR):
        for topic_dir in os.listdir(PAPER_DIR):
            topic_path = os.path.join(PAPER_DIR, topic_dir)
            if os.path.isdir(topic_path):
                papers_file = os.path.join(topic_path, "papers_info.json")
                if os.path.exists(papers_file):
                    # Get count of papers in this folder
                    try:
                        with open(papers_file, 'r', encoding='utf-8') as f:
                            papers_data = json.load(f)
                            paper_count = len(papers_data)
                            folders.append((topic_dir, paper_count))
                    except:
                        folders.append((topic_dir, 0))

    # Create enhanced markdown list
    content = "# Available Research Topics\n\n"
    if folders:
        content += f"**Storage Location**: `{PAPER_DIR}`\n\n"
        content += "| Topic | Paper Count | Access |\n"
        content += "|-------|-------------|--------|\n"
        for folder, count in folders:
            readable_name = folder.replace("_", " ").title()
            content += f"| {readable_name} | {count} papers | `@{folder}` |\n"
        content += f"\n**Total Topics**: {len(folders)}\n"
        content += "\n*Use @topic_name to access papers in that topic.*\n"
    else:
        content += f"No research topics found in `{PAPER_DIR}`.\n"
        content += "Use the `search_papers` tool to start collecting papers.\n"

    return content

@mcp.resource("papers://{topic}")
def get_topic_papers(topic: str) -> str:
    """
    Get detailed information about papers on a specific topic.
    Enhanced with better formatting and metadata.

    Args:
        topic: The research topic to retrieve papers for
    """
    topic_dir = topic.lower().replace(" ", "_")
    papers_file = os.path.join(PAPER_DIR, topic_dir, "papers_info.json")

    if not os.path.exists(papers_file):
        return f"# No papers found for topic: {topic}\n\nTry searching for papers on this topic first using the `search_papers` tool."

    try:
        with open(papers_file, 'r', encoding='utf-8') as f:
            papers_data = json.load(f)

        # Create enhanced markdown content with paper details
        content = f"# Papers on {topic.replace('_', ' ').title()}\n\n"
        content += f"**Total papers**: {len(papers_data)}\n"
        content += f"**Storage location**: `{papers_file}`\n\n"

        # Group by publication year for better organization
        papers_by_year = {}
        for paper_id, paper_info in papers_data.items():
            year = paper_info['published'][:4]  # Extract year
            if year not in papers_by_year:
                papers_by_year[year] = []
            papers_by_year[year].append((paper_id, paper_info))

        # Sort years in descending order
        for year in sorted(papers_by_year.keys(), reverse=True):
            content += f"## {year} ({len(papers_by_year[year])} papers)\n\n"
            
            for paper_id, paper_info in papers_by_year[year]:
                content += f"### {paper_info['title']}\n"
                content += f"- **Paper ID**: `{paper_id}`\n"
                content += f"- **Authors**: {', '.join(paper_info['authors'][:3])}"
                if len(paper_info['authors']) > 3:
                    content += f" *et al.* ({len(paper_info['authors'])} total)"
                content += "\n"
                content += f"- **Published**: {paper_info['published']}"
                if paper_info.get('updated') != paper_info['published']:
                    content += f" (Updated: {paper_info['updated']})"
                content += "\n"
                content += f"- **Category**: {paper_info.get('primary_category', 'N/A')}\n"
                content += f"- **PDF**: [Download PDF]({paper_info['pdf_url']})\n"
                content += f"- **arXiv**: [View on arXiv]({paper_info.get('entry_id', '#')})\n\n"
                
                # Truncated summary
                summary = paper_info['summary']
                if len(summary) > 300:
                    summary = summary[:300] + "..."
                content += f"**Abstract**: {summary}\n\n"
                content += "---\n\n"

        return content
    except json.JSONDecodeError:
        return f"# Error reading papers data for {topic}\n\nThe papers data file is corrupted."
    except Exception as e:
        return f"# Error accessing papers for {topic}\n\nError: {str(e)}"

@mcp.prompt()
def generate_enhanced_search_prompt(
    topic: str = "", 
    num_papers: int = 5,
    search_type: str = "comprehensive",
    author: str = "",
    date_filter: str = ""
) -> str:
    """
    Generate an enhanced prompt for Claude to intelligently search and analyze academic papers.
    
    Args:
        topic: Research topic to investigate
        num_papers: Number of papers to find
        search_type: Type of search - "comprehensive", "recent", "by_author", "specific_field"
        author: Specific author to focus on (optional)
        date_filter: Date filtering preference (optional)
    """
    
    base_instructions = f"""
You are an AI research assistant tasked with finding and analyzing academic papers about '{topic}'. 
Your goal is to provide comprehensive, well-organized research insights.

## INTELLIGENT SEARCH STRATEGY

Before searching, analyze the user's request and ask clarifying questions if needed:

1. **Scope Clarification**: 
   - Is this a broad survey of the field or focused on specific aspects?
   - Are there particular time periods of interest?
   - Any specific methodologies or applications to focus on?

2. **Search Optimization**:
   - If the topic is very broad, ask for refinement or search multiple specific subtopics
   - For author searches, ask if they want recent work or career overview  
   - For recent work, determine appropriate time window (days, months, years)

## ENHANCED SEARCH TOOLS AVAILABLE

Use these tools strategically based on the research need:

- `search_papers()` - Main search with extensive filtering options:
  * sort_by: "relevance", "submittedDate", "lastUpdatedDate" 
  * search_field: "all", "title", "author", "abstract", "category"
  * date_from/date_to: for date filtering (YYYYMMDD format)
  * author_search: for author-specific searches

- `search_by_author()` - Simplified author-focused search
- `search_recent_papers()` - Recent papers in last N days  

## SEARCH EXECUTION PLAN

1. **Primary Search**: Start with most relevant search strategy
2. **Refinement**: If results are too broad/narrow, refine with different parameters
3. **Supplementary Searches**: Add complementary searches as needed
4. **Analysis**: Extract and synthesize information from all found papers

## ANALYSIS AND PRESENTATION

For each paper found, extract and organize:
- Title and authors
- Publication/update dates  
- Key contributions and innovations
- Methodologies used
- Relevance to research question
- Significance in the field

Provide a synthesis including:
- Current state of research in the field
- Major trends and developments
- Key researchers and institutions
- Research gaps and future directions
- Most impactful recent papers

## ADAPTIVE QUESTIONING

If the initial request lacks specificity, ask targeted questions like:
- "Are you interested in theoretical foundations or practical applications of {topic}?"
- "Would you like papers from the last year, or a broader historical perspective?"
- "Are there specific authors or research groups you'd like me to focus on?"
- "Should I prioritize recent developments or seminal papers in the field?"

Start by analyzing the request and then proceed with your optimized search strategy."""

    # Add specific guidance based on search type
    if search_type == "recent":
        base_instructions += f"""

## RECENT RESEARCH FOCUS
You're looking for recent developments in {topic}. Use `search_recent_papers()` and sort by submission date.
Pay special attention to:
- Latest methodological advances
- Emerging trends and applications  
- Recent experimental results
- New theoretical insights"""

    elif search_type == "by_author" and author:
        base_instructions += f"""

## AUTHOR-FOCUSED ANALYSIS
You're analyzing work by {author} on {topic}. Use `search_by_author()` and consider:
- Evolution of their research over time
- Key contributions to the field
- Collaboration patterns
- Most cited or impactful papers"""

    elif search_type == "comprehensive":
        base_instructions += f"""

## COMPREHENSIVE SURVEY
Conduct a thorough analysis of {topic} using multiple search strategies:
- Start with relevance-based search for foundational papers
- Add recent papers for latest developments
- Consider different search fields (title, abstract) for completeness
- Look for review papers and surveys in the field"""

    base_instructions += f"""

## EXECUTION
Begin by briefly outlining your search strategy, then execute the searches and provide your comprehensive analysis.
Target: {num_papers} papers minimum, but adjust based on result quality and relevance.

Now proceed with your intelligent search and analysis of '{topic}'."""

    return base_instructions

if __name__ == "__main__":
    # Ensure papers directory exists (especially important for Colab)
    os.makedirs(PAPER_DIR, exist_ok=True)
    
    print(f"Starting Enhanced arXiv MCP server on 0.0.0.0:{PORT}")
    print(f"Papers will be stored in: {PAPER_DIR}")
    
    # Check if running in Google Colab
    if "/content" in PAPER_DIR:
        print("🔬 Google Colab environment detected - papers will persist in /content/papers")
    
    # Run with SSE transport (host and port already set in constructor)
    mcp.run(transport='sse')

from typing import TypedDict, List, Dict, Annotated
from app.models.article import Article, ArticleCluster
from app.models.report import (
    SummaryReport,
    FactVerificationReport,
    BiasReport,
    CredibilityReport,
    ConsensusReport,
    IntelligenceReport,
)

def append_error(left: List[str], right: List[str]) -> List[str]:
    """Reducer that appends errors to the state list."""
    return left + right

def update_summaries(
    left: Dict[str, SummaryReport], right: Dict[str, SummaryReport]
) -> Dict[str, SummaryReport]:
    """Reducer that merges summaries dictionaries by key (cluster_id)."""
    merged = left.copy()
    merged.update(right)
    return merged

def update_fact_verifications(
    left: Dict[str, FactVerificationReport], right: Dict[str, FactVerificationReport]
) -> Dict[str, FactVerificationReport]:
    """Reducer that merges fact verification reports by key (cluster_id)."""
    merged = left.copy()
    merged.update(right)
    return merged

def update_bias_analyses(
    left: Dict[str, BiasReport], right: Dict[str, BiasReport]
) -> Dict[str, BiasReport]:
    """Reducer that merges bias reports by key (cluster_id)."""
    merged = left.copy()
    merged.update(right)
    return merged

def update_credibilities(
    left: Dict[str, CredibilityReport], right: Dict[str, CredibilityReport]
) -> Dict[str, CredibilityReport]:
    """Reducer that merges credibility reports by key (cluster_id)."""
    merged = left.copy()
    merged.update(right)
    return merged

def update_consensuses(
    left: Dict[str, ConsensusReport], right: Dict[str, ConsensusReport]
) -> Dict[str, ConsensusReport]:
    """Reducer that merges consensus reports by key (cluster_id)."""
    merged = left.copy()
    merged.update(right)
    return merged

def update_final_reports(
    left: Dict[str, IntelligenceReport], right: Dict[str, IntelligenceReport]
) -> Dict[str, IntelligenceReport]:
    """Reducer that merges final intelligence reports by key (cluster_id)."""
    merged = left.copy()
    merged.update(right)
    return merged

class GraphState(TypedDict):
    """
    State definition for the LangGraph agentic multi-agent workflow.
    Tracks state elements including raw queries, gathered articles, event clusters, 
    individual agent analysis reports, and errors across steps.
    """
    # Target search query or news topic
    query: str
    
    # Collected articles and their computed event clusters
    articles: List[Article]
    clusters: List[ArticleCluster]
    
    # Active cluster IDs that require individual reports
    active_cluster_ids: List[str]
    
    # Mappings of cluster_id -> sub-agent output report
    summaries: Annotated[Dict[str, SummaryReport], update_summaries]
    fact_verifications: Annotated[Dict[str, FactVerificationReport], update_fact_verifications]
    bias_analyses: Annotated[Dict[str, BiasReport], update_bias_analyses]
    credibilities: Annotated[Dict[str, CredibilityReport], update_credibilities]
    consensuses: Annotated[Dict[str, ConsensusReport], update_consensuses]
    final_reports: Annotated[Dict[str, IntelligenceReport], update_final_reports]
    
    # Logging errors across steps in the graph
    errors: Annotated[List[str], append_error]

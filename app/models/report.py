from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from app.models.article import ArticleSource

class SummaryReport(BaseModel):
    headline: str = Field(..., description="An overarching headline summarizing the event")
    overall_summary: str = Field(..., description="A concise, high-level summary of the clustered event")
    key_developments: List[str] = Field(..., description="Bullet points highlighting key developments or facts")
    timeline: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Chronological timeline of events extracted, with keys like 'timestamp', 'event', 'source_url'"
    )

class FactualClaim(BaseModel):
    claim: str = Field(..., description="The factual statement extracted from the articles")
    sources: List[str] = Field(..., description="URLs or names of sources making or referencing this claim")
    verification_status: str = Field(
        ...,
        description="Status of claim verification: 'verified', 'contradicted', 'unverified', or 'disputed'"
    )
    analysis: str = Field(..., description="Reasoning/evidence backing the verification status")

class Contradiction(BaseModel):
    claim_a: str = Field(..., description="Claim statement from source A")
    source_a: str = Field(..., description="Source A details/URL")
    claim_b: str = Field(..., description="Contradictory claim statement from source B")
    source_b: str = Field(..., description="Source B details/URL")
    description: str = Field(..., description="Analysis of the contradiction and why they clash")

class FactVerificationReport(BaseModel):
    verified_claims: List[FactualClaim] = Field(default_factory=list, description="Factual claims verified across sources")
    disputed_claims: List[FactualClaim] = Field(default_factory=list, description="Claims that are disputed or unverified")
    contradictions: List[Contradiction] = Field(default_factory=list, description="Direct contradictions found between sources")

class ArticleBias(BaseModel):
    article_url: str = Field(..., description="URL of the article analyzed")
    political_leaning: str = Field(..., description="Assessed political stance, e.g. Left, Center-Left, Center, Center-Right, Right")
    emotional_tone: str = Field(..., description="Emotional tone of the article (e.g. neutral, alarmist, sensational, objective)")
    emotionally_charged_words: List[str] = Field(default_factory=list, description="Specific words or phrases with strong emotional charge")
    framing_analysis: str = Field(..., description="Brief analysis of how the story is framed or slanted")

class BiasReport(BaseModel):
    overall_bias_narrative: str = Field(..., description="Summary of general bias trends across the source spectrum for this cluster")
    individual_biases: List[ArticleBias] = Field(default_factory=list, description="Detailed bias analysis per article")

class SourceCredibility(BaseModel):
    source_name: str = Field(..., description="Name of the news source")
    domain: str = Field(..., description="Domain of the source")
    reliability_score: float = Field(..., description="Score from 0.0 (completely unreliable) to 1.0 (highly reliable)")
    factual_consistency: float = Field(..., description="Consistency score from 0.0 to 1.0 based on history or cross-reference")
    justification: str = Field(..., description="Explanation for the assigned scores")

class CredibilityReport(BaseModel):
    overall_cluster_credibility: float = Field(..., description="Aggregate credibility score for the cluster from 0.0 to 1.0")
    sources_credibility: List[SourceCredibility] = Field(default_factory=list, description="Credibility details for each source in the cluster")

class ConsensusReport(BaseModel):
    consensus_view: str = Field(..., description="The unified, objective narrative agreed upon by resolving conflicts")
    resolved_conflicts: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of conflicts and how they were resolved. Keys: 'conflict', 'resolution_rationale'"
    )
    unresolved_debates: List[str] = Field(
        default_factory=list,
        description="List of claims or facts that remain unresolved or contested due to lack of evidence"
    )

class IntelligenceReport(BaseModel):
    report_id: str = Field(..., description="Unique identifier for this intelligence report")
    cluster_id: str = Field(..., description="The article cluster this report is based on")
    title: str = Field(..., description="Title of the intelligence report")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")
    
    summary: SummaryReport = Field(..., description="Event summary and timeline")
    fact_verification: FactVerificationReport = Field(..., description="Factual analysis, verified/disputed claims and contradictions")
    bias_analysis: BiasReport = Field(..., description="Political slant and tone analysis across articles")
    credibility: CredibilityReport = Field(..., description="Source credibility evaluations and scores")
    consensus: ConsensusReport = Field(..., description="Consensus resolution and unified narrative")
    
    markdown_report: str = Field(..., description="The fully compiled, human-readable markdown formatted intelligence report")

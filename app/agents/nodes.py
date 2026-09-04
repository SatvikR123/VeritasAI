import logging
import re
from datetime import datetime
from typing import Dict, Any, List
from app.agents.state import GraphState
from app.models.article import Article, ArticleSource, ArticleCluster
from app.models.report import (
    SummaryReport,
    FactVerificationReport,
    BiasReport,
    CredibilityReport,
    ConsensusReport,
    IntelligenceReport,
)
from app.tools.news_api import fetch_news_articles
from app.agents.llm import get_structured_llm

logger = logging.getLogger(__name__)

# Node 1: News Collection Agent
def collect_news(state: GraphState) -> Dict[str, Any]:
    """
    Fetches raw articles matching the state query using the news API tool
    and parses them into strict Article schemas.
    """
    query = state.get("query", "")
    logger.info(f"News Collection Agent: Fetching articles for query '{query}'")
    
    VERIFIED_DOMAINS = {
        "reuters.com", "apnews.com", "bloomberg.com", "nytimes.com", 
        "theguardian.com", "bbc.co.uk", "bbc.com", "cnn.com", 
        "aljazeera.com", "wsj.com", "ft.com", "economist.com",
        "cnbc.com", "reuters.tv", "independent.co.uk"
    }
    
    try:
        # Fetch more articles initially (e.g. 8) to find verified sources, then scrape top 3
        articles_data = fetch_news_articles(query, page_size=8)
        
        # Deduplicate articles based on URL
        seen_urls = set()
        unique_articles = []
        for art in articles_data:
            url = art.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(art)
                
        # Sort to prioritize verified publishers at the top
        def is_verified(art):
            url = art.get("url", "").lower()
            return 1 if any(domain in url for domain in VERIFIED_DOMAINS) else 0
            
        unique_articles.sort(key=is_verified, reverse=True)
        
        # Select top 3 to process
        target_articles = unique_articles[:3]
        
        from app.tools.scraper import extract_article_content
        
        articles_list = []
        for art in target_articles:
            url = art["url"]
            logger.info(f"Scraping full text content from: {url}")
            
            # Scrape full text
            scraped = extract_article_content(url)
            
            if scraped and scraped.get("content") and len(scraped["content"].strip()) > 100:
                content = scraped["content"]
                author = scraped.get("author") or art.get("author")
                title = scraped.get("title") or art.get("title") or "Untitled"
                published_at = scraped.get("published_at") or art.get("published_at")
            else:
                logger.info(f"Scraping failed or returned short content for {url}. Falling back to search description.")
                content = art.get("content") or art.get("description") or ""
                author = art.get("author")
                title = art.get("title") or "Untitled"
                published_at = art.get("published_at")
                
            source = ArticleSource(
                id=art["source"].get("id"),
                name=art["source"].get("name"),
                domain=art["source"].get("domain"),
                url=art["source"].get("url")
            )
            article = Article(
                id=str(hash(url)),
                title=title,
                author=author,
                source=source,
                published_at=published_at,
                url=url,
                content=content,
                description=art.get("description"),
                url_to_image=art.get("url_to_image"),
                language=art.get("language") or "en"
            )
            articles_list.append(article)
        
        logger.info(f"News Collection Agent: Successfully gathered {len(articles_list)} articles.")
        return {"articles": articles_list}
    except Exception as e:
        logger.error(f"News Collection Agent failed: {e}")
        return {"errors": [f"Collection Agent Error: {str(e)}"]}

# Node 2: Event Clustering Agent
def cluster_articles(state: GraphState) -> Dict[str, Any]:
    """
    Groups raw articles into semantic clusters based on shared keywords or entities in the titles.
    Runs locally and deterministically.
    """
    articles = state.get("articles", [])
    logger.info(f"Event Clustering Agent: Grouping {len(articles)} articles into event clusters.")
    
    if not articles:
        return {"clusters": [], "active_cluster_ids": []}
        
    try:
        clusters_map = {}
        for art in articles:
            url_str = str(art.url).lower()
            # If mock databases are returned, automatically group them into the AetherCorp cluster
            if "mock" in url_str or "aethercorp" in art.title.lower():
                cluster_key = "aethercorp_neurallink_launch"
                topic_title = "AetherCorp NeuralLink-V2 Launch Controversy"
            else:
                # Dynamic title keyword grouping: matches overlapping title words
                title_words = [w for w in re.sub(r'[^\w\s]', '', art.title).lower().split() if len(w) > 4]
                cluster_key = "_".join(title_words[:2]) if len(title_words) >= 2 else "general_news"
                topic_title = art.title
                
            if cluster_key not in clusters_map:
                clusters_map[cluster_key] = {
                    "topic": topic_title,
                    "articles": []
                }
            clusters_map[cluster_key]["articles"].append(art)
            
        clusters_list = []
        active_cluster_ids = []
        for key, val in clusters_map.items():
            cluster_id = str(abs(hash(key)))
            cluster = ArticleCluster(
                cluster_id=cluster_id,
                topic=val["topic"],
                articles=val["articles"]
            )
            clusters_list.append(cluster)
            active_cluster_ids.append(cluster_id)
            
        logger.info(f"Event Clustering Agent: Formed {len(clusters_list)} clusters: {[c.topic for c in clusters_list]}")
        return {"clusters": clusters_list, "active_cluster_ids": active_cluster_ids}
    except Exception as e:
        logger.error(f"Event Clustering Agent failed: {e}")
        return {"errors": [f"Clustering Agent Error: {str(e)}"]}

# Node 3: Summarization Agent
def summarize_clusters(state: GraphState) -> Dict[str, Any]:
    """
    Generates high-level summaries and timelines for each event cluster.
    """
    clusters = state.get("clusters", [])
    summaries = {}
    
    for cluster in clusters:
        cid = cluster.cluster_id
        logger.info(f"Summarization Agent: Generating summary for cluster {cid}")
        
        # Prepare text representation for the LLM prompt
        articles_text = "\n\n".join([
            f"Source: {a.source.name}\nTitle: {a.title}\nContent:\n{a.content}" 
            for a in cluster.articles
        ])
        
        prompt = (
            f"You are the Summarization Agent. Read the following news articles talking about "
            f"the same event and extract the primary headline, overall summary, a list of "
            f"key developments, and a chronological timeline detailing the events.\n\n"
            f"Articles:\n{articles_text}"
        )
        
        structured_llm = get_structured_llm(SummaryReport)
        report = structured_llm.invoke(prompt)
        summaries[cid] = report
        
    return {"summaries": summaries}

# Node 4: Fact Verification Agent
def verify_facts(state: GraphState) -> Dict[str, Any]:
    """
    Extracts factual claims and detects inconsistencies or direct contradictions across sources.
    """
    clusters = state.get("clusters", [])
    fact_verifications = {}
    
    for cluster in clusters:
        cid = cluster.cluster_id
        logger.info(f"Fact Verification Agent: Verifying factual claims for cluster {cid}")
        
        articles_text = "\n\n".join([
            f"Source: {a.source.name}\nTitle: {a.title}\nContent:\n{a.content}" 
            for a in cluster.articles
        ])
        
        prompt = (
            f"You are the Fact Verification Agent. Extract major factual claims asserted in "
            f"the following articles. For each claim, evaluate the verification status ('verified', "
            f"'contradicted', 'unverified') by cross-checking sources. "
            f"Identify and list direct contradictions where source A and source B report clashing details.\n\n"
            f"Articles:\n{articles_text}"
        )
        
        structured_llm = get_structured_llm(FactVerificationReport)
        report = structured_llm.invoke(prompt)
        fact_verifications[cid] = report
        
    return {"fact_verifications": fact_verifications}

# Node 5: Bias Detection Agent
def detect_bias(state: GraphState) -> Dict[str, Any]:
    """
    Analyzes framing, tone, and political leaning across articles in the event cluster.
    """
    clusters = state.get("clusters", [])
    bias_analyses = {}
    
    for cluster in clusters:
        cid = cluster.cluster_id
        logger.info(f"Bias Detection Agent: Inspecting linguistic bias and emotional tone for cluster {cid}")
        
        articles_text = "\n\n".join([
            f"Source: {a.source.name}\nURL: {a.url}\nTitle: {a.title}\nContent:\n{a.content}" 
            for a in cluster.articles
        ])
        
        prompt = (
            f"You are the Bias Detection Agent. Analyze the political/ideological leaning (e.g. Left, Right, Center) "
            f"and emotional tone of each article. Identify framing techniques and list specific emotionally "
            f"charged words or phrases. Summarize the overall narrative bias trends across all sources.\n\n"
            f"Articles:\n{articles_text}"
        )
        
        structured_llm = get_structured_llm(BiasReport)
        report = structured_llm.invoke(prompt)
        bias_analyses[cid] = report
        
    return {"bias_analyses": bias_analyses}

# Node 6: Credibility Assessment Agent
def assess_credibility(state: GraphState) -> Dict[str, Any]:
    """
    Assigns credibility and factual consistency scores to news publishers.
    """
    clusters = state.get("clusters", [])
    credibilities = {}
    
    for cluster in clusters:
        cid = cluster.cluster_id
        logger.info(f"Credibility Assessment Agent: Computing publisher trust scores for cluster {cid}")
        
        articles_text = "\n\n".join([
            f"Source: {a.source.name}\nDomain: {a.source.domain or 'unknown'}\nTitle: {a.title}\nContent:\n{a.content}" 
            for a in cluster.articles
        ])
        
        prompt = (
            f"You are the Credibility Assessment Agent. Evaluate the credibility of the publishers of these articles. "
            f"Calculate a reliability score (0.0 to 1.0) and a factual consistency score (0.0 to 1.0) for each, "
            f"providing a brief justification. Calculate an aggregate cluster credibility score.\n\n"
            f"Articles:\n{articles_text}"
        )
        
        structured_llm = get_structured_llm(CredibilityReport)
        report = structured_llm.invoke(prompt)
        credibilities[cid] = report
        
    return {"credibilities": credibilities}

# Node 7: Consensus Generation Agent
def generate_consensus(state: GraphState) -> Dict[str, Any]:
    """
    Integrates sub-agent analysis reports and resolves clashing claims to formulate an objective narrative.
    """
    clusters = state.get("clusters", [])
    consensuses = {}
    
    summaries = state.get("summaries", {})
    fact_verifications = state.get("fact_verifications", {})
    bias_analyses = state.get("bias_analyses", {})
    credibilities = state.get("credibilities", {})
    
    for cluster in clusters:
        cid = cluster.cluster_id
        logger.info(f"Consensus Generation Agent: Integrating reports and resolving conflicts for cluster {cid}")
        
        summary = summaries.get(cid)
        fact_check = fact_verifications.get(cid)
        bias = bias_analyses.get(cid)
        credibility = credibilities.get(cid)
        
        prompt = (
            f"You are the Consensus Generation Agent. Read the analysis reports compiled by the "
            f"Summarization, Fact Verification, Bias Detection, and Credibility agents. "
            f"Formulate a consolidated, highly objective consensus narrative of the event. "
            f"Detail how you resolved conflicting claims, and list any questions that remain unresolved due to a lack of evidence.\n\n"
            f"Agent Reports:\n"
            f"Summary Report: {summary.model_dump_json() if summary else 'N/A'}\n\n"
            f"Fact Verification: {fact_check.model_dump_json() if fact_check else 'N/A'}\n\n"
            f"Bias Analysis: {bias.model_dump_json() if bias else 'N/A'}\n\n"
            f"Credibility Report: {credibility.model_dump_json() if credibility else 'N/A'}"
        )
        
        structured_llm = get_structured_llm(ConsensusReport)
        report = structured_llm.invoke(prompt)
        consensuses[cid] = report
        
    return {"consensuses": consensuses}

# Node 8: Report Generation Agent
def compile_reports(state: GraphState) -> Dict[str, Any]:
    """
    Assembles final data structures and compiles a detailed markdown report for users.
    """
    clusters = state.get("clusters", [])
    final_reports = {}
    
    summaries = state.get("summaries", {})
    fact_verifications = state.get("fact_verifications", {})
    bias_analyses = state.get("bias_analyses", {})
    credibilities = state.get("credibilities", {})
    consensuses = state.get("consensuses", {})
    
    for cluster in clusters:
        cid = cluster.cluster_id
        logger.info(f"Report Generation Agent: Formatting markdown intelligence report for cluster {cid}")
        
        summary = summaries.get(cid)
        fact_check = fact_verifications.get(cid)
        bias = bias_analyses.get(cid)
        credibility = credibilities.get(cid)
        consensus = consensuses.get(cid)
        
        # Format the comprehensive final Markdown report
        verified_count = len(fact_check.verified_claims) if fact_check else 0
        disputed_count = len(fact_check.disputed_claims) if fact_check else 0
        contradictions_count = len(fact_check.contradictions) if fact_check else 0
        credibility_score = int(credibility.overall_cluster_credibility * 100) if credibility else 80

        markdown_body = f"""# NEWS INTELLIGENCE DOSSIER: {cluster.topic}
*Compiled on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*

---

## 1. Executive Summary & Significance
**Core Headline:** {summary.headline if summary else 'N/A'}

{summary.overall_summary if summary else 'N/A'}

### Key Developments:
"""
        if summary:
            for dev in summary.key_developments:
                markdown_body += f"- {dev}\n"
        else:
            markdown_body += "- No developments reported.\n"
            
        markdown_body += "\n## 2. Chronological Timeline\n"
        if summary and summary.timeline:
            for t_item in summary.timeline:
                markdown_body += f"- **{t_item.get('timestamp', 'Unknown')[:10]}:** {t_item.get('event')} *(Source: [{t_item.get('source_url', 'Link')}]({t_item.get('source_url', '#')}))*\n"
        else:
            markdown_body += "Timeline unavailable.\n"
            
        markdown_body += "\n## 3. Fact Verification\n"
        if fact_check:
            markdown_body += "### Verified Facts:\n"
            if fact_check.verified_claims:
                for claim in fact_check.verified_claims:
                    markdown_body += f"#### **{claim.claim}**\n- **Status:** Verified\n- **Corroborating Outlets:** {', '.join(claim.sources)}\n- **Details:** {claim.analysis}\n\n"
            else:
                markdown_body += "No claims could be fully verified.\n\n"
            
            if fact_check.disputed_claims:
                markdown_body += "\n### Disputed & Unverified Assertions:\n"
                for claim in fact_check.disputed_claims:
                    markdown_body += f"#### **{claim.claim}**\n- **Status:** Unverified / Disputed\n- **Outlets:** {', '.join(claim.sources)}\n- **Analysis:** {claim.analysis}\n\n"
            
            if fact_check.contradictions:
                markdown_body += "\n### Key Conflicting Accounts:\n"
                for contra in fact_check.contradictions:
                    markdown_body += f"> [!WARNING]\n"
                    markdown_body += f"> **Contradictory Claim Conflict:**\n"
                    markdown_body += f"> - **Outpost A ({contra.source_a}):** \"{contra.claim_a}\"\n"
                    markdown_body += f"> - **Outpost B ({contra.source_b}):** \"{contra.claim_b}\"\n"
                    markdown_body += f"> - **Resolution Analysis:** {contra.description}\n\n"
        else:
            markdown_body += "Fact check details unavailable.\n"
            
        markdown_body += "\n## 4. Media Bias & Slant Analysis\n"
        if bias:
            markdown_body += f"**Narrative Trends:** {bias.overall_bias_narrative}\n\n"
            markdown_body += "| Source Outlet | Political Leaning | Emotional Tone | Key Framing Analysis | Charged Words |\n"
            markdown_body += "|---|---|---|---|---|\n"
            for art in bias.individual_biases:
                url_display = art.article_url.split('/')[-1] or 'Link'
                if len(url_display) > 40:
                    url_display = url_display[:37] + "..."
                markdown_body += f"| [{url_display}]({art.article_url}) | {art.political_leaning} | {art.emotional_tone} | {art.framing_analysis} | {', '.join(art.emotionally_charged_words) if art.emotionally_charged_words else 'None'} |\n"
        else:
            markdown_body += "Bias analysis unavailable.\n"
            
        markdown_body += "\n## 5. Source Credibility Assessment\n"
        if credibility:
            markdown_body += f"**Platform Consensus Trust Score:** `{credibility.overall_cluster_credibility * 100:.0f}%`\n\n"
            markdown_body += "| Source | Domain | Reliability Score | Consistency | Justification |\n"
            markdown_body += "|---|---|---|---|---|\n"
            for src in credibility.sources_credibility:
                markdown_body += f"| {src.source_name} | {src.domain} | `{src.reliability_score * 100:.0f}%` | `{src.factual_consistency * 100:.0f}%` | {src.justification} |\n"
        else:
            markdown_body += "Credibility details unavailable.\n"
            
        markdown_body += "\n## 6. Final Consensus Verdict\n"
        if consensus:
            markdown_body += f"### Consolidated Objective Narrative\n{consensus.consensus_view}\n\n"
            
            if consensus.resolved_conflicts:
                markdown_body += "### Conflict Resolution & Findings:\n"
                for conflict in consensus.resolved_conflicts:
                    markdown_body += f"- **Conflict Point:** {conflict.get('conflict')}\n  - *Resolution:* {conflict.get('resolution_rationale')}\n"
                    
            if consensus.unresolved_debates:
                markdown_body += "\n### Unresolved Questions & Missing Evidence:\n"
                for debate in consensus.unresolved_debates:
                    markdown_body += f"- {debate}\n"
        else:
            markdown_body += "Consensus details unavailable.\n"
            
        # Build and validate the IntelligenceReport object
        report_id = str(abs(hash(cid + str(datetime.utcnow()))))
        final_report = IntelligenceReport(
            report_id=report_id,
            cluster_id=cid,
            title=f"Veritas AI Report: {cluster.topic}",
            created_at=datetime.utcnow(),
            summary=summary or SummaryReport(headline="N/A", overall_summary="N/A", key_developments=[], timeline=[]),
            fact_verification=fact_check or FactVerificationReport(),
            bias_analysis=bias or BiasReport(overall_bias_narrative="N/A", individual_biases=[]),
            credibility=credibility or CredibilityReport(overall_cluster_credibility=0.0, sources_credibility=[]),
            consensus=consensus or ConsensusReport(consensus_view="N/A", resolved_conflicts=[], unresolved_debates=[]),
            markdown_report=markdown_body
        )
        final_reports[cid] = final_report
        
    return {"final_reports": final_reports}

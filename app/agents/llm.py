import os
import time
import logging
from typing import Type, TypeVar, Any, Optional
from pydantic import BaseModel
from langchain_core.language_models.chat_models import BaseChatModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class MockStructuredLLM:
    """
    Mock LLM wrapper that mimics .with_structured_output()
    to provide realistic output for testing the multi-agent pipeline
    when no API keys are configured.
    """
    def __init__(self, schema: Type[T]):
        self.schema = schema

    def invoke(self, input_text: Any, *args: Any, **kwargs: Any) -> T:
        schema_name = self.schema.__name__
        logger.info(f"Mocking structured output for {schema_name}")
        
        # We generate custom mock outputs matching the "AetherCorp NeuralLink-V2" topic
        if schema_name == "SummaryReport":
            return self.schema(
                headline="AetherCorp Unveils NeuralLink-V2 Amid Whistleblower Concerns",
                overall_summary=(
                    "AetherCorp has announced NeuralLink-V2, a direct-to-brain synapse mapping device "
                    "claimed to have 99.9% accuracy. However, whistleblower leaks from offshore trials "
                    "suggest potential neurological risks and database alterations to hide adverse events."
                ),
                key_developments=[
                    "AetherCorp announced NeuralLink-V2 with direct-to-brain mapping.",
                    "Whistleblower leaked reports alleging off-shore clinical trials caused neurological hemorrhaging.",
                    "AETH stock price rose 14.5% post-announcement, crossing $420.50."
                ],
                timeline=[
                    {"timestamp": "2026-06-25T08:00:00Z", "event": "AetherCorp official announcement of NeuralLink-V2", "source_url": "https://techchronicle.mock/aethercorp-neurallink-v2"},
                    {"timestamp": "2026-06-25T08:15:00Z", "event": "Global Tech Watchdog publishes whistleblower leak", "source_url": "https://globalwatchdog.mock/aethercorp-clinical-trials-secret"},
                    {"timestamp": "2026-06-25T09:00:00Z", "event": "AETH stock surges 14.5% to record high", "source_url": "https://markettribune.mock/aethercorp-stock-surges"}
                ]
            )
        elif schema_name == "FactVerificationReport":
            return self.schema(
                verified_claims=[
                    {
                        "claim": "AetherCorp announced the NeuralLink-V2 brain interface.",
                        "sources": ["The Tech Chronicle", "Global Tech Watchdog", "Global Market Tribune"],
                        "verification_status": "verified",
                        "analysis": "All sources confirm the official launch and public announcement of NeuralLink-V2."
                    },
                    {
                        "claim": "AetherCorp stock price rose 14.5% to $420.50.",
                        "sources": ["Global Market Tribune"],
                        "verification_status": "verified",
                        "analysis": "Confirmed by market metrics reported post-announcement."
                    }
                ],
                disputed_claims=[
                    {
                        "claim": "NeuralLink-V2 is 99.9% safe and causes zero tissue damage.",
                        "sources": ["The Tech Chronicle"],
                        "verification_status": "disputed",
                        "analysis": "AetherCorp claims 99.9% safety, but whistleblower documents contest this, citing clinical trial neurological injuries."
                    }
                ],
                contradictions=[
                    {
                        "claim_a": "NeuralLink-V2 has passed clinical trials with zero tissue damage.",
                        "source_a": "The Tech Chronicle (citing Elena Rostova)",
                        "claim_b": "Trial subjects experienced cognitive dissonance and minor neurological hemorrhaging, and safety logs were modified.",
                        "source_b": "Global Tech Watchdog (citing whistleblower files)",
                        "description": "The publisher reports the company's official claim of perfect safety, while the watchdog alleges physical injury and trial database tampering."
                    }
                ]
            )
        elif schema_name == "BiasReport":
            return self.schema(
                overall_bias_narrative="Coverage is polarized: Tech/Financial sources highlight stock growth and medical prospects, whereas watchdog sources focus on ethical violations and health risks.",
                individual_biases=[
                    {
                        "article_url": "https://techchronicle.mock/aethercorp-neurallink-v2",
                        "political_leaning": "Center-Right",
                        "emotional_tone": "Optimistic",
                        "emotionally_charged_words": ["groundbreaking", "transparency concerns"],
                        "framing_analysis": "Frames the device primarily as an innovative medical breakthrough with minor mentions of ethical warnings."
                    },
                    {
                        "article_url": "https://globalwatchdog.mock/aethercorp-clinical-trials-secret",
                        "political_leaning": "Left",
                        "emotional_tone": "Sensational/Alarmist",
                        "emotionally_charged_words": ["scathing", "whistleblower", "tampering", "risks"],
                        "framing_analysis": "Frames the story as a corporate cover-up of severe physical injuries, stressing regulatory violations."
                    }
                ]
            )
        elif schema_name == "CredibilityReport":
            return self.schema(
                overall_cluster_credibility=0.72,
                sources_credibility=[
                    {
                        "source_name": "The Tech Chronicle",
                        "domain": "techchronicle.mock",
                        "reliability_score": 0.80,
                        "factual_consistency": 0.85,
                        "justification": "Reports official company announcements accurately, but does not perform independent investigative checking on safety claims."
                    },
                    {
                        "source_name": "Global Tech Watchdog",
                        "domain": "globalwatchdog.mock",
                        "reliability_score": 0.65,
                        "factual_consistency": 0.70,
                        "justification": "Provides critical leaks, but relies heavily on single unverified whistleblower sources that lack peer review."
                    }
                ]
            )
        elif schema_name == "ConsensusReport":
            return self.schema(
                consensus_view=(
                    "AetherCorp has officially announced its NeuralLink-V2 brain mapping interface. "
                    "While the company asserts the device is safe and ready for launch, credible allegations "
                    "by a whistleblower suggest clinical trials in offshore clinics experienced safety issues "
                    "including minor neurological hemorrhaging. The market responded very positively, driving "
                    "the stock to a record high."
                ),
                resolved_conflicts=[
                    {
                        "conflict": "Official safety assertions vs. whistleblower clinical trial injury claims",
                        "resolution_rationale": "We report both perspectives, identifying AetherCorp's claims as official messaging and the whistleblower's reports as unverified allegations that warrant safety regulatory review."
                    }
                ],
                unresolved_debates=[
                    "Whether AetherCorp actually tampered with the clinical trial databases.",
                    "The exact severity and frequency of the neurological injuries during trials."
                ]
            )
        
        # Generic fallback
        return self.schema.model_validate({"headline": "Mock Headline"})

import sqlite3
import hashlib
import json

class LLMResponseCache:
    """
    Lightweight persistent cache using SQLite to cache structured JSON outputs of the agents.
    """
    def __init__(self, db_path: str = ".llm_cache.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS cache ("
                    "  key TEXT PRIMARY KEY,"
                    "  value TEXT"
                    ")"
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize SQLite cache: {e}")

    def get(self, key_str: str) -> Optional[str]:
        try:
            key_hash = hashlib.sha256(key_str.encode("utf-8")).hexdigest()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM cache WHERE key = ?", (key_hash,))
                row = cursor.fetchone()
                if row:
                    return row[0]
        except Exception as e:
            logger.error(f"Failed to read from cache: {e}")
        return None

    def set(self, key_str: str, value_str: str):
        try:
            key_hash = hashlib.sha256(key_str.encode("utf-8")).hexdigest()
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO cache (key, value) VALUES (?, ?)",
                    (key_hash, value_str)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to write to cache: {e}")

llm_cache = LLMResponseCache()

class StructuredOutputModel:
    def __init__(self, llm: BaseChatModel, schema: Type[T]):
        self.llm = llm
        self.schema = schema

    def invoke(self, input_text: Any, *args: Any, **kwargs: Any) -> T:
        llm_class_name = self.llm.__class__.__name__
        schema_name = self.schema.__name__
        
        # Build cache key from model type, schema, and raw input prompt
        cache_key = f"{llm_class_name}:{schema_name}:{str(input_text)}"
        cached_val = llm_cache.get(cache_key)
        if cached_val:
            logger.info(f"SQLite Cache HIT for structured LLM: {schema_name}")
            try:
                return self.schema.model_validate_json(cached_val)
            except Exception as e:
                logger.warning(f"Failed to parse cached JSON for {schema_name}: {e}. Falling back to API.")

        # Check if actual LLM supports with_structured_output
        if hasattr(self.llm, "with_structured_output"):
            try:
                structured_chain = self.llm.with_structured_output(self.schema)
            except Exception as e:
                logger.error(f"Failed to build structured chain: {e}")
                res = MockStructuredLLM(self.schema).invoke(input_text, *args, **kwargs)
                try:
                    llm_cache.set(cache_key, res.model_dump_json())
                except Exception:
                    pass
                return res
                
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    # Apply pacing sleep specifically for Groq to respect low TPM/RPM limits
                    if "ChatGroq" in self.llm.__class__.__name__:
                        pacing_delay = int(os.getenv("GROQ_PACING_DELAY", "6"))
                        sleep_time = pacing_delay if attempt == 0 else (2 ** attempt + pacing_delay)
                        logger.info(f"Pacing Groq API request (attempt {attempt + 1}/{max_retries}): sleeping {sleep_time}s...")
                        time.sleep(sleep_time)
                    elif attempt > 0:
                        sleep_time = 2 ** attempt
                        logger.info(f"Sleeping for {sleep_time} seconds before retrying...")
                        time.sleep(sleep_time)
                        
                    res = structured_chain.invoke(input_text, *args, **kwargs)
                    try:
                        llm_cache.set(cache_key, res.model_dump_json())
                    except Exception as e:
                        logger.warning(f"Failed to cache result: {e}")
                    return res
                except Exception as e:
                    err_str = str(e)
                    # Retry on rate limits (429) or transient validation/API errors (400)
                    if "429" in err_str or "rate limit" in err_str.lower() or "400" in err_str or "validation" in err_str.lower():
                        logger.warning(
                            f"Temporary error or rate limit hit on attempt {attempt + 1}/{max_retries}. "
                            f"Error: {err_str}"
                        )
                        continue
                    else:
                        logger.error(f"Structured output invoke failed: {e}. Falling back to parser.")
                        break
        
        # Fail-safe mock for local execution if API keys fail or aren't present
        res = MockStructuredLLM(self.schema).invoke(input_text, *args, **kwargs)
        try:
            llm_cache.set(cache_key, res.model_dump_json())
        except Exception:
            pass
        return res

def get_llm() -> Optional[BaseChatModel]:
    provider = os.getenv("LLM_PROVIDER", "").lower()
    
    # If LLM_PROVIDER is set to mock, return None to trigger MockStructuredLLM directly
    if provider == "mock":
        logger.info("Using Mock Intelligence as configured in LLM_PROVIDER.")
        return None
        
    if provider == "gemini" or (not provider and os.getenv("GEMINI_API_KEY")):
        from langchain_google_genai import ChatGoogleGenerativeAI
        logger.info("Initializing ChatGoogleGenerativeAI (gemini-2.5-flash)...")
        return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    elif provider == "groq" or (not provider and os.getenv("GROQ_API_KEY")):
        from langchain_groq import ChatGroq
        model_name = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        max_tokens = int(os.getenv("GROQ_MAX_TOKENS", "4096"))
        logger.info(f"Initializing ChatGroq ({model_name}) with max_tokens={max_tokens}...")
        return ChatGroq(model=model_name, temperature=0, max_tokens=max_tokens)
    elif provider == "openai" or (not provider and os.getenv("OPENAI_API_KEY")):
        from langchain_openai import ChatOpenAI
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        logger.info(f"Initializing ChatOpenAI ({model_name})...")
        return ChatOpenAI(model=model_name, temperature=0)
    
    logger.warning("No API keys found and no valid LLM_PROVIDER configured. Operations will execute using mock intelligence.")
    return None

def get_structured_llm(schema: Type[T]) -> Any:
    llm = get_llm()
    if llm is None:
        return MockStructuredLLM(schema)
    return StructuredOutputModel(llm, schema)

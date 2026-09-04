import os
import json
import logging
from app.agents.graph import app_graph

# Configure logging to stdout
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("test_workflow")

def run_workflow_test():
    print("==================================================")
    print("      RUNNING LANGGRAPH NEWS PIPELINE TEST        ")
    print("==================================================")
    
    # 1. Prepare initial state
    # We query for AetherCorp to trigger our mock system if no NewsAPI key is set
    query = "Bengaluru Daycare Horror"
    print(f"Initiating workflow with search query: '{query}'...")
    
    initial_state = {
        "query": query,
        "articles": [],
        "clusters": [],
        "summaries": {},
        "fact_verifications": {},
        "bias_analyses": {},
        "credibilities": {},
        "consensuses": {},
        "final_reports": {},
        "errors": []
    }
    
    # 2. Invoke the compiled LangGraph workflow
    print("\nExecuting graph nodes...")
    result = app_graph.invoke(initial_state)
    
    # 3. Check for errors and results
    errors = result.get("errors", [])
    if errors:
        print("\nPipeline execution encountered errors:")
        for err in errors:
            print(f"  - {err}")
            
    final_reports = result.get("final_reports", {})
    if not final_reports:
        print("\nFAIL: No intelligence reports compiled.")
        return
        
    print(f"\nSUCCESS: Pipeline compiled {len(final_reports)} intelligence reports!")
    
    # 4. Display and save the reports
    for cid, report in final_reports.items():
        print(f"\nReport ID:  {report.report_id}")
        print(f"Cluster ID: {report.cluster_id}")
        print(f"Title:      {report.title}")
        print(f"Headline:   {report.summary.headline}")
        print(f"Credibility Score: {report.credibility.overall_cluster_credibility:.2f} / 1.0")
        
        # Save markdown report to disk
        output_filename = "sample_report.md"
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(report.markdown_report)
            
        print(f"\nDetailed markdown intelligence report written to: {output_filename}")
        print("\nSnippet of Markdown Report:")
        # Print first 10 lines
        lines = report.markdown_report.split("\n")
        for line in lines[:15]:
            print(line)
        print("...")

    print("\n==================================================")
    print("Workflow execution test finished successfully!")
    print("==================================================")

if __name__ == "__main__":
    run_workflow_test()

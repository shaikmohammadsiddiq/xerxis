import json
from mcp.server.fastmcp import FastMCP
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from axe_selenium_python import Axe

# Initialize the MCP Server
mcp = FastMCP("A11y-Selenium-Server")

def run_axe_audit(url: str, tags: list = None) -> dict:
    """Helper function to run the headless browser and execute axe-core."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get(url)
        axe = Axe(driver)
        axe.inject()
        
        # If specific WCAG tags are requested, pass them to axe-core
        run_options = {}
        if tags:
            run_options["runOnly"] = {"type": "tag", "values": tags}
            return axe.run(options=run_options)
        
        return axe.run()
    finally:
        driver.quit()

@mcp.tool()
def get_summary(url: str) -> str:
    """
    Get a high-level summary of accessibility issues for a webpage.
    Use this first to check a page without consuming too many tokens.
    """
    results = run_axe_audit(url)
    violations = results.get("violations", [])
    
    # Count impacts
    impacts = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
    for v in violations:
        impact = v.get("impact")
        if impact in impacts:
            impacts[impact] += 1
            
    summary = {
        "url": url,
        "total_issues": len(violations),
        "issues_by_severity": impacts,
        "top_issues": [
            {
                "id": v.get("id"),
                "impact": v.get("impact"),
                "description": v.get("description")
            } for v in violations[:5]  # Just grab the first 5 to save space
        ],
        "passed_tests": len(results.get("passes", []))
    }
    
    return json.dumps(summary, indent=2)

@mcp.tool()
def audit_webpage(url: str, tags: list[str] = None, include_html: bool = False) -> str:
    """
    Perform a detailed accessibility audit on a webpage.
    
    Args:
        url: URL of the webpage to audit.
        tags: Optional specific accessibility tags to check (e.g., ['wcag2a', 'wcag2aa']).
        include_html: Whether to include exact HTML snippets in the results (default: False).
    """
    results = run_axe_audit(url, tags)
    
    formatted_violations = []
    
    for violation in results.get("violations", []):
        formatted_nodes = []
        
        for node in violation.get("nodes", []):
            node_data = {
                "target": node.get("target"),
                "failureSummary": node.get("failureSummary")
            }
            # Only include the raw HTML if the AI specifically asked for it
            if include_html:
                node_data["html"] = node.get("html")
                
            formatted_nodes.append(node_data)
            
        formatted_violations.append({
            "id": violation.get("id"),
            "impact": violation.get("impact"),
            "description": violation.get("description"),
            "helpUrl": violation.get("helpUrl"),
            "nodes": formatted_nodes
        })
        
    final_output = {
        "url": url,
        "total_violations": len(formatted_violations),
        "violations": formatted_violations
    }
    
    return json.dumps(final_output, indent=2)

if __name__ == "__main__":
    # Start the MCP server using standard input/output
    mcp.run()
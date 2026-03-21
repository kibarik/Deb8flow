#!/usr/bin/env python3
"""
FastMCP server for SDD (Software Design Specification) analysis.

This server provides the analyze_specification tool via Model Context Protocol.
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from fastmcp import FastMCP
except ImportError:
    print("Error: fastmcp is not installed.", file=sys.stderr)
    print("Install it with: pip install fastmcp", file=sys.stderr)
    sys.exit(1)

from src.mcp.tools.analyze_specification import analyze_specification

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastMCP server
mcp = FastMCP("SDD Analyzer")

# Register the analyze_specification tool
@mcp.tool()
async def analyze_specification_tool(
    spec_path: str = None,
    spec_content: str = None,
    spec_type: str = "SDD",
    focus_areas: list = None,
    detail_level: str = "thorough",
    config_path: str = None
) -> dict:
    """
    Analyze a software design specification using multi-agent debate.

    Runs a debate between Architect (PRO) and DevLead/QA/Security (CON)
    to identify weak points, recommendations, and unclear sections.

    Args:
        spec_path: Path to specification file (.md or .txt)
        spec_content: Raw specification content (alternative to spec_path)
        spec_type: Type of specification (PRD, SDD, TDD, UNKNOWN)
        focus_areas: Optional list of focus areas for analysis
        detail_level: Analysis detail level ('quick' or 'thorough')
        config_path: Optional path to sdd_config.yaml

    Returns:
        Dictionary with analysis results including:
        - status: success, partial, or error
        - weak_points: List of identified weak points
        - recommendations: List of improvement recommendations
        - unclear_sections: List of unclear sections
        - metadata: Analysis metadata (model, agents, time, etc.)
        - error: Error details if status is error

    Example:
        >>> result = await analyze_specification_tool(
        ...     spec_path="docs/spec.md",
        ...     detail_level="thorough"
        ... )
        >>> print(result['status'])
        success
    """
    try:
        logger.info(f"Starting SDD analysis: spec_type={spec_type}, detail_level={detail_level}")

        result = await analyze_specification(
            spec_path=spec_path,
            spec_content=spec_content,
            spec_type=spec_type,
            focus_areas=focus_areas,
            detail_level=detail_level,
            config_path=config_path
        )

        logger.info(f"SDD analysis completed: status={result['status']}")
        return result

    except Exception as e:
        logger.exception(f"Error in analyze_specification_tool: {e}")
        return {
            "status": "error",
            "weak_points": [],
            "recommendations": [],
            "unclear_sections": [],
            "metadata": {
                "model_used": "unknown",
                "agents_used": [],
                "analysis_time_ms": 0,
                "debate_mode": "unknown",
                "num_rounds": 0,
                "winner": None
            },
            "error": {
                "type": "unknown",
                "message": str(e),
                "recoverable": False,
                "suggestion": "Check server logs for details"
            }
        }


def main():
    """Main entry point for the MCP server."""
    logger.info("Starting SDD Analyzer MCP server...")

    # Run the MCP server
    mcp.run()


if __name__ == "__main__":
    main()

"""
E2E Test for analyze_specification MCP tool with real debate engine.

This test verifies that:
1. MCP server can run the tool
2. Real AI debates occur (analysis_time_ms > 60000)
3. Results contain weak_points, recommendations, and metadata
4. Multiple agents participate in the debate
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mcp.tools.analyze_specification import analyze_specification


async def main():
    """Run E2E test with real debate engine."""

    # Read test fixture
    spec_path = "tests/fixtures/valid_sdd.md"

    if not Path(spec_path).exists():
        print(f"❌ FAIL: Test fixture not found: {spec_path}")
        return False

    spec_content = Path(spec_path).read_text()

    print(f"🔍 Running E2E test with: {spec_path}")
    print(f"📝 Content length: {len(spec_content)} chars")

    # Check API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    print(f"🔑 OPENAI_API_KEY: {'SET' if openai_key else 'NOT SET'}")
    print(f"🔑 ANTHROPIC_API_KEY: {'SET' if anthropic_key else 'NOT SET'}")
    print()

    if not openai_key and not anthropic_key:
        print("❌ BLOCKER: No API keys found in environment")
        print("   Please set OPENAI_API_KEY or ANTHROPIC_API_KEY")
        print("   Example: export OPENAI_API_KEY='sk-...'")
        return False

    print("⚙️  Starting real debate analysis...")
    print("   This will take 1-5 minutes (real AI debates)")
    print("   Cost: ~$0.01-0.05 per run (gpt-4o-mini)")
    print()

    # Run analysis
    try:
        result = await analyze_specification(
            spec_content=spec_content,
            spec_type="SDD",
            detail_level="thorough"
        )
    except Exception as e:
        print(f"❌ FAIL: Exception during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Verify results
    print("📊 E2E Test Results:")
    print(f"  Status: {result['status']}")
    print(f"  Analysis Time: {result['metadata']['analysis_time_ms']}ms ({result['metadata']['analysis_time_ms']/1000:.1f}s)")
    print(f"  Model: {result['metadata']['model_used']}")
    print(f"  Agents: {result['metadata']['agents_used']}")
    print(f"  Winner: {result['metadata'].get('winner', 'N/A')}")
    print(f"  Debate Mode: {result['metadata']['debate_mode']}")
    print(f"  Rounds: {result['metadata']['num_rounds']}")
    print(f"  Weak Points: {len(result['weak_points'])} items")
    print(f"  Recommendations: {len(result['recommendations'])} items")
    print(f"  Unclear Sections: {len(result['unclear_sections'])} items")
    print()

    # Check acceptance criteria
    checks = {
        "AC1 (status SUCCESS/PARTIAL)": result['status'] in ['success', 'partial'],
        "AC2 (analysis_time_ms > 60000)": result['metadata']['analysis_time_ms'] > 60000,
        "AC3 (weak_points >= 1)": len(result['weak_points']) >= 1,
        "AC4 (agents_used >= 2)": len(result['metadata']['agents_used']) >= 2,
        "AC5 (model_used set)": bool(result['metadata']['model_used']),
    }

    all_passed = True
    for check, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {check}")
        if not passed:
            all_passed = False
    print()

    # Show sample weak points if available
    if result['weak_points']:
        print("📌 Sample Weak Points:")
        for wp in result['weak_points'][:3]:
            print(f"  - [{wp.get('id', 'N/A')}] {wp.get('title', 'No title')}")
        if len(result['weak_points']) > 3:
            print(f"  ... and {len(result['weak_points']) - 3} more")
        print()

    # Show sample recommendations if available
    if result['recommendations']:
        print("💡 Sample Recommendations:")
        for rec in result['recommendations'][:2]:
            print(f"  - {rec.get('text', 'No text')[:80]}...")
        print()

    # Check for errors
    if result.get('error'):
        print(f"⚠️  Error returned:")
        print(f"  Type: {result['error']['type']}")
        print(f"  Message: {result['error']['message']}")
        print(f"  Recoverable: {result['error']['recoverable']}")
        print(f"  Suggestion: {result['error']['suggestion']}")
        print()

    # Final verdict
    if all_passed:
        print("🎉 E2E TEST PASSED!")
        print()
        print("✅ All acceptance criteria met")
        print("✅ Real debate engine confirmed (analysis_time_ms > 60s)")
        print("✅ Multiple agents participated")
        print("✅ Weak points and recommendations extracted")
    else:
        print("⚠️  E2E TEST FAILED - Some criteria not met")
        print()
        print("Possible reasons:")
        if not checks["AC1"]:
            print("  - Status is not success/partial (check error field)")
        if not checks["AC2"]:
            print("  - Analysis was too fast (debate may not have run)")
            print("    - Check if API key is valid")
            print("    - Check network connection")
            print("    - Check if model is available")
        if not checks["AC3"]:
            print("  - No weak points extracted (parser may have failed)")
        if not checks["AC4"]:
            print("  - Not enough agents (config may be wrong)")
        if not checks["AC5"]:
            print("  - Model name not set (config issue)")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

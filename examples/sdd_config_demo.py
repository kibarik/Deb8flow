#!/usr/bin/env python3
"""
Demo script showing how to use the SDD config loader.

Usage:
    python3 examples/sdd_config_demo.py
"""

from src.shared.config.sdd_config_loader import load_sdd_config


def main():
    print("=" * 60)
    print("SDD Config Loader Demo")
    print("=" * 60)
    print()

    # Load the default config
    print("Loading config from config/sdd_config.yaml...")
    config = load_sdd_config()
    print()

    # Display LLM configuration
    print("LLM Configuration:")
    print(f"  Model: {config.llm.model}")
    print(f"  Base URL: {config.llm.base_url or '(OpenAI default)'}")
    print(f"  Temperature: {config.llm.temperature}")
    print(f"  Max Tokens: {config.llm.max_tokens}")
    print(f"  Timeout: {config.llm.timeout}s")
    print(f"  Fallback Models: {', '.join(config.llm.fallback_models) or '(none)'}")
    print()

    # Display debate configuration
    print("Debate Configuration:")
    print(f"  Mode: {config.debate.mode}")
    print(f"  Language: {config.debate.language}")
    print(f"  Max Retries: {config.debate.max_retries}")
    print(f"  Max Concurrency: {config.debate.max_concurrency}")
    print()

    # Display agents
    print("Agents Configuration:")
    print(f"  Main (PRO): {config.agents.main.name}")
    print(f"    Prompt: {config.agents.main.prompt}")
    print(f"  Opponents (CON):")
    for opponent in config.agents.opponents:
        print(f"    - {opponent.name}: {opponent.prompt}")
    print()

    # Display output configuration
    print("Output Configuration:")
    print(f"  Directory: {config.output.directory}")
    print(f"  Save Dialogues: {config.output.save_dialogues}")
    print(f"  Save Metadata: {config.output.save_metadata}")
    print()

    # Display logging configuration
    print("Logging Configuration:")
    print(f"  Level: {config.logging.level}")
    print(f"  Verbose: {config.logging.verbose}")
    print(f"  Quiet: {config.logging.quiet}")
    print()

    # Show how to get CLI args
    print("CLI Arguments Dictionary:")
    cli_args = config.get_cli_args_dict()
    for key, value in cli_args.items():
        print(f"  {key}: {value}")
    print()

    # Show environment variable substitution
    print("Environment Variable Substitution:")
    print("  Set DEBATE_MODEL=custom-model and reload to test")
    print("  Example: ${DEBATE_MODEL:gpt-4o-mini} -> actual value")
    print()

    print("=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()

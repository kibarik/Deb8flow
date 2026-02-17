"""
This module defines the BaseComponent class, which provides a foundation
for managing LLM-based workflows with optional token tracking integrated into the state.
"""
import logging
import time
from typing import Optional, List, Type, Any
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.base import RunnableSequence
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_community.chat_models import ChatZhipuAI
from langchain_community.callbacks.manager import get_openai_callback
from pydantic import BaseModel
from opentelemetry import trace
from opentelemetry.trace import get_tracer_provider
from debate_state import DebateState
from configurations.llm_config import LLMConfig, OpenAILLMConfig, AzureOpenAILLMConfig, ZaiLLMConfig, RequestyLLMConfig
from rich.console import Console
from rich.logging import RichHandler


class BaseComponent:
    """
    A foundational class for managing LLM-based workflows with token tracking.
    Can handle Azure OpenAI (AzureChatOpenAI), OpenAI (ChatOpenAI), and Zhipu AI (ChatZhipuAI).
    """

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        temperature: float = 0.0,
        max_retries: int = 5,
    ):
        """
        Initializes the BaseComponent with optional LLM configuration and temperature.

        Args:
            llm_config (Optional[LLMConfig]): Configuration for either Azure or OpenAI.
            temperature (float): Controls the randomness of LLM outputs. Defaults to 0.0.
            max_retries (int): How many times to retry on 429 errors.
        """
        logger = logging.getLogger(self.__class__.__name__)
        tracer = trace.get_tracer(__name__, tracer_provider=get_tracer_provider())

        self.logger = logger
        self._configure_rich_logger() 
        self.tracer = tracer
        self.llm: Optional[ChatOpenAI] = None
        self.output_parser: Optional[StrOutputParser] = None
        self.state: Optional[DebateState] = None
        self.prompt_template: Optional[ChatPromptTemplate] = None
        self.chain: Optional[RunnableSequence] = None
        self.documents: Optional[List] = None
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.max_retries = max_retries

        if llm_config is not None:
            self.llm = self._init_llm(llm_config, temperature)
            self.output_parser = StrOutputParser()

    def _configure_rich_logger(self):
        """Set up Rich logging with styles"""
        console = Console(width=100, color_system="auto")
        handler = RichHandler(
            console=console,
            show_time=True,
            show_level=True,
            markup=True,
            show_path=False
        )
        self.logger.addHandler(handler)
        self.logger.propagate = False

    def log_debate_event(self, message: str, prefix: str = "", style: str = ""):
        """Centralized rich-formatted logging"""
        prefix_map = {
            "PRO": "[cyan]PRO[/]",
            "CON": "[magenta]CON[/]",
            "FACT": "[red]FACT-CHECK[/]",
            "JUDGE": "[yellow]JUDGE[/]"
        }
        styled_msg = f"{prefix_map.get(prefix, prefix)}{' ' + message if message else ''}"
        self.logger.info(styled_msg, extra={"markup": True})

    def _init_llm(self, config: LLMConfig, temperature: float):
        """
        Initializes an LLM instance for either Azure OpenAI or standard OpenAI.
        """
        if isinstance(config, AzureOpenAILLMConfig):
            # If it's Azure, use the AzureChatOpenAI class
            return AzureChatOpenAI(
                deployment_name=config.deployment_name,
                azure_endpoint=config.azure_endpoint,
                openai_api_version=config.openai_api_version,
                openai_api_key=config.openai_api_key,
                temperature=temperature,
            )
        elif isinstance(config, OpenAILLMConfig):
            # If it's standard OpenAI, use the ChatOpenAI class
            return ChatOpenAI(
                model_name=config.model_name,
                openai_api_key=config.openai_api_key,
                temperature=temperature,
            )
        elif isinstance(config, ZaiLLMConfig):
            # If it's Zhipu AI, use the ChatZhipuAI class
            # Note: ChatZhipuAI reads ZHIPUAI_API_KEY from environment
            return ChatZhipuAI(
                model=config.model_name,
                temperature=temperature,
            )
        elif isinstance(config, RequestyLLMConfig):
            # If it's Requesty, use ChatOpenAI with custom base_url
            return ChatOpenAI(
                model=config.model_name,
                openai_api_key=config.req_api_key,
                base_url=config.base_url,
                temperature=temperature,
            )
        else:
            raise ValueError("Unsupported LLMConfig type.")

    def validate_initialization(self) -> None:
        """
        Ensures we have an LLM and an output parser.
        """
        if not self.llm:
            raise ValueError("LLM is not initialized. Ensure `llm_config` is provided.")
        if not self.output_parser:
            raise ValueError("Output parser is not initialized.")

    def execute_chain(self, inputs: Any) -> Any:
        """
        Executes the LLM chain, tracks token usage, and retries on rate limit errors.
        """
        if not self.chain:
            raise ValueError("No chain is initialized for execution.")

        retry_wait = 2  # Initial wait time in seconds

        for attempt in range(self.max_retries):
            try:
                with get_openai_callback() as cb:
                    result = self.chain.invoke(inputs)
                    self.logger.info("Prompt Token usage: %s", cb.prompt_tokens)
                    self.logger.info("Completion Token usage: %s", cb.completion_tokens)
                    self.prompt_tokens = cb.prompt_tokens
                    self.completion_tokens = cb.completion_tokens

                return result

            except Exception as e:
                # Log the full error for debugging
                error_str = str(e).lower()
                self.logger.error(f"API Error (attempt {attempt + 1}/{self.max_retries}): {e}")

                # Check for rate limit errors (429, rate limit, unauthorized, etc.)
                if "429" in error_str or "rate limit" in error_str or "401" in error_str:
                    self.logger.warning(
                        f"Rate limit/Auth error. Retrying in {retry_wait} seconds... "
                        f"(Attempt {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(retry_wait)
                    retry_wait *= 2
                else:
                    self.logger.error(f"Non-retryable error: {str(e)}")
                    raise e

        raise Exception("API request failed after maximum number of retries")

    def create_chain(
        self, system_template: str, human_template: str, language_setting: Optional[str] = None
    ) -> RunnableSequence:
        """
        Creates a chain for unstructured outputs.

        Args:
            system_template: The system prompt template.
            human_template: The human prompt template.
            language_setting: Optional language/style instruction for all agents.

        Returns:
            A RunnableSequence for executing the chain.
        """
        self.validate_initialization()

        # Inject language setting into system template if provided
        if language_setting:
            injection = f"\n\n**Language and Style Setting**: {language_setting}\n\n"
            system_template = injection + system_template

        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", system_template),
                ("human", human_template),
            ]
        )
        self.chain = self.prompt_template | self.llm | self.output_parser
        return self.chain

    def create_structured_output_chain(
        self, system_template: str, human_template: str, output_model: Type[BaseModel]
    ) -> RunnableSequence:
        """
        Creates a chain that yields structured outputs (parsed into a Pydantic model).
        """
        self.validate_initialization()
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", system_template),
                ("human", human_template),
            ]
        )
        self.chain = self.prompt_template | self.llm.with_structured_output(output_model)
        return self.chain

    def build_return_with_tokens(self, node_specific_data: dict) -> dict:
        """
        Convenience method to add token usage info into the return values.
        """
        return {
            **node_specific_data,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
        }

    def __call__(self, state: DebateState) -> None:
        """
        Updates the node's local copy of the state.
        """
        self.state = state
        for key, value in state.items():
            setattr(self, key, value)

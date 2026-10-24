import logging
import re
from typing import Dict, Any, List, Optional, Tuple

from app.core.config import settings
from app.models.intent import (
    IntentType,
    WorkflowType,
    CANONICAL_INTENT_WORKFLOW_MAP,
    ExecutionPlan,
    TaskPlanItem,
    RoutingSource,
)
from app.services.model_adapter import model_adapter

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Deterministic Routing Rules & Pattern Definitions
# ──────────────────────────────────────────────────────────────────────────────

# 1. Chat Patterns: Questions, explanations, conceptual definitions
EXPLANATION_PREFIX_PATTERNS = [
    r"^(explain|describe|clarify|elaborate|summarize|define|tell me about|can you explain|could you explain|please explain)\b",
    r"^(what is|what are|what was|what were|what does|how does|how do|how did|why is|why are|why does|why do|who is|who were|when did|where is|which is|is it|are there)\b",
    r"^(give me an overview of|walk me through|help me understand|teach me about)\b",
]

# 2. Research Patterns: Academic papers, literature reviews, white papers
RESEARCH_PATTERNS = [
    r"\b(write|draft|author|compose|prepare|produce)\b.*\b(research paper|academic paper|literature review|white paper|case study|academic report|scientific paper|peer-reviewed (research )?report|research study)\b",
    r"\b(review (the )?literature (on|regarding|about)|review recent papers (about|on|regarding)|conduct a literature review)\b",
    r"\b(research paper|literature review|academic essay|white paper)\b.*\b(about|on|regarding|exploring|evaluating)\b",
    r"\b(comprehensive|academic|scholarly|in-depth)\s+(research|study|report|paper)\s+(on|about|regarding)\b",
    r"\b(draft|prepare|write)\s+a\s+(comprehensive\s+)?(research study|research report)\b",
]

# 3. Software Project Patterns: Full-stack applications, complete websites, multi-file software
SOFTWARE_PROJECT_PATTERNS = [
    r"\b(build|create|develop|make|scaffold|code)\b.*\b(portfolio website|landing page|web application|web app|inventory management|ecommerce|react app|vue app|next\.?js app|marketing website|blog website|personal blog|dashboard|portal|website)\b",
    r"\b(portfolio website|landing page|inventory management (system|application|app)|ecommerce (website|app|application)|marketing website|blog website)\b",
    r"\b(full-stack|fullstack)\b.*\b(application|app|project|system|dashboard|portal)\b",
    r"\b(react|vue|next\.?js)\b.*\b(portfolio|website|web app|application|dashboard|portal)\b",
    r"\b(complete|responsive|production-ready)\s+.*\b(website|portfolio|web app|web application)\b",
    r"\b(web-based|web app)\s+.*\b(project|application)\b",
]

# 4. Code Patterns: Snippets, functions, algorithms, bug fixes, scripts
CODE_PATTERNS = [
    r"\b(write|create|implement|generate|give me|code)\b.*\b(function|script|snippet|regex|algorithm|method|class|sql query|bash script|utility|data structure|decorator)\b",
    r"^(write|implement|create|give me)\s+(a |an )?(python|javascript|typescript|c\+\+|java|go|rust|sql|bash)?\s*(function|script|class|method|regex|algorithm|snippet|data structure|decorator)\b",
    r"\b(debug|fix|troubleshoot|resolve)\b.*\b(exception|error|stack trace|bug|traceback|issue in (this|the) code|\w+error)\b",
    r"^(debug this|fix this|resolve this)\s+(python\s+)?(exception|error|bug|issue|\w+error)\b",
    r"\b(write a python function to|write a script to|debug this python exception)\b",
]

# 5. Data Analysis Patterns: Dataset evaluation, trends, CSV analysis, statistical modeling
DATA_ANALYSIS_PATTERNS = [
    r"\b(analyze|trend analysis|exploratory data analysis|eda|statistical analysis|correlat(e|ion)|regress(ion)?|summary statistics|percentiles|metrics)\b.*\b(dataset|csv|dataframe|data file|spreadsheet|uploaded data|sales data|metrics data|trend|figures|cohort data|user retention)\b",
    r"\b(analyze this (uploaded )?(csv|dataset|data|file|spreadsheet))\b",
    r"\b(analyze the (dataset|csv|data trends|sales trends|uploaded.*data))\b",
    r"\b(data analysis on|statistical summary of|evaluate trends in this csv|calculate summary statistics)\b",
    r"\b(perform|conduct|calculate)\s+(exploratory data analysis|statistical analysis|regression analysis|summary statistics)\b",
]

# Explicit Deliverable Format Recognizers
FORMAT_PATTERNS = {
    "docx": [r"\b(docx|word doc(ument)?|\.docx)\b"],
    "pdf": [r"\b(pdf|pdf document|pdf format|\.pdf)\b"],
    "zip": [r"\b(zip|zip file|archive|zip package|\.zip)\b"],
    "csv": [r"\b(csv|csv file|\.csv)\b"],
    "json": [r"\b(json|json format|\.json)\b"],
}

# Negative guards: questions about building or writing code should route to chat, not software/code
QUESTION_ABOUT_TOPIC_PATTERNS = [
    r"^(how to|how do i|how can i|how would one|what is the best way to|explain how to)\b",
    r"^(what is|what are|why is|can you explain what)\b",
]


class HybridRouter:
    """
    Hybrid AI Intent Router and Workflow Planner.
    Stage 1: Deterministic rule-based first pass with text normalization and confidence scoring.
    Stage 2: Constrained LLM-assisted planner with JSON Schema validation and bounded retries.
    Stage 3: Canonical workflow enforcement and DAG plan generation.
    """

    def __init__(self):
        self.planner_model = settings.PLANNER_MODEL
        self.timeout_seconds = settings.PLANNER_TIMEOUT_SECONDS
        self.max_retries = settings.PLANNER_MAX_RETRIES

    @staticmethod
    def normalize_text(text: str) -> str:
        """Strip markdown syntax, list numbers, quotes, extra whitespaces, and normalize case for routing."""
        t = text.strip()
        # Remove markdown code fences or backticks
        t = re.sub(r"```[\w]*\n?", "", t)
        t = t.replace("```", "").replace("`", "")
        # Strip leading enumeration / list numbering like '1.', '1)', '(1)', '- ', '* ', '• '
        t = re.sub(r"^(?:[\d]+[\.\)]|\([\d]+\)|[\-\*\•])\s*", "", t)
        # Strip curly and straight quotes
        t = t.replace("“", "").replace("”", "").replace("‘", "").replace("’", "").replace('"', '').replace("'", "")
        # Normalize whitespace
        t = re.sub(r"\s+", " ", t)
        return t.strip()

    def detect_requested_formats(self, text: str) -> List[str]:
        """Detect explicit deliverable format requests (DOCX, PDF, ZIP, CSV, JSON)."""
        formats = []
        lower = text.lower()
        for fmt, patterns in FORMAT_PATTERNS.items():
            if any(re.search(pat, lower, re.IGNORECASE) for pat in patterns):
                formats.append(fmt)
        return formats

    def check_dataset_present(self, text: str, parameters: Optional[Dict[str, Any]] = None, attachments: Optional[List[str]] = None) -> bool:
        """Determines if actual dataset access is available for data analysis."""
        if attachments and len(attachments) > 0:
            return True
        if parameters:
            if parameters.get("dataset") or parameters.get("file_path") or parameters.get("csv_data") or parameters.get("attachments"):
                return True
            if parameters.get("has_dataset") is True:
                return True
        # Check if inline CSV data is present (has commas, newlines, and tabular shape)
        lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
        if len(lines) >= 3 and all("," in line for line in lines[:3]):
            return True
        return False

    def route_deterministic(
        self,
        text: str,
        parameters: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[str]] = None,
    ) -> Optional[Tuple[IntentType, str, float]]:
        """
        Applies deterministic routing heuristics.
        Returns (IntentType, reason, confidence) if confident, or None if ambiguous.
        """
        norm = self.normalize_text(text)
        lower = norm.lower()

        # Guard: Check for empty or trivial request
        if not norm:
            return IntentType.CHAT, "Empty input defaulted to chat", 1.0

        is_question_about_topic = any(re.search(pat, lower, re.IGNORECASE) for pat in QUESTION_ABOUT_TOPIC_PATTERNS)

        # 0. Consequential / DevOps / Infrastructure Operations -> software_project (with approval gating)
        if any(k in lower for k in ["deploy", "drop production", "terminate cluster", "wipe database", "release to cluster", "drop tables"]):
            return IntentType.SOFTWARE_PROJECT, "Operational / deployment request involving software infrastructure", 0.95

        # 1. Data Analysis (Highest precedence when data/CSV explicitly mentioned)
        for pat in DATA_ANALYSIS_PATTERNS:
            if re.search(pat, lower, re.IGNORECASE):
                return IntentType.DATA_ANALYSIS, "Request explicitly asks for dataset or trend analysis", 0.95

        # 2. Research (Academic papers, literature reviews, citations)
        if not is_question_about_topic:
            for pat in RESEARCH_PATTERNS:
                if re.search(pat, lower, re.IGNORECASE):
                    return IntentType.RESEARCH, "Request explicitly asks for research paper or literature review", 0.95

        # 3. Software Project (Complete applications, websites, systems)
        if not is_question_about_topic:
            for pat in SOFTWARE_PROJECT_PATTERNS:
                if re.search(pat, lower, re.IGNORECASE):
                    return IntentType.SOFTWARE_PROJECT, "Request specifies building a complete application or website", 0.95

        # 4. Code (Standalone functions, debugging, scripts, snippets)
        if not is_question_about_topic:
            for pat in CODE_PATTERNS:
                if re.search(pat, lower, re.IGNORECASE):
                    return IntentType.CODE, "Request specifies code implementation, debugging, or script generation", 0.95

        # 5. Explanations and conceptual queries (Chat)
        for pat in EXPLANATION_PREFIX_PATTERNS:
            if re.search(pat, lower, re.IGNORECASE):
                return IntentType.CHAT, "Request is an informational question or conceptual explanation", 0.95

        # Question mark at end and no imperative project/code trigger -> Chat
        if lower.endswith("?") and not any(k in lower for k in ["build a", "write a python function", "write a research paper"]):
            return IntentType.CHAT, "Conversational question ending in question mark", 0.90

        # General single-word or short inquiries without explicit workflow verbs -> Chat
        if len(norm.split()) <= 4 and not any(k in lower for k in ["build", "write", "debug", "analyze"]):
            return IntentType.CHAT, "Short informational query without complex workflow triggers", 0.85

        # Ambiguous: could not determine with high confidence
        return None

    async def route_with_llm(
        self,
        text: str,
        parameters: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[str]] = None,
    ) -> ExecutionPlan:
        """
        Constrained LLM-assisted planner using Ollama /api/chat with JSON Schema constraints.
        Includes bounded retries and semantic consistency enforcement.
        """
        system_prompt = (
            "You are an expert AI intent classifier and workflow planner. "
            "Your task is to classify the user's request into EXACTLY ONE canonical intent and workflow pair:\n"
            "1. 'chat' -> 'answer_question': Conceptual questions, explanations, definitions, tutorials "
            "(e.g. 'What is RAG?', 'Explain Python decorators', 'How does Docker work?'). "
            "IMPORTANT: Technical topics are STILL 'chat' if the user is asking for an explanation!\n"
            "2. 'research' -> 'research_and_write': Explicit requests for research papers, literature reviews, or academic reports with citations.\n"
            "3. 'code' -> 'generate_code': Standalone functions, code snippets, bug fixes, debugging, or small scripts.\n"
            "4. 'software_project' -> 'build_software': Complete applications, full-stack websites, or multi-file software projects.\n"
            "5. 'data_analysis' -> 'analyze_data': Analyzing datasets, spreadsheets, CSV trends, or statistical metrics.\n\n"
            "You MUST respond ONLY with valid JSON conforming to the requested schema."
        )

        user_prompt = f"User Request: {text.strip()}"
        if attachments:
            user_prompt += f"\nAttachments: {', '.join(attachments)}"

        schema = {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "enum": [i.value for i in IntentType]
                },
                "workflow": {
                    "type": "string",
                    "enum": [w.value for w in WorkflowType]
                },
                "reason": {
                    "type": "string"
                },
                "confidence": {
                    "type": "number"
                }
            },
            "required": ["intent", "workflow", "reason"]
        }

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                res_json = await model_adapter.chat_structured(
                    model_id=f"ollama/{self.planner_model}",
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    json_schema=schema,
                    timeout=self.timeout_seconds
                )

                intent_str = res_json.get("intent", "").strip().lower()
                workflow_str = res_json.get("workflow", "").strip().lower()
                reason = res_json.get("reason", "Classified by constrained LLM planner")
                confidence = float(res_json.get("confidence", 0.85))

                # Validate intent enum
                if intent_str not in [i.value for i in IntentType]:
                    raise ValueError(f"Unknown intent: '{intent_str}'")

                intent = IntentType(intent_str)
                canonical_wf = CANONICAL_INTENT_WORKFLOW_MAP[intent]

                # Semantic consistency check: enforce canonical mapping
                if workflow_str != canonical_wf.value:
                    logger.warning(
                        f"LLM produced workflow mismatch: intent='{intent_str}', workflow='{workflow_str}'. "
                        f"Enforcing canonical workflow '{canonical_wf.value}'."
                    )
                    workflow = canonical_wf
                else:
                    workflow = WorkflowType(workflow_str)

                # Build validated plan
                return self.build_execution_plan(
                    intent=intent,
                    workflow=workflow,
                    reason=f"[LLM Planner] {reason}",
                    confidence=min(1.0, max(0.0, confidence)),
                    source=RoutingSource.LLM_PLANNER,
                    text=text,
                    parameters=parameters,
                    attachments=attachments
                )
            except Exception as e:
                last_error = e
                logger.warning(f"LLM planning attempt {attempt + 1} failed: {e}")

        # Bounded retries exhausted: safe fallback
        logger.error(f"All LLM planning attempts failed: {last_error}. Invoking safe deterministic fallback.")
        det_result = self.route_deterministic(text, parameters, attachments)
        fallback_intent = det_result[0] if det_result else IntentType.CHAT
        fallback_wf = CANONICAL_INTENT_WORKFLOW_MAP[fallback_intent]

        return self.build_execution_plan(
            intent=fallback_intent,
            workflow=fallback_wf,
            reason=f"[Fallback Route] LLM planner failed ({last_error}). Safely routed to {fallback_intent.value}.",
            confidence=0.5,
            source=RoutingSource.FALLBACK,
            text=text,
            parameters=parameters,
            attachments=attachments
        )

    def build_execution_plan(
        self,
        intent: IntentType,
        workflow: WorkflowType,
        reason: str,
        confidence: float,
        source: RoutingSource,
        text: str,
        parameters: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[str]] = None,
    ) -> ExecutionPlan:
        """
        Builds a strictly validated ExecutionPlan with corresponding DAG tasks
        using existing, enabled agent roles.
        """
        parameters = parameters or {}
        attachments = attachments or []
        explicit_formats = self.detect_requested_formats(text)

        # Map deliverables according to intent and explicit user formatting
        deliverables: List[str] = []
        if intent == IntentType.CHAT:
            deliverables = ["markdown"]
            if "pdf" in explicit_formats:
                deliverables.append("pdf")
            if "docx" in explicit_formats:
                deliverables.append("docx")

        elif intent == IntentType.RESEARCH:
            deliverables = ["report", "markdown"]
            if "docx" in explicit_formats or not explicit_formats:
                deliverables.append("docx")
            if "pdf" in explicit_formats or not explicit_formats:
                deliverables.append("pdf")

        elif intent == IntentType.CODE:
            deliverables = ["code"]
            if "py" in explicit_formats or "python" in text.lower():
                deliverables.append("py")

        elif intent == IntentType.SOFTWARE_PROJECT:
            deliverables = ["code", "zip"]

        elif intent == IntentType.DATA_ANALYSIS:
            deliverables = ["report", "markdown"]
            if "csv" in explicit_formats:
                deliverables.append("csv")

        # Specific input verification for Data Analysis
        requires_clarification = False
        clarification_message = None
        if intent == IntentType.DATA_ANALYSIS:
            has_dataset = self.check_dataset_present(text, parameters, attachments)
            if not has_dataset:
                requires_clarification = True
                clarification_message = (
                    "Data analysis requires an accessible dataset or file. "
                    "Please provide or upload a CSV, JSON, or tabular dataset to proceed with analysis."
                )

        # Construct DAG tasks using existing agent capabilities
        tasks: List[TaskPlanItem] = []
        selected_agents: List[str] = []

        if workflow == WorkflowType.ANSWER_QUESTION:
            selected_agents = ["writer"]
            tasks.append(
                TaskPlanItem(
                    task_id="T1-chat-answer",
                    title="Direct Answer Generation",
                    role="writer",
                    goal=f"Provide a clear, direct, and well-structured answer to: {text}",
                    depends_on=[],
                    acceptance_criteria=["Directly answers the user's inquiry", "Clear markdown formatting"],
                    requires_approval=False,
                    estimated_complexity="low"
                )
            )

        elif workflow == WorkflowType.RESEARCH_AND_WRITE:
            selected_agents = ["researcher", "writer", "reviewer"]
            tasks.extend([
                TaskPlanItem(
                    task_id="T1-research",
                    title="Evidence & Literature Gathering",
                    role="researcher",
                    goal=f"Research thoroughly and collect citations, evidence, and key findings for: {text}",
                    depends_on=[],
                    acceptance_criteria=["Comprehensive coverage", "Authoritative sources cited"],
                    requires_approval=False,
                    estimated_complexity="medium"
                ),
                TaskPlanItem(
                    task_id="T2-write",
                    title="Synthesize Comprehensive Paper",
                    role="writer",
                    goal=f"Write complete, structured research paper or report on: {text}",
                    depends_on=["T1-research"],
                    acceptance_criteria=["Clear abstract, analysis, and discussion", "Professional academic tone"],
                    requires_approval=False,
                    estimated_complexity="high"
                ),
                TaskPlanItem(
                    task_id="T3-qa",
                    title="Academic Quality Review",
                    role="reviewer",
                    goal="Review the research paper for factual accuracy and completeness",
                    depends_on=["T2-write"],
                    acceptance_criteria=["Confirm factual consistency", "Verify rigorous structure"],
                    requires_approval=False,
                    estimated_complexity="low"
                )
            ])

        elif workflow == WorkflowType.GENERATE_CODE:
            selected_agents = ["developer", "reviewer"]
            tasks.extend([
                TaskPlanItem(
                    task_id="T1-dev",
                    title="Code Implementation",
                    role="developer",
                    goal=f"Write complete, production-ready code with error handling for: {text}",
                    depends_on=[],
                    acceptance_criteria=["Working implementation", "Clean docstrings and type hints"],
                    requires_approval=False,
                    estimated_complexity="high"
                ),
                TaskPlanItem(
                    task_id="T2-review",
                    title="Code Review & Verification",
                    role="reviewer",
                    goal="Review code quality, security, and edge-case handling",
                    depends_on=["T1-dev"],
                    acceptance_criteria=["Confirm code correctness", "Check potential runtime defects"],
                    requires_approval=False,
                    estimated_complexity="medium"
                )
            ])

        elif workflow == WorkflowType.BUILD_SOFTWARE:
            selected_agents = ["researcher", "developer", "writer"]
            tasks.extend([
                TaskPlanItem(
                    task_id="T1-plan",
                    title="Architecture & Structure Planning",
                    role="researcher",
                    goal=f"Plan software architecture, file structure, and component hierarchy for: {text}",
                    depends_on=[],
                    acceptance_criteria=["Component breakdown", "File list specified"],
                    requires_approval=False,
                    estimated_complexity="low"
                ),
                TaskPlanItem(
                    task_id="T2-html",
                    title="HTML5 / Component Scaffold",
                    role="developer",
                    goal=f"Implement semantic structure and markup for: {text}",
                    depends_on=["T1-plan"],
                    acceptance_criteria=["Semantic HTML5", "Responsive container structure"],
                    requires_approval=False,
                    estimated_complexity="high"
                ),
                TaskPlanItem(
                    task_id="T3-css",
                    title="CSS Styling & Layouts",
                    role="developer",
                    goal=f"Implement responsive styling, design system tokens, and layouts for: {text}",
                    depends_on=["T2-html"],
                    acceptance_criteria=["Responsive across devices", "Modern aesthetic palette"],
                    requires_approval=False,
                    estimated_complexity="high"
                ),
                TaskPlanItem(
                    task_id="T4-js",
                    title="Client-Side Interactivity",
                    role="developer",
                    goal=f"Implement JavaScript application logic and interactivity for: {text}",
                    depends_on=["T3-css"],
                    acceptance_criteria=["Interactive logic functional", "Zero uncaught exceptions"],
                    requires_approval=False,
                    estimated_complexity="medium"
                ),
                TaskPlanItem(
                    task_id="T5-readme",
                    title="Documentation & Usage Guide",
                    role="writer",
                    goal=f"Write README.md detailing setup, architecture, and features for: {text}",
                    depends_on=["T4-js"],
                    acceptance_criteria=["Complete setup guide", "Feature documentation"],
                    requires_approval=False,
                    estimated_complexity="low"
                )
            ])

        elif workflow == WorkflowType.ANALYZE_DATA:
            selected_agents = ["analyst", "reviewer"]
            tasks.extend([
                TaskPlanItem(
                    task_id="T1-analysis",
                    title="Statistical & Trend Analysis",
                    role="analyst",
                    goal=f"Perform data evaluation, extract metrics, and analyze trends for: {text}",
                    depends_on=[],
                    acceptance_criteria=["Quantitative metrics calculated", "Clear pattern identification"],
                    requires_approval=False,
                    estimated_complexity="medium"
                ),
                TaskPlanItem(
                    task_id="T2-review",
                    title="Analysis Quality & Finding Verification",
                    role="reviewer",
                    goal="Verify validity of analytical conclusions and statistical rigor",
                    depends_on=["T1-analysis"],
                    acceptance_criteria=["Confirm analytical validity", "Actionable recommendations provided"],
                    requires_approval=False,
                    estimated_complexity="low"
                )
            ])

        return ExecutionPlan(
            intent=intent,
            workflow=workflow,
            deliverables=deliverables,
            reason=reason,
            confidence=confidence,
            routing_source=source,
            selected_agents=selected_agents,
            tasks=tasks,
            dependencies=[dep for t in tasks for dep in t.depends_on],
            constraints=["Requires dataset upload"] if requires_clarification else [],
            requires_approval=False,
            requires_clarification=requires_clarification,
            clarification_message=clarification_message,
            metadata={
                "explicit_formats": explicit_formats,
                "input_length": len(text),
                "has_dataset": not requires_clarification if intent == IntentType.DATA_ANALYSIS else True
            }
        )

    async def plan(
        self,
        text: str,
        parameters: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[str]] = None,
    ) -> ExecutionPlan:
        """
        Main routing and planning entrypoint.
        1. Validates and normalizes input.
        2. Tries deterministic routing for clear, unambiguous requests.
        3. If ambiguous, falls back to constrained LLM-assisted planner.
        4. Validates plan semantics and returns ExecutionPlan.
        """
        norm_text = self.normalize_text(text)
        if not norm_text:
            return self.build_execution_plan(
                intent=IntentType.CHAT,
                workflow=WorkflowType.ANSWER_QUESTION,
                reason="Empty request safely routed to chat.",
                confidence=1.0,
                source=RoutingSource.DETERMINISTIC,
                text=text,
                parameters=parameters,
                attachments=attachments
            )

        # 1. Deterministic First Pass
        det_res = self.route_deterministic(norm_text, parameters, attachments)
        if det_res:
            intent, reason, confidence = det_res
            workflow = CANONICAL_INTENT_WORKFLOW_MAP[intent]
            logger.info(f"Deterministic routing matched: {intent.value} -> {workflow.value} ({reason})")
            return self.build_execution_plan(
                intent=intent,
                workflow=workflow,
                reason=f"[Deterministic Rule] {reason}",
                confidence=confidence,
                source=RoutingSource.DETERMINISTIC,
                text=norm_text,
                parameters=parameters,
                attachments=attachments
            )

        # 2. Ambiguous or Complex Request -> Constrained LLM-Assisted Planning
        logger.info(f"Request '{norm_text[:60]}' is ambiguous. Escalating to LLM planner.")
        return await self.route_with_llm(norm_text, parameters, attachments)


hybrid_router = HybridRouter()

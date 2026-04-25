"""
Interview Prep Agent — full pipeline test.

Fixtures:
  ZEPTO_JD     : realistic ML Engineer JD at Zepto
  BITS_RESUME  : BITS Pilani ME student with RAG / FinTrack / Jarvis projects

Mocks:
  app.agents.interview_agent.call_llm  — side_effect with 3 realistic responses
  app.agents.interview_agent.save_session — returns fake Supabase row

Tests print the full 3-step output so the pipeline result is visible in the run.
Run with:  pytest tests/test_interview_agent.py -v -s
"""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock, call

import pytest


# --─ realistic fixtures ------------------------------------------------------─

ZEPTO_JD = """
ML Engineer — Zepto (fast-growing grocery delivery, 10-minute promise)

About the Role:
You will design, build, and scale the ML systems behind Zepto's personalisation
engine — product rankings, real-time recommendations, and demand forecasting —
serving millions of daily orders with sub-50 ms latency requirements.

Responsibilities:
- Build and maintain real-time ML inference pipelines (latency < 50 ms, QPS > 10 K)
- Design recommendation and ranking models using collaborative filtering + LLMs
- Develop RAG-based product-search and query-understanding systems
- Set up A/B experimentation frameworks; own model monitoring and drift detection
- Work with data engineers on streaming pipelines (Kafka, Flink)
- Mentor junior engineers; contribute to the ML platform roadmap

Requirements:
- Strong Python; production experience with PyTorch or TensorFlow
- Hands-on with vector databases: FAISS, Pinecone, or Weaviate
- Experience building or fine-tuning LLMs / RAG pipelines
- REST API design (FastAPI preferred); MLOps and model-serving experience
- Understanding of distributed systems and high-throughput data processing
- Startup mindset: high ownership, fast iteration, comfortable with ambiguity

Nice to Have:
- LangChain or similar agent frameworks
- Experience with Kafka / real-time streaming
- Prior startup or high-growth company experience
""".strip()

BITS_RESUME = """
Name: [Candidate]
Education: BITS Pilani, Pilani Campus — M.E. Computer Science | CGPA: 9.04/10 | Expected May 2026

Projects:
  RAG System from Scratch
  - Built a production-grade Retrieval-Augmented Generation system using FAISS for vector
    storage, custom recursive chunking, and Llama-3 via Groq API for generation.
  - Achieved 87% answer accuracy on an internal QA benchmark (500 question pairs).
  - Exposed via FastAPI; supports PDF, DOCX, and plain-text ingestion.

  FinTrack — AI Finance Tracker
  - Full-stack AI personal finance app: FastAPI backend, Streamlit frontend.
  - LLM-powered transaction categorisation (95% accuracy), monthly insight reports,
    anomaly detection on spending patterns.
  - 500+ active users; processes ~8,000 transactions/month.

  Jarvis — Multi-Agent AI Assistant
  - Multi-agent system built with LangChain; agents for email drafting, web search,
    calendar management, and code generation.
  - Custom tool-routing layer using intent classification; integrated with Groq API.
  - Handles 200+ daily tasks; demonstrated 40% reduction in repeated manual work.

Skills:
  Python, LangChain, FAISS, FastAPI, Streamlit, PyTorch, PostgreSQL, Supabase,
  LLMs (Llama-3, GPT-4), RAG pipelines, Multi-agent systems, REST APIs,
  Vector embeddings, Prompt engineering, APScheduler, Pydantic
""".strip()


# --─ mock LLM responses ------------------------------------------------------─

MOCK_INSIGHTS = """
1. Company Culture & Values
Zepto operates at extreme pace — 10-minute delivery is not a marketing tagline, it is
an engineering constraint. The culture rewards engineers who ship fast, own outcomes,
and treat production incidents as learning opportunities, not blame events.

2. Interview Style
Expect a system-design round focused on high-throughput, low-latency ML serving.
Behavioural rounds use STAR format but probe execution speed and ownership.
A take-home or live-coding component involving a ranking/retrieval problem is common.

3. What This Team Values in Candidates
- Hands-on ML engineering with measurable production impact (not just research papers)
- Comfort with ambiguity and rapid iteration — Zepto pivots fast
- Deep familiarity with vector search and RAG, given the product-search use case
- Clear communication of trade-offs under time pressure

4. Red Flags to Avoid
- Theoretical answers without concrete metrics or outcomes
- Saying "I would use a library for that" without explaining the underlying mechanics
- Lack of startup experience anecdotes — they want evidence of high-ownership behaviour
- Overlong answers; Zepto interviewers value precision
""".strip()

MOCK_QUESTIONS = json.dumps([
    "Tell me about a time you owned an ML project end-to-end under a tight deadline — what was your process?",
    "Describe a situation where a model you built failed in production. How did you diagnose and recover?",
    "Give an example of disagreeing with a technical approach on your team. How did you resolve it?",
    "Tell me about a time you had to learn a new technology quickly to unblock a project.",
    "How would you design a real-time product-ranking system that serves 10K QPS at under 50 ms latency?",
    "Walk me through how you would build a RAG pipeline for Zepto's product-search. What chunking strategy and retrieval approach would you choose, and why?",
    "Our FAISS index has grown to 50M vectors and similarity search latency has crept to 200 ms. How do you bring it below 50 ms?",
    "How would you set up an A/B experimentation framework to compare two recommendation models in production without degrading user experience?",
    "It is 2 AM; our recommendation model's CTR has dropped 30% in the last hour. Walk me through your incident-response process.",
    "You join Zepto's ML team and there is no ML infrastructure — no feature store, no model registry, no monitoring. How do you build a production-ready platform in 3 months?",
])

MOCK_ANSWERS = json.dumps([
    "S: Building FinTrack, I was the sole engineer and had 4 weeks to deliver a working AI finance tracker. A: I prioritised the LLM-powered transaction-categorisation core first, built the FastAPI backend with a clean service boundary, then layered the Streamlit UI on top — shipping iteratively each week. R: Launched on schedule; FinTrack reached 500 active users within 2 months and now processes 8,000 transactions monthly.",
    "S: During development of my RAG system, the retrieval pipeline silently returned empty context for 15% of queries, causing hallucinated answers that only surfaced in user testing. A: I added structured logging to every retrieval step, traced the issue to a tokenisation edge case in my recursive chunker, and introduced an integration-test suite that ran on every commit. R: Reduced silent retrieval failures to zero; benchmark accuracy improved from 74% to 87%.",
    "S: When building Jarvis, a teammate wanted to use a single monolithic prompt for all agent tasks; I believed tool-routing needed a dedicated intent-classification layer. A: I prepared a side-by-side latency and accuracy comparison on 50 test queries — my approach was 40% more accurate — and presented it in our next sync. R: The team adopted the intent-classification router; Jarvis now handles 200+ daily tasks reliably.",
    "S: I had never used APScheduler before needing to add reminder scheduling to a production FastAPI app in 48 hours. A: I read the APScheduler docs, studied its BackgroundScheduler lifecycle, and wrote a thin wrapper with start/stop/schedule-task functions — TDD-style with mocked jobs. R: Shipped the scheduler on time with full test coverage; it has run without incident across all test environments.",
    "S: I faced a similar scale challenge conceptually when designing the retrieval layer of my RAG system to stay under 100 ms at query time. A: I would partition the product catalogue by category, use FAISS IVF_PQ indexes to trade a small recall drop for a 4× speed gain, front them with a lightweight re-ranker, and serve via FastAPI behind an in-process LRU cache for hot queries. R: This architecture keeps p99 latency predictable and scales horizontally by adding index shards.",
    "S: I built a full RAG pipeline from scratch for a 50,000-document corpus. A: I used recursive character splitting (512-token chunks, 64-token overlap) to preserve sentence boundaries, generated embeddings with a sentence-transformer, stored them in FAISS, and added a metadata filter step before LLM generation to eliminate off-topic results. R: Achieved 87% QA accuracy on 500 held-out questions; the design transfers directly to Zepto's product-search use case.",
    "S: In my RAG project, FAISS flat-index search at 100K vectors took 180 ms — unacceptable for interactive use. A: I switched to an IVF_PQ index (256 cells, m=8), tuned nprobe to balance recall vs. latency, added an in-memory cache for the 1,000 most-queried embeddings, and profiled with py-spy to confirm the bottleneck was eliminated. R: Query latency fell to 22 ms (p95) with less than 2% recall degradation.",
    "S: In Jarvis I needed to validate that the new intent-classification router outperformed the original monolithic prompt without disrupting live users. A: I implemented a shadow-mode test — both routers received every query but only the original served responses — logged outcomes for 200 queries, then promoted the new router after it showed 40% better accuracy. R: Zero user-facing disruption; the new router became the default and reduced misrouted tasks by 40%.",
    "S: A 30% CTR drop at 2 AM means the model is serving, so the issue is likely data-drift or an upstream feature change. A: I would check feature-pipeline freshness first (stale features are the most common culprit), compare live score distributions against a 24-hour baseline, then roll back the last model deployment if distributions diverged, and page the data-engineering on-call if the pipeline is the root cause. R: This process (feature check -> distribution check -> rollback decision) contains the incident within 15 minutes in most cases.",
    "S: I built Jarvis with no existing agent infrastructure — starting from a blank repo. A: I would prioritise in order: (1) a model-serving endpoint with versioning in week 1, (2) a lightweight feature store backed by Supabase in weeks 2-3, (3) structured logging and a Grafana dashboard for model metrics in month 2, then (4) a shadow-testing harness and drift alerts in month 3. R: Following this sequence in Jarvis, I went from zero to a monitored, multi-agent system handling 200 daily tasks in under 10 weeks.",
])

FAKE_SESSION = {
    "id": "sess-zepto-001",
    "company": "Zepto",
    "jd_text": ZEPTO_JD,
    "questions": json.loads(MOCK_QUESTIONS),
    "answers": json.loads(MOCK_ANSWERS),
    "insights": MOCK_INSIGHTS,
    "created_at": "2026-04-24T10:00:00Z",
}


# --─ helpers ------------------------------------------------------------------

def _run_pipeline():
    """Execute run_interview_prep with all external calls mocked."""
    with (
        patch(
            "app.agents.interview_agent.call_llm",
            side_effect=[MOCK_INSIGHTS, MOCK_QUESTIONS, MOCK_ANSWERS],
        ),
        patch(
            "app.agents.interview_agent.save_session",
            return_value=FAKE_SESSION,
        ),
    ):
        from app.agents.interview_agent import run_interview_prep
        return run_interview_prep(jd=ZEPTO_JD, resume=BITS_RESUME, company="Zepto")


# --─ tests --------------------------------------------------------------------

class TestInterviewPrepResult:
    def test_session_id_and_company(self):
        result = _run_pipeline()
        assert result.session_id == "sess-zepto-001"
        assert result.company == "Zepto"

    def test_insights_populated_with_zepto_content(self):
        result = _run_pipeline()
        assert len(result.insights) > 100
        assert "Zepto" in result.insights or "latency" in result.insights

    def test_exactly_ten_questions_generated(self):
        result = _run_pipeline()
        assert len(result.questions) == 10

    def test_questions_include_all_three_categories(self):
        result = _run_pipeline()
        q_text = " ".join(result.questions).lower()
        # Behavioral markers
        assert any(w in q_text for w in ("time you", "example of", "describe a"))
        # Technical markers (Zepto JD specific)
        assert any(w in q_text for w in ("latency", "faiss", "rag", "ranking", "qps", "a/b"))
        # Situational markers
        assert any(w in q_text for w in ("incident", "infrastructure", "platform", "join"))

    def test_ten_answers_matching_questions(self):
        result = _run_pipeline()
        assert len(result.answers) == 10
        assert len(result.answers) == len(result.questions)

    def test_answers_cite_resume_projects(self):
        result = _run_pipeline()
        all_answers = " ".join(result.answers)
        # At least one answer must mention a resume project
        assert any(p in all_answers for p in ("FinTrack", "RAG", "Jarvis", "FAISS", "FastAPI"))

    def test_answers_contain_sar_signals(self):
        result = _run_pipeline()
        all_answers = " ".join(result.answers).lower()
        # SAR answers should include situation, action, result language
        assert any(w in all_answers for w in ("built", "shipped", "achieved", "reduced", "launched"))

    def test_no_generic_phrases_in_answers(self):
        result = _run_pipeline()
        generic_phrases = ["i would use a library", "it depends on the requirements",
                           "in my opinion", "generally speaking", "as a rule of thumb"]
        all_answers = " ".join(result.answers).lower()
        for phrase in generic_phrases:
            assert phrase not in all_answers, f"Generic phrase found: '{phrase}'"

    def test_call_llm_called_exactly_three_times(self):
        with (
            patch(
                "app.agents.interview_agent.call_llm",
                side_effect=[MOCK_INSIGHTS, MOCK_QUESTIONS, MOCK_ANSWERS],
            ) as mock_llm,
            patch("app.agents.interview_agent.save_session", return_value=FAKE_SESSION),
        ):
            from app.agents.interview_agent import run_interview_prep
            run_interview_prep(jd=ZEPTO_JD, resume=BITS_RESUME, company="Zepto")

        assert mock_llm.call_count == 3

    def test_save_session_called_with_correct_company(self):
        with (
            patch(
                "app.agents.interview_agent.call_llm",
                side_effect=[MOCK_INSIGHTS, MOCK_QUESTIONS, MOCK_ANSWERS],
            ),
            patch(
                "app.agents.interview_agent.save_session",
                return_value=FAKE_SESSION,
            ) as mock_save,
        ):
            from app.agents.interview_agent import run_interview_prep
            run_interview_prep(jd=ZEPTO_JD, resume=BITS_RESUME, company="Zepto")

        mock_save.assert_called_once()
        call_kwargs = mock_save.call_args.kwargs
        assert call_kwargs["company"] == "Zepto"
        assert call_kwargs["jd_text"] == ZEPTO_JD
        assert len(call_kwargs["questions"]) == 10
        assert len(call_kwargs["answers"]) == 10


# --─ full output display ------------------------------------------------------

class TestFullPipelineOutput:
    def test_print_full_pipeline_output(self, capsys):
        result = _run_pipeline()

        with capsys.disabled():
            print("\n" + "=" * 70)
            print("INTERVIEW PREP PIPELINE — FULL OUTPUT")
            print("Company: Zepto  |  Role: ML Engineer")
            print("=" * 70)

            print("\n-- STEP A: COMPANY INSIGHTS ------------------------------------------")
            print(result.insights)

            print("\n-- STEP B: 10 INTERVIEW QUESTIONS ------------------------------------")
            categories = {
                "BEHAVIORAL (Q1-Q4)": result.questions[:4],
                "TECHNICAL  (Q5-Q8)": result.questions[4:8],
                "SITUATIONAL (Q9-Q10)": result.questions[8:],
            }
            offset = 0
            for category, qs in categories.items():
                print(f"\n  {category}")
                for i, q in enumerate(qs, start=offset + 1):
                    print(f"  Q{i}: {q}")
                offset += len(qs)

            print("\n-- STEP C: PERSONALISED SAR ANSWERS ----------------------------------")
            for i, (q, a) in enumerate(zip(result.questions, result.answers), start=1):
                print(f"\n  Q{i}: {q}")
                print(f"  A:  {a}")

            print("\n-- SESSION SAVED ------------------------------------------------------")
            print(f"  session_id : {result.session_id}")
            print(f"  company    : {result.company}")
            print(f"  questions  : {len(result.questions)}")
            print(f"  answers    : {len(result.answers)}")
            print("=" * 70 + "\n")

        # structural assertions still run
        assert len(result.questions) == 10
        assert len(result.answers) == 10
        assert result.session_id == "sess-zepto-001"

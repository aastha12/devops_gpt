import streamlit as st
from connectors.atlas_connection import AtlasConnection
from processors.embeddings import EmbeddingModel
from processors.user_query_processor import UserQueryProcessor
from processors.llm_processor import LLMProcessor
from processors.judge_prompt import JUDGE_PROMPT
import torch
import re

# torch fix for streamlit
torch.classes.__path__ = []

# Set layout
st.set_page_config(page_title="Incident Insight Assistant", layout="centered")
st.title("🧠 SRE Incident Insight Assistant")

# Load dependencies
with st.spinner("Loading models and database..."):
    embedding_model = EmbeddingModel()
    llm_processor = LLMProcessor()
    atlas_client = AtlasConnection()
    atlas_client.ping()
    collection = atlas_client.get_collection("incidents")

# ---------- UI ----------
st.markdown("Paste your **incident log** below 👇")
user_input = st.text_area("New Incident Log", height=200, placeholder="e.g. Jenkins pipeline failed after Git error...")

# Button and checkbox in same row
col1, col2 = st.columns([2, 3])
with col1:
    analyze_button = st.button("Analyze Incident")
with col2:
    run_judge_eval = st.checkbox("Run LLM-as-Judge Evaluation", value=True)

# ---------- Main Logic ----------
if analyze_button:
    if user_input.strip():
        with st.spinner("Finding similar incidents..."):
            query_processor = UserQueryProcessor(user_query=user_input, embedding_model=embedding_model)
            similar_texts = query_processor.process_query(collection)

        if not similar_texts:
            st.warning("No similar incidents found.")
        else:
            with st.spinner("Generating insights with LLM..."):
                response = llm_processor.get_llm_response(user_input, similar_texts)

            st.session_state["llm_response"] = response
            st.session_state["user_input"] = user_input

            st.subheader("📄 Response")
            # Use the LLMProcessor's formatting method instead of local function
            formatted_response = llm_processor.format_llm_response(response)
            st.markdown(formatted_response)
    else:
        st.warning("Please enter an incident log to analyze.")

# ---------- Judge Evaluation ----------
if st.session_state.get("llm_response") and run_judge_eval:
    judge_prompt = JUDGE_PROMPT.format(
        prompt=st.session_state["user_input"],
        response=st.session_state["llm_response"]
    )

    with st.spinner("Evaluating response quality..."):
        score_response = llm_processor.get_response(judge_prompt)

    # Use the LLMProcessor's formatting method instead of local function
    formatted_score = llm_processor.format_judge_score(score_response)
    st.subheader("📊 Evaluation")
    st.markdown(formatted_score)
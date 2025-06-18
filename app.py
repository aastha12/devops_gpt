import streamlit as st
from connectors.atlas_connection import AtlasConnection
from processors.embeddings import EmbeddingModel
from processors.user_query_processor import UserQueryProcessor
from processors.llm_processor import LLMProcessor
from processors.judge_prompt import JUDGE_PROMPT
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Set layout
st.set_page_config(page_title="Incident Insight Assistant", layout="centered")
st.title("🧠 SRE Incident Insight Assistant")

# Initialize components with error handling
@st.cache_resource
def initialize_components():
    """Initialize all components with proper error handling"""
    try:
        logger.info("Initializing components...")
        
        # Initialize embedding model (now uses HuggingFace API)
        embedding_model = EmbeddingModel()
        
        # Initialize LLM processor
        llm_processor = LLMProcessor()
        
        # Initialize Atlas connection
        atlas_client = AtlasConnection()
        atlas_client.ping()
        collection = atlas_client.get_collection("incidents")
        
        logger.info("All components initialized successfully!")
        return embedding_model, llm_processor, atlas_client, collection, None
        
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        return None, None, None, None, str(e)

# Load components
embedding_model, llm_processor, atlas_client, collection, init_error = initialize_components()

if init_error:
    st.error(f"❌ Failed to initialize system: {init_error}")
    st.info("Please check your API keys and database connection.")
    st.stop()
else:
    st.success("✅ System ready! Using HuggingFace API for fast embeddings.")

# ---------- UI ----------
st.markdown("Paste your **incident log** below 👇")
user_input = st.text_area(
    "New Incident Log", 
    height=200, 
    placeholder="e.g. Jenkins pipeline failed after Git error..."
)

# Button and checkbox in same row
col1, col2 = st.columns([2, 3])
with col1:
    analyze_button = st.button("🔍 Analyze Incident", type="primary")
with col2:
    run_judge_eval = st.checkbox("Run LLM-as-Judge Evaluation", value=True)

# ---------- Main Logic ----------
if analyze_button:
    if user_input.strip():
        try:
            with st.spinner("Finding similar incidents..."):
                query_processor = UserQueryProcessor(
                    user_query=user_input, 
                    embedding_model=embedding_model
                )
                similar_texts = query_processor.process_query(collection)

            if not similar_texts:
                st.warning("No similar incidents found. Generating analysis without context...")
                similar_texts = []

            with st.spinner("Generating insights with LLM..."):
                response = llm_processor.get_llm_response(user_input, similar_texts)

            # Store in session state for judge evaluation
            st.session_state["llm_response"] = response
            st.session_state["user_input"] = user_input

            # Display results
            st.subheader("📄 Analysis Results")
            formatted_response = llm_processor.format_llm_response(response)
            st.markdown(formatted_response)

            # Show number of similar incidents found
            if similar_texts:
                st.info(f"ℹ️ Analysis based on {len(similar_texts)} similar incidents")

        except Exception as e:
            st.error(f"❌ Analysis failed: {str(e)}")
            logger.error(f"Analysis error: {e}", exc_info=True)
            
            # Offer fallback option
            st.info("💡 You can try again or contact support if the issue persists.")
    else:
        st.warning("Please enter an incident log to analyze.")

# ---------- Judge Evaluation ----------
if st.session_state.get("llm_response") and run_judge_eval:
    try:
        judge_prompt = JUDGE_PROMPT.format(
            prompt=st.session_state["user_input"],
            response=st.session_state["llm_response"]
        )

        with st.spinner("Evaluating response quality..."):
            score_response = llm_processor.get_response(judge_prompt)

        # formatted_score = llm_processor.format_judge_score(score_response)
        st.subheader("📊 Quality Evaluation")
        # st.markdown(formatted_score)
        st.markdown(score_response)
        
    except Exception as e:
        st.error(f"❌ Evaluation failed: {str(e)}")
        logger.error(f"Judge evaluation error: {e}", exc_info=True)

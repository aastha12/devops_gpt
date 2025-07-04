import streamlit as st
from connectors.atlas_connection import AtlasConnection
from processors.embeddings import EmbeddingModel
from processors.user_query_processor import UserQueryProcessor
from processors.llm_processor import LLMProcessor
from baml_client import b
from dotenv import load_dotenv
import logging
import os
from flask import Flask
from threading import Thread
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Flask app for health check
health_app = Flask(__name__)

@health_app.route('/_stcore/health')
def health_check():
    return "OK", 200

def run_health_check_server():
    health_app.run(host='0.0.0.0', port=8080)

# Start the health check server in a separate thread
health_thread = Thread(target=run_health_check_server)
health_thread.daemon = True
health_thread.start()

# Set layout
st.set_page_config(page_title="Incident Insight Assistant", layout="centered")
st.title("🧠 SRE Incident Insight Assistant")

# Add custom CSS to fix formatting issues
st.markdown("""
<style>
    /* Fix any formatting issues with XML-like tags */
    .stMarkdown p {
        margin-bottom: 1rem;
    }
    
    /* Ensure proper spacing for troubleshooting steps */
    .stMarkdown ol li {
        margin-bottom: 0.5rem;
        line-height: 1.5;
    }
    
    /* Hide any XML tags that might leak through */
    .stMarkdown code:contains("<root_cause_summary>"),
    .stMarkdown code:contains("</root_cause_summary>"),
    .stMarkdown code:contains("<troubleshooting_steps>"),
    .stMarkdown code:contains("</troubleshooting_steps>") {
        display: none;
    }
    
    /* Add some styling for status messages */
    .status-message {
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    
    .status-success {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .status-warning {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }
    
    .status-error {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)

# Initialize components with error handling and timeout
@st.cache_resource
def initialize_components():
    """Initialize all components with proper error handling and timeout"""
    try:
        logger.info("Initializing components...")
        
        # Initialize embedding model with timeout
        embedding_model = EmbeddingModel()
        
        # Initialize LLM processor
        llm_processor = LLMProcessor()
        
        # Initialize Atlas connection
        atlas_client = AtlasConnection()
        atlas_client.ping()
        collection = atlas_client.get_collection("incidents")
        
        return embedding_model, llm_processor, atlas_client, collection, None
        
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        return None, None, None, None, str(e)

# Load components with progress indicator
with st.spinner("🔄 Initializing system components..."):
    embedding_model, llm_processor, atlas_client, collection, init_error = initialize_components()


if init_error:
    st.error(f"❌ Failed to initialize system: {init_error}")
    st.info("Please check your API keys and database connection.")
    st.stop()
else:
    st.success("✅ System ready! Using HuggingFace API for embeddings.")

# ---------- UI ----------
st.markdown("Paste your **incident log** below 👇")
user_input = st.text_area(
    " ",
    height=200, 
    placeholder="e.g. Jenkins pipeline failed after Git error...",
    label_visibility="collapsed"
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
        # Clear any previous results
        if "llm_response" in st.session_state:
            del st.session_state["llm_response"]
        if "user_input" in st.session_state:
            del st.session_state["user_input"]
            
        try:
            logger.info(f"User input received: {len(user_input)} characters")

            # Step 1: Find similar incidents with timeout
            similar_texts = []
            try:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("🔍 Finding similar incidents...")
                progress_bar.progress(10)
                
                start_time = time.time()
                query_processor = UserQueryProcessor(
                    user_query=user_input, 
                    embedding_model=embedding_model
                )
                
                progress_bar.progress(30)
                similar_texts = query_processor.process_query(collection)
                
                elapsed_time = time.time() - start_time
                progress_bar.progress(60)
                
                logger.info(f"Found {len(similar_texts)} similar incidents in {elapsed_time:.2f} seconds")
                status_text.text(f"✅ Found {len(similar_texts)} similar incidents")
                
                progress_bar.progress(100)
                
                # Clean up progress indicators
                progress_bar.empty()
                status_text.empty()
                
            except Exception as e:
                logger.error(f"Error finding similar incidents: {e}", exc_info=True)
                st.error(f"❌ Error finding similar incidents: {str(e)}")
                st.info("💡 The system will attempt to continue with fallback embeddings...")
                similar_texts = []

            # Step 2: Generate LLM response
            try:
                with st.spinner("🤖 Generating insights with LLM..."):
                    start_time = time.time()
                    response = llm_processor.get_llm_response(user_input, similar_texts)
                    elapsed_time = time.time() - start_time
                    
                logger.info(f"LLM response generated in {elapsed_time:.2f} seconds")
                
            except Exception as e:
                logger.error(f"Error generating LLM response: {e}", exc_info=True)
                st.error(f"❌ Error generating LLM response: {str(e)}")
                st.stop()

            # Store in session state for judge evaluation
            st.session_state["llm_response"] = response
            st.session_state["user_input"] = user_input
            
            # Display the formatted markdown response
            st.markdown(response)

            # Show number of similar incidents found
            if similar_texts:
                st.info(f"ℹ️ Analysis based on {len(similar_texts)} similar incidents")
            else:
                st.warning("⚠️ No similar incidents found - analysis based on general knowledge")

        except Exception as e:
            st.error(f"❌ Analysis failed: {str(e)}")
            logger.error(f"Analysis error: {e}", exc_info=True)
    else:
        st.warning("⚠️ Please enter an incident log to analyze.")

# ---------- Judge Evaluation ----------
if st.session_state.get("llm_response") and run_judge_eval:
    try:
        with st.spinner("📊 Evaluating response quality..."):
            start_time = time.time()
            judge_response = b.EvaluateResponse(
                prompt=st.session_state["user_input"],
                response=st.session_state["llm_response"]
            )
            elapsed_time = time.time() - start_time
            
        logger.info(f"Judge evaluation completed in {elapsed_time:.2f} seconds")
        
        st.subheader("📊 Quality Evaluation")

        # Simplified score display
        st.markdown(f"#### Score: **{judge_response.score}/5**")
        
        # Display justification
        st.markdown(f"#### Justification:\n\n{judge_response.justification}")
        
    except Exception as e:
        st.error(f"❌ Evaluation failed: {str(e)}")
        logger.error(f"Judge evaluation error: {e}", exc_info=True)


import streamlit as st
import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from firecrawl import FirecrawlApp
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import json
from datetime import datetime

# --- Configuration & Setup ---
load_dotenv()
st.set_page_config(page_title="SG Hype Predictor 👟", page_icon="👟", layout="wide")

# Custom CSS for a "Hype" Aesthetic with Light/Dark Mode Support
st.markdown("""
<style>
    /* Default (Light Mode) styles */
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #dcdde1;
    }
    .prediction-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #ff4b4b;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: #31333F;
    }
    .hype-title {
        color: #ff4b4b;
        font-weight: bold;
        font-size: 24px;
    }

    /* Dark Mode overrides */
    @media (prefers-color-scheme: dark) {
        .stMetric {
            background-color: #1a1c24;
            border: 1px solid #3d4455;
        }
        .prediction-card {
            background-color: #1a1c24;
            color: #fafafa;
            border: 2px solid #ff4b4b;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
    }
</style>
""", unsafe_allow_html=True)

# --- Business Logic Helpers (Derived from Hype Retailer Simulator) ---
def calculate_intelligence_score(trend, influencer, search):
    # Mapping with fallbacks for robustness
    trend_map = {
        "Low": 0.8, 
        "Growing": 1.2, 
        "Viral": 1.8, 
        "Explosive": 2.5
    }
    influencer_map = {
        "Organic": 1.0, "Micro": 1.0, "Organic/Micro": 1.0,
        "Boutique": 1.3, "Seed": 1.3, "Boutique/Seed": 1.3,
        "Elite": 2.0, "A-List": 2.0, "Elite/A-List": 2.0
    }
    
    # Get values with default fallbacks if LLM hallucinates a key
    t_val = trend_map.get(trend, 1.0)
    i_val = influencer_map.get(influencer, 1.0)
    search_mult = 1 + (search / 100)
    
    return round(t_val * i_val * search_mult, 2)

# --- Data Acquisition (Firecrawl) ---
def get_hype_data(niche, user_keyword=""):
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        st.error("Firecrawl API Key missing.")
        return []
    
    app = FirecrawlApp(api_key=api_key)
    
    # Dynamic Query Logic based on Niche and Singapore Platforms
    now = datetime.now()
    time_window = now.strftime("%B %Y")
    base_query = f"Singapore {time_window} {user_keyword}"
    
    niche_queries = {
        "👟 Sneakers & Streetwear": f"{base_query} (site:reddit.com/r/singapore OR site:forums.hardwarezone.com.sg OR site:limitededt.com) 'drop' OR 'raffle' OR 'release date'",
        "💻 Tech & Gadgets": f"{base_query} (site:hardwarezone.com.sg OR site:geekculture.co OR site:vulcanpost.com) 'limited edition' OR 'pre-order' OR 'launch'",
        "🍜 F&B & Lifestyle": f"{base_query} (site:mothership.sg OR site:eatbook.sg OR site:sethlui.com) 'pop-up' OR 'viral' OR 'limited time'",
        "🧸 Luxury & Collectibles": f"{base_query} (site:lifestyleasia.com/sg OR site:tatlerasia.com) 'exclusive' OR 'collectible' OR 'collaboration'"
    }
    
    query = niche_queries.get(niche, base_query)
    
    with st.spinner(f"🔍 Searching {niche} for high-signal data..."):
        try:
            # Execute actual Firecrawl search
            res = app.search(query)
            if isinstance(res, dict) and "data" in res:
                results = [f"{item.get('title', '')}: {item.get('description', '')}" for item in res["data"]]
            elif isinstance(res, list):
                results = [f"{item.get('title', '')}: {item.get('description', '')}" for item in res]
            else:
                results = [str(res)]
            return results
        except Exception as e:
            st.error(f"Firecrawl Error: {e}")
            return []

# --- AI Prediction (Gemini) ---
def predict_hype(data_snippets, niche):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("Gemini API Key missing.")
        return None
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3, api_key=api_key)
    
    prompt_str = """
    You are a Senior Market Analyst for the {niche} vertical in Singapore.
    Identify the top 3 most probable predictions for hype retailing based on these snippets:
    {snippets}
    
    Business Context:
    - Niche Focus: {niche}
    - Intelligence Score (I): Social Velocity * Influencer Tier * Search Intent.
    - Hype Meter (0-100): Calculated from signal density and trend velocity.
    
    Instructions:
    1. Look for specific mentions of dates, locations (e.g. Orchard, Jewel), and brands.
    2. Assess the "Hype Meter" (0-100) based on social signals.
    
    Required JSON Format (STRICTLY A JSON LIST):
    [
      {{
        "product": "Product Name/Trend",
        "probability": 85,
        "rationale": "Why this will trend in Singapore specifically.",
        "intelligence_signals": {{ "trend": "Explosive", "influencer": "Elite", "search_intent": 90 }},
        "hype_meter": 95
      }},
      ...
    ]
    """
    
    prompt = PromptTemplate.from_template(prompt_str)
    
    try:
        response = llm.invoke(prompt.format(snippets="\n".join(data_snippets), niche=niche))
        content = response.content.strip()
        
        # Robust JSON extraction
        try:
            start_index = content.find('[')
            end_index = content.rfind(']') + 1
            if start_index != -1 and end_index != 0:
                json_str = content[start_index:end_index]
                predictions = json.loads(json_str)
                return predictions
            else:
                # Try cleaning common markdown artifacts if markers aren't obvious
                cleaned = content.replace('```json', '').replace('```', '').strip()
                return json.loads(cleaned)
        except json.JSONDecodeError as e:
            st.error(f"JSON Parsing Error: {e}")
            st.code(content)
            return None
    except Exception as e:
        st.error(f"Gemini Analysis Error: {e}")
        return None

# --- Main Application ---
st.title("🔥 SG Hype Retail Predictor")
st.markdown("Predicting the next big retail 'Drop' in Singapore using AI Intelligence.")

with st.sidebar:
    st.header("Control Panel")
    niche_focus = st.selectbox("Market Niche", [
        "👟 Sneakers & Streetwear", 
        "💻 Tech & Gadgets", 
        "🍜 F&B & Lifestyle", 
        "🧸 Luxury & Collectibles"
    ])
    brand_filter = st.text_input("Brand/Item Filter (Optional)", placeholder="e.g. Nike, NVIDIA, Labubu")
    
    st.markdown("---")
    if st.button("🚀 Analyze Hype Signals"):
        st.session_state.run_analysis = True

if 'run_analysis' not in st.session_state:
    st.session_state.run_analysis = False

if st.session_state.run_analysis:
    raw_data = get_hype_data(niche_focus, brand_filter)
    if raw_data:
        predictions = predict_hype(raw_data, niche_focus)
        
        if predictions:
            st.subheader(f"Top 3 {niche_focus} Predictions")
            
            for i, pred in enumerate(predictions):
                # Calculate local intelligence score for display
                intel = pred['intelligence_signals']
                i_score = calculate_intelligence_score(intel['trend'], intel['influencer'], intel['search_intent'])
                
                with st.container():
                    st.markdown(f"""
                    <div class="prediction-card">
                        <span class="hype-title">#{i+1} {pred['product']}</span>
                        <p><b>Probability:</b> {pred['probability']}%</p>
                        <p><b>Rationale:</b> {pred['rationale']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("Intelligence Score", f"{i_score}x", 
                                  help="Multiplier calculated from Trend Velocity, Influencer Tier, and Search Intent. Higher means a 'cleaner' and more viral signal.")
                    with c2:
                        st.metric("Hype Meter", f"{pred['hype_meter']}/100",
                                  help="Overall intensity of the drop. Calculated by analyzing real-time social buzz, sentiment, and trend velocity.")
                    with c3:
                        st.write("**Success Probability**")
                        st.progress(pred['probability']/100, text=f"{pred['probability']}%")
                        st.caption("Likelihood of an instant sell-out based on demand-supply delta.")
            
            # Aggregate Visualization
            st.markdown("---")
            st.subheader("Hype Landscape Analysis")
            
            # Prepare data for chart
            chart_df = pd.DataFrame([
                {
                    "Product": p['product'], 
                    "Probability": p['probability'], 
                    "Hype": p['hype_meter'],
                    "Search Intent": p['intelligence_signals']['search_intent']
                } for p in predictions
            ])
            
            fig = px.scatter(chart_df, x="Search Intent", y="Hype", size="Probability", 
                             color="Product", title="Hype vs. Search Intent Matrix",
                             hover_name="Product", size_max=60)
            st.plotly_chart(fig, use_container_width=True)

    st.session_state.run_analysis = False
else:
    st.info("👈 Use the Sidebar to trigger a new analysis based on real-time Singapore retail data.")
    
    # Static info section
    st.markdown("""
    ### How it works
    1. **Firecrawl** searches for the latest retail signals, social media buzz, and upcoming drops in Singapore.
    2. **Gemini LLM** analyzes the snippets using business logic from the [Hype Retailer Simulator](https://hype-retailer-simulator-bngud8nqlcbkuj4q8qyuzn.streamlit.app).
    3. **Intelligence Scores** are calculated based on trend velocity, influencer tiers, and search intent.
    4. **Top 3 Predictions** are ranked by their probability of becoming a major "Hype" event.
    """)

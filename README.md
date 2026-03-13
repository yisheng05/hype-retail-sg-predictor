# SG Hype Retail Predictor 👟🔥

**Identifying the next big retail 'Drop' in Singapore using Multi-Agent Intelligence.**

The SG Hype Retail Predictor is a Streamlit application that synthesizes real-time market signals from **Firecrawl** and analyzes them using **Google Gemini** LLM. It applies business logic from the "Hype Retailer Simulator" (Scarcity, Social Velocity, Intelligence Scores) to predict the top 3 most probable retail trends or product drops in Singapore.

---

## 🚀 Key Features

- **Real-Time Signal Scraping**: Uses Firecrawl to scan for upcoming drops, pop-up events, and secondary market trends (StockX, Reddit, News).
- **Hype Intelligence Analysis**: Leverages Gemini 2.0 Flash to calculate Intelligence Scores (I) based on:
    - **Trend Velocity**: TikTok/IG viral potential.
    - **Influencer Tier**: Level of curation.
    - **Search Intent**: Consumer demand signals.
- **Probability Ranking**: Predicts the success likelihood of a "Drop" based on scarcity and social velocity.
- **Interactive Visualizations**: A "Hype vs. Search Intent" matrix to visualize the competitive landscape.

---

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Search/Scraping**: Firecrawl API
- **LLM**: Google Gemini (via LangChain)
- **Data Visualization**: Plotly, Pandas
- **Domain Logic**: Hype Equation (H = (Marketing/Scarcity) * I)

---

## ⚙️ Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd hype-retail-sg-predictor
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Keys**:
   Create a `.env` file:
   ```env
   FIRECRAWL_API_KEY=your_firecrawl_key
   GEMINI_API_KEY=your_gemini_key
   ```

4. **Run the App**:
   ```bash
   streamlit run app.py
   ```

---

## 📊 Logic & Formulae: The "Hype Equation"

The application uses a deterministic model for intelligence scoring combined with a heuristic LLM-driven model for hype and probability.

### 1. Intelligence Score ($I$)
This represents the quality of the signal. It is calculated locally based on three factors identified by the AI:
- **Trend Velocity ($T$):** Low (0.8x) → Explosive (2.5x).
- **Influencer Tier ($Inf$):** Organic (1.0x) → Elite (2.0x).
- **Search Intent ($S$):** A multiplier based on search volume (0-100 index).

$$I = T \times Inf \times (1 + \frac{S}{100})$$

### 2. Hype Meter (0-100)
This represents the intensity of the "Drop." It is synthesized by Gemini by combining:
- **Scarcity Multiplier:** Lower availability (higher index) exponentially increases base hype.
- **Social Velocity:** The frequency and sentiment of mentions in local SG forums/news.
- **The Equation:** $H = \left( \frac{\text{Sentiment Density}}{\text{Scarcity Index}} \right) \times I$

### 3. Success Probability (%)
This is the "Sell-out" likelihood. It measures the delta between **Projected Demand** (derived from $I$) and **Supply** (derived from Scarcity). 
- **>80%:** Guaranteed instant sell-out; high secondary market premium expected.
- **50-80%:** Strong interest; likely to sell out within 24-48 hours.
- **<50%:** Niche appeal; supply likely meets or exceeds demand.

---

*Built for the Singapore Hype Retail Ecosystem.*

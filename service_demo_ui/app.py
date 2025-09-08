import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
import os
from datetime import datetime
from typing import Dict, Any, List
import time

# Page configuration
st.set_page_config(
    page_title="Google Play Review Analyzer",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS stilleri
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(45deg, #f0f2f6, #ffffff);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .fake-review {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
    }
    .interesting-review {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
    }
    .positive-sentiment {
        color: #4caf50;
        font-weight: bold;
    }
    .negative-sentiment {
        color: #f44336;
        font-weight: bold;
    }
    .neutral-sentiment {
        color: #ff9800;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# API URLs - Docker container network için
CORE_ANALYSIS_URL = os.getenv("CORE_ANALYSIS_URL", "http://core-analysis:8000")
EXPORT_URL = os.getenv("EXPORT_URL", "http://export:8000")

class ReviewAnalyzerUI:
    def __init__(self):
        self.setup_session_state()
    
    def setup_session_state(self):
        """Session state'i başlat"""
        if 'analysis_jobs' not in st.session_state:
            st.session_state.analysis_jobs = []
        if 'current_job' not in st.session_state:
            st.session_state.current_job = None
        if 'analysis_results' not in st.session_state:
            st.session_state.analysis_results = None
        if 'reviews_data' not in st.session_state:
            st.session_state.reviews_data = None
    
    def render_header(self):
        """Main header"""
        st.markdown('<h1 class="main-header">Google Play Review Analyzer</h1>', unsafe_allow_html=True)
        st.markdown("---")
    
    def render_sidebar(self):
        """Sidebar panel"""
        with st.sidebar:
            st.header("Analysis Settings")
            
            # App information
            st.subheader("App Information")
            app_id = st.text_input(
                "App ID",
                value="com.whatsapp",
                help="Example: com.whatsapp, com.instagram.android"
            )
            app_name = st.text_input("App Name (optional)", value="")
            
            # Analysis parameters
            st.subheader("Analysis Parameters")
            col1, col2 = st.columns(2)
            with col1:
                country = st.selectbox("Country", ["tr", "us", "gb", "de", "fr"], index=0)
                language = st.selectbox("Language", ["tr", "en", "de", "fr", "es"], index=0)
            with col2:
                count = st.slider("Review Count", 100, 5000, 1000, step=100)
                sort_option = st.selectbox("Sort By", ["newest", "oldest", "most_relevant", "rating"])
            
            # Start analysis button
            if st.button("Start Analysis", type="primary", use_container_width=True):
                self.start_analysis(app_id, app_name, country, language, count, sort_option)
            
            st.markdown("---")
            
            # Current jobs
            st.subheader("Analysis Jobs")
            self.render_job_list()
    
    def start_analysis(self, app_id: str, app_name: str, country: str, language: str, count: int, sort_option: str):
        """Start analysis"""
        try:
            with st.spinner("Starting analysis..."):
                response = requests.post(
                    f"{CORE_ANALYSIS_URL}/api/v1/analyze",
                    json={
                        "app_id": app_id,
                        "app_name": app_name,
                        "country": country,
                        "language": language,
                        "count": count,
                        "sort": sort_option
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    job_id = result["job_id"]
                    st.session_state.current_job = job_id
                    st.success(f"Analysis started! Job ID: {job_id}")
                    st.rerun()
                else:
                    st.error(f"Failed to start analysis: {response.text}")
        
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {str(e)}")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
    
    def render_job_list(self):
        """Show job list"""
        try:
            response = requests.get(f"{CORE_ANALYSIS_URL}/api/v1/jobs", timeout=10)
            if response.status_code == 200:
                jobs = response.json().get("jobs", [])
                
                for job in jobs[:5]:  # Show last 5 jobs
                    status_text = "Completed" if job["status"] == "completed" else "Running" if job["status"] == "running" else "Failed"
                    
                    if st.button(
                        f"[{status_text}] {job['job_id'][:20]}...",
                        key=f"job_{job['job_id']}",
                        use_container_width=True
                    ):
                        st.session_state.current_job = job["job_id"]
                        st.rerun()
        
        except requests.exceptions.RequestException:
            st.warning("Could not load job list")
    
    def render_main_content(self):
        """Ana içerik"""
        if st.session_state.current_job:
            self.render_analysis_results()
        else:
            self.render_welcome_screen()
    
    def render_welcome_screen(self):
        """Welcome screen"""
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            ### Welcome to Google Play Review Analyzer!
            
            This application allows you to analyze reviews of any app on the Google Play Store.
            
            **Features:**
            - **Sentiment Analysis**: Classifies reviews as positive, neutral, and negative
            - **Fake Review Detection**: Detects bot, spam and fake reviews  
            - **Interesting Review Discovery**: Finds humorous, creative and constructive reviews
            - **Data Export**: Download results in CSV and JSON formats
            
            **How to Get Started:**
            1. Enter the app ID in the left panel
            2. Configure analysis parameters
            3. Click "Start Analysis" button
            4. Review and download results
            
            **Example App IDs:**
            - `com.whatsapp` - WhatsApp
            - `com.instagram.android` - Instagram
            - `com.spotify.music` - Spotify
            - `com.netflix.mediaclient` - Netflix
            """)
    
    def render_analysis_results(self):
        """Show analysis results"""
        job_id = st.session_state.current_job
        
        # Load results
        analysis_results = self.load_analysis_results(job_id)
        
        if not analysis_results:
            st.warning("Loading analysis results...")
            time.sleep(2)
            st.rerun()
            return
        
        if analysis_results["status"] == "running":
            st.info("Analysis in progress...")
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
            st.rerun()
            return
        
        if analysis_results["status"] == "failed":
            st.error(f"Analysis failed: {analysis_results.get('error', 'Unknown error')}")
            return
        
        # Show successful analysis results
        self.display_analysis_dashboard(analysis_results)
    
    def load_analysis_results(self, job_id: str) -> Dict[str, Any]:
        """Load analysis results"""
        try:
            response = requests.get(f"{CORE_ANALYSIS_URL}/api/v1/analyze/{job_id}", timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def display_analysis_dashboard(self, results: Dict[str, Any]):
        """Display analysis dashboard"""
        # Title and basic info
        app_info = results.get("app_info", {})
        st.subheader(f"{app_info.get('title', 'Unknown App')} - Analysis Results")
        
        # Top metrics
        self.render_top_metrics(results)
        
        # Tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Overview", 
            "Sentiment Analysis", 
            "Fake Reviews", 
            "Interesting Reviews", 
            "Export Data"
        ])
        
        with tab1:
            self.render_overview_tab(results)
        
        with tab2:
            self.render_sentiment_tab(results)
        
        with tab3:
            self.render_fake_reviews_tab(results)
        
        with tab4:
            self.render_interesting_reviews_tab(results)
        
        with tab5:
            self.render_export_tab(results)
    
    def render_top_metrics(self, results: Dict[str, Any]):
        """Top metric cards"""
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Total Reviews",
                f"{results.get('total_reviews', 0):,}",
                delta=None
            )
        
        with col2:
            sentiment_dist = results.get('sentiment_distribution', {})
            positive_ratio = sentiment_dist.get('positive', 0) / max(results.get('processed_reviews', 1), 1) * 100
            st.metric(
                "Positive Rate",
                f"{positive_ratio:.1f}%",
                delta=f"{sentiment_dist.get('positive', 0)} reviews"
            )
        
        with col3:
            fake_ratio = results.get('fake_reviews_count', 0) / max(results.get('processed_reviews', 1), 1) * 100
            st.metric(
                "Fake Rate",
                f"{fake_ratio:.1f}%",
                delta=f"{results.get('fake_reviews_count', 0)} reviews",
                delta_color="inverse"
            )
        
        with col4:
            interesting_ratio = results.get('interesting_reviews_count', 0) / max(results.get('processed_reviews', 1), 1) * 100
            st.metric(
                "Interesting Rate",
                f"{interesting_ratio:.1f}%",
                delta=f"{results.get('interesting_reviews_count', 0)} reviews"
            )
        
        with col5:
            processing_time = results.get('processing_time', 0)
            st.metric(
                "Processing Time",
                f"{processing_time:.1f}s",
                delta=None
            )
    
    def render_overview_tab(self, results: Dict[str, Any]):
        """Overview tab"""
        col1, col2 = st.columns(2)
        
        with col1:
            # App information
            app_info = results.get("app_info", {})
            st.subheader("App Information")
            
            info_data = {
                "Title": app_info.get("title", "N/A"),
                "App ID": app_info.get("appId", "N/A"),
                "Score": f"{app_info.get('score', 0):.1f}/5.0",
                "Total Ratings": f"{app_info.get('ratings', 0):,}",
                "Installs": app_info.get("installs", "N/A"),
                "Developer": app_info.get("developer", "N/A"),
                "Category": app_info.get("genre", "N/A"),
            }
            
            for key, value in info_data.items():
                st.write(f"**{key}:** {value}")
        
        with col2:
            # Sentiment distribution pie chart
            sentiment_dist = results.get('sentiment_distribution', {})
            if any(sentiment_dist.values()):
                fig = px.pie(
                    values=list(sentiment_dist.values()),
                    names=list(sentiment_dist.keys()),
                    title="Sentiment Distribution",
                    color_discrete_map={
                        'positive': '#4CAF50',
                        'neutral': '#FF9800',
                        'negative': '#F44336'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
    
    def render_sentiment_tab(self, results: Dict[str, Any]):
        """Sentiment analysis tab"""
        st.subheader("Sentiment Analysis Details")
        
        # Load review data
        reviews_data = self.load_reviews_data(results["job_id"])
        
        if reviews_data and len(reviews_data) > 0:
            df = pd.DataFrame(reviews_data)
            
            # Check sentiment column
            if 'sentiment' not in df.columns:
                st.error("Sentiment analysis data not found!")
                st.info("Analysis may not be complete or there may be an issue with the data structure.")
                return
            
            # Sentiment distribution statistics
            sentiment_counts = df['sentiment'].value_counts()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                positive_count = sentiment_counts.get('positive', 0)
                positive_pct = (positive_count / len(df)) * 100
                st.metric("Positive", f"{positive_count}", f"{positive_pct:.1f}%")
            
            with col2:
                neutral_count = sentiment_counts.get('neutral', 0)
                neutral_pct = (neutral_count / len(df)) * 100
                st.metric("Neutral", f"{neutral_count}", f"{neutral_pct:.1f}%")
            
            with col3:
                negative_count = sentiment_counts.get('negative', 0)
                negative_pct = (negative_count / len(df)) * 100
                st.metric("Negative", f"{negative_count}", f"{negative_pct:.1f}%")
            
            # Sentiment distribution bar chart
            if len(sentiment_counts) > 0:
                fig = px.bar(
                    x=sentiment_counts.index,
                    y=sentiment_counts.values,
                    title="Sentiment Distribution",
                    color=sentiment_counts.index,
                    color_discrete_map={
                        'positive': '#4CAF50',
                        'neutral': '#FF9800',
                        'negative': '#F44336'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Rating vs Sentiment analizi
            col1, col2 = st.columns(2)
            
            with col1:
                # Rating distribution
                if "score" in df.columns:
                    rating_counts = df["score"].value_counts().sort_index()
                    fig = px.bar(
                        x=rating_counts.index,
                        y=rating_counts.values,
                        title="Rating Distribution",
                        labels={"x": "Rating", "y": "Review Count"},
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("⚠️ Rating information not available")

            with col2:
                # Sentiment vs Rating heatmap
                if "score" in df.columns and "sentiment" in df.columns:
                    try:
                        crosstab = pd.crosstab(df["score"], df["sentiment"])
                        fig = px.imshow(
                            crosstab.values,
                            x=crosstab.columns,
                            y=crosstab.index,
                            title="Rating vs Sentiment Analysis",
                            color_continuous_scale="Blues",
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.warning(f"⚠️ Could not generate Rating-Sentiment heatmap ({e})")
                else:
                    st.warning("⚠️ Rating or sentiment information not available")

            # Example reviews by sentiment
            st.subheader("📝 Example Reviews")
            for sentiment_type in ["positive", "negative", "neutral"]:
                sentiment_reviews = df[df["sentiment"] == sentiment_type]
                if len(sentiment_reviews) > 0:
                    with st.expander(f"{sentiment_type.title()} Reviews ({len(sentiment_reviews)} found)"):
                        for idx, review in sentiment_reviews.head(3).iterrows():
                            st.write(f"⭐ {review.get('score', 'N/A')}/5 - {review.get('content', '')[:200]}...")
                            st.write("---")
            else:
                st.warning("⚠️ No data found for sentiment analysis!")
                st.info("Analysis may not be complete yet. Please wait a few minutes and try again.")

    
    def render_fake_reviews_tab(self, results: Dict[str, Any]):
        """Fake reviews tab"""
        st.subheader("Fake Review Analysis")
        
        reviews_data = self.load_reviews_data(results["job_id"])
        
        if reviews_data and len(reviews_data) > 0:
            df = pd.DataFrame(reviews_data)
            
            # Check fake review column
            if 'is_fake' not in df.columns:
                st.error("Fake review analysis data not found!")
                st.info("Analysis may not be complete or there may be an issue with the data structure.")
                return
            
            fake_reviews = df[df['is_fake'] == True]
            total_reviews = len(df)
            fake_count = len(fake_reviews)
            fake_ratio = (fake_count / total_reviews * 100) if total_reviews > 0 else 0
            
            # Statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Fake Reviews", fake_count)
            with col2:
                st.metric("Fake Rate", f"{fake_ratio:.1f}%")
            with col3:
                genuine_count = total_reviews - fake_count
                st.metric("Genuine Reviews", genuine_count)
            
            if fake_count > 0:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader("🚨 Detected Fake Reviews")

                    # Show fake reviews
                    for idx, review in fake_reviews.head(10).iterrows():
                        with st.expander(f"Fake Review #{idx + 1} - Rating: {review.get('score', 'N/A')}/5"):
                            st.markdown('<div class="fake-review">', unsafe_allow_html=True)
                            st.write(f"**User:** {review.get('userName', 'Anonymous')}")
                            st.write(f"**Content:** {review.get('content', '')[:300]}...")
                            st.write(f"**Sentiment:** {review.get('sentiment', 'unknown')}")
                            st.write(f"**Likes:** {review.get('thumbsUpCount', 0)}")
                            if review.get('at'):
                                st.write(f"**Date:** {review.get('at', '')[:10]}")
                            st.markdown('</div>', unsafe_allow_html=True)

                    if fake_count > 10:
                        st.info(f"💡 A total of {fake_count} fake reviews detected. Showing the first 10.")

                with col2:
                    # Sentiment distribution of fake reviews
                    if "sentiment" in df.columns:
                        fake_by_sentiment = fake_reviews["sentiment"].value_counts()
                        if len(fake_by_sentiment) > 0:
                            fig = px.pie(
                                values=fake_by_sentiment.values,
                                names=fake_by_sentiment.index,
                                title="Sentiment Distribution of Fake Reviews",
                                color_discrete_map={
                                    "positive": "#4CAF50",
                                    "neutral": "#FF9800",
                                    "negative": "#F44336",
                                },
                            )
                            st.plotly_chart(fig, use_container_width=True)

                    # Rating distribution of fake reviews
                    if "score" in df.columns:
                        fake_by_rating = fake_reviews["score"].value_counts().sort_index()
                        if len(fake_by_rating) > 0:
                            fig = px.bar(
                                x=fake_by_rating.index,
                                y=fake_by_rating.values,
                                title="Rating Distribution of Fake Reviews",
                                labels={"x": "Rating", "y": "Count"},
                            )
                            st.plotly_chart(fig, use_container_width=True)

                else:
                    st.success("🎉 No fake reviews detected!")
                    st.info("This app's reviews seem to be written by real users.")

                    # Analysis details
                    st.subheader("📈 Analysis Details")
                    st.write(f"✅ **Total reviews analyzed:** {total_reviews}")
                    st.write("✅ **Fake review detection:** Successful")
                    st.write("✅ **Reliability:** High")

                # If no data is available
                if not reviews_data or len(reviews_data) == 0:
                    st.warning("⚠️ No data available for fake review analysis!")
                    st.info("The analysis may not have finished yet. Please wait a few minutes and try again.")

    
    def render_interesting_reviews_tab(self, results: Dict[str, Any]):
        """Interesting Reviews Tab"""
        st.subheader("⭐ Interesting Review Analysis")

        reviews_data = self.load_reviews_data(results["job_id"])

        if reviews_data and len(reviews_data) > 0:
            df = pd.DataFrame(reviews_data)

            # Check if column exists
            if "is_interesting" not in df.columns:
                st.error("❌ No interesting review analysis data found!")
                st.info("The analysis may not have finished yet or the data structure has an issue.")
                return

            interesting_reviews = df[df["is_interesting"] == True]
            total_reviews = len(df)
            interesting_count = len(interesting_reviews)
            interesting_ratio = (interesting_count / total_reviews * 100) if total_reviews > 0 else 0

            # Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("⭐ Interesting Reviews", interesting_count)
            with col2:
                st.metric("📊 Interesting Ratio", f"{interesting_ratio:.1f}%")
            with col3:
                normal_count = total_reviews - interesting_count
                st.metric("📝 Normal Reviews", normal_count)

            if interesting_count > 0:
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.subheader("✨ Detected Interesting Reviews")

                    # Show reviews
                    for idx, review in interesting_reviews.head(10).iterrows():
                        with st.expander(f"Interesting Review #{idx + 1} - Rating: {review.get('score', 'N/A')}/5"):
                            st.markdown('<div class="interesting-review">', unsafe_allow_html=True)
                            st.write(f"**User:** {review.get('userName', 'Anonymous')}")
                            st.write(f"**Content:** {review.get('content', '')}")
                            st.write(f"**Sentiment:** {review.get('sentiment', 'unknown')}")
                            st.write(f"**Likes:** {review.get('thumbsUpCount', 0)}")
                            if review.get("at"):
                                st.write(f"**Date:** {review.get('at', '')[:10]}")
                            st.markdown('</div>', unsafe_allow_html=True)

                    if interesting_count > 10:
                        st.info(f"💡 A total of {interesting_count} interesting reviews detected. Showing the first 10.")

                with col2:
                    # Sentiment distribution of interesting reviews
                    if "sentiment" in df.columns:
                        interesting_by_sentiment = interesting_reviews["sentiment"].value_counts()
                        if len(interesting_by_sentiment) > 0:
                            fig = px.pie(
                                values=interesting_by_sentiment.values,
                                names=interesting_by_sentiment.index,
                                title="Sentiment Distribution of Interesting Reviews",
                                color_discrete_map={
                                    "positive": "#4CAF50",
                                    "neutral": "#FF9800",
                                    "negative": "#F44336",
                                },
                            )
                            st.plotly_chart(fig, use_container_width=True)

                    # Rating distribution of interesting reviews
                    if "score" in df.columns:
                        interesting_by_rating = interesting_reviews["score"].value_counts().sort_index()
                        if len(interesting_by_rating) > 0:
                            fig = px.bar(
                                x=interesting_by_rating.index,
                                y=interesting_by_rating.values,
                                title="Rating Distribution of Interesting Reviews",
                                labels={"x": "Rating", "y": "Count"},
                            )
                            st.plotly_chart(fig, use_container_width=True)

                    # Top liked interesting reviews
                    if "thumbsUpCount" in df.columns:
                        top_liked = interesting_reviews.nlargest(5, "thumbsUpCount")
                        if len(top_liked) > 0:
                            st.subheader("👍 Top Liked Interesting Reviews")
                            for idx, review in top_liked.iterrows():
                                st.write(
                                    f"**{review.get('thumbsUpCount', 0)} likes** - "
                                    f"{review.get('content', '')[:100]}..."
                                )
            else:
                st.info("🔍 No interesting reviews detected for this analysis.")
                st.write("This might mean:")
                st.write("- Most reviews contain standard expressions")
                st.write("- Few humorous or creative reviews")
                st.write("- Limited detailed feedback")

                # Analysis details
                st.subheader("📈 Analysis Details")
                st.write(f"✅ **Total reviews analyzed:** {total_reviews}")
                st.write("✅ **Interesting review detection:** Completed")
                st.write("ℹ️ **Note:** Interesting review criteria include humor, creativity, detailed feedback")
        else:
            st.warning("⚠️ No data found for interesting review analysis!")
            st.info("The analysis may not have finished yet. Please wait a few minutes and try again.")

    
    def render_export_tab(self, results: Dict[str, Any]):
        """Export tab for downloading analysis results"""
        st.subheader("📥 Data Export")

        col1, col2 = st.columns(2)

        with col1:
            st.write("### Export Settings")

            export_format = st.selectbox("Format", ["csv", "json", "both"])
            include_fake = st.checkbox("Include fake reviews", value=True)
            include_interesting_only = st.checkbox("Only interesting reviews", value=False)

            if st.button("📥 Export Data", type="primary"):
                self.export_data(
                    results["job_id"],
                    export_format,
                    include_fake,
                    include_interesting_only,
                )

        with col2:
            st.write("### Available Export Files")
            self.show_export_files()

    
    def export_data(self, job_id: str, format: str, include_fake: bool, include_interesting_only: bool):
        
        try:
            with st.spinner("Being exported..."):
                # Önce export servisini dene
                try:
                    health_response = requests.get(f"{EXPORT_URL}/health", timeout=5)
                    if health_response.status_code == 200:
                        # Export servisi çalışıyor, API'yi kullan
                        response = requests.post(
                            f"{EXPORT_URL}/api/v1/export",
                            json={
                                "job_id": job_id,
                                "format": format,
                                "include_fake": include_fake,
                                "include_interesting_only": include_interesting_only
                            },
                            timeout=60
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success("✅ Export successful!")
                            
                            if result.get("download_url"):
                                st.markdown(f"[📥 Folder Download]({EXPORT_URL}{result['download_url']})")
                            
                            # Mevcut export dosyalarını yenile
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ Export faild: {response.text}")
                        return
                except:
                    pass
                
                # Export servisi çalışmıyorsa, local export yap
                st.info("🔄 Export service not found, local export is being performed...")
                
                # Veriyi yükle
                reviews_data = self.load_reviews_data(job_id)
                if not reviews_data:
                    st.error("❌ No data found for export!")
                    return
                
                df = pd.DataFrame(reviews_data)
                
                # Filtreleme
                if include_interesting_only:
                    df = df[df['is_interesting'] == True]
                
                if not include_fake:
                    df = df[df['is_fake'] == False]
                
                # Export klasörünü oluştur - Docker container öncelikli
                if os.path.exists("/app/exports"):
                    exports_dir = "/app/exports"  # Docker container path
                else:
                    current_dir = os.path.dirname(__file__)
                    project_root = os.path.dirname(current_dir)
                    exports_dir = os.path.join(project_root, "exports")  # Local development
                os.makedirs(exports_dir, exist_ok=True)
                
                # Dosya adı oluştur
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                created_files = []
                
                if format in ["csv", "both"]:
                    csv_filename = f"reviews_{job_id}_{timestamp}.csv"
                    csv_path = os.path.join(exports_dir, csv_filename)
                    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                    st.success(f"✅ A CSV file has been created.: {csv_filename}")
                    created_files.append(('csv', csv_path, csv_filename))
                
                if format in ["json", "both"]:
                    json_filename = f"reviews_{job_id}_{timestamp}.json"
                    json_path = os.path.join(exports_dir, json_filename)
                    df.to_json(json_path, orient='records', ensure_ascii=False, indent=2)
                    st.success(f"✅ A JSON file has been created.: {json_filename}")
                    created_files.append(('json', json_path, json_filename))
                
                st.info(f"📊 {len(df)} comment exported.")
                
                # Oluşturulan dosyaları hemen indirme seçeneği sun
                st.subheader("📥 Created Files")
                for file_type, file_path, filename in created_files:
                    try:
                        with open(file_path, 'rb') as f:
                            file_data = f.read()
                            st.download_button(
                                label=f"📥 {filename} İndir",
                                data=file_data,
                                file_name=filename,
                                mime="text/csv" if file_type == 'csv' else "application/json",
                                key=f"download_new_{filename}"
                            )
                    except Exception as e:
                        st.error(f"File read error: {str(e)}")
                
                time.sleep(2)
                st.rerun()
        
        except Exception as e:
            st.error(f"❌ Export failed: {str(e)}")
    
    def show_export_files(self):
        """Export dosyalarını göster"""
        try:
            # Exports klasörünü kontrol et - Docker container öncelikli
            if os.path.exists("/app/exports"):
                exports_dir = "/app/exports"  # Docker container path
            else:
                current_dir = os.path.dirname(__file__)
                project_root = os.path.dirname(current_dir)
                exports_dir = os.path.join(project_root, "exports")  # Local development
            
            if os.path.exists(exports_dir):
                export_files = []
                for filename in os.listdir(exports_dir):
                    if filename.endswith(('.csv', '.json')):
                        file_path = os.path.join(exports_dir, filename)
                        if os.path.exists(file_path):
                            file_stats = os.stat(file_path)
                            export_files.append({
                                'filename': filename,
                                'size': file_stats.st_size,
                                'modified': datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M'),
                                'path': file_path
                            })
                
                # En son değiştirilen dosyaları önce göster
                export_files.sort(key=lambda x: x['modified'], reverse=True)
                
                if export_files:
                    st.write("📁 **Current Export Files:**")
                    
                    for file in export_files[:10]:
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"📄 **{file['filename']}**")
                            st.write(f"   📏 Size: {file['size']:,} bytes")
                            st.write(f"   📅 Date: {file['modified']}")
                        
                        with col2:
                            # Download butonu
                            try:
                                with open(file['path'], 'rb') as f:
                                    file_data = f.read()
                                    
                                # MIME type belirleme
                                mime_type = "text/csv" if file['filename'].endswith('.csv') else "application/json"
                                
                                st.download_button(
                                    label="📥 Download",
                                    data=file_data,
                                    file_name=file['filename'],
                                    mime=mime_type,
                                    key=f"download_existing_{file['filename']}",
                                    use_container_width=True
                                )
                            except Exception as e:
                                st.error(f"❌ File read error: {str(e)}")
                        
                        st.write("---")
                else:
                    st.info("💡 No files have been exported yet. You can create new files using the ‘Export’ button above..")
            else:
                st.warning("⚠️ The Exports folder could not be found. It will be created automatically during your first export operation..")
                
        except Exception as e:
            st.error(f"❌Error while loading export files: {str(e)}")
            st.info("Please ensure that the exports folder exists and is accessible.")
    
    def load_reviews_data(self, job_id: str) -> List[Dict[str, Any]]:
        CSV dosyası oluşturuldu
        try:
            # Debug: Mevcut çalışma dizinini göster
            current_dir = os.path.dirname(__file__)
            project_root = os.path.dirname(current_dir)
            
            # Farklı dosya yollarını dene - Docker container öncelikli
            possible_paths = [
                f"/app/shared_data/reviews_{job_id}.json",  # Docker container path
                os.path.join(project_root, "shared_data", f"reviews_{job_id}.json"),  # Local development
                f"../shared_data/reviews_{job_id}.json",
                f"./shared_data/reviews_{job_id}.json",
                os.path.join(os.getcwd(), "shared_data", f"reviews_{job_id}.json"),
                os.path.abspath(f"shared_data/reviews_{job_id}.json")
            ]
            
            # Her yolu kontrol et
            for path in possible_paths:
                if os.path.exists(path):
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            st.success(f"✅ {len(data)} Comment data loaded! (Path: {os.path.basename(path)})")
                            return data
                    except Exception as e:
                        st.error(f"❌ File read error ({path}): {str(e)}")
                        continue
            
            # Dosya bulunamadı, debug bilgisi göster
            st.warning(f"⚠️ No comment data found: reviews_{job_id}.json")
            
            with st.expander("🔍 Debug Information"):
                st.write("**Required file paths:**")
                for i, path in enumerate(possible_paths, 1):
                    exists = "✅" if os.path.exists(path) else "❌"
                    st.write(f"{i}. {exists} `{path}`")
                
                st.write("**Current working directory:**")
                st.code(os.getcwd())
                
                
                shared_data_path = os.path.join(project_root, "shared_data")
                if os.path.exists(shared_data_path):
                    files = [f for f in os.listdir(shared_data_path) if f.startswith("reviews_")]
                    if files:
                        for file in sorted(files):
                            st.write(f"- {file}")
                    else:
                        st.write("No reviews file found.")
                else:
                    st.write("The shared_data folder could not be found.!")
            
            return None
            
        except Exception as e:
            st.error(f"❌ Data loading error: {str(e)}")
            return None
    
    def run(self):
        """Ana uygulamayı çalıştır"""
        self.render_header()
        self.render_sidebar()
        self.render_main_content()

# Ana uygulama
if __name__ == "__main__":
    app = ReviewAnalyzerUI()
    app.run()

# app/main.py - Yorùbá Spelling Corrector Web Application
import streamlit as st
import os
import sys
import time
from typing import List, Dict, Tuple
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Add parent directory to path to import correctors
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from correctors.base_corrector import YorubaSpellingCorrector
    from correctors.tonal_corrector import EnhancedYorubaSpellingCorrector
    from evaluation.evaluator import YorubaSpellingEvaluator
    from evaluation.test_generator import YorubaTestGenerator
except ImportError as e:
    st.error(f"❌ Import error: {e}")
    st.stop()

class YorubaSpellingApp:
    def __init__(self):
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_file_dir)  # This goes from app/ to root
        self.lexicon_path = os.path.join(root_dir, "data", "yoruba_lexicon.txt")
       
    def setup_correctors(self):
        """Initialize the spelling correctors."""
        try:
            self.basic_corrector = YorubaSpellingCorrector(self.lexicon_path)
            self.enhanced_corrector = EnhancedYorubaSpellingCorrector(self.lexicon_path)
            return True
        except Exception as e:
            st.error(f"❌ Failed to initialize correctors: {e}")
            return False
    
    def run(self):
        """Run the main application."""
        self.setup_page()
        
        # Sidebar navigation
        page = st.sidebar.selectbox(
            "Navigate to:",
            ["🏠 Home", "✍️ Text Correction", "📊 Performance", "📚 Learning", "ℹ️ About"]
        )
        
        # Page routing
        if page == "🏠 Home":
            self.home_page()
        elif page == "✍️ Text Correction":
            self.correction_page()
        elif page == "📊 Performance":
            self.performance_page()
        elif page == "📚 Learning":
            self.learning_page()
        elif page == "ℹ️ About":
            self.about_page()
    
    def setup_page(self):
        """Configure the Streamlit page."""
        st.set_page_config(
            page_title="Yorùbá Spelling Corrector",
            page_icon="📝",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS
        st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
        }
        .yoruba-text {
            font-size: 1.2rem;
            line-height: 1.6;
        }
        .correction-result {
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        .correct {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
        }
        .incorrect {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def home_page(self):
        """Display the home page."""
        st.markdown('<h1 class="main-header">📝 Yorùbá Spelling Corrector</h1>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            ## 🎯 Welcome to the Yorùbá Spelling Correction System
            
            This intelligent application helps you write correct Yorùbá text by:
            
            - ✅ **Correcting spelling errors** in Yorùbá text
            - 🎵 **Restoring proper diacritics** and tone marks  
            - 📚 **Supporting multiple contexts** (educational, conversational, literary)
            - 🧠 **Using advanced algorithms** with tonal disambiguation
            
            ### 🚀 Quick Start:
            1. Go to **✍️ Text Correction** to correct your Yorùbá text
            2. Visit **📚 Learning** to understand common errors
            3. Check **📊 Performance** to see system accuracy
            """)
        
        with col2:
            st.image("https://via.placeholder.com/300x200/1f77b4/ffffff?text=Yoruba+AI", 
                    caption="Yorùbá Language Technology")
            
            st.info("""
            **Did you know?**
            Yorùbá has three tone marks:
            - **Dò** (low): à, è, ì, ò, ù
            - **Mí** (high): á, é, í, ó, ú  
            - **Rẹ** (mid): a, e, i, o, u
            """)
        
        # Quick correction demo
        st.markdown("---")
        st.subheader("🎮 Quick Demo")
        
        demo_text = st.text_input("Try a quick correction:", "mo fe ka iwe yoruba")
        
        if demo_text:
            with st.spinner("Correcting..."):
                basic_result = self.basic_corrector.correct_text(demo_text)
                enhanced_result = self.enhanced_corrector.correct_text_with_context(demo_text)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Basic Correction:**")
                st.code(basic_result, language="text")
            
            with col2:
                st.write("**Enhanced Correction:**")
                st.code(enhanced_result, language="text")
    
    def correction_page(self):
        """Display the text correction interface."""
        st.header("✍️ Yorùbá Text Correction")
        
        # Correction mode selection
        col1, col2 = st.columns([2, 1])
        
        with col1:
            input_method = st.radio(
                "Input method:",
                ["📝 Enter text", "📁 Upload file"]
            )
        
        with col2:
            correction_mode = st.selectbox(
                "Correction mode:",
                ["🧠 Enhanced (Context-aware)", "⚡ Basic (Fast)"]
            )
        
        # Text input area
        if input_method == "📝 Enter text":
            user_text = st.text_area(
                "Enter Yorùbá text to correct:",
                height=150,
                placeholder="Type your Yorùbá text here...\nExample: 'mo fe ka iwe yoruba'"
            )
        else:
            uploaded_file = st.file_uploader("Upload text file", type=['txt'])
            if uploaded_file:
                user_text = uploaded_file.getvalue().decode("utf-8")
            else:
                user_text = ""
        
        # Correction options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            show_suggestions = st.checkbox("Show word suggestions", value=True)
        
        with col2:
            highlight_changes = st.checkbox("Highlight changes", value=True)
        
        with col3:
            if st.button("🔄 Correct Text", type="primary"):
                if user_text:
                    self.process_correction(user_text, correction_mode, show_suggestions, highlight_changes)
                else:
                    st.warning("Please enter some text to correct.")
    
    def process_correction(self, text: str, mode: str, show_suggestions: bool, highlight_changes: bool):
        """Process text correction and display results."""
        with st.spinner("🔄 Correcting text..."):
            start_time = time.time()
            
            if "Enhanced" in mode:
                corrected_text = self.enhanced_corrector.correct_text_with_context(text)
                corrector_name = "Enhanced Corrector"
            else:
                corrected_text = self.basic_corrector.correct_text(text)
                corrector_name = "Basic Corrector"
            
            processing_time = time.time() - start_time
        
        # Display results
        st.success(f"✅ Correction completed in {processing_time:.2f}s using {corrector_name}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📥 Original Text")
            st.text_area("", text, height=150, key="original")
        
        with col2:
            st.subheader("📤 Corrected Text")
            st.text_area("", corrected_text, height=150, key="corrected")
        
        # Show detailed analysis
        if show_suggestions:
            self.show_word_analysis(text, corrected_text)
        
        # Show changes highlighted
        if highlight_changes and text != corrected_text:
            self.show_changes(text, corrected_text)
    
    def show_word_analysis(self, original: str, corrected: str):
        """Show detailed word-by-word analysis."""
        st.subheader("🔍 Word Analysis")
        
        original_words = original.split()
        corrected_words = corrected.split()
        
        analysis_data = []
        
        for i, (orig, corr) in enumerate(zip(original_words, corrected_words)):
            status = "✅ Correct" if orig == corr else "🔄 Corrected"
            analysis_data.append({
                "Word #": i + 1,
                "Original": orig,
                "Corrected": corr,
                "Status": status,
                "Suggestions": self.get_suggestions(orig) if orig != corr else "No change needed"
            })
        
        if analysis_data:
            df = pd.DataFrame(analysis_data)
            st.dataframe(df, use_container_width=True)
    
    def get_suggestions(self, word: str) -> str:
        """Get correction suggestions for a word."""
        matches = self.enhanced_corrector.find_closest_matches(word, max_matches=3)
        return ", ".join(matches) if matches else "No suggestions"
    
    def show_changes(self, original: str, corrected: str):
        """Show text with changes highlighted."""
        st.subheader("🎨 Changes Highlighted")
        
        # Simple diff visualization
        orig_words = original.split()
        corr_words = corrected.split()
        
        html_output = "<div class='yoruba-text'>"
        
        for i in range(max(len(orig_words), len(corr_words))):
            if i < len(orig_words) and i < len(corr_words):
                if orig_words[i] != corr_words[i]:
                    html_output += f"<del style='color: red'>{orig_words[i]}</del> "
                    html_output += f"<ins style='color: green'>{corr_words[i]}</ins> "
                else:
                    html_output += f"{orig_words[i]} "
            elif i < len(orig_words):
                html_output += f"<del style='color: red'>{orig_words[i]}</del> "
            else:
                html_output += f"<ins style='color: green'>{corr_words[i]}</ins> "
        
        html_output += "</div>"
        st.markdown(html_output, unsafe_allow_html=True)
    
    def performance_page(self):
        """Display system performance metrics."""
        st.header("📊 System Performance")
        
        if st.button("🔄 Run Performance Evaluation"):
            with st.spinner("Running comprehensive evaluation..."):
                try:
                    evaluator = YorubaSpellingEvaluator(self.lexicon_path)
                    results = evaluator.run_complete_evaluation()
                    
                    if results:
                        self.display_performance_results(results)
                    else:
                        st.error("Evaluation failed to produce results.")
                
                except Exception as e:
                    st.error(f"Evaluation error: {e}")
        else:
            st.info("Click the button above to run performance evaluation")
            
            # Show sample performance data
            self.display_sample_performance()
    
    def display_performance_results(self, results: Dict):
        """Display performance evaluation results."""
        basic = results['basic_results']['overall']
        enhanced = results['enhanced_results']['overall']
        
        # Overall metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Accuracy", f"{enhanced['accuracy']:.1%}", 
                     f"{(enhanced['accuracy'] - basic['accuracy']):.1%}")
        
        with col2:
            st.metric("F1 Score", f"{enhanced['f1_score']:.1%}",
                     f"{(enhanced['f1_score'] - basic['f1_score']):.1%}")
        
        with col3:
            st.metric("Processing Time", f"{enhanced['avg_processing_time']:.3f}s",
                     f"{(enhanced['avg_processing_time'] - basic['avg_processing_time']):.3f}s")
        
        with col4:
            improvement = enhanced['accuracy'] - basic['accuracy']
            st.metric("Improvement", f"{improvement:.1%}")
        
        # Context performance chart
        self.create_performance_chart(results)
        
        # Detailed results
        st.subheader("Detailed Results")
        st.json(results['basic_results'])
    
    def display_sample_performance(self):
        """Display sample performance data for demonstration."""
        st.warning("Showing sample data. Run evaluation for actual results.")
        
        sample_data = {
            'Context': ['Educational', 'Conversational', 'Literary', 'Overall'],
            'Basic Accuracy': [0.75, 0.68, 0.72, 0.72],
            'Enhanced Accuracy': [0.88, 0.82, 0.85, 0.85]
        }
        
        df = pd.DataFrame(sample_data)
        
        fig = px.bar(df, x='Context', y=['Basic Accuracy', 'Enhanced Accuracy'],
                    title="Sample Performance by Context",
                    barmode='group')
        
        st.plotly_chart(fig, use_container_width=True)
    
    def create_performance_chart(self, results: Dict):
        """Create performance visualization charts."""
        contexts = ['educational', 'conversational', 'literary']
        
        basic_acc = [results['basic_results'][ctx]['accuracy'] for ctx in contexts]
        enhanced_acc = [results['enhanced_results'][ctx]['accuracy'] for ctx in contexts]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Basic Corrector',
            x=[ctx.capitalize() for ctx in contexts],
            y=basic_acc,
            marker_color='lightblue'
        ))
        
        fig.add_trace(go.Bar(
            name='Enhanced Corrector',
            x=[ctx.capitalize() for ctx in contexts],
            y=enhanced_acc,
            marker_color='royalblue'
        ))
        
        fig.update_layout(
            title="Accuracy by Context",
            xaxis_title="Context",
            yaxis_title="Accuracy",
            yaxis_tickformat=".0%",
            barmode='group'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def learning_page(self):
        """Display educational content about Yorùbá spelling."""
        st.header("📚 Learning Yorùbá Spelling")
        
        tab1, tab2, tab3, tab4 = st.tabs(["🎵 Diacritics", "📝 Common Errors", "🧪 Practice", "📖 Resources"])
        
        with tab1:
            st.subheader("Yorùbá Diacritics Guide")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                ### Tone Marks
                - **Dò** (Low): à, è, ì, ò, ù
                - **Mí** (High): á, é, í, ó, ú
                - **Rẹ** (Mid): a, e, i, o, u
                
                ### Dot Under Letters
                - **ṣ** - 'sh' sound
                - **ẹ** - open 'e' sound  
                - **ọ** - open 'o' sound
                """)
            
            with col2:
                st.markdown("""
                ### Examples
                - **ọmọ** (child) vs omo
                - **ilé** (house) vs ile
                - **ṣe** (do) vs se
                - **àwọn** (they) vs awon
                
                ### Importance
                Correct diacritics change meaning:
                - **oko** (husband) vs **ọkọ** (vehicle)
                - **igba** (200) vs **ìgbà** (time)
                """)
        
        with tab2:
            st.subheader("Common Spelling Errors")
            
            common_errors = [
                {"Error": "omo", "Correct": "ọmọ", "Meaning": "child"},
                {"Error": "ile", "Correct": "ilé", "Meaning": "house"},
                {"Error": "se", "Correct": "ṣe", "Meaning": "do"},
                {"Error": "awon", "Correct": "àwọn", "Meaning": "they"},
                {"Error": "yoruba", "Correct": "Yorùbá", "Meaning": "Yoruba people"},
            ]
            
            st.table(common_errors)
        
        with tab3:
            st.subheader("Practice Exercises")
            
            exercises = [
                {"Exercise": "Correct: 'mo fe ka iwe'", "Answer": "mo fẹ́ kàwé"},
                {"Exercise": "Correct: 'awa omo ile'", "Answer": "àwọn ọmọ ilé"},
                {"Exercise": "Correct: 'ise yin dun'", "Answer": "iṣẹ́ yín dùn"},
            ]
            
            for i, ex in enumerate(exercises, 1):
                with st.expander(f"Exercise {i}: {ex['Exercise']}"):
                    st.write(f"**Answer:** {ex['Answer']}")
        
        with tab4:
            st.subheader("Learning Resources")
            st.markdown("""
            - [Yorùbá Dictionary](https://yorubadictionary.com)
            - [Yorùbá Orthography Guide](https://www.omniglot.com/writing/yoruba.htm)
            - [Yorùbá Language Learning](https://www.memrise.com/courses/english/yoruba/)
            """)
    
    def about_page(self):
        """Display information about the project."""
        st.header("ℹ️ About This Project")
        
        st.markdown("""
        ## Yorùbá Spelling Corrector
        
        ### 🎯 Research Objectives
        This project addresses Objective 5 of a comprehensive research study on Yorùbá computational linguistics:
        
        **Objective 5:** Develop a user-friendly application that demonstrates the functionality of the corrector.
        
        ### 🧠 Technical Approach
        - **Hybrid System**: Combines rule-based and statistical methods
        - **Tonal Disambiguation**: Advanced algorithms for Yorùbá tone marks
        - **Context Awareness**: Uses surrounding words for better corrections
        - **Comprehensive Lexicon**: Based on extensive Yorùbá language data
        
        ### 🛠️ Technology Stack
        - **Python** with Streamlit for the web interface
        - **Custom NLP algorithms** for Yorùbá language processing
        - **Machine Learning** for contextual understanding
        - **Evaluation Framework** for performance measurement
        
        ### 📊 Research Context
        This application is part of a larger research project that includes:
        - Lexicon development and curation
        - Algorithm design and optimization  
        - Comprehensive evaluation across multiple contexts
        - User-friendly application development
        
        ### 👨‍💻 Development
        Built with ❤️ for the Yorùbá language community.
        """)

def main():
    """Main function to run the Streamlit app."""
    app = YorubaSpellingApp()
    if app.setup_correctors():
        app.run()
    else:
        st.error("Failed to initialize the application. Please check your setup.")

if __name__ == "__main__":
    main()
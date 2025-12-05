# app/main.py - Yorùbá Spelling Corrector Web Application (Minimal Version)
import streamlit as st
import os
import sys
import time
import pandas as pd

# Add parent directory to path to import correctors
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from correctors.base_corrector import YorubaSpellingCorrector
    from correctors.tonal_corrector import EnhancedYorubaSpellingCorrector
except ImportError as e:
    st.error(f"❌ Import error: {e}")
    st.stop()

class YorubaSpellingApp:
    def __init__(self):
        self.lexicon_path = "data/yoruba_lexicon.txt"
        self.setup_correctors()
    
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
            ["🏠 Home", "✍️ Text Correction", "📚 Learning", "ℹ️ About"]
        )
        
        # Page routing
        if page == "🏠 Home":
            self.home_page()
        elif page == "✍️ Text Correction":
            self.correction_page()
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
    
    def home_page(self):
        """Display the home page."""
        st.title("📝 Yorùbá Spelling Corrector")
        
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
            """)
        
        with col2:
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
        
        # Text input area
        user_text = st.text_area(
            "Enter Yorùbá text to correct:",
            height=150,
            placeholder="Type your Yorùbá text here...\nExample: 'mo fe ka iwe yoruba'"
        )
        
        # Correction options
        col1, col2 = st.columns(2)
        
        with col1:
            correction_mode = st.selectbox(
                "Correction mode:",
                ["🧠 Enhanced (Context-aware)", "⚡ Basic (Fast)"]
            )
        
        with col2:
            show_analysis = st.checkbox("Show word analysis", value=True)
        
        if st.button("🔄 Correct Text", type="primary"):
            if user_text:
                self.process_correction(user_text, correction_mode, show_analysis)
            else:
                st.warning("Please enter some text to correct.")
    
    def process_correction(self, text: str, mode: str, show_analysis: bool):
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
            st.text_area("", text, height=150, key="original", label_visibility="collapsed")
        
        with col2:
            st.subheader("📤 Corrected Text")
            st.text_area("", corrected_text, height=150, key="corrected", label_visibility="collapsed")
        
        # Show detailed analysis
        if show_analysis and text != corrected_text:
            self.show_word_analysis(text, corrected_text)
    
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
    
    def learning_page(self):
        """Display educational content about Yorùbá spelling."""
        st.header("📚 Learning Yorùbá Spelling")
        
        tab1, tab2 = st.tabs(["🎵 Diacritics Guide", "📝 Common Errors"])
        
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
                {"Error": "fe", "Correct": "fẹ́", "Meaning": "want"},
                {"Error": "ka iwe", "Correct": "kàwé", "Meaning": "read"},
            ]
            
            st.table(common_errors)
    
    def about_page(self):
        """Display information about the project."""
        st.header("ℹ️ About This Project")
        
        st.markdown("""
        ## Yorùbá Spelling Corrector
        
        ### 🎯 Research Objectives
        This project addresses **Objective 5** of a comprehensive research study on Yorùbá computational linguistics:
        
        **Objective 5:** Develop a user-friendly application that demonstrates the functionality of the corrector.
        
        ### 🧠 Technical Approach
        - **Hybrid System**: Combines rule-based and statistical methods
        - **Tonal Disambiguation**: Advanced algorithms for Yorùbá tone marks
        - **Context Awareness**: Uses surrounding words for better corrections
        - **Comprehensive Lexicon**: Based on extensive Yorùbá language data
        
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
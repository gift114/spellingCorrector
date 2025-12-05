import os
import sys
import time
import uuid
import streamlit as st
import pandas as pd

# adjust path so correctors package is importable
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(CURRENT_DIR)
sys.path.append(ROOT)

from correctors.lexicon_corrector import LexiconIntegratedCorrector
from correctors.base_corrector import YorubaSpellingCorrector
from correctors.tonal_corrector import EnhancedYorubaSpellingCorrector

st.set_page_config(page_title="Yorùbá Spelling Corrector", page_icon="📝", layout="wide")


@st.cache_resource
def get_basic_corrector(lexicon_path, corpus_path=None):
    return LexiconIntegratedCorrector(lexicon_path, corpus_path=corpus_path)


@st.cache_resource
def get_enhanced_corrector(lexicon_path):
    return EnhancedYorubaSpellingCorrector(lexicon_path)


class YorubaSpellingApp:
    def __init__(self):
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_file_dir)
        self.lexicon_path = os.path.join(root_dir, "data", "yoruba_lexicon.txt")
        corpus_candidate = os.path.join(root_dir, "data", "yoruba_corpus.txt")
        self.corpus_path = corpus_candidate if os.path.exists(corpus_candidate) else None

    def run(self):
        st.title("📝 Yorùbá Spelling Corrector")

        # Initialize correctors
        with st.spinner("Initializing correctors..."):
            try:
                self.basic_corrector = get_basic_corrector(
                    self.lexicon_path,
                    corpus_path=self.corpus_path
                )
                self.enhanced_corrector = get_enhanced_corrector(self.lexicon_path)
            except Exception as e:
                st.error(f"Failed to initialize correctors: {e}")
                st.stop()

        # Sidebar page navigation
        page = st.sidebar.selectbox(
            "Navigate to:",
            ["🏠 Home", "✍️ Text Correction", "📚 Learning", "ℹ️ About"]
        )

        if page == "🏠 Home":
            self.home_page()
        elif page == "✍️ Text Correction":
            self.correction_page()
        elif page == "📚 Learning":
            self.learning_page()
        elif page == "ℹ️ About":
            self.about_page()

    def home_page(self):

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("""
            ## 🎯 Welcome to the Yorùbá Spelling Correction System

            This intelligent application helps you write correct Yorùbá text by:

            - ✅ Correcting spelling errors in Yorùbá text  
            - 🎵 Restoring proper diacritics and tone marks  
            - 📚 Supporting multiple contexts like education, conversation, and literature  
            - 🧠 Using advanced algorithms with tonal disambiguation

            ### 🚀 Quick Start
            1. Go to **✍️ Text Correction** to correct your Yorùbá text
            2. Visit **📚 Learning** to explore common spelling rules
            """)

        with col2:
            st.image(
                "https://via.placeholder.com/300x200/1f77b4/ffffff?text=Yoruba+AI",
                caption="Yorùbá Language Technology"
            )

            st.info("""
            **Did you know?**  
            Yorùbá has three tone marks:

            - Dò (low): à, è, ì, ò, ù  
            - Mí (high): á, é, í, ó, ú  
            - Rẹ (mid): a, e, i, o, u
            """)

        st.markdown("---")
        st.subheader("🎮 Quick Demo")

        demo_text = st.text_input("Try a quick correction:", "mo fe ka iwe yoruba", key="home_demo_input")

        if demo_text:
            with st.spinner("Correcting..."):
                try:
                    basic_result = self.basic_corrector.correct_text(demo_text)
                except Exception:
                    basic_result = "Error processing basic correction"

                try:
                    enhanced_result = self.enhanced_corrector.correct_text_with_context(demo_text)
                except Exception:
                    enhanced_result = "Enhanced correction not supported"

            demo_col1, demo_col2 = st.columns(2)

            with demo_col1:
                st.write("**Basic Correction:**")
                st.code(basic_result)

            with demo_col2:
                st.write("**Enhanced Correction:**")
                st.code(enhanced_result)

    def correction_page(self):
        st.header("✍️ Yorùbá Text Correction")

        if "correction_results" not in st.session_state:
            st.session_state.correction_results = None

        if "input_text_area" not in st.session_state:
            st.session_state.input_text_area = ""

        user_text = st.text_area(
            "Enter Yorùbá text to correct:",
            value=st.session_state.input_text_area,
            height=150,
            key="input_text_area_widget"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Correct Text"):
                st.session_state.input_text_area = user_text
                self.perform_correction(user_text)

        with col2:
            if st.button("🗑️ Clear"):
                st.session_state.correction_results = None
                st.session_state.input_text_area = ""

        if st.session_state.correction_results:
            self.display_results()

    def perform_correction(self, text):
        if not text.strip():
            st.warning("Please enter some text.")
            return

        with st.spinner("Correcting..."):
            start = time.time()
            try:
                corrected_basic = self.basic_corrector.correct_text(text)
            except Exception:
                corrected_basic = text
            try:
                corrected_enhanced = self.enhanced_corrector.correct_text_with_context(text)
            except Exception:
                corrected_enhanced = text
            elapsed = time.time() - start

        uid = uuid.uuid4().hex

        st.session_state.correction_results = {
            "original": text,
            "corrected_basic": corrected_basic,
            "corrected_enhanced": corrected_enhanced,
            "time": elapsed,
            "uid": uid
        }

    def display_results(self):
        results = st.session_state.correction_results
        uid = results["uid"]

        st.success(f"Correction completed in {results['time']:.2f} seconds")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📥 Original Text")
            st.text_area("", results["original"], height=200, key=f"orig_{uid}")

        with col2:
            st.subheader("📤 Corrected Text (Enhanced)")
            st.text_area("", results["corrected_enhanced"], height=200, key=f"corr_{uid}")

        if results["original"] != results["corrected_enhanced"]:
            st.divider()
            self.word_analysis(results["original"], results["corrected_enhanced"])

    def word_analysis(self, original, corrected):
        st.subheader("🔍 Word by Word Analysis")

        orig = original.split()
        corr = corrected.split()
        max_len = max(len(orig), len(corr))
        orig += [""] * (max_len - len(orig))
        corr += [""] * (max_len - len(corr))

        rows = []
        for i, (o, c) in enumerate(zip(orig, corr), start=1):
            if not o:
                continue

            status = "Correct" if o == c else "Changed"

            try:
                # Use enhanced corrector's closest match function
                suggestions = self.enhanced_corrector.find_closest_matches(o, max_matches=3)
                sug = ", ".join(suggestions) if suggestions else "No suggestions"
            except Exception:
                sug = "No data"

            rows.append({
                "Index": i,
                "Original": o,
                "Corrected": c,
                "Status": status,
                "Suggestions": sug
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)

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
        ## Diacritc Aware Spelling Corrector For Yorùbá Language
        
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
    app = YorubaSpellingApp()
    app.run()


if __name__ == "__main__":
    main()

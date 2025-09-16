import streamlit as st
import requests
import json
import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from config.settings import EMBEDDINGS_FILE

# Page config
st.set_page_config(
    page_title="Semantic Video Search",
    page_icon="🎬",
    layout="wide"
)

# API endpoint
API_BASE = "http://localhost:8000"


def load_video_data():
    """Load video metadata"""
    try:
        with open(EMBEDDINGS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def search_videos(query, max_results=5):
    """Search videos via API"""
    try:
        response = requests.post(
            f"{API_BASE}/search",
            json={"query": query, "max_results": max_results},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Search failed: {str(e)}")
        return None


def get_health_status():
    """Check API health"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        return response.json()
    except:
        return {"status": "offline"}


def main():
    st.title("🎬 Semantic Video Search POC")
    st.write("Search through videos using natural language queries")

    # Sidebar - System Status
    with st.sidebar:
        st.header("System Status")

        # API Status
        health = get_health_status()
        if health["status"] == "healthy":
            st.success("✅ API Online")
            st.write(f"Index ID: `{health.get('index_id', 'N/A')[:8]}...`")
        elif health["status"] == "no_index":
            st.warning("⚠️ No index found")
            st.write("Run embedding generation first")
        else:
            st.error("❌ API Offline")
            st.write("Start the API server first")

        # Video Data Status
        video_data = load_video_data()
        if video_data:
            st.success("✅ Embeddings loaded")
            st.write(f"Videos: {len(video_data.get('videos', []))}")
        else:
            st.error("❌ No embeddings found")

        st.divider()

        # Instructions
        st.header("Setup")
        st.write("""
        1. Add videos to `data/videos/`
        2. Run: `python -m src.embeddings.generate`
        3. Start API: `python -m src.api.main`
        4. Use this interface to search
        """)

    # Main search interface
    col1, col2 = st.columns([3, 1])

    with col1:
        query = st.text_input(
            "Enter your search query:",
            placeholder="e.g., person talking, outdoor scene, laughter, office meeting"
        )

    with col2:
        max_results = st.selectbox("Max results:", [3, 5, 10], index=1)

    # Search options
    col_options1, col_options2 = st.columns([1, 1])
    with col_options1:
        search_context = st.checkbox("Search with context", value=True, 
                                     help="Includes surrounding context in search results")
    with col_options2:
        show_video = st.checkbox("Show videos", value=True, 
                                 help="Display video players in results")
    
    # Search button
    if st.button("🔍 Search", type="primary") or query:
        if not query.strip():
            st.warning("Please enter a search query")
            return
            
        if health["status"] != "healthy":
            st.error("API not ready. Check system status in sidebar.")
            return

        with st.spinner("Searching videos..."):
            results = search_videos(query, max_results)

        if results:
            # Add more prominent results header in darker color to match Twelve Labs UI
            st.markdown(
                f'<div style="background-color: #1e3a2d; color: white; padding: 8px 15px; border-radius: 5px; margin-bottom: 15px;">'
                f'<h3 style="margin: 0;">Found {results["total_results"]} results</h3>'
                f'</div>',
                unsafe_allow_html=True
            )

            # Display results
            for i, result in enumerate(results["results"], 1):
                with st.container():
                    # Create a card-like container with border and padding that matches Twelve Labs style
                    st.markdown("""
                    <style>
                    .result-card {
                        border: 1px solid #ddd;
                        border-radius: 8px;
                        padding: 0;
                        margin-bottom: 24px;
                        background-color: white;
                        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                    }
                    .result-header {
                        background-color: #2c4c3b;
                        color: white;
                        padding: 10px 15px;
                        margin: 0;
                        border-top-left-radius: 8px;
                        border-top-right-radius: 8px;
                        border-bottom: 1px solid #ddd;
                    }
                    .result-content {
                        padding: 15px;
                    }
                    .text-block {
                        background-color: #f9f9f9;
                        border-radius: 5px;
                        padding: 10px;
                        margin-bottom: 10px;
                        border-left: 3px solid #2c4c3b;
                    }
                    .confidence-indicator {
                        font-weight: bold;
                        display: inline-block;
                        padding: 4px 10px;
                        border-radius: 12px;
                        color: white;
                    }
                    .high-confidence {
                        background-color: #28a745;
                    }
                    .medium-confidence {
                        background-color: #fd7e14;
                    }
                    .low-confidence {
                        background-color: #dc3545;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # Create the card header and content separately
                    st.markdown(f'<div class="result-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="result-header"><h3>Result {i}: {result["filename"]}</h3></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="result-content">', unsafe_allow_html=True)
                    
                    # Use a more balanced column layout
                    col1, col2, col3 = st.columns([2, 1, 1])

                    with col1:
                        if result["clip_text"]:
                            # Use custom styling for text display
                            st.markdown(
                                f'<div class="text-block">'
                                f'<strong>Text:</strong> {result["clip_text"]}'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(
                                '<div class="text-block" style="color: #666;">'
                                '<em>No text transcript available</em>'
                                '</div>',
                                unsafe_allow_html=True
                            )

                    with col2:
                        # Handle confidence as string or float
                        confidence_value = result['confidence']
                        
                        # Determine confidence class and display
                        confidence_class = ""
                        
                        if isinstance(confidence_value, str):
                            confidence_display = confidence_value
                            if confidence_value.lower() == "high":
                                confidence_class = "high-confidence"
                            elif confidence_value.lower() == "medium":
                                confidence_class = "medium-confidence"
                            elif confidence_value.lower() == "low":
                                confidence_class = "low-confidence"
                        else:
                            # For numeric values
                            if confidence_value > 0.7:
                                confidence_display = "high"
                                confidence_class = "high-confidence"
                            elif confidence_value > 0.4:
                                confidence_display = "medium"
                                confidence_class = "medium-confidence"
                            else:
                                confidence_display = "low"
                                confidence_class = "low-confidence"
                            
                        # Display confidence with badge styling like in Twelve Labs UI
                        st.markdown(
                            f'<div style="text-align: center;">'
                            f'<p><strong>Confidence</strong></p>'
                            f'<div class="confidence-indicator {confidence_class}">'
                            f'{confidence_display}'
                            f'</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

                    with col3:
                        if result["start"] > 0 or (result["end"] > 0 and result["end"] != result["start"]):
                            start_time = result['start']
                            end_time = result['end']
                            duration = end_time - start_time
                            
                            # Format as minutes:seconds if duration is long enough
                            if end_time >= 60:
                                start_formatted = f"{int(start_time//60)}:{int(start_time%60):02d}"
                                end_formatted = f"{int(end_time//60)}:{int(end_time%60):02d}"
                                st.write(f"**Time:** {start_formatted} - {end_formatted}")
                            else:
                                st.write(f"**Time:** {start_time:.1f}s - {end_time:.1f}s")
                                
                            # Display duration
                            st.caption(f"Duration: {duration:.1f}s")
                        else:
                            st.write("**Full video**")
                            # If we have the video filepath, we can try to get the duration
                            video_filepath = result.get('video_filepath', 'unknown')
                            if video_filepath != 'unknown' and Path(video_filepath).exists():
                                try:
                                    # This is a placeholder - in a real app you'd use a video 
                                    # processing library like moviepy or ffmpeg to get the duration
                                    st.caption("Full video duration available")
                                except:
                                    pass

                    # Only show video if the checkbox is checked
                    if show_video:
                        # Video display section
                        st.write("**Video Preview:**")
                        
                        # Get video filepath
                        video_filepath = result.get('video_filepath', 'unknown')
                        
                        # For displaying thumbnail or play button
                        video_col1, video_col2 = st.columns([3, 1])
                        
                        with video_col1:
                            # Check if the video file exists
                            if video_filepath != 'unknown' and Path(video_filepath).exists():
                                # Create a video player with a start time if specified
                                if result["start"] > 0:
                                    # Streamlit's video player supports seeking with start_time parameter
                                    # Store exact start and end times for UI display
                                    exact_start = result["start"]
                                    exact_end = result["end"] if result["end"] > result["start"] else exact_start + 30
                                    
                                    # Add a highlighted message showing the exact clip segment
                                    st.info(f"Playing clip segment: {exact_start:.2f}s - {exact_end:.2f}s")
                                    st.video(video_filepath, start_time=int(exact_start))
                                    
                                    # Optional: Add a progress bar to show position within the clip
                                    clip_duration = exact_end - exact_start
                                    if clip_duration > 1:  # Only show for clips longer than 1 second
                                        st.progress(0.5)  # Show progress at 50% (streamlit limitation - can't update dynamically)
                                        st.caption(f"Clip duration: {clip_duration:.2f}s")
                                else:
                                    st.video(video_filepath)
                            else:
                                # If video file not found, show a placeholder
                                if result.get('thumbnail_url'):
                                    st.image(result['thumbnail_url'], caption="Video thumbnail")
                                else:
                                    st.error("Video file not found")
                    
                        with video_col2:
                            if video_filepath != 'unknown' and Path(video_filepath).exists():
                                st.write("**Video Controls:**")
                                
                                # Create more precise navigation buttons
                                start_time = result["start"] if result["start"] > 0 else 0
                                end_time = result["end"] if result["end"] > result["start"] else start_time + 30
                                
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    if st.button(f"⏮️ Start", key=f"jump_{i}_start"):
                                        st.session_state[f"video_{i}_time"] = int(start_time)
                                        st.rerun()
                                
                                with col_b:
                                    if st.button(f"⏭️ End", key=f"jump_{i}_end"):
                                        st.session_state[f"video_{i}_time"] = int(end_time)
                                        st.rerun()
                                
                                if end_time - start_time > 5:  # Only show mid-point for longer clips
                                    mid_point = (start_time + end_time) / 2
                                    if st.button(f"⏺️ Middle ({mid_point:.1f}s)", key=f"jump_{i}_mid"):
                                        st.session_state[f"video_{i}_time"] = int(mid_point)
                                        st.rerun()
                                
                                # Add precise time navigation
                                st.write("**Timestamp Navigation:**")
                                exact_time = st.slider(
                                    "Position (seconds)", 
                                    min_value=float(max(0, start_time-5)), 
                                    max_value=float(end_time+5),
                                    value=float(start_time),
                                    step=0.5,
                                    key=f"slider_{i}"
                                )
                                
                                if st.button("Jump to Position", key=f"jump_{i}_custom"):
                                    st.session_state[f"video_{i}_time"] = exact_time
                                    st.rerun()
                                
                                # Add video info 
                                st.write("**Video Info:**")
                                if result.get('filename'):
                                    st.caption(f"File: {result.get('filename')}")
                            
                    # Video file info with cleaner display
                    col_info1, col_info2, col_info3 = st.columns([1, 1, 1])
                    with col_info1:
                        st.caption(f"Video ID: `{result['video_id']}`")
                    with col_info2:
                        score = result.get('score', 0.0)
                        if isinstance(score, (int, float)):
                            st.caption(f"Match Score: {score:.1f}")
                        else:
                            st.caption(f"Match Score: {score}")
                    with col_info3:
                        st.caption(f"File: {result.get('filename', 'unknown')}")

                    # Add download button if file exists
                    if video_filepath != 'unknown' and Path(video_filepath).exists():
                        with open(video_filepath, "rb") as file:
                            video_bytes = file.read()
                            st.download_button(
                                label="Download Video",
                                data=video_bytes,
                                file_name=result.get('filename', 'video.mp4'),
                                mime="video/mp4"
                            )

                    # Close the container divs
                    st.markdown('</div></div>', unsafe_allow_html=True)

        else:
            st.error("Search failed or no results found")


    # Example queries
    st.subheader("💡 Example Queries")
    example_queries = [
        "person talking",
        "outdoor scene",
        "laughter or smiling",
        "office or indoor setting",
        "close-up of face",
        "hand gestures",
        "background music",
        "text or writing"
    ]

    cols = st.columns(2)
    for i, example in enumerate(example_queries):
        col = cols[i % 2]
        with col:
            if st.button(f"🎯 {example}", key=f"example_{i}"):
                st.query_params.query = example
                st.rerun()

    # Footer
    st.divider()
    st.caption("Powered by Twelve Labs API • Semantic Video Search POC")


if __name__ == "__main__":
    main()
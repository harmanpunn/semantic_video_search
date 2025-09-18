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


def search_videos(query=None, image=None, max_results=5, search_options=None):
    """Search videos via API using text or image"""
    try:
        if search_options is None:
            search_options = ["visual", "audio"]
            
        if query:  # Text search
            response = requests.post(
                f"{API_BASE}/search",
                json={
                    "query": query, 
                    "max_results": max_results,
                    "search_options": search_options
                },
                timeout=30
            )
        elif image:  # Image search
            # Create multipart form data with the image file
            files = {"image_file": (image.name, image.getvalue(), f"image/{image.type.split('/')[1]}")}
            data = {
                "max_results": str(max_results),
                "search_options": ",".join(search_options)
            }
            
            response = requests.post(
                f"{API_BASE}/search/image",
                files=files,
                data=data,
                timeout=60  # Longer timeout for image uploads
            )
        else:
            st.error("No query or image provided for search")
            return None
            
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
    # Add search type selector
    search_type = st.radio(
        "Search by:",
        ["Text", "Image"],
        horizontal=True,
        key="search_type"
    )
    
    col1, col2 = st.columns([3, 1])

    # Different search inputs based on selected search type
    if search_type == "Text":
        with col1:
            query = st.text_input(
                "Enter your search query:",
                placeholder="e.g., person talking, outdoor scene, laughter, office meeting",
                key="search_query_input"
            )
            uploaded_image = None
    else:  # Image search
        with col1:
            uploaded_image = st.file_uploader(
                "Upload an image to search for similar video content:",
                type=["jpg", "jpeg", "png"],
                key="image_upload",
                help="Image must be JPEG/PNG, at least 64x64 pixels, and under 5MB"
            )
            
            if uploaded_image:
                # Preview the uploaded image
                st.image(uploaded_image, width=250, caption="Search image preview")
            query = None

    with col2:
        max_results = st.selectbox("Max results:", [3, 5, 10], index=1, key="max_results_select")

    # Search options
    col_options1, col_options2 = st.columns([1, 1])
    with col_options1:
        search_options = st.multiselect(
            "Search options:", 
            ["visual", "audio"], 
            default=["visual", "audio"],
            key="search_options_select"
        )
    with col_options2:
        show_video = st.checkbox("Show videos", value=True, 
                                help="Display video players in results",
                                key="show_video_checkbox")
    
    # Search button - enabled for text search with query or image search with uploaded image
    search_enabled = (search_type == "Text" and query and query.strip()) or (search_type == "Image" and uploaded_image is not None)
    
    if st.button("🔍 Search", type="primary", disabled=not search_enabled) or (search_type == "Text" and query):
        # Different validations based on search type
        if search_type == "Text" and (not query or not query.strip()):
            st.warning("Please enter a search query")
            return
        elif search_type == "Image" and not uploaded_image:
            st.warning("Please upload an image to search with")
            return
            
        if health["status"] != "healthy":
            st.error("API not ready. Check system status in sidebar.")
            return

        with st.spinner("Searching videos..."):
            # Use the appropriate search method based on selected type
            if search_type == "Text":
                results = search_videos(query=query, max_results=max_results, search_options=search_options)
            else:  # Image search
                results = search_videos(image=uploaded_image, max_results=max_results, search_options=search_options)

        if results:
            # Minimalist results header
            st.markdown(
                f'<div style="background-color: #f1f3f2; color: #2c4c3b; padding: 8px 12px; border-left: 3px solid #2c4c3b; margin-bottom: 15px; font-weight: 500;">'
                f'Found {results["total_results"]} results'
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
                        border: 1px solid #eaeaea;
                        border-radius: 6px;
                        padding: 0;
                        margin-bottom: 20px;
                        background-color: white;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                    }
                    .result-header {
                        background-color: #f5f5f5;
                        color: #333;
                        padding: 8px 12px;
                        margin: 0;
                        border-top-left-radius: 6px;
                        border-top-right-radius: 6px;
                        border-bottom: 1px solid #eaeaea;
                        font-weight: 500;
                    }
                    .result-content {
                        padding: 12px;
                    }
                    .text-block {
                        background-color: #fafafa;
                        border-radius: 4px;
                        padding: 8px 10px;
                        margin-bottom: 10px;
                        border-left: 2px solid #ccc;
                        font-size: 14px;
                    }
                    .confidence-indicator {
                        font-weight: 500;
                        display: inline-block;
                        padding: 3px 8px;
                        border-radius: 4px;
                        color: white;
                        font-size: 12px;
                        letter-spacing: 0.3px;
                    }
                    .high-confidence {
                        background-color: #27ae60;
                    }
                    .medium-confidence {
                        background-color: #f39c12;
                    }
                    .low-confidence {
                        background-color: #e74c3c;
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
                        # Create two columns for video and raw data
                        video_col, data_col = st.columns([1, 1])
                        
                        # Left column for video (smaller size)
                        with video_col:
                            st.write("**Video Preview:**")
                            
                            # Get video filepath
                            video_filepath = result.get('video_filepath', 'unknown')
                            
                            # Check if the video file exists
                            if video_filepath != 'unknown' and Path(video_filepath).exists():
                                # Create a video player with a start time if specified
                                if result["start"] > 0:
                                    # Store exact start and end times for UI display
                                    exact_start = result["start"]
                                    exact_end = result["end"] if result["end"] > result["start"] else exact_start + 30
                                    
                                    # Add a compact message showing the exact clip segment
                                    st.caption(f"Clip: {exact_start:.2f}s - {exact_end:.2f}s")
                                    st.video(video_filepath, start_time=int(exact_start))
                                else:
                                    st.video(video_filepath)
                                
                                # Display simple video info
                                if result.get('filename'):
                                    st.caption(f"File: {result.get('filename')}")
                            else:
                                # If video file not found, show a placeholder
                                if result.get('thumbnail_url'):
                                    st.image(result['thumbnail_url'], caption="Video thumbnail")
                                else:
                                    st.error("Video file not found")
                        
                        # Right column for raw API data
                        with data_col:
                            st.write("**Raw API Response:**")
                            # Create a clean display of the raw result data
                            with st.expander("View details", expanded=False):
                                # Create a copy of the result without the video path for cleaner display
                                display_result = result.copy()
                                if 'video_filepath' in display_result:
                                    display_result['video_filepath'] = '...' + display_result['video_filepath'][-30:] if len(display_result['video_filepath']) > 30 else display_result['video_filepath']
                                
                                st.json(display_result)
                            
                            # Show key metadata in a more readable format
                            st.caption("**Key Data Points:**")
                            metadata_cols = st.columns(2)
                            with metadata_cols[0]:
                                st.markdown(f"**Video ID:** `{result.get('video_id', 'N/A')}`")
                                st.markdown(f"**Confidence:** `{result.get('confidence', 'N/A')}`")
                            with metadata_cols[1]:
                                st.markdown(f"**Start:** `{result.get('start', 0):.2f}s`")  
                                st.markdown(f"**End:** `{result.get('end', 0):.2f}s`")
                            
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
                                mime="video/mp4",
                                key=f"download_btn_{i}_{result.get('video_id', i)}"  # Add unique key for each download button
                            )

                    # Close the container divs
                    st.markdown('</div></div>', unsafe_allow_html=True)

        else:
            st.error("Search failed or no results found")

    # Footer
    st.divider()
    st.caption("Powered by Twelve Labs API • Semantic Video Search POC")


if __name__ == "__main__":
    main()
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Output to console
    ]
)
logger = logging.getLogger("semantic_video_search")

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.embeddings.twelve_labs_client import TwelveLabsClient
from config.settings import EMBEDDINGS_FILE, MAX_SEARCH_RESULTS

client = TwelveLabsClient()
index_id = None


class SearchQuery(BaseModel):
    query: str
    max_results: int = MAX_SEARCH_RESULTS


class SearchResult(BaseModel):
    video_id: str
    filename: str
    confidence: str  # Updated to accept string values like "high", "medium"
    score: float = 0.0
    start: float = 0.0
    end: float = 0.0
    clip_text: str = ""
    thumbnail_url: Optional[str] = None  # Made properly optional with Optional type
    video_filepath: str = "unknown"  # Path to the video file


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int


def load_index_id():
    """Load index ID from embeddings file"""
    global index_id
    try:
        with open(EMBEDDINGS_FILE, 'r') as f:
            data = json.load(f)
            index_id = data.get("index_id")
            return index_id is not None
    except FileNotFoundError:
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown events"""
    # Startup: Load index ID
    if not load_index_id():
        print("Warning: No embeddings file found. Run embedding generation first.")
    yield
    # Shutdown: Any cleanup code would go here


# Create FastAPI app with lifespan handler
app = FastAPI(
    title="Semantic Video Search API", 
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Semantic Video Search API", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if index_id:
        return {"status": "healthy", "index_id": index_id}
    else:
        return {"status": "no_index", "message": "Run embedding generation first"}


@app.post("/search", response_model=SearchResponse)
async def search_videos(query: SearchQuery):
    """Search videos with text query"""
    logger.info(f"Received search request with query: '{query.query}', max_results: {query.max_results}")
    
    if not index_id:
        logger.error("Search failed: No index found")
        raise HTTPException(
            status_code=400,
            detail="No index found. Run embedding generation first."
        )

    try:
        logger.info(f"Searching index {index_id} with query: '{query.query}'")
        
        # Prepare search options
        search_options = {
            "search_options": ["visual", "audio"],
            "threshold": "medium",
            "operator": "or",
            "page_limit": query.max_results,
            "adjust_confidence_level": 0.5
        }
        
        logger.debug(f"Search options: {search_options}")
        
        # Search using Twelve Labs API
        result = client.search_text(
            index_id=index_id,
            query=query.query,
            options=search_options
        )

        logger.info(f"Search result success: {result['success']}")
        
        if not result["success"]:
            error_msg = f"Search failed: {result['error']}"
            logger.error(error_msg)
            raise HTTPException(
                status_code=500,
                detail=error_msg
            )

        search_data = result["data"]
        logger.debug(f"Search data keys: {search_data.keys() if isinstance(search_data, dict) else 'Not a dict'}")
        
        search_results = []

        # Process search results
        data_items = search_data.get("data", [])
        logger.info(f"Number of results: {len(data_items)}")
        
        try:
            for i, item in enumerate(data_items[:query.max_results]):
                logger.debug(f"Processing result {i+1}")
                logger.debug(f"Item keys: {item.keys() if isinstance(item, dict) else 'Not a dict'}")
                
                # Extract video filename from metadata
                metadata = item.get("metadata", {})
                filename = metadata.get("filename", "unknown") if isinstance(metadata, dict) else "unknown"
                logger.debug(f"Filename: {filename}")
                
                # Make sure clip_text is always a string
                clip_text = item.get("clip_text", "")
                if clip_text is None:
                    clip_text = ""
                
                # Handle thumbnail_url properly - keep it None if it's None
                thumbnail_url = item.get("thumbnail_url")
                
                # Find the filepath for the video from the embeddings file
                video_filepath = "unknown"
                try:
                    with open(EMBEDDINGS_FILE, 'r') as f:
                        embeddings_data = json.load(f)
                        video_id = item.get("video_id", "")
                        for video in embeddings_data.get("videos", []):
                            if video.get("video_id") == video_id:
                                filename = video.get("filename", filename)
                                video_filepath = video.get("filepath", "unknown")
                                break
                except Exception as e:
                    logger.error(f"Error finding video filepath: {str(e)}")
                
                search_result = SearchResult(
                    video_id=item.get("video_id", ""),
                    filename=filename,
                    confidence=item.get("confidence", "unknown"),  # Default to "unknown" for confidence
                    score=item.get("score", 0.0),
                    start=item.get("start", 0.0),
                    end=item.get("end", 0.0),
                    clip_text=clip_text,
                    thumbnail_url=thumbnail_url,  # This can now be None
                    video_filepath=video_filepath  # Add the actual video file path
                )
                search_results.append(search_result)
        except Exception as e:
            import traceback
            logger.error(f"Error processing search results: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Continue with whatever results we managed to process

        logger.info(f"Returning {len(search_results)} search results")
        
        return SearchResponse(
            query=query.query,
            results=search_results,
            total_results=len(search_results)
        )
    except Exception as e:
        import traceback
        error_msg = f"Unexpected search error: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Exception type: {type(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )


@app.get("/videos")
async def list_videos():
    """List all indexed videos"""
    try:
        with open(EMBEDDINGS_FILE, 'r') as f:
            data = json.load(f)
            videos = data.get("videos", [])
            return {"videos": videos, "total": len(videos)}
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="No embeddings file found"
        )


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Semantic Video Search API...")
    logger.info("API docs available at: http://localhost:8000/docs")
    
    # Run with log level set to show all logs
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
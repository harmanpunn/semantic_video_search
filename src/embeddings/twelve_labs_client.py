from twelvelabs import TwelveLabs
from twelvelabs.indexes import IndexesCreateRequestModelsItem
from typing import List, Dict, Any
import logging
from config.settings import TWELVE_LABS_API_KEY

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Output to console
    ]
)
logger = logging.getLogger("twelvelabs_client")


class TwelveLabsClient:
    def __init__(self):
        self.client = TwelveLabs(api_key=TWELVE_LABS_API_KEY)

    def test_connection(self) -> Dict[str, Any]:
        """Test API connectivity"""
        try:
            # Test by listing indexes (should work if API key is valid)
            indexes = self.client.indexes.list()
            print("Available Clients:")
            for client in indexes:
                print(f" - {client.index_name}")
            return {"success": True, "data": list(indexes)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_index(self, index_name: str, engines: List[str] = None) -> Dict[str, Any]:
        """Create a new index for videos"""
        if engines is None:
            engines = ["pegasus1.2", "marengo2.7"]

        try:
            models = [
                IndexesCreateRequestModelsItem(
                    model_name="marengo2.7",
                    model_options=["visual", "audio"],
                ),
                IndexesCreateRequestModelsItem(
                    model_name="pegasus1.2",
                    model_options=["visual", "audio"],
                ),
            ]

            index = self.client.indexes.create(
                index_name=index_name,
                models=models
            )
            return {"success": True, "data": {"_id": index.id, "name": index_name}}
        except Exception as e:
            print(f"Error creating index: {e}")
            return {"success": False, "error": str(e)}

    def upload_video(self, index_id: str, video_path: str, language: str = "en") -> Dict[str, Any]:
        """Upload a video to the index"""
        try:
            # Open the file as a binary file object
            with open(video_path, 'rb') as file_obj:
                # Pass the open file object to the SDK
                task = self.client.tasks.create(
                    index_id=index_id,
                    video_file=file_obj,
                )
                
                print(f"Upload complete. The unique identifier of your video is {task.video_id}. And the task ID is {task.id}.")
                return {"success": True, "data": {"_id": task.id}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Check video processing task status"""
        try:
            task = self.client.tasks.retrieve(task_id)
            return {"success": True, "data": {"status": task.status, "video_id": task.video_id}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_video_info(self, video_id: str) -> Dict[str, Any]:
        """Get video information"""
        try:
            video = self.client.videos.retrieve(video_id)
            return {"success": True, "data": {"id": video.id, "filename": video.metadata.filename if hasattr(video, 'metadata') and video.metadata else "unknown"}}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def wait_for_task_completion(self, task_id: str, sleep_interval: float = 5.0) -> Dict[str, Any]:
        """Wait for a video indexing task to complete"""
        try:
            # Use the SDK's wait_for_done method
            task = self.client.tasks.wait_for_done(
                task_id=task_id,
                sleep_interval=sleep_interval,
                callback=lambda t: print(f"  Status={t.status}")
            )
            
            if task.status != "ready":
                return {"success": False, "error": f"Indexing failed with status {task.status}"}
                
            return {"success": True, "data": {"video_id": task.video_id, "status": task.status}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_text(self, index_id: str, query: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Search videos with text query"""
        try:
            # Set up default options if none provided
            if options is None:
                options = {}
            
            logger.debug(f"Search query: '{query}' for index_id: {index_id}")
            logger.debug(f"Search options: {options}")
            
            # Prepare search parameters based on documentation
            search_params = {
                "index_id": index_id,
                "query_text": query,
                "search_options": options.get("search_options", ["visual", "audio"]),
                "threshold": options.get("threshold", "medium"),
                "group_by": options.get("group_by", None),  # Can be "video" or None
                "operator": options.get("operator", "or"),
                "page_limit": options.get("page_limit", 10)
            }
            
            # Add optional parameters only if they're provided
            if "adjust_confidence_level" in options:
                search_params["adjust_confidence_level"] = options["adjust_confidence_level"]
            
            if "sort_option" in options:
                search_params["sort_option"] = options["sort_option"]
                
            if "filter" in options:
                search_params["filter"] = options["filter"]
            
            # Remove None values to avoid SDK errors
            search_params = {k: v for k, v in search_params.items() if v is not None}
            logger.debug(f"Final search parameters: {search_params}")
            
            # Execute the search
            logger.info("Executing search...")
            search_results = self.client.search.query(**search_params)
            logger.info("Search executed successfully")
            
            # Inspect the search results structure
            logger.debug(f"Search results type: {type(search_results)}")
            logger.debug(f"Search results dir: {dir(search_results)}")
            
            # Convert to our expected format
            results = []
            
            # For debugging, try to inspect the first few results
            try:
                item_count = 0
                for item in search_results:
                    item_count += 1
                    logger.debug(f"Processing result item {item_count}")
                    logger.debug(f"Item type: {type(item)}")
                    logger.debug(f"Item dir: {dir(item)}")
                    
                    # Handle grouped results (when group_by="video")
                    if hasattr(item, 'id') and hasattr(item, 'clips') and item.clips:
                        logger.debug(f"Item is a grouped result with {len(item.clips)} clips")
                        for clip in item.clips:
                            results.append({
                                "video_id": clip.video_id,
                                "confidence": getattr(clip, 'confidence', 0.0),
                                "score": getattr(clip, 'score', 0.0),
                                "start": getattr(clip, 'start', 0.0),
                                "end": getattr(clip, 'end', 0.0),
                                "metadata": {"filename": getattr(clip, 'filename', 'unknown')},
                                "clip_text": getattr(clip, 'transcription', ''),
                                "thumbnail_url": getattr(clip, 'thumbnail_url', '')
                            })
                    # Handle individual results
                    else:
                        logger.debug(f"Item is an individual result")
                        logger.debug(f"Item video_id: {getattr(item, 'video_id', 'Not found')}")
                        logger.debug(f"Item confidence: {getattr(item, 'confidence', 'Not found')}")
                        
                        results.append({
                            "video_id": getattr(item, 'video_id', ''),
                            "confidence": getattr(item, 'confidence', 0.0),
                            "score": getattr(item, 'score', 0.0),
                            "start": getattr(item, 'start', 0.0),
                            "end": getattr(item, 'end', 0.0),
                            "metadata": {"filename": getattr(item, 'filename', 'unknown')},
                            "clip_text": getattr(item, 'transcription', ''),
                            "thumbnail_url": getattr(item, 'thumbnail_url', '')
                        })
                        
                    # Limit the number of items processed for debugging
                    if item_count >= 5:
                        logger.debug("Limiting to first 5 results for debugging")
                        break
            except Exception as e:
                logger.error(f"Error processing search results: {str(e)}")
            
            logger.info(f"Total results processed: {len(results)}")
            return {"success": True, "data": {"data": results}}
        except Exception as e:
            import traceback
            logger.error(f"Search failed with exception: {str(e)}")
            logger.error(f"Exception type: {type(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}
            
    def search_image(self, index_id: str, image_file, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Search videos with image query"""
        try:
            # Set up default options if none provided
            if options is None:
                options = {}
            
            logger.debug(f"Image search for index_id: {index_id}")
            logger.debug(f"Search options: {options}")
            
            # Prepare search parameters based on documentation
            search_params = {
                "index_id": index_id,
                "query_media_type": "image",
                "query_media_file": image_file,  # This is the file object
                "search_options": options.get("search_options", ["visual"]),
                "threshold": options.get("threshold", "medium"),
                "group_by": options.get("group_by", None),  # Can be "video" or None
                "operator": options.get("operator", "or"),
                "page_limit": options.get("page_limit", 10)
            }
            
            # Add optional parameters only if they're provided
            if "adjust_confidence_level" in options:
                search_params["adjust_confidence_level"] = options["adjust_confidence_level"]
            
            if "sort_option" in options:
                search_params["sort_option"] = options["sort_option"]
                
            if "filter" in options:
                search_params["filter"] = options["filter"]
            
            # Remove None values to avoid SDK errors
            search_params = {k: v for k, v in search_params.items() if v is not None}
            logger.debug(f"Final image search parameters: {search_params}")
            
            # Execute the search
            logger.info("Executing image search...")
            search_results = self.client.search.query(**search_params)
            logger.info("Image search executed successfully")
            
            # Convert to our expected format
            results = []
            
            # For debugging, try to inspect the first few results
            try:
                item_count = 0
                for item in search_results:
                    item_count += 1
                    logger.debug(f"Processing result item {item_count}")
                    logger.debug(f"Item type: {type(item)}")
                    logger.debug(f"Item dir: {dir(item)}")
                    
                    # Handle grouped results (when group_by="video")
                    if hasattr(item, 'id') and hasattr(item, 'clips') and item.clips:
                        logger.debug(f"Item is a grouped result with {len(item.clips)} clips")
                        for clip in item.clips:
                            results.append({
                                "video_id": clip.video_id,
                                "confidence": getattr(clip, 'confidence', 0.0),
                                "score": getattr(clip, 'score', 0.0),
                                "start": getattr(clip, 'start', 0.0),
                                "end": getattr(clip, 'end', 0.0),
                                "metadata": {"filename": getattr(clip, 'filename', 'unknown')},
                                "clip_text": getattr(clip, 'transcription', ''),
                                "thumbnail_url": getattr(clip, 'thumbnail_url', '')
                            })
                    # Handle individual results
                    else:
                        logger.debug(f"Item is an individual result")
                        logger.debug(f"Item video_id: {getattr(item, 'video_id', 'Not found')}")
                        logger.debug(f"Item confidence: {getattr(item, 'confidence', 'Not found')}")
                        
                        results.append({
                            "video_id": getattr(item, 'video_id', ''),
                            "confidence": getattr(item, 'confidence', 0.0),
                            "score": getattr(item, 'score', 0.0),
                            "start": getattr(item, 'start', 0.0),
                            "end": getattr(item, 'end', 0.0),
                            "metadata": {"filename": getattr(item, 'filename', 'unknown')},
                            "clip_text": getattr(item, 'transcription', ''),
                            "thumbnail_url": getattr(item, 'thumbnail_url', '')
                        })
            except Exception as e:
                logger.error(f"Error processing image search results: {str(e)}")
            
            logger.info(f"Total image search results processed: {len(results)}")
            return {"success": True, "data": {"data": results}}
        except Exception as e:
            import traceback
            logger.error(f"Image search failed with exception: {str(e)}")
            logger.error(f"Exception type: {type(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}
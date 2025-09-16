# Semantic Video Search POC

A minimal proof-of-concept for multimodal semantic video search using Twelve Labs API.

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set up API key
cp .env.example .env
# Edit .env with your Twelve Labs API key from https://playground.twelvelabs.io/
```

### 2. Add Sample Videos
Place 5 short videos (≤15 seconds each) in `data/videos/`:
- Supported formats: MP4, MOV, AVI
- Naming: video1.mp4, video2.mp4, etc.

### 3. Test API Connection
```bash
python test_connection.py
```

### 4. Generate Embeddings
```bash
python -m src.embeddings.generate
```

### 5. Start Services
```bash
# Terminal 1: Start API server
python -m src.api.main

# Terminal 2: Start frontend
streamlit run src/frontend/app.py
```

### 6. Access the Application
- Frontend: http://localhost:8501
- API docs: http://localhost:8000/docs

## 💰 Cost Estimation

### Twelve Labs Pricing
- **Embedding generation**: $0.0015 per minute
- **5 videos × 15 seconds**: 1.25 minutes = **~$0.002 total**
- **Text queries**: Negligible cost (<$0.01 each)
- **Total POC cost**: **< $1.00**

### Budget Breakdown
```
Video Processing:    $0.002
Text Queries (100):  $1.00
Vector DB (FAISS):   $0.00 (local)
Development:         $0.00 (local)
------------------------
Total Estimated:     $1.00
Target Budget:       $100.00
Remaining:           $99.00
```

## 🔍 Example Queries

- "person talking"
- "outdoor scene"
- "laughter or smiling"
- "office meeting"
- "close-up of face"
- "background music"
- "text or writing on screen"

## 📁 Project Structure

```
semantic_video_search/
├── data/videos/              # Video files (add your own)
├── src/
│   ├── embeddings/
│   │   ├── twelve_labs_client.py    # API client
│   │   └── generate.py              # Embedding generator
│   ├── database/
│   │   └── vector_db.py             # FAISS vector database
│   ├── api/
│   │   └── main.py                  # FastAPI search endpoint
│   └── frontend/
│       └── app.py                   # Streamlit interface
├── config/
│   └── settings.py           # Configuration
├── test_connection.py        # API connectivity test
├── requirements.txt          # Dependencies
└── .env.example             # Environment template
```

## 🛠 Technical Details

### API Features
- Multimodal search (visual, audio, transcript)
- Real-time video processing
- Confidence scoring
- Timestamp-based results

### Architecture
- **Backend**: FastAPI for search API
- **Frontend**: Streamlit for user interface
- **Database**: FAISS for vector storage (with Twelve Labs native search)
- **Embeddings**: Twelve Labs Pegasus + Marengo engines

## 📊 Performance Metrics

- **Processing time**: ~30-60 seconds per video
- **Search latency**: <2 seconds
- **Accuracy**: Multimodal semantic understanding
- **Scalability**: Designed for 5-video POC

## 🔧 Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Check API key in `.env`
   - Verify internet connectivity
   - Confirm account has API access

2. **No Videos Found**
   - Add videos to `data/videos/`
   - Check supported formats (MP4, MOV, AVI)
   - Ensure videos are ≤15 seconds

3. **Embedding Generation Failed**
   - Check video file integrity
   - Verify API quota/billing
   - Wait for processing completion

4. **Search Not Working**
   - Ensure API server is running (port 8000)
   - Check embeddings were generated
   - Verify index creation succeeded

## 🎯 Next Steps

1. **Scale Up**: Add more videos and test performance
2. **Enhance UI**: Add video preview capabilities
3. **Optimize**: Implement caching and batch processing
4. **Deploy**: Move to cloud infrastructure
5. **Monitor**: Add cost tracking and usage analytics
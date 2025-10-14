#!/bin/bash

echo "Starting BullBear Debates..."

cd "$(dirname "$0")/.."

echo "Starting Reddit ingestion..."
python3 backend/ingest_reddit.py &

echo "Starting RSS ingestion..."
python3 backend/ingest_rss.py &

echo "Starting classifier loop..."
python3 backend/classifier_loop.py &

echo "Starting FastAPI server..."
cd backend
uvicorn app:app --reload --port 8000 &
cd ..

echo "Waiting 5 seconds for backend to start..."
sleep 5

echo "Starting Next.js frontend..."
cd frontend
npm run dev &
cd ..

echo "All services started!"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "Press Ctrl+C to stop all services"

wait
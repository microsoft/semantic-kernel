docker image build -t inference_app:latest .

docker run -p 5000:5000 -d inference_app:latest
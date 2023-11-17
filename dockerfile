FROM python:3.11
WORKDIR /code
COPY req.txt req.txt
RUN pip install -r req.txt
RUN pip install --no-cache-dir --upgrade -r req.txt

EXPOSE 8080
COPY . .
CMD ["python3", "app/main.py"]
#Base Image to use
FROM python:3.11-slim

#Copy Requirements.txt file
COPY requirements.txt /requirements.txt

#install all requirements in requirements.txt
RUN pip install -r /requirements.txt

#Copy all files in current directory
COPY . /

# Run migration
CMD ["python3", "migrate.py"]

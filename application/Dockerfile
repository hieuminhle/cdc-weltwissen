#Base Image to use
FROM python:3.11-slim

#Expose port 8080
EXPOSE 8080

#Copy Requirements.txt file into app directory
COPY requirements.txt /app/requirements.txt

#install all requirements in requirements.txt
RUN pip install -r /app/requirements.txt

#Copy all files in current directory into app directory
COPY ./app /app

#Change Working Directory to app directory
WORKDIR /app/backend

#Run the application on port 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

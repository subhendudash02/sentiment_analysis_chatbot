# Setup

Create a file ".env" and paste the mongoDB URL and Gemini API. Don't enclose the string in inverted commas, paste it as it is.

```
GEMINI_API=<gemini-url>
MONGODB_URL=<mongodb-url>
```

# Initialization

1. Front-end

```
npm start
```

2. Backend

```
uvicorn api:app --host 127.0.0.1 --port 8000 --reload
```
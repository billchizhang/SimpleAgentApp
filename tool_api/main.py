from fastapi import FastAPI, HTTPException, Query
from typing import Optional
from datetime import date
import random

app = FastAPI()

@app.get("/weather")
def get_weather(city: str, date_str: str = Query(..., alias="date")):
    """
    Input: city name and date
    Output: a dict with date, city name and a random temp in C
    """
    # Simply generating a random temperature between -10 and 35 Celsius
    temp_c = round(random.uniform(-10, 35), 2)
    return {
        "date": date_str,
        "city": city,
        "temperature_c": temp_c
    }

@app.get("/uppercase")
def get_uppercase(text: str):
    """
    Input: text string
    Output: capitalized text
    """
    return {"text": text.upper()}

@app.get("/lowercase")
def get_lowercase(text: str):
    """
    Input: text string
    Output: lowercase text
    """
    return {"text": text.lower()}

@app.get("/count_word")
def count_word(text: str):
    """
    Input: text string
    Output: number of english words
    """
    # Simple split by whitespace
    word_count = len(text.split())
    return {"word_count": word_count}

@app.get("/calculate")
def calculate(a: float, b: float, operation: str):
    """
    Input: float a, float b, operation (limited to +, -, *, /)
    Output: the result
    """
    if operation == "+":
        result = a + b
    elif operation == "-":
        result = a - b
    elif operation == "*":
        result = a * b
    elif operation == "/":
        if b == 0:
            raise HTTPException(status_code=400, detail="Division by zero")
        result = a / b
    else:
        raise HTTPException(status_code=400, detail="Invalid operation. Supported: +, -, *, /")
    
    return {"result": result}

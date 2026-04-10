TOOLS = [
    {
        "name": "extract_cv",
        "description": (
            "Extract structured information from a CV. "
            "Return candidate info, seniority, technologies with level and experience, and languages."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "cv_text": {
                    "type": "string",
                    "description": "Full raw CV text"
                }
            },
            "required": ["cv_text"],
            "additionalProperties": False
        }
    }
]
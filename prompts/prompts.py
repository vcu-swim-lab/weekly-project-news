# prompts/prompts.py

def individual_instructions(param1, param2, param3, param4):
    return f"Above is JSON data describing {param1} from a GitHub project. Give {param4} describing what this {param2} is about, starting with 'This {param3}'. "

def general_instructions(param1, param2, param3, param4, param5, param6, param7):
    instructions = f"Generate a bulleted list in markdown BASED ON THE DATA ABOVE ONLY where each bullet point starts with a concise topic covered by multiple {param1} in bold text, followed by a colon, followed by a one paragraph summary that must contain {param6} sentences describing the topic's {param2}. This topic, colon, and paragraph summary must all be on the same line on the same bullet point. Do NOT make up content that is not explicitly stated in the data. "
    
    if param5:
        print("Param5 activated")
        instructions += f"After each bullet point summary, there should be a single bullet point containing a list of just the URLs of the {param3} that the topic covers like this [ URL1 , URL2, ...], no other text. Each URL must look like markdown WITHOUT the https://github.com/ in brackets, but only including the https://github.com/ in parentheses (ex. [issues/82966](https://github.com/issues/82966)). In the clickable portion of the hyperlink, include the topic type (e.g., 'issues') and the last portion of the path (e.g., '82966'). "
    
    if param7:
        print("Param7 is activated")
        instructions += f"After each bullet point summary, there should be a single bullet point containing a list of just the URLs of the {param3} that the topic covers like this [ URL1 , URL2, ...], no other text. Each URL must look like markdown WITHOUT the https://github.com/ in brackets, but only including the https://github.com/ in parentheses (ex. [pull/63524](https://github.com/pull/63524)). In the clickable portion of the hyperlink, include the topic type (e.g., 'pull') and the last portion of the path (e.g., '63524'). "
    
    instructions += f"You must clump {param4} with similar topics together, so there are fewer bullet points. Show the output in markdown in a code block. Ensure the link list is formatted as a comma-separated list of shortened links exactly as mentioned earlier. DO NOT deviate from this format.\n"
    
    return instructions

def pull_request_instructions():
    return """
Generate a one-paragraph summary of the pull request describing its purpose, key changes, and context. Do not include specific commit details in this paragraph. Do not add extra content or make up data beyond what is provided.
"""

def discussion_instructions():
    return """First, write a one-paragraph summary capturing the trajectory of a GitHub conversation. Be concise and objective, describing usernames, sentiments, tones, and triggers of tension without including specific topics, claims, or arguments. For example, 'username1 expresses frustration that username2's solution did not work'. Start your answer with 'This GitHub conversation'. 
After the summary, on the same line, provide a single number to 2 decimal places on a 0 to 1 scale, indicating the likelihood of toxicity in future comments. Use a scale where:
- 0.0 to 0.3 means very little toxicity,
- 0.3 to 0.6 means a moderate possibility,
- 0.6 to 1.0 means a high likelihood of toxicity.
Do not add any extra text or newlines in this part.
Then, on the same line, provide a brief, comma-separated list of specific reasons for assigning the score. For example, 'Rapid escalation, aggressive language'. Do not include any other details or newlines."""
DISCUSSION_INSTRUCTIONS = """First, write a one-paragraph summary capturing the trajectory of a GitHub conversation. Be concise and objective, describing usernames, sentiments, tones, and triggers of tension without including specific topics, claims, or arguments. For example, 'username1 expresses frustration that username2's solution did not work'. Start your answer with 'This GitHub conversation'. 
After the summary, on the same line, provide a single number to 2 decimal places on a 0 to 1 scale, indicating the likelihood of toxicity in future comments. Use a scale where:
- 0.0 to 0.3 means very little toxicity,
- 0.3 to 0.6 means a moderate possibility,
- 0.6 to 1.0 means a high likelihood of toxicity.
Do not add any extra text or newlines in this part.
Then, on the same line, provide a brief, comma-separated list of specific reasons for assigning the score. For example, 'Rapid escalation, aggressive language'. Do not include any other details or newlines."""
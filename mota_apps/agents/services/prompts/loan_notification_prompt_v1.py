from langchain.prompts import PromptTemplate

loan_notification_prompt_v1 = PromptTemplate(
    input_variables=["loans"],
    template="""You are a financial platform's notification system.

Available Loans (JSON, unpaid or partially paid loans):
{loans}

Task:
Generate a heartfelt email notification for members with unpaid or partially paid loans. Include:
- Greeting and empathetic introduction.
- List of loans with member name, amount borrowed, amount paid, amount left to pay, borrow date, and status.
- Heartfelt call-to-action to pay loans as soon as possible.
- Closing message with contact information.

Output:
Return a valid JSON object with:
- "message": string (markdown-supported email message)
- "loans": array of objects with member_name and loan details

Ensure:
- Professional, empathetic, and concise message.
- Include all loan details.
- Return only the JSON object, without extra text or code fences.
"""
)
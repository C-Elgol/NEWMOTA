import json
import re
import logging
from datetime import datetime
from typing import Any, List

from django.conf import settings
from django.utils import timezone

from mota_apps.finance.models import Loan
from mota_apps.agents.services.prompts.loan_notification_prompt_v1 import loan_notification_prompt_v1
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

class LoanNotificationAgent:
    def __init__(self, prompt_version: str = "v1") -> None:
        self.prompt_version = prompt_version
        self.prompt_template = loan_notification_prompt_v1
        self.llm = self._load_llm()
        logger.debug(f"Initialized LoanNotificationAgent with prompt_version={prompt_version}")

    def _load_llm(self):
        from mota_apps.agents.services.load_llm import load_llm
        return load_llm(
            model_name="gpt-4-turbo",
            api_key=settings.OPENAI_API_KEY,
            base_url="https://api.openai.com",
            temperature=0.7,
        )

    def get_unpaid_loans(self, season_date: datetime) -> List[Loan]:
        loans = list(
            Loan.objects.filter(
                season_date=season_date,
                status__in=['UNPAID', 'PARTIAL']
            ).select_related("member")
            .order_by("-created")[:100]
        )
        logger.debug(f"Found {len(loans)} unpaid/partially paid loans for season {season_date}")
        return loans

    def build_prompt(self, loans: List[Loan]) -> str:
        loans_data = [
            {
                "member_name": loan.member.get_full_name,
                "amount_borrowed": float(loan.amount_borrowed),
                "amount_paid": float(loan.amount_paid),
                "amount_left_to_pay": float(loan.amount_left_to_pay),
                "borrow_date": loan.borrow_date.strftime('%Y-%m-%d'),
                "status": loan.status,
            }
            for loan in loans
        ]
        loans_json = json.dumps(loans_data, indent=2)
        logger.debug(f"Generated loans JSON: {loans_json}")

        try:
            prompt = self.prompt_template.format(loans=loans_json)
            logger.debug(f"Formatted prompt: {prompt[:200]}...")
            return prompt
        except Exception as e:
            logger.error(f"Prompt formatting failed: {str(e)}")
            fallback_prompt = f"""You are a financial platform's notification system.

Available Loans (JSON, unpaid or partially paid loans):
{loans_json}

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
            logger.debug(f"Fallback prompt: {fallback_prompt[:200]}...")
            return fallback_prompt

    def run_agent(self, season_date: datetime) -> dict[str, Any]:
        loans = self.get_unpaid_loans(season_date)
        if not loans:
            logger.info("No unpaid or partially paid loans found")
            return {"message": "", "loans": []}

        inputs = self.build_prompt(loans)
        message = HumanMessage(content=inputs)
        logger.debug(f"Invoking LLM with message: {message.content[:100]}...")

        try:
            response = self.llm.invoke([message])
            text = getattr(response, "content", "")
            logger.debug(f"Raw LLM response: {text[:200]}...")
        except Exception as e:
            logger.error(f"LLM invocation failed: {str(e)}")
            raise ValueError(f"LLM invocation failed: {str(e)}")

        if not text:
            logger.error("Missing content in agent response")
            raise ValueError("Missing content in agent response")

        cleaned_json = re.sub(r"^```json|```$", "", text.strip(), flags=re.MULTILINE).strip()
        logger.debug(f"Cleaned JSON response: {cleaned_json[:200]}...")

        try:
            parsed_data = json.loads(cleaned_json)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            raise ValueError(f"Invalid JSON output from agent: {e}")

        required_keys = {"message", "loans"}
        if not required_keys.issubset(parsed_data.keys()):
            logger.error(f"Missing required keys in response: {required_keys - parsed_data.keys()}")
            raise ValueError(f"Missing required keys in response: {required_keys - parsed_data.keys()}")

        logger.info(f"Agent run successful, found {len(parsed_data['loans'])} loans")
        logger.debug(f"Generated message: {parsed_data['message'][:200]}...")
        return parsed_data
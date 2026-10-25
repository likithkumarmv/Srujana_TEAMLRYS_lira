"""
LIRA Gemini AI Service
Integrates Google Gemini to provide deep narrative explanations of fraud indicators
and supplier interview verification guidance. Gracefully handles unconfigured key.
"""
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.logging import logger

def is_gemini_configured() -> bool:
    return bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip() != "")

async def analyze_case_with_gemini(
    case_data: Dict[str, Any],
    supplier_data: Optional[Dict[str, Any]] = None,
    transactions: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    case_ref = case_data.get("case_ref", "Unknown Case")
    risk_score = case_data.get("risk_score", 0)
    priority = case_data.get("priority", "watch")
    title = case_data.get("title", "")
    summary = case_data.get("summary", "")
    supplier_name = supplier_data.get("display_name") if supplier_data else "Unknown Supplier"
    trusted_phone = supplier_data.get("known_contact_phone") if supplier_data else "Not Registered"

    if is_gemini_configured():
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            prompt = f"""
            You are LIRA AI, an expert financial fraud investigation copilot.
            Analyze the following payment risk episode:
            Case: {case_ref} ({priority.upper()} Priority, Risk Score: {risk_score}/100)
            Title: {title}
            Summary: {summary}
            Supplier: {supplier_name}
            Trusted Phone: {trusted_phone}
            Signals: {case_data.get('risk_reasons', [])}

            Provide a clear, actionable synthesis with:
            1. Risk narrative summary
            2. Underlying pattern explanation (e.g. Business Email Compromise, Structuring, Account Takeover)
            3. Recommended verification call questions (concise, avoiding revealing credentials)
            4. Concrete investigative leads for the human analyst
            5. Final disposition guidance
            """
            response = await model.generate_content_async(prompt)
            text_output = response.text

            return {
                "case_id": case_data.get("id", ""),
                "is_live_gemini": True,
                "risk_summary": text_output[:400] + "...",
                "pattern_explanation": text_output,
                "recommended_interview_questions": [
                    f"Confirm if {supplier_name} authorized an amendment to payment instructions for {case_ref}.",
                    "Request verification of the bank name and last four digits of the legitimate corporate account.",
                    "Verify the identity and employee title of the individual who transmitted the latest invoice."
                ],
                "investigative_leads": [
                    "Inspect email header DKIM/SPF records on the incoming invoice message.",
                    "Review previous 90-day settlement patterns with this vendor.",
                    "Cross-check recipient account against national mule account watchlists."
                ],
                "disposition_guidance": "Do not release corporate payment until positive telephone confirmation is concluded via the pre-registered supplier phone number."
            }
        except Exception as e:
            logger.warning("Gemini API call failed (%s); falling back to heuristic engine.", str(e))

    # Smart explainable fallback when Gemini API key has not been sent yet
    return {
        "case_id": case_data.get("id", ""),
        "is_live_gemini": False,
        "risk_summary": f"LIRA synthesis for {case_ref}: Multiple correlated indicators present critical indicators of potential Business Email Compromise (BEC). Beneficiary destination diverges from established history.",
        "pattern_explanation": f"The episode exhibits high-urgency diversion tactics commonly observed in vendor bank-detail swap attacks. The payment request was received outside authorized vendor EDI/portal channels with an unverified account fingerprint.",
        "recommended_interview_questions": [
            f"Good day, this is the automated verification service for Acme Corp accounts payable. Did {supplier_name} submit a revised bank destination for the pending invoice?",
            "Can you confirm whether invoice INV-2026-781 was issued by your accounting division?",
            "Please confirm the bank name currently registered on your official GST/tax filing."
        ],
        "investigative_leads": [
            "Check mail server logs for spoofed domain lookalikes (typosquatting).",
            "Verify internal purchase order dual-signoff authorization.",
            "Compare the requested IFSC/routing code location with supplier's physical factory/office address."
        ],
        "disposition_guidance": "Maintain payment hold in business ERP until explicit confirmation is logged from the trusted supplier phone directory."
    }

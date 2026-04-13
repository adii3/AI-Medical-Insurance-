RAG_KB = {
    "age": (
        "Age can materially affect long-term premium risk because chronic conditions and care "
        "utilization tend to increase over time."
    ),
    "bmi": (
        "Higher BMI is commonly associated with elevated metabolic and cardiovascular risk, which "
        "can increase predicted premiums."
    ),
    "smoker_status": (
        "Active smoking is a strong premium driver because it raises expected future care costs "
        "across respiratory and cardiovascular outcomes."
    ),
    "recent_hospitalizations": (
        "Recent hospitalizations indicate recent acute care usage and are a strong proxy for near-term "
        "cost volatility."
    ),
    "base_risk_score": (
        "The base risk score acts as an aggregate measure of prior actuarial or clinical burden."
    ),
    "dependents": (
        "Dependent count can influence utilization patterns and affordability pressure when evaluating "
        "coverage choices."
    ),
    "subscription_tier": (
        "Subscription tier changes pricing expectations because richer coverage usually carries a higher "
        "base premium."
    ),
    "region": (
        "Region affects premiums because healthcare delivery cost structures and market conditions vary by province."
    ),
}


def rag_retrieve(feature_names: list[str], profile: dict, top_n: int = 5) -> list[str]:
    snippets = []
    for feature_name in feature_names:
        snippet = RAG_KB.get(feature_name)
        if snippet and snippet not in snippets:
            snippets.append(snippet)
        if len(snippets) >= top_n:
            break

    if profile.get("smoker_status") and RAG_KB["smoker_status"] not in snippets:
        snippets.append(RAG_KB["smoker_status"])
    return snippets[:top_n]


def build_rag_narrative(
    profile: dict,
    risk_probability: float,
    premium_estimate_monthly: float,
    factors: list[dict],
) -> str:
    risk_label = "HIGH" if risk_probability >= 0.65 else "MODERATE" if risk_probability >= 0.4 else "LOW"
    lines = [
        f"**Estimated Monthly Premium:** ${premium_estimate_monthly:.2f}",
        "",
        f"**Predicted Risk Level:** {risk_label} ({risk_probability:.1%})",
        "",
        "### Top contributing factors",
    ]
    for factor in factors[:5]:
        lines.append(
            f"- `{factor['feature_name']}`: {factor['plain_language']} "
            f"({factor['direction']}, impact {factor['value']:+.2f})"
        )

    snippets = rag_retrieve([factor["feature_name"] for factor in factors[:5]], profile)
    if snippets:
        lines.append("")
        lines.append("### Plain-language context")
        for snippet in snippets:
            lines.append(f"> {snippet}")

    lines.append("")
    lines.append(
        "*Explanation generated from the platform risk model and feature contribution logic.*"
    )
    return "\n".join(lines)

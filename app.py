import streamlit as st


def calculate_utilization(balance: float, limit: float) -> float:
    if limit <= 0:
        return 0.0
    return round((balance / limit) * 100, 2)


def aggregate_accounts(accounts: list[dict]) -> tuple[float, float, float]:
    total_balance = sum(acc["balance"] for acc in accounts if acc["limit"] > 0)
    total_limit = sum(acc["limit"] for acc in accounts if acc["limit"] > 0)
    return total_balance, total_limit, calculate_utilization(total_balance, total_limit)


def estimate_score_improvement(utilization: float, score_gap: float) -> float:
    if utilization <= 10:
        return min(score_gap, 12)
    if utilization <= 30:
        return min(score_gap, 8)
    if utilization <= 50:
        return min(score_gap, 4)
    return min(score_gap, 1.5)


def allocate_budget(accounts: list[dict], budget: float) -> dict[str, float]:
    remaining = budget
    payments = {}
    ordered = sorted(
        [acc for acc in accounts if acc["balance"] > 0 and acc["limit"] > 0],
        key=lambda acc: (calculate_utilization(acc["balance"], acc["limit"]), acc["balance"]),
        reverse=True,
    )

    for acc in ordered:
        if remaining <= 0:
            payments[acc["name"]] = 0.0
            continue
        payment = min(remaining, acc["balance"])
        payments[acc["name"]] = round(payment, 2)
        acc["balance"] = round(acc["balance"] - payment, 2)
        remaining -= payment

    for acc in accounts:
        payments.setdefault(acc["name"], 0.0)

    return payments


def calculate_required_budget(total_balance: float, desired_months: int) -> float:
    """Calculate minimum monthly budget to pay down all debt within desired months."""
    if desired_months <= 0:
        return total_balance
    return round(total_balance / desired_months, 2)


def suggest_budgets(total_balance: float, current_util: float, desired_months: int) -> dict:
    """Suggest realistic monthly budget options based on debt and timeline."""
    minimum = calculate_required_budget(total_balance, desired_months)
    conservative = round(minimum * 1.2, 2)  # 20% buffer for utilization reduction impact
    aggressive = round(minimum * 1.5, 2)    # 50% buffer for faster score improvement
    
    return {
        "minimum": minimum,
        "conservative": conservative,
        "aggressive": aggressive,
    }


def build_timeline(current_score: int, desired_score: int, accounts: list[dict], budget: float):
    timeline = []
    months = 0
    overall_balance, overall_limit, current_util = aggregate_accounts(accounts)
    score = current_score

    while months < 60 and score < desired_score and overall_balance > 0:
        months += 1
        payments = allocate_budget(accounts, budget)
        total_payment = sum(payments.values())
        overall_balance, overall_limit, current_util = aggregate_accounts(accounts)
        score_gap = max(0, desired_score - score)

        improvement = estimate_score_improvement(current_util, score_gap)
        score = min(desired_score, score + improvement)

        if current_util <= 10 and score < desired_score:
            score = min(desired_score, score + 2)
        elif current_util <= 30 and score < desired_score:
            score = min(desired_score, score + 1)

        payment_lines = [f"{name} ${amount:,.2f}" for name, amount in payments.items() if amount > 0]
        account_action = ", ".join(payment_lines) if payment_lines else "no account payments"
        action = f"Pay ${total_payment:,.2f} distributed across {account_action}. Prioritize highest-utilization accounts."
        if current_util <= 10:
            action += " Maintain very low utilization across all revolving accounts."
        elif current_util <= 30:
            action += " Keep overall utilization below 30% to support bureau score movement."

        timeline.append(
            {
                "month": months,
                "balance": round(overall_balance, 2),
                "utilization": current_util,
                "action": action,
                "impact": "Aggregate utilization reduction across multiple accounts improves the reported bureau score trajectory.",
            }
        )

        if overall_balance <= 0 and score < desired_score:
            score = min(desired_score, score + 2)

    return {
        "timeline": timeline,
        "estimated_months": len(timeline),
        "final_score": round(score),
        "final_utilization": current_util,
        "feasible": score >= desired_score,
    }


st.set_page_config(page_title="Canadian Credit Optimization", layout="centered")
st.title("Canadian Credit Planning — Streamlit Demo")
st.markdown(
    "Enter your current Canadian credit profile and monthly paydown budget to generate a month-by-month repayment strategy."
)

with st.form("credit_form"):
    current_score = st.number_input("Current Credit Score", min_value=300, max_value=900, value=620, step=1)
    desired_score = st.number_input("Desired Credit Score", min_value=300, max_value=900, value=750, step=1)

    st.subheader("Credit Card Accounts")
    num_credit_cards = st.number_input("Number of credit cards", min_value=1, max_value=8, value=2, step=1)
    accounts = []
    for i in range(int(num_credit_cards)):
        balance = st.number_input(
            f"Credit Card {i+1} Balance (CAD)",
            min_value=0.0,
            value=0.0 if i != 0 else 3500.0,
            step=100.0,
            format="%.2f",
            key=f"card_balance_{i}",
        )
        limit = st.number_input(
            f"Credit Card {i+1} Limit (CAD)",
            min_value=0.0,
            value=8000.0 if i == 0 else 4000.0 if i == 1 else 0.0,
            step=100.0,
            format="%.2f",
            key=f"card_limit_{i}",
        )
        accounts.append({"name": f"Credit Card {i+1}", "balance": balance, "limit": limit})

    st.subheader("Unsecured Line(s) of Credit")
    num_loc_accounts = st.number_input("Number of unsecured LOCs", min_value=0, max_value=4, value=1, step=1)
    for i in range(int(num_loc_accounts)):
        balance = st.number_input(
            f"Unsecured LOC {i+1} Balance (CAD)",
            min_value=0.0,
            value=2200.0 if i == 0 else 0.0,
            step=100.0,
            format="%.2f",
            key=f"loc_balance_{i}",
        )
        limit = st.number_input(
            f"Unsecured LOC {i+1} Limit (CAD)",
            min_value=0.0,
            value=5000.0 if i == 0 else 0.0,
            step=100.0,
            format="%.2f",
            key=f"loc_limit_{i}",
        )
        accounts.append({"name": f"Unsecured LOC {i+1}", "balance": balance, "limit": limit})

    desired_months = st.number_input("Desired months to achieve the target score", min_value=1, max_value=60, value=12, step=1)
    
    st.subheader("Budget Guidance")
    total_balance, total_limit, current_util = aggregate_accounts(accounts)
    if total_balance > 0:
        suggested_budgets = suggest_budgets(total_balance, current_util, int(desired_months))
        st.info(
            f"📊 **Budget Suggestions for {int(desired_months)} months:**\n\n"
            f"- **Minimum:** ${suggested_budgets['minimum']:,.2f}/month (bare minimum to pay down all debt)\n"
            f"- **Conservative:** ${suggested_budgets['conservative']:,.2f}/month (20% buffer for utilization reduction)\n"
            f"- **Aggressive:** ${suggested_budgets['aggressive']:,.2f}/month (50% buffer for faster score improvement)"
        )
    
    monthly_budget = st.number_input("Your Monthly Paydown Budget (CAD)", min_value=0.0, value=800.0, step=50.0, format="%.2f")
    submitted = st.form_submit_button("Generate Plan")

if submitted:
    if desired_score <= current_score:
        st.warning("Your desired score must be higher than your current score to model an improvement plan.")
    elif monthly_budget <= 0:
        st.warning("Enter a positive monthly paydown budget to build a repayment timeline.")
    else:
        total_balance, total_limit, current_utilization = aggregate_accounts(accounts)

        if total_limit <= 0:
            st.error("Enter at least one valid credit limit to compute utilization.")
        else:
            result = build_timeline(current_score, desired_score, [acc.copy() for acc in accounts], monthly_budget)
            within_target = result['feasible'] and result['estimated_months'] <= desired_months
            timeline_note = (
                f"Achievable within the desired {desired_months} months horizon." if within_target
                else f"The model projects {result['estimated_months']} months to reach the target score under the current budget."
            )

            st.subheader("Executive Summary")
            st.markdown(
                f"- **Target Achievability:** {'Feasible' if result['feasible'] else 'Challenging'}\n"
                f"- **Desired Timeline:** {desired_months} Months\n"
                f"- **Estimated Months to Goal:** {result['estimated_months']} Months\n"
                f"- **Budget Alignment:** {'Within target horizon' if within_target else 'More time required'}\n"
                f"- **Primary Optimization Strategy:** Reduce aggregate utilization by paying down the highest-utilization account buckets first while keeping LOC utilization aligned with credit card reporting thresholds.\n"
                f"- **Timeline Note:** {timeline_note}"
            )

            suggested_budgets = suggest_budgets(total_balance, current_utilization, int(desired_months))
            if monthly_budget < suggested_budgets['minimum']:
                st.warning(
                    f"⚠️ **Budget Alert:** Your monthly budget of ${monthly_budget:,.2f} is below the minimum of ${suggested_budgets['minimum']:,.2f} "
                    f"needed to fully pay down your debt within {int(desired_months)} months. "
                    f"Consider increasing your budget or extending your timeline."
                )
            elif monthly_budget < suggested_budgets['conservative']:
                st.info(
                    f"ℹ️ **Budget Info:** Your budget is adequate but modest. Consider ${suggested_budgets['conservative']:,.2f}/month "
                    f"(conservative) or ${suggested_budgets['aggressive']:,.2f}/month (aggressive) for faster score improvement."
                )
            else:
                st.success(
                    f"✅ **Budget Strength:** Your budget of ${monthly_budget:,.2f} exceeds the minimum required. "
                    f"This will help you reach your score target faster than {int(desired_months)} months."
                )


            st.subheader("Financial Metrics Overview")
            st.write(
                {
                    "Current Credit Score": current_score,
                    "Desired Credit Score": desired_score,
                    "Current Utilization Ratio": f"{current_utilization:.2f}%",
                    "Available Monthly Paydown Budget": f"${monthly_budget:,.2f} CAD",
                }
            )

            st.subheader("Per-Account Utilization Breakdown")
            utilization_rows = []
            for acc in accounts:
                utilization_rows.append(
                    {
                        "Account": acc["name"],
                        "Balance": f"${acc['balance']:,.2f}",
                        "Limit": f"${acc['limit']:,.2f}",
                        "Utilization": f"{calculate_utilization(acc['balance'], acc['limit']):.2f}%",
                    }
                )
            st.table(utilization_rows)

            st.subheader("Month-by-Month Action Plan")
            st.table(
                [
                    {
                        "Month": step["month"],
                        "Target Balance (End of Month)": f"${step['balance']:,.2f}",
                        "Project Utilization %": f"{step['utilization']:.2f}%",
                        "Specific Action Required": step["action"],
                        "Expected Score Impact": step["impact"],
                    }
                    for step in result["timeline"]
                ]
            )

            st.subheader("Strategic Optimization Notes")
            st.markdown(
                "- Reported utilization is driven by all revolving accounts together; keep each credit card and LOC as low as possible.\n"
                "- Allocate payments to accounts with the highest utilization first, then move to lower-utilization accounts if budget remains.\n"
                "- Use statement close dates to ensure the lowest possible balance is reported to Equifax and TransUnion.\n"
                "- Keep existing accounts open and avoid closing older lines while optimizing credit score improvement."
            )

            st.caption(
                "Disclaimer: This output is an algorithmic simulation based on Canadian credit optimization trends and does not constitute a guaranteed credit score outcome."
            )

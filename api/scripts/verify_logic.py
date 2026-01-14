import asyncio
import logging
from agents.explainer import explainer_agent
from agents.evaluator import evaluator_agent
from models.schemas import AgeLevel, UnderstandingState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_backend_logic():
    print("\n--- 🔍 STARTING LOGIC VERIFICATION ---\n")

    # 1. Test Explainer Agent (Age 6)
    print("STEP 1: Testing Explainer Agent (Age 6) for concept 'Gravity'...")
    explanation_6 = await explainer_agent.get_initial_explanation("Gravity", AgeLevel.SIX)
    print(f"\n[Age 6 Explanation]:\n{explanation_6}")
    
    # 2. Test Explainer Agent (Age 10)
    print("\nSTEP 2: Testing Explainer Agent (Age 10) for concept 'Gravity'...")
    explanation_10 = await explainer_agent.get_initial_explanation("Gravity", AgeLevel.TEN)
    print(f"\n[Age 10 Explanation]:\n{explanation_10}")

    # 3. Test Evaluator Agent (The 'Brain')
    print("\nSTEP 3: Testing Evaluator Agent (Understanding Assessment)...")
    child_message = "So gravity is like a magnet in the ground?"
    state, reasoning, hint = await evaluator_agent.evaluate_understanding(
        concept="Gravity",
        last_explanation=explanation_6,
        child_message=child_message
    )
    print(f"\n[Child Message]: {child_message}")
    print(f"[Evaluator State]: {state}")
    print(f"[Evaluator Reasoning]: {reasoning}")
    print(f"[Evaluator Hint]: {hint}")

    # 4. Test Adaptive Response
    print("\nSTEP 4: Testing Adaptive Response based on feedback...")
    history = [
        {"role": "assistant", "content": explanation_6},
        {"role": "user", "content": child_message}
    ]
    adaptive_response = await explainer_agent.get_adaptive_response(
        concept="Gravity",
        age_level=AgeLevel.SIX,
        child_message="Tell me more about the magnet part!",
        history=history
    )
    print(f"\n[AI Adaptive Response]:\n{adaptive_response}")

    print("\n--- ✅ LOGIC VERIFICATION COMPLETE ---\n")

if __name__ == "__main__":
    asyncio.run(verify_backend_logic())


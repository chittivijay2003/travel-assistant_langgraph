"""
Test Script for Travel Assistant API (Assignment D3)
====================================================
This script performs BASIC SANITY CHECKS on the /travel-assistant endpoint.
It validates that the API returns properly formatted travel recommendations.
"""

import requests
import sys
from typing import Dict, Any, Tuple
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================
BASE_URL = f"http://localhost:{os.getenv('API_PORT', '8000')}"
ENDPOINT = "/travel-assistant"
OUTPUT_FILE = "output.txt"


# =============================================================================
# HELPER CLASSES
# =============================================================================
class Colors:
    """ANSI color codes for terminal output"""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


class Logger:
    """Dual logger: writes to both console and file"""

    def __init__(self, filename: str):
        self.filename = filename
        with open(self.filename, "w", encoding="utf-8") as f:
            f.write(f"{'=' * 70}\n")
            f.write(f"Test Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'=' * 70}\n\n")

    def log(self, message: str, color: str = "", file_only: bool = False):
        """Print to console with color and write plain text to file"""
        if not file_only:
            print(f"{color}{message}{Colors.RESET if color else ''}")
        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(message + "\n")


# Initialize logger
logger = Logger(OUTPUT_FILE)


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================
def validate_response_structure(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validates that the response contains required fields:
    - response (string)
    - used_tools (array of strings)
    """
    if not isinstance(data, dict):
        return False, f"Response should be a JSON object, got {type(data).__name__}"

    if "response" not in data:
        return False, "Missing required field: response"

    if "used_tools" not in data:
        return False, "Missing required field: used_tools"

    if not isinstance(data["response"], str):
        return (
            False,
            f"Field 'response' should be a string, got {type(data['response']).__name__}",
        )

    if not isinstance(data["used_tools"], list):
        return (
            False,
            f"Field 'used_tools' should be an array, got {type(data['used_tools']).__name__}",
        )

    for tool in data["used_tools"]:
        if not isinstance(tool, str):
            return (
                False,
                f"Items in 'used_tools' should be strings, got {type(tool).__name__}",
            )

    return True, "Response structure is valid"


def validate_content(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validates that the response contains meaningful content."""
    if len(data.get("response", "")) < 10:
        return False, "response is too short"
    if len(data.get("used_tools", [])) < 1:
        return False, "used_tools should contain at least one tool"

    return True, "Response contains meaningful content"


# =============================================================================
# TEST EXECUTION
# =============================================================================
def run_test(
    test_name: str, payload: Dict[str, Any], expect_success: bool = True
) -> Dict[str, Any]:
    """Runs a single test against the API endpoint."""
    logger.log(f"\n{'=' * 70}", Colors.BLUE)
    logger.log(f"{test_name}", Colors.BLUE + Colors.BOLD)
    logger.log(f"{'=' * 70}", Colors.BLUE)
    logger.log(f"Payload: {payload}")

    result = {"passed": False, "message": ""}

    try:
        response = requests.post(f"{BASE_URL}{ENDPOINT}", json=payload, timeout=120)
        logger.log(f"Status Code: {response.status_code}")

        if response.status_code == 200 and expect_success:
            data = response.json()
            logger.log(f"\n--- Response ---")
            logger.log(f"response: {data.get('response', '')[:100]}...")
            logger.log(f"used_tools: {data.get('used_tools', [])}")

            # Log full response to file
            logger.log(f"\n--- Full Response ---", file_only=True)
            logger.log(str(data), file_only=True)

            # Validate structure
            struct_valid, struct_msg = validate_response_structure(data)
            if not struct_valid:
                result["message"] = struct_msg
                logger.log(f"\n[FAILED] {struct_msg}", Colors.RED)
                return result

            # Validate content
            content_valid, content_msg = validate_content(data)
            if not content_valid:
                result["message"] = content_msg
                logger.log(f"\n[FAILED] {content_msg}", Colors.RED)
                return result

            result["passed"] = True
            result["message"] = "Valid response"
            logger.log(f"\n[PASSED]", Colors.GREEN)
            return result

        elif response.status_code in [400, 422] and not expect_success:
            result["passed"] = True
            result["message"] = "Correctly rejected invalid input"
            logger.log(f"\n[PASSED] Validation error as expected", Colors.GREEN)
            return result

        else:
            result["message"] = f"Unexpected status code: {response.status_code}"
            try:
                logger.log(f"Error detail: {response.json()}")
            except:
                logger.log(f"Response: {response.text[:200]}")
            logger.log(f"\n[FAILED] {result['message']}", Colors.RED)
            return result

    except requests.exceptions.ConnectionError:
        result["message"] = f"Connection refused. Is the server running on {BASE_URL}?"
        logger.log(f"\n[FAILED] {result['message']}", Colors.RED)
        return result
    except requests.exceptions.Timeout:
        result["message"] = "Request timed out after 120 seconds"
        logger.log(f"\n[FAILED] {result['message']}", Colors.RED)
        return result
    except Exception as e:
        result["message"] = f"Error: {str(e)}"
        logger.log(f"\n[FAILED] {result['message']}", Colors.RED)
        return result


# =============================================================================
# MAIN EXECUTION
# =============================================================================
def main():
    """Run all tests and calculate final score"""

    logger.log("=" * 70, Colors.BOLD + Colors.BLUE)
    logger.log("Travel Assistant API (D3) - Test Suite", Colors.BOLD + Colors.BLUE)
    logger.log("=" * 70, Colors.BOLD + Colors.BLUE)
    logger.log("\nThis test validates the /travel-assistant endpoint.\n")

    test_cases = [
        {
            "name": "Test 1: Flight Query",
            "payload": {
                "prompt": "Find me flights to Tokyo, Japan for June 1 - June 5, 2025"
            },
            "expect_success": True,
        },
        {
            "name": "Test 2: Weather Query",
            "payload": {
                "prompt": "What is the weather forecast for Paris, France in July?"
            },
            "expect_success": True,
        },
        {
            "name": "Test 3: Attractions Query",
            "payload": {
                "prompt": "What are the top attractions to visit in New York, USA?"
            },
            "expect_success": True,
        },
        {
            "name": "Test 4: Invalid Input (Missing prompt)",
            "payload": {},
            "expect_success": False,
        },
        {
            "name": "Test 5: Invalid Input (Empty prompt)",
            "payload": {"prompt": ""},
            "expect_success": False,
        },
    ]

    results = []
    for tc in test_cases:
        result = run_test(tc["name"], tc["payload"], tc["expect_success"])
        results.append(result)

    # ==========================================================================
    # CALCULATE FINAL RESULTS
    # ==========================================================================
    tests_passed = sum(1 for r in results if r["passed"])
    total_tests = len(test_cases)

    logger.log(f"\n{'=' * 70}", Colors.BOLD)
    logger.log("FINAL RESULTS", Colors.BOLD + Colors.BLUE)
    logger.log(f"{'=' * 70}", Colors.BOLD)
    logger.log(f"Tests Passed: {tests_passed}/{total_tests}", Colors.BOLD)

    logger.log(f"\n--- Test Breakdown ---")
    for i, (tc, res) in enumerate(zip(test_cases, results), 1):
        status = "✓" if res["passed"] else "✗"
        logger.log(f"  {status} Test {i}: {res['message']}")

    logger.log(f"\n{'=' * 70}")

    if tests_passed == total_tests:
        logger.log("ALL TESTS PASSED!", Colors.GREEN + Colors.BOLD)
        sys.exit(0)
    else:
        logger.log("SOME TESTS FAILED", Colors.RED + Colors.BOLD)
        sys.exit(1)


if __name__ == "__main__":
    main()

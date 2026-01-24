"""
Unit tests for learn-claude-code agents.

These tests don't require API calls - they verify code structure and logic.
"""
import os
import sys
import importlib.util

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# Import Tests
# =============================================================================

def test_imports():
    """Test that all agent modules can be imported."""
    agents = [
        "v0_bash_agent",
        "v0_bash_agent_mini",
        "v1_basic_agent",
        "v2_todo_agent",
        "v3_subagent",
        "v4_skills_agent"
    ]

    for agent in agents:
        spec = importlib.util.find_spec(agent)
        assert spec is not None, f"Failed to find {agent}"
        print(f"  Found: {agent}")

    print("PASS: test_imports")
    return True


# =============================================================================
# TodoManager Tests
# =============================================================================

def test_todo_manager_basic():
    """Test TodoManager basic operations."""
    from v2_todo_agent import TodoManager

    tm = TodoManager()

    # Test valid update
    result = tm.update([
        {"content": "Task 1", "status": "pending", "activeForm": "Doing task 1"},
        {"content": "Task 2", "status": "in_progress", "activeForm": "Doing task 2"},
    ])

    assert "Task 1" in result
    assert "Task 2" in result
    assert len(tm.items) == 2

    print("PASS: test_todo_manager_basic")
    return True


def test_todo_manager_constraints():
    """Test TodoManager enforces constraints."""
    from v2_todo_agent import TodoManager

    tm = TodoManager()

    # Test: only one in_progress allowed (should raise or return error)
    try:
        result = tm.update([
            {"content": "Task 1", "status": "in_progress", "activeForm": "Doing 1"},
            {"content": "Task 2", "status": "in_progress", "activeForm": "Doing 2"},
        ])
        # If no exception, check result contains error
        assert "Error" in result or "error" in result.lower()
    except ValueError as e:
        # Exception is expected - constraint enforced
        assert "in_progress" in str(e).lower()

    # Test: max 20 items
    tm2 = TodoManager()
    many_items = [{"content": f"Task {i}", "status": "pending", "activeForm": f"Doing {i}"} for i in range(25)]
    try:
        tm2.update(many_items)
    except ValueError:
        pass  # Exception is fine
    assert len(tm2.items) <= 20

    print("PASS: test_todo_manager_constraints")
    return True


# =============================================================================
# Reminder Tests
# =============================================================================

def test_reminder_constants():
    """Test reminder constants are defined correctly."""
    from v2_todo_agent import INITIAL_REMINDER, NAG_REMINDER

    assert "<reminder>" in INITIAL_REMINDER
    assert "</reminder>" in INITIAL_REMINDER
    assert "<reminder>" in NAG_REMINDER
    assert "</reminder>" in NAG_REMINDER
    assert "todo" in NAG_REMINDER.lower() or "Todo" in NAG_REMINDER

    print("PASS: test_reminder_constants")
    return True


def test_nag_reminder_in_agent_loop():
    """Test NAG_REMINDER injection is inside agent_loop."""
    import inspect
    from v2_todo_agent import agent_loop, NAG_REMINDER

    source = inspect.getsource(agent_loop)

    # NAG_REMINDER should be referenced in agent_loop
    assert "NAG_REMINDER" in source, "NAG_REMINDER should be in agent_loop"
    assert "rounds_without_todo" in source, "rounds_without_todo check should be in agent_loop"
    assert "results.insert" in source or "results.append" in source, "Should inject into results"

    print("PASS: test_nag_reminder_in_agent_loop")
    return True


# =============================================================================
# Configuration Tests
# =============================================================================

def test_env_config():
    """Test environment variable configuration."""
    # Save original values
    orig_model = os.environ.get("MODEL_ID")
    orig_base = os.environ.get("ANTHROPIC_BASE_URL")

    try:
        # Set test values
        os.environ["MODEL_ID"] = "test-model-123"
        os.environ["ANTHROPIC_BASE_URL"] = "https://test.example.com"

        # Re-import to pick up new env vars
        import importlib
        import v1_basic_agent
        importlib.reload(v1_basic_agent)

        assert v1_basic_agent.MODEL == "test-model-123", f"MODEL should be test-model-123, got {v1_basic_agent.MODEL}"

        print("PASS: test_env_config")
        return True

    finally:
        # Restore original values
        if orig_model:
            os.environ["MODEL_ID"] = orig_model
        else:
            os.environ.pop("MODEL_ID", None)
        if orig_base:
            os.environ["ANTHROPIC_BASE_URL"] = orig_base
        else:
            os.environ.pop("ANTHROPIC_BASE_URL", None)


def test_default_model():
    """Test default model when env var not set."""
    orig = os.environ.pop("MODEL_ID", None)

    try:
        import importlib
        import v1_basic_agent
        importlib.reload(v1_basic_agent)

        assert "claude" in v1_basic_agent.MODEL.lower(), f"Default model should contain 'claude': {v1_basic_agent.MODEL}"

        print("PASS: test_default_model")
        return True

    finally:
        if orig:
            os.environ["MODEL_ID"] = orig


# =============================================================================
# Tool Schema Tests
# =============================================================================

def test_tool_schemas():
    """Test tool schemas are valid."""
    from v1_basic_agent import TOOLS

    required_tools = {"bash", "read_file", "write_file", "edit_file"}
    tool_names = {t["name"] for t in TOOLS}

    assert required_tools.issubset(tool_names), f"Missing tools: {required_tools - tool_names}"

    for tool in TOOLS:
        assert "name" in tool
        assert "description" in tool
        assert "input_schema" in tool
        assert tool["input_schema"].get("type") == "object"

    print("PASS: test_tool_schemas")
    return True


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    tests = [
        test_imports,
        test_todo_manager_basic,
        test_todo_manager_constraints,
        test_reminder_constants,
        test_nag_reminder_in_agent_loop,
        test_env_config,
        test_default_model,
        test_tool_schemas,
    ]

    failed = []
    for test_fn in tests:
        name = test_fn.__name__
        print(f"\n{'='*50}")
        print(f"Running: {name}")
        print('='*50)
        try:
            if not test_fn():
                failed.append(name)
        except Exception as e:
            print(f"FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed.append(name)

    print(f"\n{'='*50}")
    print(f"Results: {len(tests) - len(failed)}/{len(tests)} passed")
    print('='*50)

    if failed:
        print(f"FAILED: {failed}")
        sys.exit(1)
    else:
        print("All unit tests passed!")
        sys.exit(0)

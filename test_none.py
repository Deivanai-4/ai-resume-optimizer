def test_none():
    content = {"experience": None}
    
    # Simulate _validate_and_patch
    validated_exp = []
    try:
        for exp in content.get("experience", []):
            if isinstance(exp, dict):
                validated_exp.append(exp)
        print("Success")
    except Exception as e:
        print("Crash!", type(e), str(e))

test_none()

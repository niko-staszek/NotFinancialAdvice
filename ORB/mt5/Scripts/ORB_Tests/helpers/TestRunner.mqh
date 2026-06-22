//+------------------------------------------------------------------+
//| TestRunner.mqh — shared assertion macros for PAC_Tests scripts    |
//| Output format: each assertion emits exactly one MQL5TEST line     |
//| consumed by tools/run_mql5_tests.py                                |
//+------------------------------------------------------------------+
#property strict

#define EMIT_PASS(name) \
    Print("MQL5TEST {\"test\":\"", name, "\",\"result\":\"PASS\"}")

#define EMIT_FAIL(name, exp, got) \
    Print("MQL5TEST {\"test\":\"", name, \
          "\",\"result\":\"FAIL\",\"expected\":\"", (string)(exp), \
          "\",\"got\":\"", (string)(got), "\"}")

// Float equality with tolerance
#define ASSERT_NEAR(actual, expected, tol, name) { \
    if (MathAbs((actual) - (expected)) > (tol)) { EMIT_FAIL(name, expected, actual); } \
    else { EMIT_PASS(name); } \
}

// Exact double equality
#define ASSERT_EQ(actual, expected, name) ASSERT_NEAR(actual, expected, 1e-9, name)

// Integer equality
#define ASSERT_EQ_INT(actual, expected, name) { \
    if ((actual) != (expected)) { EMIT_FAIL(name, expected, actual); } \
    else { EMIT_PASS(name); } \
}

// Boolean true
#define ASSERT_TRUE(cond, name) { \
    if (!(cond)) { EMIT_FAIL(name, "true", "false"); } \
    else { EMIT_PASS(name); } \
}

// Boolean false
#define ASSERT_FALSE(cond, name) ASSERT_TRUE(!(cond), name)

// String equality
#define ASSERT_STR_EQ(actual, expected, name) { \
    if ((actual) != (expected)) { EMIT_FAIL(name, expected, actual); } \
    else { EMIT_PASS(name); } \
}

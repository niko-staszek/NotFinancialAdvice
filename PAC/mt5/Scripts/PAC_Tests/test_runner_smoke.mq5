//+------------------------------------------------------------------+
//| test_runner_smoke.mq5 — verify TestRunner.mqh macros work         |
//+------------------------------------------------------------------+
#property strict
#include "helpers\\TestRunner.mqh"

void OnStart() {
    ASSERT_NEAR(0.1 + 0.2, 0.3, 1e-9, "float_arithmetic_tolerance");
    ASSERT_EQ_INT(2 + 2, 4, "integer_addition");
    ASSERT_TRUE(true, "literal_true");
    ASSERT_FALSE(false, "literal_false");
    ASSERT_STR_EQ("hello", "hello", "string_equality");
    Print("test_runner_smoke: 5 assertions emitted");
}

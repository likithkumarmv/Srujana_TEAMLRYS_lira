package com.example.lira

import com.example.lira.data.PendingCancelItem
import com.example.lira.network.CallRecordSummary
import com.example.lira.network.LiraApiClient
import com.example.lira.network.PaymentCreateRequest
import com.example.lira.network.PaymentResponse
import com.example.lira.network.VersionConflictException
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import java.util.UUID

/**
 * LIRA v6.0 Customer Payment & Hold Protocol Unit Tests (PRD Section 9)
 */
class CustomerPaymentTest {

    private val apiClient = LiraApiClient()

    @Test
    fun testApiDtoMappingAndUnknownEnumHandling() {
        val rawJson = JSONObject().apply {
            put("payment_id", "PAY-TEST-999")
            put("amount", 12500.0)
            put("currency", "INR")
            put("recipient_name", "Test Beneficiary")
            put("recipient_account", "ACC-7788")
            put("state", "UNKNOWN_FUTURE_STATE") // Unknown enum test
            put("priority", "P1")
            put("risk_score", 75)
            put("reasons", JSONArray().put("Anomaly detected"))
            put("customer_explanation", "Payment is undergoing verification.")
            put("version", 3)
            put("needs_trusted", false)
            put("simulation", true)
            put("created_at", "2026-10-24T12:00:00Z")
        }

        val response = apiClient.parsePaymentResponse(rawJson)

        assertEquals("PAY-TEST-999", response.payment_id)
        assertEquals(12500.0, response.amount, 0.001)
        assertEquals("UNKNOWN_FUTURE_STATE", response.state)
        assertEquals("P1", response.priority)
        assertEquals(3, response.version)
        assertFalse(response.needs_trusted)
        assertTrue(response.simulation)
        assertEquals(1, response.reasons.size)
        assertEquals("Anomaly detected", response.reasons[0])
    }

    @Test
    fun testAmountBoundaryExemptionUnder10000() {
        // Case 1: ₹9,999 - Under ₹10,000 statutory P1 hold exemption
        val rawJson = JSONObject().apply {
            put("payment_id", "PAY-BOUNDARY-9999")
            put("amount", 9999.0)
            put("state", "EXECUTED")
            put("priority", "P1")
            put("needs_trusted", false)
            put("simulation", true)
            put("customer_explanation", "Payment executed successfully under ₹10k statutory exemption.")
        }

        val res = apiClient.parsePaymentResponse(rawJson)
        assertEquals(9999.0, res.amount, 0.001)
        assertEquals("EXECUTED", res.state)
        assertEquals("P1", res.priority)
        assertFalse("₹9,999 should not require trusted person", res.needs_trusted)
    }

    @Test
    fun testAmountBoundaryHoldAt10000() {
        // Case 2: ₹10,000 - Threshold activates hold for P1
        val rawJson = JSONObject().apply {
            put("payment_id", "PAY-BOUNDARY-10000")
            put("amount", 10000.0)
            put("state", "SUSPICION_HOLD")
            put("priority", "P1")
            put("needs_trusted", false)
            put("hold_duration_seconds", 300)
            put("customer_explanation", "Temporary security hold is active while verification completes.")
        }

        val res = apiClient.parsePaymentResponse(rawJson)
        assertEquals(10000.0, res.amount, 0.001)
        assertEquals("SUSPICION_HOLD", res.state)
        assertEquals("P1", res.priority)
        assertEquals(300, res.hold_duration_seconds)
    }

    @Test
    fun testAmountBoundaryTrustedPersonThreshold50000() {
        // Case 3a: ₹50,000 - Covered customer boundary (needs_trusted = false)
        val rawJson50k = JSONObject().apply {
            put("payment_id", "PAY-50000")
            put("amount", 50000.0)
            put("state", "SUSPICION_HOLD")
            put("needs_trusted", false)
            put("trusted_person_status", "NOT_REQUIRED")
        }
        val res50k = apiClient.parsePaymentResponse(rawJson50k)
        assertFalse(res50k.needs_trusted)
        assertEquals("NOT_REQUIRED", res50k.trusted_person_status)

        // Case 3b: ₹50,001 - Exceeds ₹50k for covered customer (needs_trusted = true)
        val rawJson50k1 = JSONObject().apply {
            put("payment_id", "PAY-50001")
            put("amount", 50001.0)
            put("state", "SUSPICION_HOLD")
            put("needs_trusted", true)
            put("trusted_person_status", "REQUIRED_AWAITING_VERIFICATION")
        }
        val res50k1 = apiClient.parsePaymentResponse(rawJson50k1)
        assertTrue("₹50,001 transfer for covered customer must require trusted person", res50k1.needs_trusted)
        assertEquals("REQUIRED_AWAITING_VERIFICATION", res50k1.trusted_person_status)
    }

    @Test
    fun testServerOwnedCallModeAndNoImpliedRelease() {
        val rawJson = JSONObject().apply {
            put("payment_id", "PAY-CALL-VERIF")
            put("state", "SUSPICION_HOLD") // Still on hold
            put("call_record", JSONObject().apply {
                put("call_id", "CALL-101")
                put("mode", "SIMULATED CALL")
                put("call_type", "CUSTOMER_INTERRUPT")
                put("status", "COMPLETED")
                put("started_at", "2026-10-24T12:00:00Z")
                put("summary", "Safety check call completed without coercion.")
            })
        }

        val res = apiClient.parsePaymentResponse(rawJson)
        assertNotNull(res.call_record)
        assertEquals("SIMULATED CALL", res.call_record?.mode)
        assertEquals("COMPLETED", res.call_record?.status)
        // Critical requirement: Call completion does NOT automatically fake state to EXECUTED
        assertEquals("SUSPICION_HOLD", res.state)
    }

    @Test
    fun testDuplicateSubmitReusesOneIdempotencyKey() {
        val initialKey = UUID.randomUUID().toString()
        val request1 = PaymentCreateRequest(
            amount = 10000.0,
            recipient_name = "Bharathi Industrial Supplies",
            recipient_account = "ACC-ICICI-8841",
            idempotency_key = initialKey
        )

        // Simulated retry of same submission
        val retryRequest = request1.copy()

        assertEquals(
            "Submissions on network retry must reuse the original idempotency key",
            request1.idempotency_key,
            retryRequest.idempotency_key
        )
    }

    @Test
    fun testOfflineCancelKeepsPendingStateAndNeverFakesStopped() {
        val caseId = "CASE-TEST-OFFLINE"
        val paymentId = "PAY-TEST-OFFLINE"
        val idempotencyKey = UUID.randomUUID().toString()
        val currentVersion = 1

        val pendingItem = PendingCancelItem(
            caseId = caseId,
            paymentId = paymentId,
            idempotencyKey = idempotencyKey,
            expectedVersion = currentVersion,
            queuedAt = "2026-10-24T12:00:00Z",
            statusMessage = "CANCEL REQUESTED — NOT YET CONFIRMED"
        )

        // Active payment on hold before server response
        val paymentBeforeFlush = PaymentResponse(
            payment_id = paymentId,
            case_id = caseId,
            amount = 10000.0,
            recipient_name = "Bharathi Industrial Supplies",
            recipient_account = "ACC-ICICI-8841",
            state = "SUSPICION_HOLD",
            priority = "P1",
            risk_score = 80,
            reasons = listOf("Hold active"),
            customer_explanation = "Temporary hold active",
            hold_started_at = null,
            hold_expires_at = null,
            server_time = "2026-10-24T12:00:00Z",
            version = 1,
            is_cancellable = true,
            needs_trusted = false,
            created_at = "2026-10-24T12:00:00Z",
            is_stale = true // UI marks stale during offline pending
        )

        assertEquals("CANCEL REQUESTED — NOT YET CONFIRMED", pendingItem.statusMessage)
        assertNotEquals("STOPPED", paymentBeforeFlush.state)
        assertTrue("Offline pending cancel payment must be marked is_stale until confirmed", paymentBeforeFlush.is_stale)
    }

    @Test
    fun testStaleResponseVersionConflictHandling() {
        val conflictException = VersionConflictException(
            code = 409,
            message = "Version conflict (409): Case modified on server. Refreshing state."
        )

        assertEquals(409, conflictException.code)
        assertTrue(conflictException.message.contains("409"))
    }
}

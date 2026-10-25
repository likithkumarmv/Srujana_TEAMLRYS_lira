package com.example.lira.data

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class SyncVersionResponse(
    val version: Int = 142,
    val sync_version: Int? = null,
    val server_time: String = ""
) {
    val effectiveVersion: Int get() = sync_version ?: version
}

@Serializable
data class TrustedPerson(
    val name: String = "Anil",
    val phone: String = "+91 98765 43210",
    val active_from: String = "26 Oct",
    val status: String = "ACTIVE"
)

@Serializable
data class CustomerProfile(
    val id: String = "CUST-RAO-01",
    val name: String = "Mrs. R. Rao",
    val email: String = "mrs.rao@demobank.lira",
    val role: String = "CUSTOMER",
    val account_number: String = "ACC-5012-4821",
    val balance_paise: Long = 124500000L, // ₹12,45,000
    val reserved_paise: Long = 0L,
    val trusted_person: TrustedPerson = TrustedPerson(),
    val open_payment: PaymentItem? = null,
    val version: Int = 1
)

@Serializable
data class DemoTokenRequest(
    val email: String,
    val password: String? = null
)

@Serializable
data class DemoTokenResponse(
    @SerialName("access_token") val accessToken: String = "",
    @SerialName("token_type") val tokenType: String = "bearer",
    val role: String? = null,
    val email: String? = null,
    @SerialName("customer_id") val customerId: String? = null
)

@Serializable
data class PaymentItem(
    val id: String = "",
    val payment_id: String = "",
    val case_id: String? = null,
    val amount: Double = 0.0,
    val amount_paise: Long? = null,
    val currency: String = "INR",
    val recipient_name: String = "",
    val payee_name: String = "",
    val recipient_account: String = "",
    val payee_account: String = "",
    val memo: String? = null,
    val purpose: String? = null,
    val state: String = "EXECUTED", // EXECUTED, PAUSED, STOPPED
    val raw_state: String = "",     // LAG_HOLD, SUSPICION_HOLD, etc.
    val priority: String = "PASS",  // P1, P2, P3, PASS
    val one_line_reason: String = "",
    val reasons: List<String> = emptyList(),
    val time_left_s: Int = 0,
    val hold_started_at: String? = null,
    val hold_expires_at: String? = null,
    val version: Int = 1,
    val call_status_lines: List<String> = emptyList(),
    val officer_clearance_recorded: Boolean = false,
    val officer_clearance_note: String? = null,
    val created_at: String = "",
    val timestamp: String = "",
    val is_cancellable: Boolean = false
) {
    val effectiveId: String get() = if (payment_id.isNotBlank()) payment_id else id
    val effectiveAmount: Double get() = if (amount > 0.0) amount else ((amount_paise ?: 0L) / 100.0)
    val effectiveRecipientName: String get() = recipient_name.ifBlank { payee_name.ifBlank { "Demo Payee" } }
    val effectiveRecipientAccount: String get() = recipient_account.ifBlank { payee_account }
    val effectiveMemo: String? get() = memo ?: purpose
    val effectiveCreatedAt: String get() = created_at.ifBlank { timestamp }
}

@Serializable
data class PaymentListResponse(
    val items: List<PaymentItem> = emptyList(),
    val total: Int = 0
)

@Serializable
data class PaymentCreateRequest(
    val amount: Double? = null,
    val amount_paise: Long? = null,
    val payee_account_id: String? = null,
    val recipient_name: String? = null,
    val recipient_account: String? = null,
    val purpose: String? = "Transfer",
    val memo: String? = null,
    val idempotency_key: String
)

@Serializable
data class CancelRequest(
    val idempotency_key: String,
    val displayed_version: Int,
    val reason: String = "Customer cancelled via mobile app"
)

@Serializable
data class CancelResponse(
    val cancelled: Boolean,
    val case_id: String,
    val status: String,
    val version: Int,
    val reason: String
)

@Serializable
data class ReconfirmRequest(
    val case_id: String,
    val displayed_version: Int,
    val idempotency_key: String
)

@Serializable
data class ReconfirmResponse(
    val confirmed: Boolean,
    val case_id: String = "",
    val state: String = "PAUSED",
    val version: Int = 1,
    val message: String
)

@Serializable
data class HelpRequest(
    val case_id: String,
    val idempotency_key: String
)

@Serializable
data class HelpResponse(
    val message: String
)

@Serializable
data class TrustedPersonRequest(
    val name: String,
    val phone: String,
    val idempotency_key: String
)

@Serializable
data class PayeeItem(
    val id: String,
    val name: String,
    val account: String,
    val category: String = "Verified",
    val description: String = ""
)

@Serializable
data class PayeeListResponse(
    val payees: List<PayeeItem> = emptyList()
)

data class PendingCancelAction(
    val caseId: String,
    val paymentId: String,
    val idempotencyKey: String,
    val displayedVersion: Int,
    val requestedAt: Long = System.currentTimeMillis()
)

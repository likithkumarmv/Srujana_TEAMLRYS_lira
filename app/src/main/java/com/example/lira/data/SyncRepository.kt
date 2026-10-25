package com.example.lira.data

import android.util.Log
import com.example.lira.network.NetworkClient
import com.example.lira.network.SupabaseAuthManager
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.serialization.json.*
import retrofit2.HttpException
import java.text.NumberFormat
import java.text.SimpleDateFormat
import java.util.*
import java.util.concurrent.ConcurrentHashMap

object SyncRepository {
    private const val TAG = "SyncRepository"

    private val _customerProfile = MutableStateFlow<CustomerProfile?>(null)
    val customerProfile: StateFlow<CustomerProfile?> = _customerProfile.asStateFlow()

    private val _payments = MutableStateFlow<List<PaymentItem>>(emptyList())
    val payments: StateFlow<List<PaymentItem>> = _payments.asStateFlow()

    private val _openPayment = MutableStateFlow<PaymentItem?>(null)
    val openPayment: StateFlow<PaymentItem?> = _openPayment.asStateFlow()

    private val _payees = MutableStateFlow<List<PayeeItem>>(emptyList())
    val payees: StateFlow<List<PayeeItem>> = _payees.asStateFlow()

    private val _isOffline = MutableStateFlow(false)
    val isOffline: StateFlow<Boolean> = _isOffline.asStateFlow()

    private val _lastSuccessfulSyncAt = MutableStateFlow<Long?>(null)
    val lastSuccessfulSyncAt: StateFlow<Long?> = _lastSuccessfulSyncAt.asStateFlow()

    private val _offlineBannerText = MutableStateFlow<String?>(null)
    val offlineBannerText: StateFlow<String?> = _offlineBannerText.asStateFlow()

    private val _isSyncing = MutableStateFlow(false)
    val isSyncing: StateFlow<Boolean> = _isSyncing.asStateFlow()

    private val _actionInProgress = MutableStateFlow(false)
    val actionInProgress: StateFlow<Boolean> = _actionInProgress.asStateFlow()

    private val _conflictMessage = MutableStateFlow<String?>(null)
    val conflictMessage: StateFlow<String?> = _conflictMessage.asStateFlow()

    private val _endStateNotice = MutableStateFlow<String?>(null)
    val endStateNotice: StateFlow<String?> = _endStateNotice.asStateFlow()

    private val _pendingCancel = MutableStateFlow<PendingCancelAction?>(null)
    val pendingCancel: StateFlow<PendingCancelAction?> = _pendingCancel.asStateFlow()

    // IN-MEMORY IDEMPOTENCY ONLY (Zero SharedPreferences/SQLite!)
    private val inMemoryIdempotencyKeys = ConcurrentHashMap<String, String>()

    private var pollingJob: Job? = null
    private var cancelRetryJob: Job? = null
    private var livenessJob: Job? = null
    private var lastKnownVersion = -1

    fun getOrCreateIdempotencyKey(actionId: String): String {
        return inMemoryIdempotencyKeys.getOrPut(actionId) { UUID.randomUUID().toString() }
    }

    fun clearIdempotencyKey(actionId: String) {
        inMemoryIdempotencyKeys.remove(actionId)
    }

    fun clearConflictMessage() {
        _conflictMessage.value = null
    }

    fun clearEndStateNotice() {
        _endStateNotice.value = null
    }

    fun startForegroundSync(scope: CoroutineScope) {
        stopForegroundSync()

        // 1. Version polling job (every 2s)
        pollingJob = scope.launch(Dispatchers.IO) {
            while (isActive) {
                checkAndPollSync()
                delay(2000L)
            }
        }

        // 2. Liveness & offline threshold checker (6s rule)
        livenessJob = scope.launch(Dispatchers.IO) {
            while (isActive) {
                val last = _lastSuccessfulSyncAt.value
                val now = System.currentTimeMillis()
                if (last != null && (now - last) > 6000L) {
                    _isOffline.value = true
                    _offlineBannerText.value = "Offline — showing last confirmed data from ${formatIstTime(last)}"
                }
                delay(1000L)
            }
        }

        // 3. Offline cancellation retry job (every 3s)
        cancelRetryJob = scope.launch(Dispatchers.IO) {
            while (isActive) {
                val pending = _pendingCancel.value
                if (pending != null && !_isOffline.value) {
                    executeCancel(pending)
                }
                delay(3000L)
            }
        }
    }

    fun stopForegroundSync() {
        pollingJob?.cancel()
        pollingJob = null
        livenessJob?.cancel()
        livenessJob = null
        cancelRetryJob?.cancel()
        cancelRetryJob = null
    }

    suspend fun checkAndPollSync() {
        try {
            val versionResp = NetworkClient.apiService.getSyncVersion()
            val now = System.currentTimeMillis()
            _lastSuccessfulSyncAt.value = now
            _isOffline.value = false
            _offlineBannerText.value = null

            if (versionResp.effectiveVersion != lastKnownVersion || _customerProfile.value == null) {
                lastKnownVersion = versionResp.effectiveVersion
                refetchAll()
            }
        } catch (e: Exception) {
            Log.w(TAG, "Sync version poll failed: ${e.message}")
            if (!SupabaseAuthManager.isSignedIn()) {
                // If user was signed out (e.g. auth failed), do not treat as offline
                return
            }
            if (e is HttpException && e.code() == 401) {
                return
            }
            val now = System.currentTimeMillis()
            val last = _lastSuccessfulSyncAt.value
            if (last == null || (now - last) > 6000L) {
                _isOffline.value = true
                val timeStr = if (last != null) formatIstTime(last) else formatIstTime(now)
                _offlineBannerText.value = "Offline — showing last confirmed data from $timeStr"
            }
        }
    }

    suspend fun refetchAll() = withContext(Dispatchers.IO) {
        _isSyncing.value = true
        try {
            val email = SupabaseAuthManager.authenticatedEmail.value
            val profile = NetworkClient.apiService.getMe(email)
            _customerProfile.value = profile

            val paymentsElement = NetworkClient.apiService.getPayments(email)
            val items: List<PaymentItem> = if (paymentsElement is JsonArray) {
                NetworkClient.json.decodeFromJsonElement<List<PaymentItem>>(paymentsElement)
            } else if (paymentsElement is JsonObject && paymentsElement.containsKey("items")) {
                NetworkClient.json.decodeFromJsonElement<PaymentListResponse>(paymentsElement).items
            } else {
                emptyList()
            }

            // Normalize state (e.g. SUSPICION_HOLD -> PAUSED)
            val normalizedItems = items.map { item ->
                val mappedState = when (item.state.uppercase()) {
                    "SUSPICION_HOLD", "LAG_HOLD", "HELD", "HOLD", "PAUSED" -> "PAUSED"
                    "STOPPED", "CANCELLED", "BLOCKED" -> "STOPPED"
                    else -> "EXECUTED"
                }
                item.copy(state = mappedState, raw_state = item.state)
            }

            _payments.value = normalizedItems

            // Open payment if active paused/held
            _openPayment.value = profile.open_payment ?: normalizedItems.firstOrNull { it.state == "PAUSED" }

            // Payees
            if (_payees.value.isEmpty()) {
                try {
                    val payeesResp = NetworkClient.apiService.getPayees()
                    _payees.value = payeesResp.payees
                } catch (_: Exception) {}
            }

            val now = System.currentTimeMillis()
            _lastSuccessfulSyncAt.value = now
            _isOffline.value = false
            _offlineBannerText.value = null
        } catch (e: Exception) {
            Log.e(TAG, "Refetch all data failed: ${e.message}", e)
        } finally {
            _isSyncing.value = false
        }
    }

    suspend fun submitPayment(
        amount: Double,
        recipientName: String,
        recipientAccount: String,
        memo: String?
    ): Result<PaymentItem> = withContext(Dispatchers.IO) {
        val actionKey = "PAYMENT_${recipientAccount}_$amount"
        val idemKey = getOrCreateIdempotencyKey(actionKey)
        _actionInProgress.value = true

        try {
            val email = SupabaseAuthManager.authenticatedEmail.value
            val resp = NetworkClient.apiService.createPayment(
                PaymentCreateRequest(
                    amount = amount,
                    amount_paise = (amount * 100).toLong(),
                    payee_account_id = recipientAccount,
                    recipient_name = recipientName,
                    recipient_account = recipientAccount,
                    purpose = memo ?: "Transfer",
                    memo = memo,
                    idempotency_key = idemKey
                ),
                email = email
            )

            if (resp.isSuccessful && resp.body() != null) {
                clearIdempotencyKey(actionKey)
                val bodyElement = resp.body()!!
                val payment = parsePaymentCreateResult(bodyElement, amount, recipientName, recipientAccount, memo)
                refetchAll()
                Result.success(payment)
            } else {
                val err = resp.errorBody()?.string() ?: "Payment request failed (${resp.code()})"
                Result.failure(Exception(err))
            }
        } catch (e: Exception) {
            Result.failure(e)
        } finally {
            _actionInProgress.value = false
        }
    }

    private fun parsePaymentCreateResult(
        element: JsonElement,
        fallbackAmount: Double,
        fallbackRecipientName: String,
        fallbackRecipientAccount: String,
        fallbackMemo: String?
    ): PaymentItem {
        return try {
            if (element is JsonObject) {
                val pObj = element["payment"]?.let { if (it is JsonObject) it else null }
                val cObj = element["case"]?.let { if (it is JsonObject) it else null }
                val rawState = element["state"]?.jsonPrimitive?.contentOrNull
                    ?: cObj?.get("state")?.jsonPrimitive?.contentOrNull
                    ?: "EXECUTED"

                val mappedState = when (rawState.uppercase()) {
                    "SUSPICION_HOLD", "LAG_HOLD", "HELD", "HOLD", "PAUSED" -> "PAUSED"
                    "STOPPED", "CANCELLED", "BLOCKED" -> "STOPPED"
                    else -> "EXECUTED"
                }

                val pId = pObj?.get("id")?.jsonPrimitive?.contentOrNull
                    ?: cObj?.get("transaction_id")?.jsonPrimitive?.contentOrNull
                    ?: "TXN-${System.currentTimeMillis()}"

                val cId = cObj?.get("id")?.jsonPrimitive?.contentOrNull

                val amt = pObj?.get("amount")?.jsonPrimitive?.doubleOrNull
                    ?: (pObj?.get("amount_paise")?.jsonPrimitive?.longOrNull?.let { it / 100.0 })
                    ?: (cObj?.get("amount_paise")?.jsonPrimitive?.longOrNull?.let { it / 100.0 })
                    ?: fallbackAmount

                val recName = pObj?.get("receiver_name")?.jsonPrimitive?.contentOrNull
                    ?: cObj?.get("masked_payee")?.jsonPrimitive?.contentOrNull
                    ?: fallbackRecipientName

                val recAcc = pObj?.get("receiver_account")?.jsonPrimitive?.contentOrNull
                    ?: cObj?.get("payee_account")?.jsonPrimitive?.contentOrNull
                    ?: fallbackRecipientAccount

                val reasons = cObj?.get("reasons")?.let {
                    if (it is JsonArray) {
                        it.mapNotNull { r -> r.jsonPrimitive.contentOrNull }
                    } else emptyList()
                } ?: emptyList()

                val policyOutcome = cObj?.get("policy_outcome")?.jsonPrimitive?.contentOrNull ?: ""
                val priority = cObj?.get("priority")?.jsonPrimitive?.contentOrNull ?: "PASS"

                PaymentItem(
                    id = pId,
                    payment_id = pId,
                    case_id = cId,
                    amount = amt,
                    recipient_name = recName,
                    recipient_account = recAcc,
                    memo = fallbackMemo,
                    state = mappedState,
                    raw_state = rawState,
                    priority = priority,
                    one_line_reason = policyOutcome,
                    reasons = reasons,
                    time_left_s = 900,
                    version = element["sync_version"]?.jsonPrimitive?.intOrNull ?: 1
                )
            } else {
                NetworkClient.json.decodeFromJsonElement<PaymentItem>(element)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error parsing payment response: ${e.message}", e)
            PaymentItem(
                id = "TXN-${System.currentTimeMillis()}",
                amount = fallbackAmount,
                recipient_name = fallbackRecipientName,
                recipient_account = fallbackRecipientAccount,
                memo = fallbackMemo,
                state = "PAUSED"
            )
        }
    }

    fun requestCancelPayment(caseId: String, paymentId: String, currentVersion: Int, scope: CoroutineScope) {
        val actionKey = "CANCEL_$caseId"
        val idemKey = getOrCreateIdempotencyKey(actionKey)
        val pending = PendingCancelAction(
            caseId = caseId,
            paymentId = paymentId,
            idempotencyKey = idemKey,
            displayedVersion = currentVersion
        )
        _pendingCancel.value = pending

        if (!_isOffline.value) {
            scope.launch(Dispatchers.IO) {
                executeCancel(pending)
            }
        }
    }

    private suspend fun executeCancel(action: PendingCancelAction) = withContext(Dispatchers.IO) {
        try {
            val resp = NetworkClient.apiService.cancelCase(
                id = action.caseId,
                req = CancelRequest(
                    idempotency_key = action.idempotencyKey,
                    displayed_version = action.displayedVersion
                )
            )

            if (resp.isSuccessful) {
                val body = resp.body()
                clearIdempotencyKey("CANCEL_${action.caseId}")
                _pendingCancel.value = null

                if (body != null) {
                    if (!body.cancelled) {
                        _endStateNotice.value = body.reason
                    }
                    refetchAll()
                }
            } else if (resp.code() == 409) {
                clearIdempotencyKey("CANCEL_${action.caseId}")
                _pendingCancel.value = null
                _conflictMessage.value = "This payment changed. Showing the latest status."
                refetchAll()
            }
        } catch (e: Exception) {
            Log.w(TAG, "Cancel attempt deferred (offline or network error): ${e.message}")
        }
    }

    suspend fun reconfirmPayment(caseId: String, displayedVersion: Int): Result<ReconfirmResponse> = withContext(Dispatchers.IO) {
        val actionKey = "RECONFIRM_$caseId"
        val idemKey = getOrCreateIdempotencyKey(actionKey)
        _actionInProgress.value = true

        try {
            val resp = NetworkClient.apiService.reconfirmPayment(
                ReconfirmRequest(
                    case_id = caseId,
                    displayed_version = displayedVersion,
                    idempotency_key = idemKey
                )
            )

            if (resp.isSuccessful && resp.body() != null) {
                clearIdempotencyKey(actionKey)
                val body = resp.body()!!
                refetchAll()
                Result.success(body)
            } else if (resp.code() == 409) {
                clearIdempotencyKey(actionKey)
                _conflictMessage.value = "This payment changed. Showing the latest status."
                refetchAll()
                Result.failure(Exception("This payment changed. Showing the latest status."))
            } else {
                Result.failure(Exception(resp.errorBody()?.string() ?: "Reconfirm failed (${resp.code()})"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        } finally {
            _actionInProgress.value = false
        }
    }

    suspend fun requestHelp(caseId: String): Result<String> = withContext(Dispatchers.IO) {
        val actionKey = "HELP_$caseId"
        val idemKey = getOrCreateIdempotencyKey(actionKey)
        _actionInProgress.value = true

        try {
            val resp = NetworkClient.apiService.requestHelp(
                HelpRequest(
                    case_id = caseId,
                    idempotency_key = idemKey
                )
            )

            if (resp.isSuccessful && resp.body() != null) {
                clearIdempotencyKey(actionKey)
                refetchAll()
                Result.success(resp.body()!!.message)
            } else {
                Result.failure(Exception("Help request failed"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        } finally {
            _actionInProgress.value = false
        }
    }

    suspend fun updateTrustedPerson(name: String, phone: String): Result<String> = withContext(Dispatchers.IO) {
        val actionKey = "TRUSTED_${name}_$phone"
        val idemKey = getOrCreateIdempotencyKey(actionKey)
        _actionInProgress.value = true

        try {
            val resp = NetworkClient.apiService.updateTrustedPerson(
                TrustedPersonRequest(
                    name = name,
                    phone = phone,
                    idempotency_key = idemKey
                )
            )

            if (resp.isSuccessful && resp.body() != null) {
                clearIdempotencyKey(actionKey)
                refetchAll()
                Result.success(resp.body()!!.message)
            } else {
                Result.failure(Exception("Failed to update trusted person"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        } finally {
            _actionInProgress.value = false
        }
    }

    // Currency and time formatters
    fun formatInr(amount: Double): String {
        return try {
            val format = NumberFormat.getCurrencyInstance(Locale("en", "IN"))
            format.maximumFractionDigits = 0
            format.format(amount)
        } catch (_: Exception) {
            "₹%,.0f".format(amount)
        }
    }

    fun formatPaise(paise: Long): String {
        return formatInr(paise / 100.0)
    }

    fun formatIstTime(timestampMillis: Long): String {
        val sdf = SimpleDateFormat("HH:mm:ss", Locale.ENGLISH).apply {
            timeZone = TimeZone.getTimeZone("Asia/Kolkata")
        }
        return sdf.format(Date(timestampMillis))
    }

    fun formatIstIso(isoStr: String?): String {
        if (isoStr.isNullOrBlank()) return "--:--"
        return try {
            val iso = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.ENGLISH).apply {
                timeZone = TimeZone.getTimeZone("UTC")
            }
            val target = SimpleDateFormat("dd MMM, HH:mm", Locale.ENGLISH).apply {
                timeZone = TimeZone.getTimeZone("Asia/Kolkata")
            }
            val date = iso.parse(isoStr.take(19)) ?: Date()
            target.format(date)
        } catch (_: Exception) {
            isoStr
        }
    }
}

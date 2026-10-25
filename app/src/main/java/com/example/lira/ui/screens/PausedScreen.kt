package com.example.lira.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.lira.data.PaymentItem
import com.example.lira.data.SyncRepository
import com.example.lira.ui.components.OfflineBanner
import com.example.lira.ui.components.PaymentStateChip
import com.example.lira.ui.components.PermanentSimulationBanner
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

@Composable
fun PausedScreen(
    initialPayment: PaymentItem,
    onNavigateBack: () -> Unit,
    onNavigateToResult: (PaymentItem) -> Unit
) {
    val coroutineScope = rememberCoroutineScope()
    val isOffline by SyncRepository.isOffline.collectAsState()
    val offlineText by SyncRepository.offlineBannerText.collectAsState()
    val actionInProgress by SyncRepository.actionInProgress.collectAsState()
    val pendingCancel by SyncRepository.pendingCancel.collectAsState()
    val conflictMessage by SyncRepository.conflictMessage.collectAsState()
    val endStateNotice by SyncRepository.endStateNotice.collectAsState()

    // Observe latest updates to this payment from SyncRepository
    val openPayment by SyncRepository.openPayment.collectAsState()
    val allPayments by SyncRepository.payments.collectAsState()

    val currentPayment = remember(openPayment, allPayments) {
        val updated = allPayments.firstOrNull { it.effectiveId == initialPayment.effectiveId || it.case_id == initialPayment.case_id }
            ?: (if (openPayment?.effectiveId == initialPayment.effectiveId || openPayment?.case_id == initialPayment.case_id) openPayment else null)
            ?: initialPayment
        updated
    }

    // Auto-navigate to result if payment transitioned out of PAUSED
    LaunchedEffect(currentPayment.state) {
        if (currentPayment.state == "EXECUTED" || currentPayment.state == "STOPPED") {
            onNavigateToResult(currentPayment)
        }
    }

    // Local countdown ticker re-synced on each refetch
    var secondsRemaining by remember { mutableIntStateOf(currentPayment.time_left_s) }
    LaunchedEffect(currentPayment.time_left_s) {
        secondsRemaining = currentPayment.time_left_s
    }

    LaunchedEffect(Unit) {
        while (true) {
            delay(1000L)
            if (secondsRemaining > 0) {
                secondsRemaining -= 1
            }
        }
    }

    var showCautionDialog by remember { mutableStateOf(false) }
    var backendAnswerDialog by remember { mutableStateOf<String?>(null) }
    var helpDialogMessage by remember { mutableStateOf<String?>(null) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF090D16))
    ) {
        PermanentSimulationBanner()

        if (isOffline && offlineText != null) {
            OfflineBanner(text = offlineText ?: "Offline")
        }

        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 18.dp, vertical = 14.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Header bar
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(onClick = onNavigateBack) {
                    Text("←", color = Color.White, fontSize = 22.sp)
                }
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    text = "Payment Status",
                    color = Color.White,
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold
                )
            }

            // Conflict banner (409)
            if (conflictMessage != null) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(10.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF7F1D1D))
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(12.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = conflictMessage ?: "",
                            color = Color.White,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.weight(1f)
                        )
                        Text(
                            text = "✕",
                            color = Color.White,
                            fontSize = 14.sp,
                            modifier = Modifier.clickable { SyncRepository.clearConflictMessage() }
                        )
                    }
                }
            }

            // Main Held Banner Card
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(18.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFF1E1508)),
                border = CardDefaults.outlinedCardBorder().copy(brush = androidx.compose.ui.graphics.SolidColor(Color(0xFFD97706)))
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(20.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    // Pill
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(8.dp))
                            .background(Color(0xFF78350F))
                            .border(1.dp, Color(0xFFF59E0B), RoundedCornerShape(8.dp))
                            .padding(horizontal = 12.dp, vertical = 6.dp)
                    ) {
                        Text(
                            text = "SIMULATED PAYMENT · HELD BY LIRA",
                            color = Color(0xFFFDE68A),
                            fontSize = 12.sp,
                            fontWeight = FontWeight.ExtraBold,
                            fontFamily = FontFamily.Monospace,
                            letterSpacing = 0.5.sp
                        )
                    }

                    Spacer(modifier = Modifier.height(14.dp))

                    Text(
                        text = "Your money has not left your account.",
                        color = Color.White,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold,
                        textAlign = TextAlign.Center
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    Text(
                        text = currentPayment.one_line_reason.ifBlank {
                            "This payment differs from your recent activity. A temporary security hold is active while safety verification completes."
                        },
                        color = Color(0xFFCBD5E1),
                        fontSize = 13.sp,
                        textAlign = TextAlign.Center,
                        lineHeight = 18.sp
                    )

                    Spacer(modifier = Modifier.height(18.dp))

                    // Amount
                    Text(
                        text = SyncRepository.formatInr(currentPayment.effectiveAmount),
                        color = Color.White,
                        fontSize = 36.sp,
                        fontWeight = FontWeight.ExtraBold
                    )
                    Text(
                        text = "To: ${currentPayment.effectiveRecipientName} (${currentPayment.effectiveRecipientAccount})",
                        color = Color(0xFF94A3B8),
                        fontSize = 13.sp
                    )
                }
            }

            // Timer & Status Card
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFF131D2E)),
                border = CardDefaults.outlinedCardBorder().copy(brush = androidx.compose.ui.graphics.SolidColor(Color(0xFF26354D)))
            ) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "HOLD TIME REMAINING",
                            color = Color(0xFF94A3B8),
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace
                        )
                        Text(
                            text = if (secondsRemaining > 0) "${secondsRemaining}s" else "Hold Concluded",
                            color = if (secondsRemaining > 0) Color(0xFFFBBF24) else Color(0xFF34D399),
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace
                        )
                    }

                    HorizontalDivider(color = Color(0xFF2A3952))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "AUTHORITATIVE VERSION",
                            color = Color(0xFF94A3B8),
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace
                        )
                        Text(
                            text = "v${currentPayment.version}",
                            color = Color(0xFF60A5FA),
                            fontSize = 13.sp,
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.Bold
                        )
                    }

                    // Officer clearance status line
                    if (currentPayment.officer_clearance_recorded) {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clip(RoundedCornerShape(8.dp))
                                .background(Color(0xFF064E3B))
                                .padding(10.dp)
                        ) {
                            Column {
                                Text(
                                    text = "✓ Officer clearance recorded",
                                    color = Color(0xFF34D399),
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.Bold
                                )
                                if (!currentPayment.officer_clearance_note.isNullOrBlank()) {
                                    Text(
                                        text = currentPayment.officer_clearance_note ?: "",
                                        color = Color(0xFFA7F3D0),
                                        fontSize = 11.sp
                                    )
                                }
                            }
                        }
                    }

                    // Safety call lines from backend
                    currentPayment.call_status_lines.forEach { line ->
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("📞", fontSize = 13.sp)
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(
                                text = line,
                                color = Color(0xFF93C5FD),
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Medium
                            )
                        }
                    }
                }
            }

            // Pending Cancel Banner (if cancel was requested offline)
            if (pendingCancel != null && pendingCancel?.caseId == currentPayment.case_id) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF451A03)),
                    border = CardDefaults.outlinedCardBorder().copy(brush = androidx.compose.ui.graphics.SolidColor(Color(0xFFF59E0B)))
                ) {
                    Row(
                        modifier = Modifier.padding(14.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(18.dp),
                            color = Color(0xFFFBBF24),
                            strokeWidth = 2.dp
                        )
                        Spacer(modifier = Modifier.width(10.dp))
                        Column {
                            Text(
                                text = "CANCEL REQUESTED — not yet confirmed",
                                color = Color(0xFFFBBF24),
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace
                            )
                            Text(
                                text = "Will automatically confirm once reconnected to bank.",
                                color = Color(0xFFFDE68A),
                                fontSize = 11.sp
                            )
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Action Buttons
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(10.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // "Cancel payment" - ALWAYS VISIBLE WHILE PAUSED!
                Button(
                    onClick = {
                        val caseId = currentPayment.case_id ?: currentPayment.payment_id
                        SyncRepository.requestCancelPayment(
                            caseId = caseId,
                            paymentId = currentPayment.payment_id,
                            currentVersion = currentPayment.version,
                            scope = coroutineScope
                        )
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(50.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFDC2626)),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Text(
                        text = "Cancel payment",
                        color = Color.White,
                        fontSize = 15.sp,
                        fontWeight = FontWeight.Bold
                    )
                }

                // "I still want to send" -> caution dialog
                OutlinedButton(
                    onClick = {
                        showCautionDialog = true
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(50.dp),
                    colors = ButtonDefaults.outlinedButtonColors(
                        containerColor = Color(0xFF1E293B),
                        contentColor = Color.White
                    ),
                    border = ButtonDefaults.outlinedButtonBorder.copy(
                        brush = androidx.compose.ui.graphics.SolidColor(Color(0xFF334155))
                    ),
                    shape = RoundedCornerShape(12.dp),
                    enabled = !isOffline && !actionInProgress
                ) {
                    if (actionInProgress) {
                        CircularProgressIndicator(modifier = Modifier.size(18.dp), color = Color.White, strokeWidth = 2.dp)
                    } else {
                        Text(
                            text = "I still want to send",
                            fontSize = 14.sp,
                            fontWeight = FontWeight.SemiBold
                        )
                    }
                }

                Spacer(modifier = Modifier.height(4.dp))

                // Small link "Need help?"
                Text(
                    text = "Need help?",
                    color = if (isOffline) Color(0xFF64748B) else Color(0xFF60A5FA),
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Medium,
                    modifier = Modifier.clickable(enabled = !isOffline && !actionInProgress) {
                        val caseId = currentPayment.case_id ?: currentPayment.payment_id
                        coroutineScope.launch {
                            val res = SyncRepository.requestHelp(caseId)
                            res.onSuccess { msg ->
                                helpDialogMessage = msg
                            }
                        }
                    }
                )
            }
        }
    }

    // Caution Dialog for "I still want to send"
    if (showCautionDialog) {
        AlertDialog(
            onDismissRequest = { showCautionDialog = false },
            title = {
                Text(
                    text = "Security Caution",
                    color = Color.White,
                    fontWeight = FontWeight.Bold
                )
            },
            text = {
                Text(
                    text = "Real police and courts never ask you to transfer money. Continue?",
                    color = Color(0xFFCBD5E1),
                    fontSize = 15.sp,
                    lineHeight = 20.sp
                )
            },
            confirmButton = {
                Button(
                    onClick = {
                        showCautionDialog = false
                        val caseId = currentPayment.case_id ?: currentPayment.payment_id
                        coroutineScope.launch {
                            val res = SyncRepository.reconfirmPayment(caseId, currentPayment.version)
                            res.onSuccess { answer ->
                                if (answer.confirmed) {
                                    onNavigateToResult(currentPayment.copy(state = "EXECUTED"))
                                } else {
                                    backendAnswerDialog = answer.message
                                }
                            }.onFailure { err ->
                                backendAnswerDialog = err.message ?: "Conditions are not yet met."
                            }
                        }
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF10B981))
                ) {
                    Text("Continue", color = Color(0xFF042F2E), fontWeight = FontWeight.Bold)
                }
            },
            dismissButton = {
                OutlinedButton(
                    onClick = { showCautionDialog = false },
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFFCBD5E1))
                ) {
                    Text("Cancel")
                }
            },
            containerColor = Color(0xFF1E293B)
        )
    }

    // Backend's answer dialog for reconfirm
    if (backendAnswerDialog != null) {
        AlertDialog(
            onDismissRequest = { backendAnswerDialog = null },
            title = {
                Text("Verification Status", color = Color.White, fontWeight = FontWeight.Bold)
            },
            text = {
                Text(backendAnswerDialog ?: "", color = Color(0xFFCBD5E1), fontSize = 14.sp)
            },
            confirmButton = {
                Button(
                    onClick = { backendAnswerDialog = null },
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF10B981))
                ) {
                    Text("Understood", color = Color(0xFF042F2E), fontWeight = FontWeight.Bold)
                }
            },
            containerColor = Color(0xFF1E293B)
        )
    }

    // "Need help?" response dialog
    if (helpDialogMessage != null) {
        AlertDialog(
            onDismissRequest = { helpDialogMessage = null },
            title = {
                Text("Support Request", color = Color.White, fontWeight = FontWeight.Bold)
            },
            text = {
                Text(helpDialogMessage ?: "A bank officer will call you.", color = Color(0xFFCBD5E1), fontSize = 14.sp)
            },
            confirmButton = {
                Button(
                    onClick = { helpDialogMessage = null },
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF10B981))
                ) {
                    Text("OK", color = Color(0xFF042F2E), fontWeight = FontWeight.Bold)
                }
            },
            containerColor = Color(0xFF1E293B)
        )
    }

    // End State Notice Dialog
    if (endStateNotice != null) {
        AlertDialog(
            onDismissRequest = { SyncRepository.clearEndStateNotice() },
            title = {
                Text("Payment Notice", color = Color.White, fontWeight = FontWeight.Bold)
            },
            text = {
                Text(endStateNotice ?: "", color = Color(0xFFCBD5E1), fontSize = 14.sp)
            },
            confirmButton = {
                Button(
                    onClick = { SyncRepository.clearEndStateNotice() },
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF10B981))
                ) {
                    Text("OK", color = Color(0xFF042F2E), fontWeight = FontWeight.Bold)
                }
            },
            containerColor = Color(0xFF1E293B)
        )
    }
}

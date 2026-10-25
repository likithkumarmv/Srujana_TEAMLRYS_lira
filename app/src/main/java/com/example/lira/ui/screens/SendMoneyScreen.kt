package com.example.lira.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.lira.data.PayeeItem
import com.example.lira.data.PaymentItem
import com.example.lira.data.SyncRepository
import com.example.lira.ui.components.IndianKeypad
import com.example.lira.ui.components.OfflineBanner
import com.example.lira.ui.components.PermanentSimulationBanner
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SendMoneyScreen(
    onNavigateBack: () -> Unit,
    onNavigateToPaused: (PaymentItem) -> Unit,
    onNavigateToResult: (PaymentItem) -> Unit
) {
    val coroutineScope = rememberCoroutineScope()
    val payees by SyncRepository.payees.collectAsState()
    val isOffline by SyncRepository.isOffline.collectAsState()
    val offlineText by SyncRepository.offlineBannerText.collectAsState()
    val actionInProgress by SyncRepository.actionInProgress.collectAsState()

    var selectedPayee by remember {
        mutableStateOf<PayeeItem?>(
            payees.firstOrNull { it.name.contains("Bharathi", ignoreCase = true) } ?: payees.firstOrNull()
        )
    }

    LaunchedEffect(payees) {
        if (selectedPayee == null && payees.isNotEmpty()) {
            selectedPayee = payees.firstOrNull { it.name.contains("Bharathi", ignoreCase = true) } ?: payees.first()
        }
    }

    var amountString by remember { mutableStateOf("850000") }
    var purpose by remember { mutableStateOf("Court Security Deposit Guarantee") }
    var errorMessage by remember { mutableStateOf<String?>(null) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF090D16))
    ) {
        PermanentSimulationBanner()

        if (isOffline && offlineText != null) {
            OfflineBanner(text = offlineText ?: "Offline")
        }

        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 18.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
            contentPadding = PaddingValues(top = 12.dp, bottom = 24.dp)
        ) {
            // Header
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    IconButton(onClick = onNavigateBack) {
                        Text("←", color = Color.White, fontSize = 22.sp)
                    }
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = "Send Money",
                        color = Color.White,
                        fontSize = 20.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            // Payee Selector Card
            item {
                Text(
                    text = "SELECT RECIPIENT",
                    color = Color(0xFF94A3B8),
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 0.5.sp
                )
                Spacer(modifier = Modifier.height(6.dp))

                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    val defaultPayees = if (payees.isEmpty()) listOf(
                        PayeeItem("P-1", "Apex Cloud Services", "ACC-9912-1042", "Verified", "Routine IT bill · Safe"),
                        PayeeItem("P-2", "Bharathi Industrial Supplies", "ACC-8841-2091", "Flagged Beneficiary", "Changed beneficiary · High risk demo"),
                        PayeeItem("P-3", "National Cyber Crime Escrow", "ACC-9902-8811", "Threat", "Simulated police/court scam")
                    ) else payees

                    defaultPayees.forEach { payee ->
                        val isSelected = selectedPayee?.name == payee.name
                        Card(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable { selectedPayee = payee },
                            shape = RoundedCornerShape(12.dp),
                            colors = CardDefaults.cardColors(
                                containerColor = if (isSelected) Color(0xFF132B24) else Color(0xFF131D2E)
                            ),
                            border = CardDefaults.outlinedCardBorder().copy(
                                brush = androidx.compose.ui.graphics.SolidColor(
                                    if (isSelected) Color(0xFF10B981) else Color(0xFF26354D)
                                )
                            )
                        ) {
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(12.dp),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Column(modifier = Modifier.weight(1f)) {
                                    Text(
                                        text = payee.name,
                                        color = Color.White,
                                        fontSize = 14.sp,
                                        fontWeight = FontWeight.Bold
                                    )
                                    Text(
                                        text = "${payee.account} · ${payee.description}",
                                        color = Color(0xFF94A3B8),
                                        fontSize = 11.sp
                                    )
                                }
                                if (isSelected) {
                                    Text("✓", color = Color(0xFF10B981), fontSize = 16.sp, fontWeight = FontWeight.Bold)
                                }
                            }
                        }
                    }
                }
            }

            // Amount Display Card
            item {
                val amountDouble = amountString.toDoubleOrNull() ?: 0.0
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF131D2E)),
                    border = CardDefaults.outlinedCardBorder().copy(brush = androidx.compose.ui.graphics.SolidColor(Color(0xFF26354D)))
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(18.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(
                            text = "AMOUNT (INR)",
                            color = Color(0xFF94A3B8),
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = SyncRepository.formatInr(amountDouble),
                            color = Color.White,
                            fontSize = 34.sp,
                            fontWeight = FontWeight.ExtraBold
                        )

                        Spacer(modifier = Modifier.height(10.dp))

                        // Quick Presets
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(6.dp)
                        ) {
                            listOf("9999", "10000", "50000", "850000").forEach { preset ->
                                val label = when (preset) {
                                    "9999" -> "₹9,999"
                                    "10000" -> "₹10,000"
                                    "50000" -> "₹50,000"
                                    else -> "₹8,50,000"
                                }
                                OutlinedButton(
                                    onClick = { amountString = preset },
                                    modifier = Modifier.weight(1f),
                                    contentPadding = PaddingValues(horizontal = 4.dp, vertical = 4.dp),
                                    shape = RoundedCornerShape(8.dp),
                                    colors = ButtonDefaults.outlinedButtonColors(
                                        containerColor = if (amountString == preset) Color(0xFF10B981).copy(alpha = 0.2f) else Color(0xFF1E293B),
                                        contentColor = if (amountString == preset) Color(0xFF34D399) else Color(0xFFCBD5E1)
                                    ),
                                    border = ButtonDefaults.outlinedButtonBorder.copy(
                                        brush = androidx.compose.ui.graphics.SolidColor(
                                            if (amountString == preset) Color(0xFF10B981) else Color(0xFF334155)
                                        )
                                    )
                                ) {
                                    Text(label, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                                }
                            }
                        }
                    }
                }
            }

            // Keypad
            item {
                IndianKeypad(
                    onDigit = { digit ->
                        if (amountString.length < 9) {
                            amountString = if (amountString == "0") digit else amountString + digit
                        }
                    },
                    onDelete = {
                        if (amountString.isNotEmpty()) {
                            amountString = amountString.dropLast(1)
                        }
                    },
                    onClear = {
                        amountString = "0"
                    }
                )
            }

            // Purpose / Memo Input
            item {
                OutlinedTextField(
                    value = purpose,
                    onValueChange = { purpose = it },
                    label = { Text("Transfer Purpose / Note") },
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = Color(0xFF10B981),
                        unfocusedBorderColor = Color(0xFF334155),
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White
                    ),
                    shape = RoundedCornerShape(10.dp)
                )
            }

            if (errorMessage != null) {
                item {
                    Text(
                        text = errorMessage ?: "",
                        color = Color(0xFFEF4444),
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Medium
                    )
                }
            }

            // Submit Button
            item {
                val amountDouble = amountString.toDoubleOrNull() ?: 0.0
                Button(
                    onClick = {
                        val payee = selectedPayee ?: return@Button
                        coroutineScope.launch {
                            errorMessage = null
                            val result = SyncRepository.submitPayment(
                                amount = amountDouble,
                                recipientName = payee.name,
                                recipientAccount = payee.account,
                                memo = purpose
                            )

                            result.onSuccess { payment ->
                                if (payment.state == "PAUSED") {
                                    onNavigateToPaused(payment)
                                } else {
                                    onNavigateToResult(payment)
                                }
                            }.onFailure { err ->
                                errorMessage = err.message ?: "Payment request failed"
                            }
                        }
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF10B981)),
                    shape = RoundedCornerShape(12.dp),
                    enabled = !isOffline && !actionInProgress && amountDouble > 0 && selectedPayee != null
                ) {
                    if (actionInProgress) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(20.dp),
                            color = Color(0xFF042F2E),
                            strokeWidth = 2.dp
                        )
                    } else {
                        Text(
                            text = if (isOffline) "Offline — Sending Disabled" else "Confirm & Pay ${SyncRepository.formatInr(amountDouble)}",
                            color = Color(0xFF042F2E),
                            fontWeight = FontWeight.Bold,
                            fontSize = 16.sp
                        )
                    }
                }
            }
        }
    }
}

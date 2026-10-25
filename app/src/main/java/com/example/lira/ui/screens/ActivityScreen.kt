package com.example.lira.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.lira.data.PaymentItem
import com.example.lira.data.SyncRepository
import com.example.lira.ui.components.OfflineBanner
import com.example.lira.ui.components.PaymentStateChip
import com.example.lira.ui.components.PermanentSimulationBanner

@Composable
fun ActivityScreen(
    onNavigateBack: () -> Unit,
    onNavigateToPaused: (PaymentItem) -> Unit,
    onNavigateToResult: (PaymentItem) -> Unit
) {
    val payments by SyncRepository.payments.collectAsState()
    val isOffline by SyncRepository.isOffline.collectAsState()
    val offlineText by SyncRepository.offlineBannerText.collectAsState()

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
            verticalArrangement = Arrangement.spacedBy(12.dp),
            contentPadding = PaddingValues(top = 12.dp, bottom = 24.dp)
        ) {
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
                        text = "Transaction Activity",
                        color = Color.White,
                        fontSize = 20.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            item {
                Text(
                    text = "ALL SIMULATED PAYMENTS (${payments.size})",
                    color = Color(0xFF94A3B8),
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 0.5.sp
                )
            }

            if (payments.isEmpty()) {
                item {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 40.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "No payments recorded yet",
                            color = Color(0xFF64748B),
                            fontSize = 14.sp
                        )
                    }
                }
            } else {
                items(payments, key = { it.effectiveId }) { item ->
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable {
                                if (item.state == "PAUSED") {
                                    onNavigateToPaused(item)
                                } else {
                                    onNavigateToResult(item)
                                }
                            },
                        shape = RoundedCornerShape(12.dp),
                        colors = CardDefaults.cardColors(containerColor = Color(0xFF131D2E)),
                        border = CardDefaults.outlinedCardBorder().copy(brush = androidx.compose.ui.graphics.SolidColor(Color(0xFF26354D)))
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(14.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    text = item.effectiveRecipientName,
                                    color = Color.White,
                                    fontSize = 15.sp,
                                    fontWeight = FontWeight.Bold
                                )
                                Spacer(modifier = Modifier.height(2.dp))
                                Text(
                                    text = "${item.effectiveRecipientAccount} · ${SyncRepository.formatIstIso(item.effectiveCreatedAt)}",
                                    color = Color(0xFF64748B),
                                    fontSize = 11.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                                if (item.one_line_reason.isNotBlank()) {
                                    Spacer(modifier = Modifier.height(4.dp))
                                    Text(
                                        text = item.one_line_reason,
                                        color = Color(0xFF94A3B8),
                                        fontSize = 11.sp,
                                        maxLines = 1
                                    )
                                }
                            }

                            Column(horizontalAlignment = Alignment.End) {
                                Text(
                                    text = SyncRepository.formatInr(item.effectiveAmount),
                                    color = Color.White,
                                    fontSize = 15.sp,
                                    fontWeight = FontWeight.Bold
                                )
                                Spacer(modifier = Modifier.height(4.dp))
                                PaymentStateChip(state = item.state)
                            }
                        }
                    }
                }
            }
        }
    }
}

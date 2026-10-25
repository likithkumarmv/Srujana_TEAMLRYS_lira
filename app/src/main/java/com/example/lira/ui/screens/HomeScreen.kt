package com.example.lira.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.lira.data.CustomerProfile
import com.example.lira.data.PaymentItem
import com.example.lira.data.SyncRepository
import com.example.lira.network.SupabaseAuthManager
import com.example.lira.ui.components.OfflineBanner
import com.example.lira.ui.components.PaymentStateChip
import com.example.lira.ui.components.PermanentSimulationBanner
import kotlinx.coroutines.launch

@Composable
fun HomeScreen(
    onNavigateToSend: () -> Unit,
    onNavigateToActivity: () -> Unit,
    onNavigateToTrustedPerson: () -> Unit,
    onNavigateToPaused: (PaymentItem) -> Unit,
    onNavigateToResult: (PaymentItem) -> Unit,
    onSignOut: () -> Unit
) {
    val coroutineScope = rememberCoroutineScope()
    val profile by SyncRepository.customerProfile.collectAsState()
    val payments by SyncRepository.payments.collectAsState()
    val openPayment by SyncRepository.openPayment.collectAsState()
    val isOffline by SyncRepository.isOffline.collectAsState()
    val offlineText by SyncRepository.offlineBannerText.collectAsState()

    val currentProfile = profile ?: CustomerProfile()
    val trustedPersonText = "Trusted person: ${currentProfile.trusted_person.name}, active from ${currentProfile.trusted_person.active_from}"

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
            verticalArrangement = Arrangement.spacedBy(16.dp),
            contentPadding = PaddingValues(top = 16.dp, bottom = 32.dp)
        ) {
            // Top App Bar / User Profile Row
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(
                            text = "DEMO BANK",
                            color = Color(0xFF10B981),
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace,
                            letterSpacing = 1.sp
                        )
                        Text(
                            text = currentProfile.name,
                            color = Color.White,
                            fontSize = 20.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Text(
                            text = currentProfile.account_number,
                            color = Color(0xFF64748B),
                            fontSize = 12.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }

                    OutlinedButton(
                        onClick = {
                            coroutineScope.launch {
                                SupabaseAuthManager.signOut()
                                onSignOut()
                            }
                        },
                        colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFF94A3B8)),
                        border = ButtonDefaults.outlinedButtonBorder.copy(
                            brush = androidx.compose.ui.graphics.SolidColor(Color(0xFF334155))
                        ),
                        shape = RoundedCornerShape(8.dp),
                        contentPadding = PaddingValues(horizontal = 12.dp, vertical = 6.dp)
                    ) {
                        Text("Sign Out", fontSize = 12.sp)
                    }
                }
            }

            // Primary Account Balance Card
            item {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(18.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF131D2E)),
                    border = CardDefaults.outlinedCardBorder().copy(brush = androidx.compose.ui.graphics.SolidColor(Color(0xFF26354D)))
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(
                                Brush.verticalGradient(
                                    colors = listOf(Color(0xFF16253B), Color(0xFF0F1A2A))
                                )
                            )
                            .padding(20.dp)
                    ) {
                        Text(
                            text = "AVAILABLE BALANCE",
                            color = Color(0xFF94A3B8),
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace,
                            letterSpacing = 1.sp
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = SyncRepository.formatPaise(currentProfile.balance_paise),
                            color = Color.White,
                            fontSize = 32.sp,
                            fontWeight = FontWeight.ExtraBold
                        )

                        Spacer(modifier = Modifier.height(14.dp))
                        HorizontalDivider(color = Color(0xFF2A3952), thickness = 1.dp)
                        Spacer(modifier = Modifier.height(14.dp))

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column {
                                Text(
                                    text = "Reserved for paused payments",
                                    color = Color(0xFFCBD5E1),
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.Medium
                                )
                                Text(
                                    text = SyncRepository.formatPaise(currentProfile.reserved_paise),
                                    color = if (currentProfile.reserved_paise > 0) Color(0xFFFBBF24) else Color(0xFF64748B),
                                    fontSize = 15.sp,
                                    fontWeight = FontWeight.Bold
                                )
                            }

                            if (currentProfile.reserved_paise > 0) {
                                PaymentStateChip(state = "PAUSED")
                            }
                        }
                    }
                }
            }

            // Protection Status Card
            item {
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { onNavigateToTrustedPerson() },
                    shape = RoundedCornerShape(14.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF0F231D)),
                    border = CardDefaults.outlinedCardBorder().copy(brush = androidx.compose.ui.graphics.SolidColor(Color(0xFF134E3A)))
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(14.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Box(
                            modifier = Modifier
                                .size(36.dp)
                                .clip(CircleShape)
                                .background(Color(0xFF064E3B)),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = "🛡️",
                                fontSize = 16.sp
                            )
                        }

                        Spacer(modifier = Modifier.width(12.dp))

                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = "Protection Status",
                                color = Color(0xFF34D399),
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace,
                                letterSpacing = 0.5.sp
                            )
                            Text(
                                text = trustedPersonText,
                                color = Color.White,
                                fontSize = 13.sp,
                                fontWeight = FontWeight.SemiBold
                            )
                        }

                        Text(
                            text = "Manage →",
                            color = Color(0xFF34D399),
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }

            // Active Paused Payment Alert (If open payment exists)
            if (openPayment != null && openPayment?.state == "PAUSED") {
                item {
                    val p = openPayment!!
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onNavigateToPaused(p) },
                        shape = RoundedCornerShape(14.dp),
                        colors = CardDefaults.cardColors(containerColor = Color(0xFF381E08)),
                        border = CardDefaults.outlinedCardBorder().copy(brush = androidx.compose.ui.graphics.SolidColor(Color(0xFFD97706)))
                    ) {
                        Column(
                            modifier = Modifier.padding(16.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Text("⚠️", fontSize = 14.sp)
                                    Spacer(modifier = Modifier.width(6.dp))
                                    Text(
                                        text = "SIMULATED PAYMENT · HELD BY LIRA",
                                        color = Color(0xFFFBBF24),
                                        fontSize = 11.sp,
                                        fontWeight = FontWeight.Bold,
                                        fontFamily = FontFamily.Monospace
                                    )
                                }
                                PaymentStateChip(state = "PAUSED")
                            }

                            Text(
                                text = "Payment to ${p.recipient_name} (${SyncRepository.formatInr(p.amount)}) is held for safety review.",
                                color = Color.White,
                                fontSize = 13.sp,
                                fontWeight = FontWeight.SemiBold
                            )

                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    text = if (p.time_left_s > 0) "Time remaining: ${p.time_left_s}s" else "Awaiting clearance",
                                    color = Color(0xFFFCD34D),
                                    fontSize = 12.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                                Text(
                                    text = "View Status →",
                                    color = Color(0xFFFBBF24),
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.Bold
                                )
                            }
                        }
                    }
                }
            }

            // Action Buttons
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Button(
                        onClick = onNavigateToSend,
                        modifier = Modifier
                            .weight(1f)
                            .height(50.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF10B981)),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Text(
                            text = "💸 Send Money",
                            color = Color(0xFF042F2E),
                            fontWeight = FontWeight.Bold,
                            fontSize = 15.sp
                        )
                    }

                    OutlinedButton(
                        onClick = onNavigateToActivity,
                        modifier = Modifier
                            .weight(1f)
                            .height(50.dp),
                        colors = ButtonDefaults.outlinedButtonColors(
                            containerColor = Color(0xFF1E293B),
                            contentColor = Color.White
                        ),
                        border = ButtonDefaults.outlinedButtonBorder.copy(
                            brush = androidx.compose.ui.graphics.SolidColor(Color(0xFF334155))
                        ),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Text(
                            text = "📜 All Activity",
                            fontWeight = FontWeight.SemiBold,
                            fontSize = 14.sp
                        )
                    }
                }
            }

            // Recent Payments Header
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "RECENT PAYMENTS",
                        color = Color(0xFF94A3B8),
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace,
                        letterSpacing = 0.5.sp
                    )
                    Text(
                        text = "View All",
                        color = Color(0xFF10B981),
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.clickable { onNavigateToActivity() }
                    )
                }
            }

            // Recent Payments List
            val recentItems = payments.take(5)
            if (recentItems.isEmpty()) {
                item {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 24.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "No recent payments recorded",
                            color = Color(0xFF64748B),
                            fontSize = 13.sp
                        )
                    }
                }
            } else {
                items(recentItems, key = { it.effectiveId }) { item ->
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
                                    text = SyncRepository.formatIstIso(item.effectiveCreatedAt),
                                    color = Color(0xFF64748B),
                                    fontSize = 11.sp
                                )
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

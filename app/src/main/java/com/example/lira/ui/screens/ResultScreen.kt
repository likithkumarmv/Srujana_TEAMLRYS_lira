package com.example.lira.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.lira.data.PaymentItem
import com.example.lira.data.SyncRepository
import com.example.lira.ui.components.PaymentStateChip
import com.example.lira.ui.components.PermanentSimulationBanner

@Composable
fun ResultScreen(
    payment: PaymentItem,
    onNavigateHome: () -> Unit
) {
    val isStopped = payment.state == "STOPPED"

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF090D16))
    ) {
        PermanentSimulationBanner()

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            verticalArrangement = Arrangement.SpaceBetween,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Column(
                modifier = Modifier.fillMaxWidth(),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Spacer(modifier = Modifier.height(24.dp))

                // Icon Circle
                Box(
                    modifier = Modifier
                        .size(68.dp)
                        .clip(CircleShape)
                        .background(if (isStopped) Color(0xFF334155) else Color(0xFF064E3B)),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = if (isStopped) "🛑" else "✓",
                        fontSize = 30.sp,
                        color = Color.White
                    )
                }

                Spacer(modifier = Modifier.height(18.dp))

                Text(
                    text = if (isStopped) "PAYMENT STOPPED" else "PAYMENT EXECUTED",
                    color = Color.White,
                    fontSize = 22.sp,
                    fontWeight = FontWeight.ExtraBold,
                    letterSpacing = 1.sp
                )

                Text(
                    text = if (isStopped) "Your money stays in your account." else "Funds transferred successfully.",
                    color = if (isStopped) Color(0xFFF87171) else Color(0xFF34D399),
                    fontSize = 14.sp,
                    fontWeight = FontWeight.SemiBold
                )

                Spacer(modifier = Modifier.height(18.dp))
                PaymentStateChip(state = payment.state)

                Spacer(modifier = Modifier.height(28.dp))

                // Details Card
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF131D2E)),
                    border = CardDefaults.outlinedCardBorder().copy(brush = androidx.compose.ui.graphics.SolidColor(Color(0xFF26354D)))
                ) {
                    Column(
                        modifier = Modifier.padding(18.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text("Amount", color = Color(0xFF94A3B8), fontSize = 13.sp)
                            Text(
                                text = SyncRepository.formatInr(payment.effectiveAmount),
                                color = Color.White,
                                fontSize = 16.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text("Recipient", color = Color(0xFF94A3B8), fontSize = 13.sp)
                            Text(payment.effectiveRecipientName, color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
                        }

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text("Account", color = Color(0xFF94A3B8), fontSize = 13.sp)
                            Text(payment.effectiveRecipientAccount, color = Color(0xFFCBD5E1), fontSize = 13.sp, fontFamily = FontFamily.Monospace)
                        }

                        HorizontalDivider(color = Color(0xFF2A3952))

                        Text("Backend Decision Reason:", color = Color(0xFF94A3B8), fontSize = 12.sp, fontWeight = FontWeight.Bold)
                        Text(
                            text = payment.one_line_reason.ifBlank {
                                if (isStopped) "Payment was cancelled and stopped before execution. Funds remained untouched."
                                else "Standard safety verified payment. Executed without hold."
                            },
                            color = Color(0xFFCBD5E1),
                            fontSize = 13.sp,
                            lineHeight = 18.sp
                        )

                        if (!payment.case_id.isNullOrBlank()) {
                            HorizontalDivider(color = Color(0xFF2A3952))
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Text("LIRA Case Ref", color = Color(0xFF64748B), fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                                Text(payment.case_id, color = Color(0xFF60A5FA), fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                            }
                        }
                    }
                }
            }

            Button(
                onClick = onNavigateHome,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF10B981)),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text(
                    text = "Back to Home",
                    color = Color(0xFF042F2E),
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
}

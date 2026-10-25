package com.example.lira.ui.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.lira.ui.theme.*
import kotlinx.coroutines.launch

@Composable
fun PermanentSimulationBanner() {
    val infiniteTransition = rememberInfiniteTransition(label = "pulse")
    val alpha by infiniteTransition.animateFloat(
        initialValue = 0.4f,
        targetValue = 1.0f,
        animationSpec = infiniteRepeatable(
            animation = tween(1200, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulseAlpha"
    )

    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .statusBarsPadding(),
        color = Color(0xFF0F172A),
        border = null
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 14.dp, vertical = 6.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.Center
        ) {
            Box(
                modifier = Modifier
                    .size(8.dp)
                    .clip(CircleShape)
                    .background(Color(0xFF10B981).copy(alpha = alpha))
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = "SIMULATED PAYMENT · DEMO BANK",
                color = Color(0xFF94A3B8),
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                fontFamily = FontFamily.Monospace,
                letterSpacing = 1.sp
            )
        }
    }
}

@Composable
fun OfflineBanner(
    text: String,
    onRetry: (() -> Unit)? = null
) {
    val coroutineScope = androidx.compose.runtime.rememberCoroutineScope()
    val retryAction = onRetry ?: {
        coroutineScope.launch {
            com.example.lira.data.SyncRepository.checkAndPollSync()
        }
    }

    Surface(
        modifier = Modifier.fillMaxWidth(),
        color = Color(0xFF334155),
        border = null
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 7.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.Center
            ) {
                Box(
                    modifier = Modifier
                        .size(7.dp)
                        .clip(CircleShape)
                        .background(Color(0xFFEF4444))
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = text,
                    color = Color(0xFFF1F5F9),
                    fontSize = 12.sp,
                    fontWeight = FontWeight.SemiBold,
                    textAlign = TextAlign.Center
                )
                Spacer(modifier = Modifier.width(10.dp))
                Surface(
                    shape = RoundedCornerShape(4.dp),
                    color = Color(0xFF475569),
                    modifier = Modifier.clickable { retryAction() }
                ) {
                    Text(
                        text = "Retry",
                        color = Color.White,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp)
                    )
                }
            }
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = "Server: ${com.example.lira.BuildConfig.API_BASE_URL}",
                color = Color(0xFF94A3B8),
                fontSize = 10.sp,
                fontFamily = FontFamily.Monospace,
                textAlign = TextAlign.Center
            )
        }
    }
}

@Composable
fun PaymentStateChip(state: String) {
    val (bgColor, textColor, borderCol, label) = when (state.uppercase()) {
        "EXECUTED" -> Quadruple(Color(0xFF064E3B), Color(0xFF34D399), Color(0xFF059669), "EXECUTED")
        "PAUSED", "SUSPICION_HOLD", "LAG_HOLD" -> Quadruple(Color(0xFF78350F), Color(0xFFFBBF24), Color(0xFFD97706), "PAUSED")
        "STOPPED" -> Quadruple(Color(0xFF1E293B), Color(0xFFF87171), Color(0xFF475569), "STOPPED · money stays")
        else -> Quadruple(Color(0xFF1E293B), Color(0xFF94A3B8), Color(0xFF334155), state)
    }

    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(6.dp))
            .background(bgColor)
            .border(1.dp, borderCol, RoundedCornerShape(6.dp))
            .padding(horizontal = 9.dp, vertical = 4.dp),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = label,
            color = textColor,
            fontSize = 11.sp,
            fontWeight = FontWeight.Bold,
            fontFamily = FontFamily.Monospace,
            letterSpacing = 0.5.sp
        )
    }
}

data class Quadruple<A, B, C, D>(val first: A, val second: B, val third: C, val fourth: D)

@Composable
fun IndianKeypad(
    onDigit: (String) -> Unit,
    onDelete: () -> Unit,
    onClear: () -> Unit
) {
    val keys = listOf(
        listOf("1", "2", "3"),
        listOf("4", "5", "6"),
        listOf("7", "8", "9"),
        listOf("C", "0", "⌫")
    )

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        keys.forEach { row ->
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                row.forEach { key ->
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .height(52.dp)
                            .clip(RoundedCornerShape(10.dp))
                            .background(Color(0xFF1E293B))
                            .border(1.dp, Color(0xFF334155), RoundedCornerShape(10.dp))
                            .clickable {
                                when (key) {
                                    "⌫" -> onDelete()
                                    "C" -> onClear()
                                    else -> onDigit(key)
                                }
                            },
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = key,
                            color = if (key == "C" || key == "⌫") Color(0xFF94A3B8) else Color.White,
                            fontSize = 20.sp,
                            fontWeight = FontWeight.SemiBold
                        )
                    }
                }
            }
        }
    }
}

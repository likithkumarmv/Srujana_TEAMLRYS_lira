package com.example.lira.ui.screens

import androidx.compose.foundation.background
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.lira.data.CustomerProfile
import com.example.lira.data.SyncRepository
import com.example.lira.ui.components.OfflineBanner
import com.example.lira.ui.components.PermanentSimulationBanner
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TrustedPersonScreen(
    onNavigateBack: () -> Unit
) {
    val coroutineScope = rememberCoroutineScope()
    val profile by SyncRepository.customerProfile.collectAsState()
    val isOffline by SyncRepository.isOffline.collectAsState()
    val offlineText by SyncRepository.offlineBannerText.collectAsState()
    val actionInProgress by SyncRepository.actionInProgress.collectAsState()

    val currentProfile = profile ?: CustomerProfile()
    val currentTrusted = currentProfile.trusted_person

    var nameInput by remember { mutableStateOf("") }
    var phoneInput by remember { mutableStateOf("") }
    var noticeMessage by remember { mutableStateOf<String?>(null) }
    var showRevokeDialog by remember { mutableStateOf(false) }

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
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(onClick = onNavigateBack) {
                    Text("←", color = Color.White, fontSize = 22.sp)
                }
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    text = "Trusted Person Protection",
                    color = Color.White,
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold
                )
            }

            // Current Trusted Person Card
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFF0F241C)),
                border = CardDefaults.outlinedCardBorder().copy(brush = androidx.compose.ui.graphics.SolidColor(Color(0xFF134E3A)))
            ) {
                Column(
                    modifier = Modifier.padding(18.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Text(
                        text = "CURRENT TRUSTED PERSON",
                        color = Color(0xFF34D399),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                    Text(
                        text = currentTrusted.name.ifBlank { "None assigned" },
                        color = Color.White,
                        fontSize = 22.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "Active from: ${currentTrusted.active_from}",
                        color = Color(0xFFA7F3D0),
                        fontSize = 13.sp
                    )
                    Text(
                        text = "Contact: ${currentTrusted.phone}",
                        color = Color(0xFF6EE7B7),
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace
                    )

                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "When payments exceed ₹50,000, your trusted person helps verify your safety before funds are disbursed.",
                        color = Color(0xFFCBD5E1),
                        fontSize = 12.sp,
                        lineHeight = 16.sp
                    )
                }
            }

            // Notice after update
            if (noticeMessage != null) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF1E293B)),
                    border = CardDefaults.outlinedCardBorder().copy(brush = androidx.compose.ui.graphics.SolidColor(Color(0xFF3B82F6)))
                ) {
                    Text(
                        text = noticeMessage ?: "",
                        color = Color(0xFF93C5FD),
                        fontSize = 13.sp,
                        fontWeight = FontWeight.SemiBold,
                        modifier = Modifier.padding(14.dp)
                    )
                }
            }

            // Add / Change Form Card
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFF131D2E)),
                border = CardDefaults.outlinedCardBorder().copy(brush = androidx.compose.ui.graphics.SolidColor(Color(0xFF26354D)))
            ) {
                Column(
                    modifier = Modifier.padding(18.dp),
                    verticalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    Text(
                        text = "CHANGE TRUSTED PERSON",
                        color = Color(0xFF94A3B8),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )

                    OutlinedTextField(
                        value = nameInput,
                        onValueChange = { nameInput = it },
                        label = { Text("Trusted Person Full Name") },
                        modifier = Modifier.fillMaxWidth(),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = Color(0xFF10B981),
                            unfocusedBorderColor = Color(0xFF334155),
                            focusedTextColor = Color.White,
                            unfocusedTextColor = Color.White
                        )
                    )

                    OutlinedTextField(
                        value = phoneInput,
                        onValueChange = { phoneInput = it },
                        label = { Text("Phone Number (+91)") },
                        modifier = Modifier.fillMaxWidth(),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = Color(0xFF10B981),
                            unfocusedBorderColor = Color(0xFF334155),
                            focusedTextColor = Color.White,
                            unfocusedTextColor = Color.White
                        )
                    )

                    Button(
                        onClick = {
                            coroutineScope.launch {
                                val res = SyncRepository.updateTrustedPerson(nameInput, phoneInput)
                                res.onSuccess { msg ->
                                    noticeMessage = "Your new trusted person can approve payments after 24 hours."
                                    nameInput = ""
                                    phoneInput = ""
                                }
                            }
                        },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(48.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF10B981)),
                        shape = RoundedCornerShape(10.dp),
                        enabled = !isOffline && !actionInProgress && nameInput.isNotBlank() && phoneInput.isNotBlank()
                    ) {
                        if (actionInProgress) {
                            CircularProgressIndicator(modifier = Modifier.size(20.dp), color = Color(0xFF042F2E))
                        } else {
                            Text("Update Trusted Person", color = Color(0xFF042F2E), fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }

            // Revoke Button
            OutlinedButton(
                onClick = { showRevokeDialog = true },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(48.dp),
                colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFFEF4444)),
                border = ButtonDefaults.outlinedButtonBorder.copy(
                    brush = androidx.compose.ui.graphics.SolidColor(Color(0xFF7F1D1D))
                ),
                shape = RoundedCornerShape(10.dp),
                enabled = !isOffline && currentTrusted.name.isNotBlank()
            ) {
                Text("Revoke Trusted Person", fontWeight = FontWeight.Bold)
            }
        }
    }

    if (showRevokeDialog) {
        AlertDialog(
            onDismissRequest = { showRevokeDialog = false },
            title = { Text("Revoke Trusted Person", color = Color.White) },
            text = { Text("Are you sure you want to remove your trusted person? Your account will have standard safeguards.", color = Color(0xFFCBD5E1)) },
            confirmButton = {
                Button(
                    onClick = {
                        showRevokeDialog = false
                        coroutineScope.launch {
                            SyncRepository.updateTrustedPerson("", "")
                            noticeMessage = "Trusted person removed."
                        }
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFEF4444))
                ) {
                    Text("Revoke", color = Color.White, fontWeight = FontWeight.Bold)
                }
            },
            dismissButton = {
                OutlinedButton(onClick = { showRevokeDialog = false }) {
                    Text("Cancel", color = Color.White)
                }
            },
            containerColor = Color(0xFF1E293B)
        )
    }
}
